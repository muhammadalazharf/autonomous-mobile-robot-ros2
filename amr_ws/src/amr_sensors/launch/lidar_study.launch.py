"""
Launch khusus: LiDAR saja + node X,Y calculator + RViz2.

ATURAN MODUL 3: Parameter ada di config/sensors.yaml.
Hanya launch argument 'record' yang boleh override (karena ini input user).

Cara pakai:
  ros2 launch amr_sensors lidar_study.launch.py
  ros2 launch amr_sensors lidar_study.launch.py record:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_sensors'),
        'config', 'sensors.yaml')

    record_arg = DeclareLaunchArgument(
        'record', default_value='false',
        description='Rekam data LiDAR ke CSV (true/false)')

    rplidar = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar',
        parameters=[config],
    )

    lidar_xy = Node(
        package='amr_sensors',
        executable='lidar_xy',
        name='lidar_xy',
        parameters=[config, {'record': LaunchConfiguration('record')}],
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
    )

    return LaunchDescription([
        record_arg,
        rplidar,
        lidar_xy,
        rviz2,
    ])
