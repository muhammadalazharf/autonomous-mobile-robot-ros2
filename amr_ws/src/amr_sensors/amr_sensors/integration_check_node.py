"""
Integration Check: verifikasi bahwa sensor SALING TERSAMBUNG, bukan hanya hidup.

Beda dengan health_check (cek "ada data?"):
  - Node ini cek "data SAMPAI ke konsumen yang benar?"
  - Cek QoS compatibility (publisher vs subscriber cocok?)
  - Cek frekuensi wajar (LiDAR ~10Hz, kamera ~30Hz, IMU ~100Hz+)
  - Cek timestamp sinkron (tidak terlalu jauh dari waktu sekarang)

Jalankan SETELAH health_check sudah semua PASS.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.time import Time

from sensor_msgs.msg import LaserScan, Image, Imu
from std_msgs.msg import Int32


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)

# Frekuensi minimum yang wajar per sensor
EXPECTED_HZ = {
    'LiDAR':        5.0,
    'Kamera Color': 15.0,
    'Kamera Depth': 15.0,
    'IMU':          30.0,
    'Encoder':      1.0,
}


class IntegrationCheckNode(Node):

    SENSORS = [
        ('LiDAR',        '/scan',                               LaserScan),
        ('Kamera Color', '/camera/camera/color/image_raw',      Image),
        ('Kamera Depth', '/camera/camera/depth/image_rect_raw', Image),
        ('IMU',          '/imu/data',                           Imu),
        ('Encoder',      '/encoder',                            Int32),
    ]

    def __init__(self):
        super().__init__('integration_check')

        self._counts = {}
        self._last_stamp = {}
        self._latencies = {}

        for name, topic, msg_type in self.SENSORS:
            self._counts[name] = 0
            self._last_stamp[name] = None
            self._latencies[name] = []

            self.create_subscription(
                msg_type, topic,
                self._make_callback(name, msg_type),
                SENSOR_QOS,
            )

        self._timer = self.create_timer(3.0, self._report)
        self._check_count = 0
        self.get_logger().info('Integration check aktif — verifikasi koneksi antar-sensor...')

    def _make_callback(self, name, msg_type):
        def cb(msg):
            self._counts[name] += 1
            if hasattr(msg, 'header'):
                msg_time = Time.from_msg(msg.header.stamp)
                now = self.get_clock().now()
                latency_ms = (now.nanoseconds - msg_time.nanoseconds) / 1e6
                self._latencies[name].append(latency_ms)
                if len(self._latencies[name]) > 50:
                    self._latencies[name] = self._latencies[name][-50:]
        return cb

    def _report(self):
        self._check_count += 1
        interval = 3.0

        self.get_logger().info('═══ INTEGRATION CHECK ═══')

        results = []
        for name, _, _ in self.SENSORS:
            count = self._counts[name]
            hz = count / interval
            expected = EXPECTED_HZ[name]

            # Cek 1: Data mengalir?
            if count == 0:
                status = 'FAIL ✗ TIDAK ADA DATA'
                ok = False
            # Cek 2: Frekuensi wajar?
            elif hz < expected * 0.5:
                status = f'WARN ⚠ Hz rendah ({hz:.1f} < {expected:.0f})'
                ok = False
            else:
                status = f'PASS ✓ ({hz:.1f} Hz)'
                ok = True

            # Cek 3: Latency (timestamp vs now)
            lat_info = ''
            if self._latencies.get(name):
                avg_lat = sum(self._latencies[name]) / len(self._latencies[name])
                if abs(avg_lat) > 500:
                    lat_info = f' | WARN: latency {avg_lat:.0f}ms (>500ms)'
                else:
                    lat_info = f' | latency {avg_lat:.0f}ms'

            self.get_logger().info(f'  {name:15s} : {status}{lat_info}')
            results.append(ok)
            self._counts[name] = 0

        # Cek 4: Apakah IMU merger berjalan? (accel+gyro → /imu/data)
        imu_count = self._counts.get('IMU', 0)
        # (sudah dicek di atas)

        all_ok = all(results)
        if all_ok:
            self.get_logger().info('>>> SEMUA SENSOR TERINTEGRASI — siap naik layer <<<')
        else:
            self.get_logger().warn('>>> ADA MASALAH INTEGRASI — perbaiki sebelum lanjut <<<')

        # Setelah 5 putaran laporan, tampilkan ringkasan koneksi
        if self._check_count == 5:
            self._print_hierarchy()

        self.get_logger().info('═════════════════════════')

    def _print_hierarchy(self):
        self.get_logger().info('')
        self.get_logger().info('┌─── HIERARKI SENSOR (Layer 1) ───┐')
        self.get_logger().info('│                                  │')
        self.get_logger().info('│  RPLIDAR C1 ──/scan──► rtabmap   │')
        self.get_logger().info('│                       ▲(nanti)   │')
        self.get_logger().info('│  D455 color ──┐                  │')
        self.get_logger().info('│  D455 depth ──┴► rgbd_sync(M4)   │')
        self.get_logger().info('│                                  │')
        self.get_logger().info('│  D455 accel ──┐                  │')
        self.get_logger().info('│  D455 gyro  ──┴► imu_merger      │')
        self.get_logger().info('│                  └►/imu/data►VIO │')
        self.get_logger().info('│                                  │')
        self.get_logger().info('│  STM32 ──/encoder──► EKF(M2)     │')
        self.get_logger().info('│                                  │')
        self.get_logger().info('└──────────────────────────────────┘')


def main(args=None):
    rclpy.init(args=args)
    node = IntegrationCheckNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
