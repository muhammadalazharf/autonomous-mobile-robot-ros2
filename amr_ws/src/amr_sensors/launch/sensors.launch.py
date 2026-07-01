"""
Launch semua sensor AMR.

ATURAN MODUL 3: Tidak ada parameter di file ini.
Semua parameter ada di config/sensors.yaml (satu tempat, satu kebenaran).

Cara pakai di NUC:
  ros2 launch amr_sensors sensors.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_sensors'),
        'config', 'sensors.yaml')

    rplidar = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar',
        parameters=[config],
    )

    realsense = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        name='camera',
        namespace='camera',
        parameters=[config],
    )

    imu_merger = Node(
        package='amr_sensors',
        executable='imu_merger',
        name='imu_merger',
    )

    health_check = Node(
        package='amr_sensors',
        executable='health_check',
        name='health_check',
    )

    return LaunchDescription([
        rplidar,
        realsense,
        imu_merger,
        health_check,
    ])
