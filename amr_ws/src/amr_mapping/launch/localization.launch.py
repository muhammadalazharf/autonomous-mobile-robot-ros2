"""
Launch Layer 3: RTAB-Map Localization (pakai peta .db yang sudah direkam).

Beda dengan mapping.launch.py:
  - mapping  = bikin peta baru (Mem/IncrementalMemory: true)
  - localization = pakai peta lama, cari posisi di dalamnya (Mem/IncrementalMemory: false)

Cara pakai:
  ros2 launch amr_mapping localization.launch.py database_path:=/home/azhar/maps/lab.db
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    database_arg = DeclareLaunchArgument(
        'database_path',
        description='Path ke database peta .db (WAJIB diisi)')

    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('amr_mapping'),
                'launch', 'mapping.launch.py')
        ),
        launch_arguments={
            'localization': 'true',
            'database_path': LaunchConfiguration('database_path'),
        }.items(),
    )

    return LaunchDescription([
        database_arg,
        mapping_launch,
    ])
