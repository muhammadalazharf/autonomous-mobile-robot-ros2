"""
nav2.launch.py
===============
Launch Nav2 stack untuk Ackermann robot.

Mode DEMO (tanpa failover): Nav2 publish langsung ke /cmd_vel.
Failover controller HARUS dimatikan (use_failover:=false di amr_full.launch.py).
Joystick R1 = rem darurat manual (manual_override di stm32_bridge).

Usage:
    ros2 launch amr_slam nav2.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_share = get_package_share_directory('amr_slam')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')

    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_launch = os.path.join(
        nav2_bringup_share, 'launch', 'navigation_launch.py'
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                'use_sim_time': 'false',
                'params_file':  nav2_params,
                'autostart':    'true',
            }.items(),
        ),
    ])
