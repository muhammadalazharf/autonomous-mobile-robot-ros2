from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([

        # LiDAR Slamtec C1
        Node(
            package='rplidar_ros',
            executable='rplidar_node',
            name='rplidar_node',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 460800,
                'frame_id': 'laser_frame',
                'angle_compensate': True,
                'scan_mode': 'Sensitivity',
            }],
            output='screen'
        ),

        # GPS U-Blox
        Node(
            package='nmea_navsat_driver',
            executable='nmea_serial_driver',
            name='gps_node',
            parameters=[{
                'port': '/dev/ttyACM0',
                'baud': 9600,
                'frame_id': 'gps_frame',
            }],
            output='screen'
        ),

        # Intel RealSense D455
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense_camera',
            parameters=[{
                'enable_color': True,
                'enable_depth': True,
                'enable_pointcloud': False,
            }],
            output='screen'
        ),

    ])