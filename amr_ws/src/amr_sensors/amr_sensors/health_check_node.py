"""
Health-check node: verifikasi semua sensor hidup SEBELUM mapping/navigasi.

Ini obat langsung untuk kegagalan 7.1 sistem lama:
"Tidak dilihat integrasi sensor sudah tersambung atau belum."

Node ini subscribe ke 5 topic sensor dengan QoS yang BENAR (BestEffort),
hitung apakah data mengalir, dan cetak PASS/FAIL per sensor setiap 2 detik.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import LaserScan, Image, Imu
from std_msgs.msg import Int32


# === KONTRAK QoS — dirancang oleh mahasiswa, dieksekusi oleh profesor ===
# Aturan: semua sensor = BestEffort (data sering, butuh terbaru bukan lengkap)
SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)


class HealthCheckNode(Node):

    # Daftar sensor wajib: (nama tampilan, topic, tipe pesan)
    SENSORS = [
        ('LiDAR',        '/scan',                          LaserScan),
        ('Kamera Color', '/camera/camera/color/image_raw', Image),
        ('Kamera Depth', '/camera/camera/depth/image_rect_raw', Image),
        ('IMU',          '/imu/data',                      Imu),
        ('Encoder',      '/encoder',                       Int32),
    ]

    def __init__(self):
        super().__init__('health_check')

        self._counts = {}
        self._subs = []

        for name, topic, msg_type in self.SENSORS:
            self._counts[name] = 0
            sub = self.create_subscription(
                msg_type,
                topic,
                self._make_callback(name),
                SENSOR_QOS,
            )
            self._subs.append(sub)

        self._timer = self.create_timer(2.0, self._report)
        self.get_logger().info('Health-check aktif. Menunggu data sensor...')

    def _make_callback(self, name):
        def cb(msg):
            self._counts[name] += 1
        return cb

    def _report(self):
        self.get_logger().info('─── HEALTH CHECK ───')
        all_ok = True
        for name, _, _ in self.SENSORS:
            count = self._counts[name]
            status = 'PASS ✓' if count > 0 else 'FAIL ✗'
            hz = count / 2.0
            self.get_logger().info(f'  {name:15s} : {status}  ({hz:.1f} Hz)')
            if count == 0:
                all_ok = False
            self._counts[name] = 0

        if all_ok:
            self.get_logger().info('>>> SEMUA SENSOR HIDUP — boleh lanjut mapping <<<')
        else:
            self.get_logger().warn('>>> ADA SENSOR MATI — JANGAN mulai mapping! <<<')
        self.get_logger().info('────────────────────')


def main(args=None):
    rclpy.init(args=args)
    node = HealthCheckNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
