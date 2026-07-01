"""
IMU Merger: gabung accelerometer + gyroscope dari RealSense D455
menjadi satu topic /imu/data (sensor_msgs/Imu).

Di sistem lama, node ini TIDAK di-launch oleh bringup (jebakan #7 handover),
sehingga IMU mati dan VIO tidak punya "tambalan" saat kamera buta.

Di sistem baru: node ini WAJIB hidup sebelum VIO dinyalakan.
QoS: BestEffort (sensor cepat, 100-200 Hz).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Imu
from message_filters import ApproximateTimeSynchronizer, Subscriber


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)


class ImuMergerNode(Node):

    def __init__(self):
        super().__init__('imu_merger')

        self._pub = self.create_publisher(Imu, '/imu/data', SENSOR_QOS)

        self._sub_accel = Subscriber(
            self, Imu, '/camera/camera/accel/sample', qos_profile=SENSOR_QOS)
        self._sub_gyro = Subscriber(
            self, Imu, '/camera/camera/gyro/sample', qos_profile=SENSOR_QOS)

        self._sync = ApproximateTimeSynchronizer(
            [self._sub_accel, self._sub_gyro],
            queue_size=20,
            slop=0.05,
        )
        self._sync.registerCallback(self._on_sync)

        self.get_logger().info('IMU Merger aktif — menunggu accel + gyro...')

    def _on_sync(self, accel_msg, gyro_msg):
        merged = Imu()
        merged.header = gyro_msg.header
        merged.header.frame_id = 'camera_imu_optical_frame'

        merged.angular_velocity = gyro_msg.angular_velocity
        merged.angular_velocity_covariance = gyro_msg.angular_velocity_covariance

        merged.linear_acceleration = accel_msg.linear_acceleration
        merged.linear_acceleration_covariance = accel_msg.linear_acceleration_covariance

        # Orientasi tidak tersedia dari raw IMU (belum ada AHRS filter)
        merged.orientation_covariance[0] = -1.0

        self._pub.publish(merged)


def main(args=None):
    rclpy.init(args=args)
    node = ImuMergerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
