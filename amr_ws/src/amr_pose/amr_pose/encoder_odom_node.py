"""
Encoder Odometry — ubah pulsa encoder mentah menjadi nav_msgs/Odometry.

Peran: INPUT LEMAH ke EKF. Bukan sumber pose utama.
Kovarians BESAR = "aku curiga padamu, encoder."

Hanya menyediakan kecepatan maju (vx). Posisi dan heading
diserahkan ke VIO yang lebih akurat.

PENTING: tanda (sign) encoder harus diverifikasi di NUC!
  Dorong robot maju → /encoder harus NAIK (positif).
  Kalau turun (negatif) → balik tanda di baris yang ditandai.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import Int32
from nav_msgs.msg import Odometry


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)


class EncoderOdomNode(Node):

    def __init__(self):
        super().__init__('encoder_odom')

        self.declare_parameter('wheel_radius', 0.0775)
        self.declare_parameter('pulses_per_revolution', 3858)
        self.declare_parameter('publish_rate', 20.0)

        radius = self.get_parameter('wheel_radius').value
        ppr = self.get_parameter('pulses_per_revolution').value
        self._dist_per_tick = (2.0 * math.pi * radius) / ppr

        self._last_encoder = None
        self._last_time = None
        self._vx = 0.0

        self._sub = self.create_subscription(
            Int32, '/encoder', self._on_encoder, SENSOR_QOS)

        self._pub = self.create_publisher(Odometry, '/encoder_odom', 10)

        rate = self.get_parameter('publish_rate').value
        self._timer = self.create_timer(1.0 / rate, self._publish)

        self.get_logger().info(
            f'Encoder odom aktif — {ppr} PPR, radius {radius}m, '
            f'dist/tick = {self._dist_per_tick:.6f}m')

    def _on_encoder(self, msg: Int32):
        now = self.get_clock().now()

        if self._last_encoder is not None and self._last_time is not None:
            delta_ticks = msg.data - self._last_encoder
            dt = (now.nanoseconds - self._last_time.nanoseconds) / 1e9

            if dt > 0.001:
                # ▼▼▼ VERIFIKASI TANDA DI NUC ▼▼▼
                # Dorong robot maju → delta_ticks harus POSITIF
                # Kalau negatif, ubah baris di bawah menjadi: delta_ticks = -delta_ticks
                delta_dist = delta_ticks * self._dist_per_tick
                self._vx = delta_dist / dt

        self._last_encoder = msg.data
        self._last_time = now

    def _publish(self):
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'

        # Hanya isi kecepatan maju — posisi TIDAK diisi (biar VIO yang handle)
        odom.twist.twist.linear.x = self._vx

        # KOVARIANS BESAR = "aku curiga padamu, encoder"
        # Diagonal: [vx, vy, vz, wx, wy, wz]
        # vx kovarians = 1.0 (besar, artinya: "tebakan ini bisa meleset ±1 m/s")
        odom.twist.covariance[0] = 1.0    # vx — curiga
        odom.twist.covariance[7] = 99.0   # vy — tidak ada data, sangat curiga
        odom.twist.covariance[14] = 99.0  # vz — tidak ada data
        odom.twist.covariance[21] = 99.0  # wx — tidak ada data
        odom.twist.covariance[28] = 99.0  # wy — tidak ada data
        odom.twist.covariance[35] = 99.0  # wz — tidak ada data

        self._pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = EncoderOdomNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
