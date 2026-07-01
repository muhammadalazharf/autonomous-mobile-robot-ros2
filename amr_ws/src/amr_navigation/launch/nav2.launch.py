"""
Launch Layer 4: Nav2 — Navigasi Otonom.

ATURAN MODUL 3: Semua parameter di config/nav2_params.yaml.

Prasyarat:
  - Layer 1 (sensor) PASS
  - Layer 2 (pose/EKF) aktif
  - Layer 3 (mapping/localization) aktif + peta tersedia

Cara pakai:
  ros2 launch amr_navigation nav2.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_navigation'),
        'config', 'nav2_params.yaml')

    lifecycle_nodes = [
        'controller_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'velocity_smoother',
    ]

    nav2_nodes = []

    for node_name in lifecycle_nodes:
        nav2_nodes.append(
            Node(
                package='nav2_' + node_name.replace('_server', '').replace('_navigator', '_navigator') if node_name != 'velocity_smoother' else 'nav2_velocity_smoother',
                executable=node_name,
                name=node_name,
                parameters=[config],
                output='screen',
            )
        )

    # Lifecycle manager — nyalakan semua node Nav2 secara urut
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        parameters=[{
            'autostart': True,
            'node_names': lifecycle_nodes,
        }],
    )

    return LaunchDescription(nav2_nodes + [lifecycle_manager])
