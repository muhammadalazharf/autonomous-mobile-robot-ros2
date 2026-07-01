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

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',
            # PENTING: autorepeat HARUS 0 (mati). Kalau >0, joy_node terus
            # mem-publish perintah joystick TERAKHIR walau controller sudah
            # putus (Bluetooth reset) — ini melumpuhkan watchdog joystick di
            # stm32_bridge dan menahan perintah mundur ke motor. Dengan
            # autorepeat mati, saat BT putus /joy benar-benar berhenti →
            # watchdog fire → motor di-stop. Jitter analog stick sudah cukup
            # menjaga /joy tetap mengalir saat driving normal.
            'autorepeat_rate': 0.0,
        }],
    )

    stm32_bridge = Node(
        package='amr_motor',
        executable='stm32_bridge',
        name='stm32_bridge',
        parameters=[config],
    )

    return LaunchDescription([joy_node, stm32_bridge])
