"""
Launch Layer 3: RTAB-Map Mapping (SLAM 3D).

Menyalakan 4 node:
1. rgbd_sync     — gabung color + depth (QoS: BestEffort ✓)
2. rgbd_odometry — VIO dari kamera + IMU
3. rtabmap       — SLAM: mapping + loop closure
4. depthimage_to_laserscan — depth → fake scan untuk Nav2 (nanti)

ATURAN MODUL 3: Semua parameter di config/rtabmap.yaml.

Prasyarat:
  - Layer 1 (sensor) PASS semua
  - Layer 2 (pose/EKF) aktif
  - /imu/data harus hidup (imu_merger dari amr_sensors)

Cara pakai:
  ros2 launch amr_mapping mapping.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_mapping'),
        'config', 'rtabmap.yaml')

    use_localization = DeclareLaunchArgument(
        'localization', default_value='false',
        description='true = mode localization (pakai peta .db), false = mode mapping')

    database_arg = DeclareLaunchArgument(
        'database_path', default_value='~/.ros/rtabmap.db',
        description='Path ke database peta (.db)')

    # --- rgbd_sync: gabung color + depth ---
    rgbd_sync = Node(
        package='rtabmap_sync',
        executable='rgbd_sync',
        name='rgbd_sync',
        parameters=[config],
        remappings=[
            ('rgb/image', '/camera/camera/color/image_raw'),
            ('depth/image', '/camera/camera/depth/image_rect_raw'),
            ('rgb/camera_info', '/camera/camera/color/camera_info'),
        ],
    )

    # --- VIO: estimasi gerak dari kamera + IMU ---
    vio = Node(
        package='rtabmap_odom',
        executable='rgbd_odometry',
        name='vio',
        parameters=[config],
        remappings=[
            ('rgbd_image', '/rgbd_image'),
            ('imu', '/imu/data'),
        ],
    )

    # --- rtabmap: SLAM ---
    rtabmap = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        parameters=[config, {
            'Mem/IncrementalMemory': LaunchConfiguration('localization') == 'false',
            'database_path': LaunchConfiguration('database_path'),
        }],
        remappings=[
            ('rgbd_image', '/rgbd_image'),
            ('scan', '/scan'),
            ('odom', '/rtabmap/odom'),
        ],
        arguments=['--delete_db_on_start'],
    )

    # --- depthimage_to_laserscan: untuk Nav2 nanti ---
    depth_to_scan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depth_to_laserscan',
        parameters=[{
            'scan_height': 1,
            'output_frame_id': 'base_footprint',
            'range_min': 0.3,
            'range_max': 10.0,
        }],
        remappings=[
            ('depth', '/camera/camera/depth/image_rect_raw'),
            ('depth_camera_info', '/camera/camera/depth/camera_info'),
            ('scan', '/depth_scan'),
        ],
    )

    return LaunchDescription([
        use_localization,
        database_arg,
        rgbd_sync,
        vio,
        rtabmap,
        depth_to_scan,
    ])
