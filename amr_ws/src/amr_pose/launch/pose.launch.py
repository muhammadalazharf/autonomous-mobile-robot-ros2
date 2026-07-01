"""
Launch Layer 2: Pose Estimation (EKF + encoder).

ATURAN MODUL 3: Semua parameter di config/*.yaml.
  - config/encoder.yaml → parameter encoder
  - config/ekf.yaml     → konfigurasi EKF (sumber, kovarians)

Prasyarat: Layer 1 (sensor) harus sudah PASS.

Cara pakai:
  ros2 launch amr_pose pose.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pose_config_dir = get_package_share_directory('amr_pose')

    encoder_config = os.path.join(pose_config_dir, 'config', 'encoder.yaml')
    ekf_config = os.path.join(pose_config_dir, 'config', 'ekf.yaml')

    encoder_odom = Node(
        package='amr_pose',
        executable='encoder_odom',
        name='encoder_odom',
        parameters=[encoder_config],
    )

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        parameters=[ekf_config],
    )

    return LaunchDescription([
        encoder_odom,
        ekf,
    ])
