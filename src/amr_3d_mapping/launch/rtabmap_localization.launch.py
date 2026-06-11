"""
rtabmap_localization.launch.py (VIO + LiDAR Revision — 2026)
==============================
Launch RTAB-Map dalam mode LOCALIZATION dengan Visual-Inertial Odometry (VIO).
Menggunakan peta fixed (.db) yang sudah jadi dari Fase 1.
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ---- Launch arguments ----
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation time (gazebo only)')

    database_path_arg = DeclareLaunchArgument(
        'database_path', default_value='~/.ros/rtabmap.db',
        description='Path ke file .db hasil mapping')

    # ---- Topic args: D455 double namespace (/camera/camera/...) ----
    rgb_topic_arg = DeclareLaunchArgument(
        'rgb_topic',
        default_value='/camera/camera/color/image_raw',
        description='RGB image topic (D455: /camera/camera/color/image_raw)')

    depth_topic_arg = DeclareLaunchArgument(
        'depth_topic',
        default_value='/camera/camera/aligned_depth_to_color/image_raw',
        description='Depth aligned ke RGB (dari align_depth.enable=True)')

    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera/camera/color/camera_info',
        description='RGB camera info')

    scan_topic_arg = DeclareLaunchArgument(
        'scan_topic', default_value='/scan',
        description='LiDAR scan topic')

    # ---- Config path ----
    config_path = PathJoinSubstitution([
        FindPackageShare('amr_3d_mapping'),
        'config',
        'rtabmap_mapping.yaml'
    ])

    # =================================================================
    # NODE 1: IMU MERGER (Preserve Patch #2 & #6)
    # =================================================================
    imu_merger_node = Node(
        package='amr_controller',
        executable='imu_merger_node.py',
        name='imu_merger',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'accel_topic': '/camera/camera/accel/sample',
                'gyro_topic': '/camera/camera/gyro/sample',
            }
        ],
    )

    # =================================================================
    # NODE 2: RGB-D SYNC (rgbd_sync)
    # =================================================================
    rgbd_sync_node = Node(
        package='rtabmap_sync',
        executable='rgbd_sync',
        name='rgbd_sync',
        output='screen',
        parameters=[
            config_path,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        remappings=[
            ('rgb/image',       LaunchConfiguration('rgb_topic')),
            ('depth/image',     LaunchConfiguration('depth_topic')),
            ('rgb/camera_info', LaunchConfiguration('camera_info_topic')),
        ],
    )

    # =================================================================
    # NODE 3: RGB-D ODOMETRY (rgbd_odometry) (Preserve Patch #7)
    # =================================================================
    rgbd_odometry_node = Node(
        package='rtabmap_odom',
        executable='rgbd_odometry',
        name='rgbd_odometry',
        output='screen',
        parameters=[
            config_path,
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'subscribe_rgbd': True,
                'subscribe_imu': True,
                'approx_sync': True,
                'queue_size': 30,
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'publish_tf': True,     
                'Odom/Strategy': '0',          
                'Odom/GuessMotion': 'true',    
                'Odom/MaxVariance': '0.01',    # Filter strict VIO
                'Odom/ResetCountdown': '1',    
                'Vis/MaxFeatures': '1000',     
                'Vis/MinInliers': '2',         
                'GFTT/MinDistance': '5',       
                'GFTT/QualityLevel': '0.001',
                'OdomF2M/MaxSize': '1000',
                'Reg/Force3DoF': 'true',       
            }
        ],
        remappings=[
            ('rgbd_image', '/rgbd_image'),   
            ('imu',        '/imu/data'),      
            ('odom',       '/rtabmap/odom'),  
        ],
    )

    # =================================================================
    # NODE 4: RTAB-Map LOCALIZATION Node
    # =================================================================
    rtabmap_localization_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[
            config_path,
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'database_path': LaunchConfiguration('database_path'),
                'subscribe_depth': False,
                'subscribe_rgbd': True,
                'subscribe_scan': True,
                'subscribe_odom_info': False,
                'approx_sync': True,
                'approx_sync_max_interval': 0.05,
                'queue_size': 30,
                'sync_queue_size': 30,
                'frame_id': 'base_link',
                'map_frame_id': 'map',
                'odom_frame_id': 'odom',
                'tf_delay': 0.05,
                'tf_tolerance': 0.1,
                'wait_for_transform': 0.2,
                'publish_tf': True,
                # ---- MODIFIKASI ABSOLUT LOCALIZATION (Seksi 7 & 8) ----
                'Mem/IncrementalMemory': 'false', # Matikan fungsi mapping/menambah node
                'Mem/InitWMWithAllNodes': 'true',  # Load seluruh isi database ke working memory
                # --------------------------------------------------------
                'Mem/SaveDepth16Format': 'true',
                'Mem/RehearsalSimilarity': '0.45',
                'Mem/STMSize': '30',
                'Reg/Strategy': '2',
                'Reg/Force3DoF': 'true',
                'Icp/PointToPlane': 'true',
                'Icp/Iterations': '15',
                'Icp/VoxelSize': '0.05',
                'Icp/MaxCorrespondenceDistance': '0.1',
                'Grid/FromDepth': 'false',
                'Grid/Sensor': '1',                # Grid murni dibangun dari LaserScan LiDAR
                'Grid/RangeMax': '5.0',
                'Grid/CellSize': '0.05',
                'Grid/RayTracing': 'true',
                'Grid/3D': 'false',
                'Rtabmap/LoopThr': '0.11',
                'RGBD/NeighborLinkRefining': 'true',
                'RGBD/ProximityBySpace': 'true',
            },
        ],
        remappings=[
            ('rgbd_image', '/rgbd_image'),
            ('scan',       LaunchConfiguration('scan_topic')),
            ('odom',       '/rtabmap/odom'),
        ],
        arguments=['--ros-args', '--log-level', 'INFO'],
    )

    # =================================================================
    # NODE 5: depthimage_to_laserscan
    # =================================================================
    depth_to_scan_node = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depth_to_laserscan',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'scan_height': 10,           
            'scan_time': 0.033,          
            'range_min': 0.2,            
            'range_max': 5.0,            
            'output_frame': 'camera_color_optical_frame',
        }],
        remappings=[
            ('image',       LaunchConfiguration('depth_topic')),
            ('camera_info', LaunchConfiguration('camera_info_topic')),
            ('scan',        '/depth_scan'),  
        ],
    )

    return LaunchDescription([
        use_sim_time_arg,
        database_path_arg,
        rgb_topic_arg,
        depth_topic_arg,
        camera_info_topic_arg,
        scan_topic_arg,
        imu_merger_node,       
        rgbd_sync_node,        
        rgbd_odometry_node,    
        rtabmap_localization_node,     
        depth_to_scan_node,    
    ])
