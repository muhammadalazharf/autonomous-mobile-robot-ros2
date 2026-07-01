"""
Launch STM32 bridge node.

ATURAN MODUL 3: Tidak ada parameter di file ini.
Semua parameter ada di config/motor.yaml.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_motor'),
        'config', 'motor.yaml')

    stm32_bridge = Node(
        package='amr_motor',
        executable='stm32_bridge',
        name='stm32_bridge',
        parameters=[config],
    )

    return LaunchDescription([stm32_bridge])
