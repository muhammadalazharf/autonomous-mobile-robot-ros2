"""
STM32 Serial Bridge — Layer 1, interface motor + encoder.

Membaca encoder dari STM32 via serial → publish /encoder (Int32, BestEffort).
Menerima /cmd_vel → konversi ke V:{pwm},S:{angle} → kirim ke STM32.

Protokol serial STM32 → NUC:
  E:{delta_encoder}\n     — delta pulsa encoder sejak laporan terakhir

Protokol NUC → STM32:
  V:{pwm},S:{angle}\n     — PWM (0–255) dan sudut kemudi (derajat)

CATATAN KRITIS (dari HANDOVER_REBUILD):
  - Tanda encoder HARUS diverifikasi di hardware:
    Dorong robot maju → /encoder harus NAIK (positif).
    Kalau turun, balik tanda di baris yang ditandai.
  - Ackermann: tidak ada perintah mundur (keep vx >= 0 ke STM32)
    kecuali firmware sudah support PWM negatif.
"""

import math
import threading
import serial

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import Int32
from geometry_msgs.msg import Twist


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)

CMD_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)


class Stm32BridgeNode(Node):

    def __init__(self):
        super().__init__('stm32_bridge')

        self.declare_parameter('serial_port', '/dev/stm32')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('wheelbase', 0.5)
        self.declare_parameter('max_pwm', 255)
        self.declare_parameter('max_speed', 0.5)
        self.declare_parameter('max_steering_angle', 30.0)

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        self._wheelbase = self.get_parameter('wheelbase').value
        self._max_pwm = self.get_parameter('max_pwm').value
        self._max_speed = self.get_parameter('max_speed').value
        self._max_steer = self.get_parameter('max_steering_angle').value

        self._ser = None
        try:
            self._ser = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f'Serial terhubung: {port} @ {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'GAGAL buka serial {port}: {e}')

        self._encoder_pub = self.create_publisher(Int32, '/encoder', SENSOR_QOS)

        self._cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self._on_cmd_vel, CMD_QOS)

        if self._ser is not None:
            self._read_thread = threading.Thread(
                target=self._serial_read_loop, daemon=True)
            self._read_thread.start()

        self.get_logger().info('STM32 bridge aktif')

    def _serial_read_loop(self):
        while rclpy.ok():
            try:
                line = self._ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('E:'):
                    # ▼▼▼ VERIFIKASI TANDA DI NUC ▼▼▼
                    # Dorong robot maju → /encoder harus NAIK (positif)
                    # Kalau turun, ubah baris berikut: delta = -int(line[2:])
                    delta = int(line[2:])
                    msg = Int32()
                    msg.data = delta
                    self._encoder_pub.publish(msg)
            except ValueError:
                pass
            except serial.SerialException as e:
                self.get_logger().warn(
                    f'Serial read error: {e}', throttle_duration_sec=5.0)

    def _on_cmd_vel(self, msg: Twist):
        if self._ser is None:
            return

        vx = msg.linear.x
        wz = msg.angular.z

        # Map kecepatan → PWM (0–255, hanya positif)
        pwm = int(abs(vx) / self._max_speed * self._max_pwm)
        pwm = max(0, min(pwm, self._max_pwm))

        # Ackermann: steering angle dari geometry kendaraan
        if abs(vx) > 0.01:
            angle_rad = math.atan(self._wheelbase * wz / vx)
        else:
            angle_rad = 0.0
        angle_deg = math.degrees(angle_rad)
        angle_deg = max(-self._max_steer, min(angle_deg, self._max_steer))

        try:
            cmd = f'V:{pwm},S:{angle_deg:.1f}\n'
            self._ser.write(cmd.encode('utf-8'))
        except serial.SerialException as e:
            self.get_logger().warn(
                f'Serial write error: {e}', throttle_duration_sec=5.0)

    def destroy_node(self):
        if self._ser is not None and self._ser.is_open:
            self._ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Stm32BridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
