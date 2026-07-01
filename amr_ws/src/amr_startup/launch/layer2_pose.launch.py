"""
Master launch — Layer 1 + 2: Sensor + Pose (EKF).

Gerbang: Layer 1 PASS → baru boleh nyalakan ini.

Cara pakai:
  ros2 launch amr_startup layer2_pose.launch.py
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

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

    return LaunchDescription([sensors, pose])
