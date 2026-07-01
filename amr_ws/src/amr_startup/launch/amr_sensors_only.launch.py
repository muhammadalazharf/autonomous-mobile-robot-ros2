"""
Master launch — Layer 1: Sensor saja + Health Check.

Ini launch PERTAMA yang dijalankan saat deploy ke NUC.
Gerbang Modul 1: semua sensor harus PASS sebelum naik ke layer berikutnya.

Cara pakai di NUC:
  ros2 launch amr_startup amr_sensors_only.launch.py
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    sensors_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_sensors'),
                'launch',
                'sensors.launch.py',
            )
        )
    )

    return LaunchDescription([
        sensors_launch,
    ])
