"""
LiDAR X,Y Calculator & Recorder.

Fungsi:
1. Subscribe /scan (BestEffort)
2. Tiap laser beam: hitung x,y dari polar (sudut, jarak) → kartesian
3. Publish ke RViz2 sebagai titik-titik berwarna (merah=dekat, hijau=jauh)
4. Tampilkan obstacle terdekat (jarak, sudut, x, y)
5. Rekam data ke CSV jika parameter 'record' = true

Rumus (dari Metode Numerik):
  x = jarak × cos(sudut)
  y = jarak × sin(sudut)
"""

import math
import csv
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)


class LidarXYNode(Node):

    def __init__(self):
        super().__init__('lidar_xy')

        self.declare_parameter('record', False)
        self.declare_parameter('record_dir', os.path.expanduser('~/lidar_data'))
        self.declare_parameter('max_display_range', 12.0)

        self._sub = self.create_subscription(
            LaserScan, '/scan', self._on_scan, SENSOR_QOS)

        self._pub_markers = self.create_publisher(
            MarkerArray, '/lidar_xy/markers', 10)

        self._pub_nearest = self.create_publisher(
            Marker, '/lidar_xy/nearest', 10)

        self._csv_file = None
        self._csv_writer = None
        self._scan_count = 0

        if self.get_parameter('record').value:
            self._setup_csv()

        self.get_logger().info('LiDAR X,Y node aktif — visualisasi + rekam data')

    def _setup_csv(self):
        record_dir = os.path.expanduser(self.get_parameter('record_dir').value)
        os.makedirs(record_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(record_dir, f'lidar_{timestamp}.csv')
        self._csv_file = open(path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow([
            'scan_id', 'beam_index', 'sudut_rad', 'sudut_deg',
            'jarak_m', 'x_m', 'y_m',
        ])
        self.get_logger().info(f'Rekam data ke: {path}')

    def _on_scan(self, msg: LaserScan):
        self._scan_count += 1
        max_range = self.get_parameter('max_display_range').value

        marker_array = MarkerArray()

        # === Marker POINTS: semua titik x,y berwarna ===
        points_marker = Marker()
        points_marker.header = msg.header
        points_marker.ns = 'lidar_xy_points'
        points_marker.id = 0
        points_marker.type = Marker.POINTS
        points_marker.action = Marker.ADD
        points_marker.scale.x = 0.03
        points_marker.scale.y = 0.03

        nearest_range = float('inf')
        nearest_angle = 0.0
        nearest_x = 0.0
        nearest_y = 0.0

        for i, jarak in enumerate(msg.ranges):
            if jarak < msg.range_min or jarak > msg.range_max:
                continue
            if math.isinf(jarak) or math.isnan(jarak):
                continue

            sudut = msg.angle_min + i * msg.angle_increment

            # === INTI: polar → kartesian ===
            x = jarak * math.cos(sudut)
            y = jarak * math.sin(sudut)

            point = Point()
            point.x = x
            point.y = y
            point.z = 0.0
            points_marker.points.append(point)

            # Warna: merah (dekat/bahaya) → kuning → hijau (jauh/aman)
            ratio = min(jarak / max_range, 1.0)
            color = ColorRGBA()
            color.a = 1.0
            if ratio < 0.3:
                color.r = 1.0
                color.g = ratio / 0.3
                color.b = 0.0
            elif ratio < 0.6:
                color.r = 1.0 - (ratio - 0.3) / 0.3
                color.g = 1.0
                color.b = 0.0
            else:
                color.r = 0.0
                color.g = 1.0
                color.b = (ratio - 0.6) / 0.4
            points_marker.colors.append(color)

            # Cari obstacle terdekat
            if jarak < nearest_range:
                nearest_range = jarak
                nearest_angle = sudut
                nearest_x = x
                nearest_y = y

            # Rekam ke CSV
            if self._csv_writer and self._scan_count % 10 == 0:
                self._csv_writer.writerow([
                    self._scan_count, i,
                    f'{sudut:.4f}', f'{math.degrees(sudut):.1f}',
                    f'{jarak:.3f}', f'{x:.3f}', f'{y:.3f}',
                ])

        marker_array.markers.append(points_marker)
        self._pub_markers.publish(marker_array)

        # === Marker obstacle terdekat: bola merah + teks jarak ===
        if nearest_range < float('inf'):
            nearest_marker = Marker()
            nearest_marker.header = msg.header
            nearest_marker.ns = 'lidar_nearest'
            nearest_marker.id = 0
            nearest_marker.type = Marker.TEXT_VIEW_FACING
            nearest_marker.action = Marker.ADD
            nearest_marker.pose.position.x = nearest_x
            nearest_marker.pose.position.y = nearest_y
            nearest_marker.pose.position.z = 0.15
            nearest_marker.scale.z = 0.12
            nearest_marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0)
            nearest_marker.text = (
                f'TERDEKAT: {nearest_range:.2f}m\n'
                f'sudut: {math.degrees(nearest_angle):.0f} deg\n'
                f'x={nearest_x:.2f} y={nearest_y:.2f}'
            )
            self._pub_nearest.publish(nearest_marker)

            if self._scan_count % 50 == 0:
                self.get_logger().info(
                    f'Obstacle terdekat: {nearest_range:.2f}m '
                    f'@ {math.degrees(nearest_angle):.0f}° '
                    f'(x={nearest_x:.2f}, y={nearest_y:.2f})'
                )

    def destroy_node(self):
        if self._csv_file:
            self._csv_file.close()
            self.get_logger().info('File CSV ditutup.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = LidarXYNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
