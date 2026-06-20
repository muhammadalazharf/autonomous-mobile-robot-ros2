# 04 — Inventaris Interface ROS 2

Topic, node, service, action, dan TF frame yang teridentifikasi dari source/launch. Item tanpa bukti file ditandai status.

| nama | jenis | message_type | publisher | subscriber | fungsi | package | bukti | status |
|---|---|---|---|---|---|---|---|---|
| /scan | topic | sensor_msgs/LaserScan | rplidar_node | rtabmap, nav2, slam_toolbox, failover | Laser scan 2D | amr_bringup | src/amr_bringup/launch/sensors_launch.py | Terverifikasi dari file |
| /cmd_vel | topic | geometry_msgs/Twist | failover / nav2 (mode demo) | stm32_bridge | Perintah kecepatan ke aktuator | amr_controller | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| /cmd_vel_nav | topic | geometry_msgs/Twist | nav2 controller | failover | cmd_vel dari Nav2 (input arbiter) | amr_failover | src/amr_failover/amr_failover/failover_controller.py | Terverifikasi dari file |
| /cmd_vel_visual | topic | geometry_msgs/Twist | vr_inference | failover | cmd_vel dari visual regression | amr_failover | src/amr_failover/amr_failover/failover_controller.py | Terverifikasi dari file |
| /cmd_vel_joy | topic | geometry_msgs/Twist | teleop_twist_joy | failover | cmd_vel dari joystick | amr_failover | src/amr_failover/amr_failover/failover_controller.py | Terverifikasi dari file |
| /odom | topic | nav_msgs/Odometry | odometry_publisher / rgbd_odometry | nav2, rtabmap | Odometry pose+twist (50 Hz) | amr_controller | src/amr_controller/scripts/odometry_publisher.py | Terverifikasi dari file |
| /encoder | topic | std_msgs/Int32 | stm32_bridge | odometry_publisher | Encoder delta ticks | amr_controller | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| /joy | topic | sensor_msgs/Joy | joy_node | stm32_bridge, odometry_publisher, failover | Input joystick (deadman R1=btn5) | amr_bringup | src/amr_bringup/config/joy_params.yaml | Terverifikasi dari file |
| /imu/data | topic | sensor_msgs/Imu | imu_merger | rgbd_odometry | IMU gabungan accel+gyro | amr_controller | src/amr_controller/scripts/imu_merger_node.py | Terverifikasi dari file |
| /rgbd_image | topic | rtabmap_msgs/RGBDImage | rgbd_sync | rtabmap, rgbd_odometry | RGB+Depth tersinkron | amr_3d_mapping | src/amr_3d_mapping/config/rtabmap_mapping.yaml | Terverifikasi dari file |
| /map | topic | nav_msgs/OccupancyGrid | rtabmap / slam_toolbox | nav2 static_layer, failover | Occupancy grid 2D | amr_3d_mapping | src/amr_3d_mapping/config/rtabmap_mapping.yaml | Terverifikasi dari file |
| /cloud_map | topic | sensor_msgs/PointCloud2 | rtabmap | RViz/Foxglove | Point cloud 3D | amr_3d_mapping | src/amr_3d_mapping/config/rtabmap_mapping.yaml | Terverifikasi dari file |
| /depth_scan | topic | sensor_msgs/LaserScan | (depthimage_to_laserscan?) | nav2 costmap (DIMATIKAN) | Laserscan dari depth (dinonaktifkan di costmap) | amr_slam | src/amr_slam/config/nav2_params.yaml | Catatan/progress (perlu validasi sumber) (node penghasil perlu validasi) |
| /amr/line_segments | topic | visualization_msgs/MarkerArray | lidar_line_segments_node | RViz/Foxglove | Segmen garis dinding (RANSAC) | amr_visual_regression | src/amr_visual_regression/amr_visual_regression/lidar_line_segments_node.py | Terverifikasi dari file |
| /failover_status | topic | std_msgs/String | failover_controller | monitor | Status state machine (JSON) | amr_failover | src/amr_failover/amr_failover/failover_controller.py | Terverifikasi dari file |
| /navigate_to_pose | action | nav2_msgs/action/NavigateToPose | bt_navigator (server) | klien goal | Aksi navigasi ke goal | amr_slam | src/amr_slam/launch/nav2.launch.py | Terverifikasi dari file |
| /slam_toolbox/save_map | service | slam_toolbox/srv/SaveMap | slam_toolbox | - | Simpan peta 2D | amr_slam | src/amr_slam/config/slam_mapping.yaml | Terverifikasi dari file |
| /localization_pose | topic | geometry_msgs/PoseWithCovarianceStamped | (rtabmap localization) | - | Pose hasil lokalisasi | amr_3d_mapping | - | Tidak ditemukan di repo/file saat ini (tidak dikonfigurasi eksplisit; perlu validasi) |
| map | TF frame | tf2 | rtabmap/slam_toolbox | nav2 | Frame global peta | amr_3d_mapping | src/amr_3d_mapping/config/rtabmap_mapping.yaml | Terverifikasi dari file |
| odom | TF frame | tf2 | rgbd_odometry / odometry_publisher | nav2 | Frame odometry | amr_controller | src/amr_controller/scripts/odometry_publisher.py | Terverifikasi dari file |
| base_footprint -> base_link | TF transform | tf2 | robot_state_publisher | semua | Naik z=wheel_radius | amr_description | src/amr_description/urdf/amr_description.urdf.xacro | Terverifikasi dari file |
| base_link -> laser_frame | TF transform | tf2 | robot_state_publisher | rtabmap/nav2 | LiDAR z=0.25 m | amr_description | src/amr_description/urdf/amr_description.urdf.xacro | Terverifikasi dari file |
| base_link -> camera_link | TF transform | tf2 | robot_state_publisher | rtabmap | Kamera x=0.35, z=0.20 m | amr_description | src/amr_description/urdf/amr_description.urdf.xacro | Terverifikasi dari file |


## Catatan TF Tree lengkap

`map -> odom -> base_footprint -> base_link -> {chassis, 4 roda, 2 steering_link, laser_frame, camera_link -> {color/depth_optical_frame}}`

Diagram TF tersedia di repo: `frames_2026-06-09_22.08.25.pdf` dan `frames_2026-06-09_22.09.38.pdf` (output view_frames).
