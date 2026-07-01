"""
Rekam data mentah semua sensor ke rosbag.

Output: ~/amr_bags/[timestamp]/
Isi: LiDAR, Color, Depth, IMU, Encoder, Odometry, TF

Cara pakai:
  ros2 launch amr_startup record_sensors.launch.py

Cara replay nanti:
  ros2 bag play ~/amr_bags/[folder]
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from datetime import datetime


def generate_launch_description():

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    bag_dir = f'~/amr_bags/{timestamp}'

    record = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', bag_dir,

            # --- Layer 1: Sensor mentah ---
            '/scan',                                # LiDAR
            '/camera/camera/color/image_raw',       # Kamera RGB
            '/camera/camera/depth/image_rect_raw',  # Kamera Depth
            '/camera/camera/color/camera_info',     # Intrinsics RGB
            '/camera/camera/depth/camera_info',     # Intrinsics Depth
            '/camera/camera/accel/sample',          # Accelerometer mentah
            '/camera/camera/gyro/sample',           # Gyroscope mentah
            '/imu/data',                            # IMU merged
            '/encoder',                             # Encoder mentah

            # --- Layer 2: Pose ---
            '/encoder_odom',                        # Odometry encoder
            '/odometry/filtered',                   # EKF output

            # --- Layer 3: Mapping ---
            '/rtabmap/odom',                        # VIO output
            '/rgbd_image',                          # Synced RGBD
            '/rtabmap/info',                        # Loop closure info

            # --- Layer 5: Brain ---
            '/brain/state',                         # FSM state

            # --- TF (WAJIB untuk replay) ---
            '/tf',
            '/tf_static',
        ],
        output='screen',
    )

    return LaunchDescription([record])
