"""
Master launch — Layer 1 + 2 + 3(localization) + 4: Full navigation stack.

Gerbang: Peta .db sudah ada dari mapping → baru boleh nyalakan ini.

Cara pakai:
  ros2 launch amr_startup layer4_navigation.launch.py database_path:=/home/azhar/maps/lab.db
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    db_arg = DeclareLaunchArgument(
        'database_path',
        description='Path ke peta .db hasil mapping')

    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_sensors'),
                'launch', 'sensors.launch.py')))

    pose = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_pose'),
                'launch', 'pose.launch.py')))

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_mapping'),
                'launch', 'localization.launch.py')),
        launch_arguments={
            'database_path': LaunchConfiguration('database_path'),
        }.items())

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_navigation'),
                'launch', 'nav2.launch.py')))

    return LaunchDescription([db_arg, sensors, pose, localization, nav2])
