from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([

        # Node 1: Baca joystick fisik -> /joy
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{
                'device_id': 0,
                'deadzone': 0.05,
                'autorepeat_rate': 20.0,
            }],
            output='screen'
        ),

        # Node 2: /joy -> Serial STM32 "V:...,S:..."
        Node(
            package='amr_controller',
            executable='stm32_bridge',
            name='stm32_bridge',
            output='screen'
        ),

    ])