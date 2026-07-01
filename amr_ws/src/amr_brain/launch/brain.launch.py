"""
Launch Layer 5: Brain — Hierarki Perilaku (FSM).

ATURAN MODUL 3: Semua parameter di config/brain.yaml.

Prasyarat:
  - Layer 1–4 aktif (sensor, pose, mapping, navigation)

Cara pakai:
  ros2 launch amr_brain brain.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_brain'),
        'config', 'brain.yaml')

    brain = Node(
        package='amr_brain',
        executable='brain',
        name='brain',
        parameters=[config],
        output='screen',
    )

    return LaunchDescription([brain])
