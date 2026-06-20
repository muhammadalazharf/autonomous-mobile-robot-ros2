# KERANGKA LAPORAN AMR — Terisi Data (auto-generated)

_Dihasilkan otomatis oleh `laporan_data_amr.py` pada 2026-06-20._

> Setiap subbab di bawah sudah diisi DATA AKTUAL + poin bahasan + bukti yang perlu disiapkan.
> Tinggal kembangkan menjadi paragraf naratif. Tetap jaga kejujuran teknis.


---
## Identitas Proyek

- **judul:** Autonomous Mobile Robot (AMR) 4WD Ackermann Indoor
- **mata_kuliah:** Project Based Learning (PjBL)
- **semester:** Genap 2025/2026
- **kelompok:** 4-24
- **prodi:** Sarjana Terapan Teknologi Rekayasa Otomasi
- **departemen:** Teknik Elektro Otomasi, Fakultas Vokasi
- **institusi:** Institut Teknologi Sepuluh Nopember (ITS) Surabaya
- **bulan:** Juni 2026
- **lingkungan_operasi:** indoor / laboratorium (E105)

### Tim

- **Mararevi Subagyo** (2040241036): Integrasi sistem, dokumentasi laporan, analisis database mapping, Nav2 bringup, lokalisasi
- **Muhammad Al Azhar Faradis** (2040241017): ROS2, RTAB-Map, Nav2, kalibrasi odometry, debugging software
- **Anwar Rifa'i** (2040241021): Hardware, wiring, STM32, aktuator, pengujian robot

### Timeline Kronologis

| Periode | Fase | Kegiatan |
|---------|------|----------|
| Awal | Platform & integrasi | Rakit 4WD Ackermann, ROS2 Humble di NUC, STM32 bridge, joystick |
| 8-9 Jun | Stabilisasi VIO | Tuning anti-drift (STMSize 30->10, MaxVariance, ResetCountdown) |
| 14 Jun | Kalibrasi odometry | Uji 5 jarak -> PPR 1496->3858 (R²=0,998) |
| 15 Jun | Fix brownout | PWM software ramping (anti voltage-sag NUC) |
| s/d 17 Jun | Mapping iteratif | 24 berkas .db; temukan masalah duplikat/korup/near-static |
| 17 Jun | Lokalisasi lock | Breakthrough lokalisasi (Plan A) |
| 18 Jun | Re-mapping bersih | 1 loop pendek -> lab_demo_18jun.db (peta demo tervalidasi) |
| 19 Jun | Nav2 bringup | Rantai 8 gerbang selesai -> bringup sukses; robot otonom |
| 19 Jun | Fix loop rejection | Ambang localization disamakan dgn mapping |
| 20 Jun | Fix arah kemudi | Bench test: negasi steer_rad |

---
## BAB II — Perancangan & Realisasi (per subbab)


### 2.3.2 Penempatan Sensor dan Komponen Elektronik

**Data acuan:**
- **komputer_onboard:**
  - **model:** Intel NUC 13 i7 (NUC13ANHi7)
  - **fungsi:** Pusat komputasi: perception, RTAB-Map, Nav2, ROS2
- **mikrokontroler:**
  - **model:** STM32F407
  - **antarmuka:** USB Virtual COM Port, baud 115200
  - **fungsi:** Kendali motor + servo kemudi, baca encoder, jembatan ke ROS2
- **penggerak:**
  - **motor:** Motor PG45 (DC gear motor + encoder)
  - **konfigurasi:** 4WD via 1 motor + 2 differential + shaft
- **kemudi:**
  - **servo:** DSSERVO D25
  - **tipe:** Ackermann 2WS (2 roda depan tersinkron mekanis)
  - **rentang:** ±45°
- **lidar:**
  - **model:** RPLIDAR C1 (2D 360°)
  - **baud:** 460800
  - **topik:** /scan
  - **frame:** laser_frame
  - **scan_mode:** Standard
- **kamera:**
  - **model:** Intel RealSense D455 (RGB-D + IMU internal)
  - **profil_rgb:** 848x480x30
  - **profil_depth:** 848x480x30
  - **imu:** gyro + accel (chip BMI055)
- **catu_daya:**
  - **baterai:** Ovonic 5300 mAh 6S (LiPo)
  - **tegangan_aman_min:** > 22 V (di bawah ini servo brownout)
- **kontroler_manual:**
  - **perangkat:** Joystick PS4/PS5 (DualShock)
  - **deadman:** Tombol R1 (button index 5)
  - **axis_linear:** axis 1 (stick kiri atas/bawah)
  - **axis_steer:** axis 3 (stick kanan kiri/kanan)
- **gps:** DICOPOT (platform indoor; antena GNSS tidak terpasang)
- **keselamatan_fisik:** PERLU_KONFIRMASI: keberadaan push button / emergency stop fisik. Di software: deadman R1 + state EMERGENCY_STOP pada failover_controller.
- **wheelbase_m:** 0.5
- **track_width_m:** 0.4
- **wheel_radius_m:** 0.0775
- **wheel_width_m:** 0.06
- **chassis_lwh_m:** (0.6, 0.35, 0.15)
- **chassis_mass_kg:** 6.0
- **steering_range_deg:** 45
- **min_turning_radius_m:** 0,5–0,9 (Nav2 memakai 0,90)
- **lidar_height_m:** 0.25
- **camera_x_m:** 0.35
- **camera_height_m:** 0.2
- **tf_tree:**
  - base_footprint
  -  └ base_link  (origin di sumbu roda, z = wheel_radius)
  -     ├ chassis
  -     ├ rear_left_wheel / rear_right_wheel  (continuous Y)
  -     ├ front_left_steering_link  -> front_left_wheel  (revolute Z + continuous Y)
  -     ├ front_right_steering_link -> front_right_wheel
  -     ├ laser_frame   (RPLIDAR C1, z=0,25 m)
  -     └ camera_link   (RealSense D455, x=0,35 m, z=0,20 m)
  -         ├ color_optical_frame  (REP-103: rpy -90,0,-90)
  -         └ depth_optical_frame
- **tf_chain_navigasi:** map -> odom -> base_footprint -> base_link
- **static_tf_bridge:**
  - color_optical_frame  -> camera_color_optical_frame
  - depth_optical_frame  -> camera_depth_optical_frame

**Poin bahasan:**
- LiDAR di z=0,25 m tanpa halangan (scan 360° bebas)
- Kamera depan x=0,35 m, z=0,20 m
- NUC, STM32, driver, baterai 6S pada sasis 0,6×0,35 m
- Pemisahan jalur daya logika vs motor (anti noise)

**⚠️ Bukti yang perlu disiapkan:** Foto tata letak hardware + skema wiring (Lampiran B)

### 2.3.3 Integrasi Tombol Keselamatan

**Data acuan:**
- **deadman:** R1 joystick (button 5)
- **failover_estop:** publish /cmd_vel = (0,0)          (merah)

**Poin bahasan:**
- Deadman R1: lepas = motor stop (manual)
- Software EMERGENCY_STOP: min scan < 0,30 m -> cmd_vel (0,0)
- Watchdog cmd_vel timeout 500 ms -> motor stop

**⚠️ Bukti yang perlu disiapkan:** PERLU_KONFIRMASI keberadaan push button / e-stop FISIK; bila tidak ada, jelaskan e-stop software.

### 2.4.1 Instalasi Lingkungan ROS 2

**Data acuan:**
- **os:** Ubuntu 22.04 LTS
- **ros:** ROS 2 Humble Hawksbill
- **rmw:** rmw_cyclonedds_cpp
- **ros_domain_id:** 42
- **workspace_nuc:** ~/amr_starter
- **build:** colcon build --symlink-install
- **middleware:** DDS (discovery, QoS, pub/sub antar-node)
- **visualisasi:** RViz2, Foxglove
- **slam_3d:** RTAB-Map 0.22.1
- **navigasi:** Navigation2 (Nav2)
- **slam_2d:** SLAM Toolbox (online async)
- **ml_fallback:** scikit-learn (RandomForestRegressor, tanpa CNN)

**Poin bahasan:**
- Ubuntu 22.04 + ROS 2 Humble
- RMW CycloneDDS, DOMAIN_ID 42
- Konsep node/topic/service/action/DDS

**⚠️ Bukti yang perlu disiapkan:** Screenshot `ros2 doctor` / `ros2 node list`

### 2.4.2 Penyiapan Workspace AMR

**Data acuan:**
- **workspace:** ~/amr_starter
- **build:** colcon build --symlink-install
- **amr_description:**
  - **kategori:** utama
  - **peran:** Model robot URDF/Xacro: sasis, 4 roda, 2 steering link, LiDAR, kamera; TF tree
  - **file:**
    - urdf/amr_description.urdf.xacro
    - urdf/amr_macros.xacro
    - urdf/amr_inertia.xacro
- **amr_controller:**
  - **kategori:** utama
  - **peran:** Jembatan hardware + odometry
  - **file:**
    - src/stm32_bridge.cpp (C++)
    - scripts/odometry_publisher.py
    - scripts/imu_merger_node.py
- **amr_bringup:**
  - **kategori:** utama
  - **peran:** Orkestrasi launch keseluruhan sistem
  - **file:**
    - launch/amr_full.launch.py (master)
    - launch/sensors_launch.py
    - launch/amr_launch.py
    - config/joy_params.yaml
- **amr_3d_mapping:**
  - **kategori:** utama
  - **peran:** SLAM 3D RTAB-Map (RGB-D + LiDAR + IMU), VIO
  - **file:**
    - config/rtabmap_mapping.yaml
    - config/rtabmap_localization.yaml
    - launch/rtabmap_mapping.launch.py
    - launch/rtabmap_localization.launch.py
    - launch/vio_only.launch.py
- **amr_slam:**
  - **kategori:** utama
  - **peran:** SLAM Toolbox 2D + konfigurasi Nav2
  - **file:**
    - config/nav2_params.yaml
    - launch/nav2.launch.py
    - config/slam_mapping.yaml
    - config/slam_localization.yaml
- **amr_visual_regression:**
  - **kategori:** pendukung
  - **peran:** Path B fallback: regresi depth-statistic (RandomForest) + ekstraksi segmen garis LiDAR (RANSAC)
  - **file:**
    - amr_visual_regression/data_collector_node.py
    - amr_visual_regression/feature_extractor.py
    - amr_visual_regression/vr_inference_node.py
    - amr_visual_regression/lidar_line_segments_node.py
    - scripts/train.py
- **amr_failover:**
  - **kategori:** pendukung
  - **peran:** Arbiter cmd_vel (state machine SLAM/Visual/Joy/E-Stop)
  - **file:**
    - amr_failover/failover_controller.py
    - launch/failover.launch.py

**Poin bahasan:**
- Workspace ~/amr_starter
- colcon --symlink-install (YAML/launch berlaku tanpa rebuild)
- 7 package modular

**⚠️ Bukti yang perlu disiapkan:** Struktur folder src/ (tree)

### 2.4.3 Penyiapan Dependensi Sistem

**Data acuan:**
- **deps:**
  - rplidar_ros
  - realsense2_camera
  - rtabmap_ros
  - navigation2 / nav2_bringup
  - slam_toolbox
  - robot_state_publisher
  - joy / teleop_twist_joy
  - scikit-learn, joblib, opencv (VR)

**Poin bahasan:**
- Driver sensor, RTAB-Map, Nav2, serial, RViz
- Script: scripts/install_deps.sh, install_rtabmap_deps.sh

**⚠️ Bukti yang perlu disiapkan:** Daftar `rosdep` / isi script install

### 2.5.1 Struktur Modular Software AMR

**Data acuan:**
- **alasan:** Tiap fungsi dapat dikembangkan & diuji terpisah; isolasi kegagalan; reuse

**Poin bahasan:**
- Pemisahan perception/mapping/navigation/control
- Launch berlapis (master amr_full memanggil sub-launch)

**⚠️ Bukti yang perlu disiapkan:** Diagram dependency package

### 2.5.2 Fungsi Package Utama

**Data acuan:**
- **amr_description:**
  - **kategori:** utama
  - **peran:** Model robot URDF/Xacro: sasis, 4 roda, 2 steering link, LiDAR, kamera; TF tree
  - **file:**
    - urdf/amr_description.urdf.xacro
    - urdf/amr_macros.xacro
    - urdf/amr_inertia.xacro
- **amr_controller:**
  - **kategori:** utama
  - **peran:** Jembatan hardware + odometry
  - **file:**
    - src/stm32_bridge.cpp (C++)
    - scripts/odometry_publisher.py
    - scripts/imu_merger_node.py
- **amr_bringup:**
  - **kategori:** utama
  - **peran:** Orkestrasi launch keseluruhan sistem
  - **file:**
    - launch/amr_full.launch.py (master)
    - launch/sensors_launch.py
    - launch/amr_launch.py
    - config/joy_params.yaml
- **amr_3d_mapping:**
  - **kategori:** utama
  - **peran:** SLAM 3D RTAB-Map (RGB-D + LiDAR + IMU), VIO
  - **file:**
    - config/rtabmap_mapping.yaml
    - config/rtabmap_localization.yaml
    - launch/rtabmap_mapping.launch.py
    - launch/rtabmap_localization.launch.py
    - launch/vio_only.launch.py
- **amr_slam:**
  - **kategori:** utama
  - **peran:** SLAM Toolbox 2D + konfigurasi Nav2
  - **file:**
    - config/nav2_params.yaml
    - launch/nav2.launch.py
    - config/slam_mapping.yaml
    - config/slam_localization.yaml

**Poin bahasan:**
- amr_description, amr_controller, amr_bringup, amr_3d_mapping, amr_slam

### 2.5.3 Package Pendukung Keandalan Sistem

**Data acuan:**
- **amr_visual_regression:**
  - **kategori:** pendukung
  - **peran:** Path B fallback: regresi depth-statistic (RandomForest) + ekstraksi segmen garis LiDAR (RANSAC)
  - **file:**
    - amr_visual_regression/data_collector_node.py
    - amr_visual_regression/feature_extractor.py
    - amr_visual_regression/vr_inference_node.py
    - amr_visual_regression/lidar_line_segments_node.py
    - scripts/train.py
- **amr_failover:**
  - **kategori:** pendukung
  - **peran:** Arbiter cmd_vel (state machine SLAM/Visual/Joy/E-Stop)
  - **file:**
    - amr_failover/failover_controller.py
    - launch/failover.launch.py
- **peran:** Arbiter cmd_vel — pilih sumber kendali sesuai kondisi
- **states:**
  - **SLAM_ACTIVE:** publish /cmd_vel = /cmd_vel_nav  (default, hijau)
  - **VISUAL_FALLBACK:** publish /cmd_vel = /cmd_vel_visual (kuning)
  - **JOY_OVERRIDE:** publish /cmd_vel = /cmd_vel_joy   (biru, deadman R1)
  - **EMERGENCY_STOP:** publish /cmd_vel = (0,0)          (merah)
- **trigger:**
  - SLAM unhealthy >= fallback_delay (2 s) -> VISUAL_FALLBACK
  - SLAM healthy >= recovery_delay (5 s) -> SLAM_ACTIVE (histeresis)
  - Deadman R1 ditekan -> JOY_OVERRIDE
  - min /scan range < emergency_min_range (0,30 m) -> EMERGENCY_STOP
- **param_kunci:**
  - **control_rate:** 20.0
  - **scan_timeout_s:** 1.0
  - **map_timeout_s:** 10.0
  - **emergency_min_range:** 0.3
- **status_demo:** DIBYPASS saat demo (Nav2 -> /cmd_vel langsung). Konsekuensi: tanpa auto e-stop; R1 = rem darurat manual.
- **pendekatan:** Regresi depth-statistic klasik (RandomForestRegressor, scikit-learn) TANPA CNN
- **pipeline:**
  - data_collector_node (rekam dataset saat teleop)
  - train.py (offline, Random Forest)
  - vr_inference_node (real-time -> /cmd_vel_visual)
- **input:** depth image (ROI), num_regions=9
- **output:** linear.x (vx) + angular.z (steering)
- **safety:** min_depth < safety_min_depth (0,4 m) -> velocity = 0
- **peran:** Ekstraksi segmen garis dari LiDAR — representasi dinding sebagai entitas utuh (menjawab kritik dosen: bukan titik diskrit)
- **algoritma:** Split-and-Merge + RANSAC line fitting
- **alasan:** O(N) + RANSAC robust outlier; lebih murah dari Hough Transform untuk 720+ titik @ 10 Hz pada NUC tanpa GPU
- **output:** /amr/line_segments (MarkerArray), /amr/line_count (Int32)
- **korelasi_matkul:** Pengolahan Citra Digital — least-squares & regresi robust

**Poin bahasan:**
- amr_failover: arbiter cmd_vel 4 state
- amr_visual_regression: fallback depth-regression + line segments

**⚠️ Bukti yang perlu disiapkan:** Screenshot /failover_status atau marker RViz

### 2.6.1 Integrasi STM32 dengan Aktuator

**Data acuan:**
- **tx:** V:{pwm},S:{sudut}\n  (pwm bisa negatif)
- **rx:** E:{delta}\n  (encoder delta ticks)
- **max_pwm:** 4000
- **max_steer_deg:** 45
- **steer_trim_deg:** -5
- **ramping:** MAX_PWM_STEP=400 per panggilan (anti inrush brownout); e-stop (V=0) bypass ramp
- **topik_encoder:** /encoder (std_msgs/Int32)
- **gate_autonomous:** autonomous_enabled (default false; set true saat runtime)
- **konvensi_arah:** V positif = maju (kabel motor sudah ditukar fisik oleh lab)
- **servo:**
  - **servo:** DSSERVO D25
  - **tipe:** Ackermann 2WS (2 roda depan tersinkron mekanis)
  - **rentang:** ±45°
- **motor:**
  - **motor:** Motor PG45 (DC gear motor + encoder)
  - **konfigurasi:** 4WD via 1 motor + 2 differential + shaft

**Poin bahasan:**
- Protokol serial V:{pwm},S:{sudut} / E:{delta}
- Dual-mode: manual (joystick) & autonomous (cmd_vel)
- Konversi Ackermann steer = atan(L*w/v)

**⚠️ Bukti yang perlu disiapkan:** Foto wiring STM32 + log serial

### 2.6.2 Pengujian Kendali Manual Joystick

**Data acuan:**
- **perangkat:** Joystick PS4/PS5 (DualShock)
- **deadman:** Tombol R1 (button index 5)
- **axis_linear:** axis 1 (stick kiri atas/bawah)
- **axis_steer:** axis 3 (stick kanan kiri/kanan)
- **joy_params:** axis_linear=1, axis_angular=3, enable_button=5

**Poin bahasan:**
- Deadman R1 wajib ditekan untuk gerak
- Uji respons motor & servo sebelum autonomous

**⚠️ Bukti yang perlu disiapkan:** Video uji manual; output /joy

### 2.6.3 Pembacaan Encoder untuk Odometry

**Data acuan:**
- **topik:**
  - **model:** Bicycle kinematic (Ackermann)
  - **rumus:**
    - dist_per_tick = 2*pi*wheel_radius / PPR
    - vx = delta_dist / dt
    - delta_theta = (vx / wheelbase) * tan(steering) * dt
    - x += delta_dist * cos(theta + delta_theta/2)
    - y += delta_dist * sin(theta + delta_theta/2)
    - theta += delta_theta
  - **publish_rate_hz:** 50
  - **sumber_setir:** /joy (axis 3). CATATAN: saat autonomous murni, sudut setir tidak terbaca dari /cmd_vel -> yaw odom tak update; dikoreksi RTAB-Map. (rekomendasi: sinkron dari /cmd_vel)
  - **encoder_format:** auto-detect cumulative vs delta
  - **publish_tf:** Kondisional: True hanya saat use_rtabmap=false (anti TF konflik)
- **protokol_rx:** E:{delta}\n  (encoder delta ticks)

**Poin bahasan:**
- Encoder delta -> /encoder (Int32)
- Auto-detect cumulative vs delta
- Sumber utama odometry roda

**⚠️ Bukti yang perlu disiapkan:** Plot /encoder vs gerak

### 2.7.1 Integrasi Sensor LiDAR

**Data acuan:**
- **model:** RPLIDAR C1 (2D 360°)
- **baud:** 460800
- **topik:** /scan
- **frame:** laser_frame
- **scan_mode:** Standard

**Poin bahasan:**
- RPLIDAR C1 baud 460800 -> /scan, frame laser_frame
- QoS BestEffort (SensorDataQoS)

**⚠️ Bukti yang perlu disiapkan:** Screenshot RViz /scan

### 2.7.2 Integrasi Kamera RGB-D

**Data acuan:**
- **enable_color:** True
- **enable_depth:** True
- **depth_profile:** 848x480x30
- **rgb_profile:** 848x480x30
- **align_depth:** True
- **enable_pointcloud:** False
- **publish_tf:** False
- **enable_gyro:** True
- **enable_accel:** True
- **unite_imu_method:** 2
- **temporal_filter:** True
- **spatial_filter:** True
- **decimation_filter:** False
- **rgb_gain:** 64
- **rgb_exposure:** 156
- **auto_exposure:** True
- **catatan:** Profil 848x480x30 TIDAK BOLEH diubah (konsisten dgn kalibrasi). Gain dinaikkan untuk area gelap (VIO tracking).
- **imu_merger:** gabung accel+gyro -> /imu/data

**Poin bahasan:**
- RealSense D455 RGB+Depth 848x480x30, align_depth
- IMU gyro+accel (digabung imu_merger_node, slop 50 ms)
- Profil TIDAK diubah (konsisten kalibrasi)

**⚠️ Bukti yang perlu disiapkan:** Screenshot RViz pointcloud/depth

### 2.7.3 Validasi Data Sensor di RViz

**Data acuan:**
- **topik_cek:**
  - /scan
  - /camera/.../image_raw
  - /camera/.../aligned_depth_to_color/image_raw

**Poin bahasan:**
- Verifikasi sensor terbaca sebelum mapping
- Cek `ros2 topic hz` untuk laju data

**⚠️ Bukti yang perlu disiapkan:** Screenshot RViz scan + point cloud

### 2.8.1 Pemodelan Robot dalam URDF/Xacro

**Data acuan:**
- **wheelbase_m:** 0.5
- **track_width_m:** 0.4
- **wheel_radius_m:** 0.0775
- **wheel_width_m:** 0.06
- **chassis_lwh_m:** (0.6, 0.35, 0.15)
- **chassis_mass_kg:** 6.0
- **steering_range_deg:** 45
- **min_turning_radius_m:** 0,5–0,9 (Nav2 memakai 0,90)
- **lidar_height_m:** 0.25
- **camera_x_m:** 0.35
- **camera_height_m:** 0.2
- **file:**
  - urdf/amr_description.urdf.xacro
  - urdf/amr_macros.xacro
  - urdf/amr_inertia.xacro

**Poin bahasan:**
- Sasis, 4 roda, 2 steering link, LiDAR, kamera
- Parameter geometri (wheelbase 0,5; track 0,4; r 0,0775)

**⚠️ Bukti yang perlu disiapkan:** Screenshot model di RViz

### 2.8.2 Penyusunan Transform Antar-Frame

**Data acuan:**
- **tf_tree:**
  - base_footprint
  -  └ base_link  (origin di sumbu roda, z = wheel_radius)
  -     ├ chassis
  -     ├ rear_left_wheel / rear_right_wheel  (continuous Y)
  -     ├ front_left_steering_link  -> front_left_wheel  (revolute Z + continuous Y)
  -     ├ front_right_steering_link -> front_right_wheel
  -     ├ laser_frame   (RPLIDAR C1, z=0,25 m)
  -     └ camera_link   (RealSense D455, x=0,35 m, z=0,20 m)
  -         ├ color_optical_frame  (REP-103: rpy -90,0,-90)
  -         └ depth_optical_frame
- **tf_chain_navigasi:** map -> odom -> base_footprint -> base_link
- **static_tf_bridge:**
  - color_optical_frame  -> camera_color_optical_frame
  - depth_optical_frame  -> camera_depth_optical_frame

**Poin bahasan:**
- TF tree base_footprint -> base_link -> sensor/roda
- Optical frame REP-103
- Static TF bridge ke frame RealSense

**⚠️ Bukti yang perlu disiapkan:** Output `ros2 run tf2_tools view_frames` (PDF frames)

### 2.8.3 Visualisasi Model Robot di RViz

**Data acuan:**
- **chain:** map -> odom -> base_footprint -> base_link

**Poin bahasan:**
- Validasi posisi relatif sensor
- robot_state_publisher

**⚠️ Bukti yang perlu disiapkan:** Screenshot RobotModel + TF di RViz

### 2.9.1 Pengujian Jarak Odometry

**Data acuan:**
- **data_odom_m:**
  - 0.5
  - 1.0
  - 1.5
  - 2.0
  - 2.5
- **data_real_cm:**
  - 22
  - 41
  - 61
  - 81
  - 96
- **metode:** Uji odom-vs-meteran pada 5 jarak acuan

**Poin bahasan:**
- Uji 5 jarak (0,5–2,5 m)
- Bandingkan odom vs meteran

**⚠️ Bukti yang perlu disiapkan:** Tabel data + foto pengukuran meteran

### 2.9.2 Koreksi Nilai PPR Encoder

**Data acuan:**
- **metode:** Uji odom-vs-meteran pada 5 jarak acuan
- **tanggal:** 14 Juni 2026
- **data_odom_m:**
  - 0.5
  - 1.0
  - 1.5
  - 2.0
  - 2.5
- **data_real_cm:**
  - 22
  - 41
  - 61
  - 81
  - 96
- **fit:** real = 0,3877 × odom (proporsional lewat origin)
- **r_squared:** 0.998
- **faktor_over_report:** 2.58
- **ppr_lama:** 1496
- **ppr_efektif:** 3858
- **dist_per_tick_lama_mm:** 0.3255
- **dist_per_tick_baru_mm:** 0.1262
- **korelasi_matkul:** Metode Numerik — regresi kuadrat terkecil (least squares)

**Poin bahasan:**
- Over-report 2,58×
- PPR 1496 -> 3858
- dist_per_tick 0,3255 -> 0,1262 mm

### 2.9.3 Evaluasi Akurasi Odometry

**Data acuan:**
- **fit:** real = 0,3877 × odom (proporsional lewat origin)
- **R2:** 0.998
- **korelasi:** Metode Numerik — regresi kuadrat terkecil (least squares)

**Poin bahasan:**
- Regresi R²=0,998 -> odometry konsisten
- Kaitan metode numerik (least squares)

**⚠️ Bukti yang perlu disiapkan:** Plot regresi real vs odom

### 2.10.1 Akuisisi Data Mapping

**Data acuan:**
- **input:** RGB+Depth+Scan+IMU+odom
- **sync:** approx 0,05 s
- **Odom/Strategy:** 0 (Frame-to-Map)
- **Odom/GuessMotion:** true (IMU bantu prediksi gerak)
- **Vis/MaxFeatures:** 1000
- **Vis/MinInliers:** 8
- **GFTT/MinDistance:** 5
- **GFTT/QualityLevel:** 0.001
- **Odom/MaxVariance:** 0.01 (buang frame tak yakin — anti scattered cloud)
- **Odom/ResetCountdown:** 5 (toleran motion blur)
- **OdomF2M/MaxSize:** 1000

**Poin bahasan:**
- Mode SYNC RGB-D+LiDAR+IMU
- VIO sebagai sumber pose

**⚠️ Bukti yang perlu disiapkan:** Screenshot rtabmap_viz saat mapping

### 2.10.2 Pembentukan Pose Graph

**Data acuan:**
- **Reg/Strategy:** 2 (Vis + ICP)
- **Reg/Force3DoF:** true (x, y, yaw saja)
- **Icp/PointToPlane:** true
- **Icp/Iterations:** 15
- **Icp/VoxelSize:** 0.05
- **Icp/MaxCorrespondenceDistance:** 0.1
- **Vis/FeatureType:** 8 (GFTT/BRIEF)
- **Vis/MaxFeatures:** 1000
- **Vis/MinInliers:** 8
- **Kp/MaxFeatures:** 400
- **Kp/DetectorStrategy:** 8
- **Grid/CellSize:** 0.05
- **Grid/RangeMax:** 5.0
- **Grid/RayTracing:** true
- **Rtabmap/LoopThr:** 0.05
- **Rtabmap/DetectionRate:** 2.0
- **Rtabmap/TimeThr:** 700
- **RGBD/NeighborLinkRefining:** true
- **RGBD/ProximityBySpace:** true
- **RGBD/OptimizeMaxError:** 5.0
- **RGBD/LoopClosureReextractFeatures:** true
- **RGBD/LocalRadius:** 5.0
- **Optimizer/GravitySigma:** 0.3 (IMU gravity constraint aktif)
- **Mem/STMSize:** 10
- **Mem/IncrementalMemory:** true
- **sinkronisasi:** approx_sync slop 0,05 s (RGB+Depth+Scan+IMU)

**Poin bahasan:**
- Node, keyframe, link neighbor, loop closure
- Reg/Strategy 2 (Vis+ICP), gravity constraint

**⚠️ Bukti yang perlu disiapkan:** Screenshot graph view DatabaseViewer

### 2.10.3 Penyimpanan Hasil Mapping

**Data acuan:**
- **format:** SQLite .db
- **isi:** node+keyframe+link+RGB+depth+scan

**Poin bahasan:**
- .db = artefak bukti utama mapping
- database_path, Mem/IncrementalMemory=true

**⚠️ Bukti yang perlu disiapkan:** Output `rtabmap-info <db>`

### 2.11.1 Identifikasi Status Database

**Data acuan:**
- **db_ditemukan:** 24
- **db_terbaca:** 22
- **db_rusak_malformed:** 2
- **db_kosong:** 3
- **db_valid:** 19

**Poin bahasan:**
- 24 ditemukan -> 19 valid, 3 kosong, 2 rusak

**⚠️ Bukti yang perlu disiapkan:** Output script analisis read-only

### 2.11.2 Analisis Node, Keyframe, Link, dan Loop Closure

**Data acuan:**
- **db_utama:**
  - **nama:** mapping_20260611_MASTER.db
  - **nodes:** 1526
  - **loop_closure:** 754
  - **link_total:** 987
- **eksploratif:**
  - **nama:** lab_vio_1620.db
  - **nodes:** 758
  - **keyframe:** 316
  - **link:** 760
  - **loop_closure:** 130
  - **durasi:** 13m23s
  - **jarak_m:** 43.511
  - **bbox_m2:** 45.706

**Poin bahasan:**
- Arti tiap parameter sebagai indikator kualitas SLAM
- Loop closure sehat = graf terhubung global

### 2.11.3 Analisis Deduplikasi dan Database Utama

**Data acuan:**
- **mentah:**
  - **pose:** 16317
  - **keyframe:** 2500
  - **link:** 11500
  - **loop_closure:** 7675
- **dedup:**
  - **pose:** 11739
  - **keyframe:** 1798
  - **link:** 8539
  - **loop_closure:** 5413
- **near_static:**
  - test.db (682/683 LC, 0,236 m, 0 m²)
  - lab_final_malam_ini.db (215/215, 0,167 m)
  - lab_remap3_223920.db (186/186, 0 m²)
- **anomali:** lab_remap3_212606.db (884 node tapi hanya 1,941 m; bbox 0,005 m²)

**Poin bahasan:**
- Mentah vs dedup
- mapping_20260611_MASTER.db = acuan agregat
- Sesi near-static bukan bukti utama

### 2.12.1 Evaluasi Kualitas Peta Awal

**Data acuan:**
- **masalah:** Peta panjang berulang (~175 m, ~1224 pose, 1,2 GB) -> drift VIO akumulatif -> 3D cloud ghosting

**Poin bahasan:**
- Identifikasi drift/ghosting pada peta lama

**⚠️ Bukti yang perlu disiapkan:** Screenshot cloud ghosting (pembanding)

### 2.12.2 Pelaksanaan Remapping

**Data acuan:**
- **file:** lab_demo_18jun.db
- **tanggal:** 18 Juni 2026
- **lokasi:** Lab E105 ITS
- **rtabmap_version:** 0.22.1
- **sessions:** 1
- **durasi_s:** 1012
- **trajektori_m:** 28.9
- **pose_optimized:** 448
- **nodes_ltm:** 1846
- **words:** 126506
- **neighbor_links:** 447
- **avg_keyframe_dist_m:** 0.06
- **global_loop_closure:** 125
- **proximity_loop_closure:** 648
- **ukuran_db_mb:** 743
- **komposisi_db:** Depth 56% · RGB 25% · Features 10% · Grid 5%
- **verdict:** Peta bersih tervalidasi; loop closure diterima saat lokalisasi.

**Poin bahasan:**
- Re-mapping 1 loop pendek bersih (28,9 m, 17 menit)
- Prinsip kualitas > kuantitas

**⚠️ Bukti yang perlu disiapkan:** Output rtabmap-info lab_demo_18jun.db

### 2.12.3 Penentuan Peta Acuan

**Data acuan:**
- **acuan_demo:** lab_demo_18jun.db
- **metrik:** 125 global + 648 proximity LC, 448 pose

**Poin bahasan:**
- lab_demo_18jun.db dipilih untuk localization & Nav2

**⚠️ Bukti yang perlu disiapkan:** Screenshot loop closure hijau

### 2.13.1 Penggunaan Peta sebagai Referensi Posisi

**Data acuan:**
- **mode:** Mem/IncrementalMemory=false, Mem/InitWMWithAllNodes=true
- **peta:** lab_demo_18jun.db

**Poin bahasan:**
- Load .db read-only; track tanpa tambah node permanen

**⚠️ Bukti yang perlu disiapkan:** Log mode localization

### 2.13.2 Penyesuaian Parameter Localization

**Data acuan:**
- **mode:** Mem/IncrementalMemory=false, Mem/InitWMWithAllNodes=true
- **prinsip:** Ambang localization HARUS = ambang mapping (baked di .db). Lebih ketat = loop closure valid selalu ditolak.
- **tabel_perbandingan:**
  - Rtabmap/LoopThr
  - 0,05
  - 0,11 (2x ketat)
  - 0,05
  - Vis/MinInliers
  - 8
  - 10
  - 8
  - Rtabmap/DetectionRate
  - 2,0
  - 1,0 Hz
  - 2,0
  - Kp/MaxFeatures
  - 400
  - (hilang)
  - 400
  - Kp/DetectorStrategy
  - 8
  - (hilang)
  - 8
  - RGBD/LoopClosureReextractFeatures
  - true
  - (hilang)
  - true
  - RGBD/OptimizeMaxError
  - 5,0
  - 3,0 (default)
  - 5,0
  - Mem/STMSize
  - 10
  - (hilang)
  - 10

**Poin bahasan:**
- Root cause loop rejection: ambang localization > mapping
- Samakan LoopThr, MinInliers, DetectionRate, Kp/*, dll

### 2.13.3 Validasi Localization Lock

**Data acuan:**
- **indikator:** loop closure diterima (hijau), pose stabil

**Poin bahasan:**
- Pastikan lock sebelum kirim goal Nav2

**⚠️ Bukti yang perlu disiapkan:** Screenshot loop closure hijau / log /localization_pose / RMSE vs ground truth

### 2.14.1 Konfigurasi Komponen Nav2

**Data acuan:**
- **planner:**
  - **plugin:** nav2_smac_planner/SmacPlannerHybrid
  - **motion_model:** DUBIN (Ackermann maju)
  - **minimum_turning_radius:** 0.9
  - **reverse_penalty:** 2.0
  - **angle_quantization_bins:** 72
  - **allow_unknown:** true
- **controller:**
  - **plugin:** nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController
  - **desired_linear_vel:** 0.3
  - **lookahead_dist:** 0.6
  - **use_rotate_to_heading:** false (Ackermann tak bisa putar di tempat)
  - **allow_reversing:** true
- **costmap:**
  - **resolution:** 0.05
  - **robot_radius:** 0.28
  - **inflation_radius:** 0.25
  - **local:** 4x4 m rolling window; voxel_layer + inflation_layer
  - **global:** static + obstacle + inflation
  - **observation_sources:** scan (LiDAR) saja — depth_scan dimatikan
- **smoother:** nav2_smoother::SimpleSmoother
- **behaviors:**
  - spin
  - backup
  - drive_on_heading
  - wait
- **velocity_smoother:** max_velocity [0,3; 0; 0,5]; max_accel [1,0; 0; 1,5]
- **bt_xml:** /opt/ros/humble/share/nav2_bt_navigator/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml
- **mode_demo:** Tanpa failover; Nav2 -> /cmd_vel langsung; rem darurat R1 wajib.
- **format_:::**
  - nav2_controller (SimpleProgressChecker, SimpleGoalChecker)
  - nav2_costmap_2d (Voxel/Obstacle/Static/InflationLayer)
  - nav2_regulated_pure_pursuit_controller
  - nav2_smoother (SimpleSmoother)
  - nav2_waypoint_follower (WaitAtWaypoint)
- **format_/:**
  - nav2_smac_planner (SmacPlannerHybrid)
  - nav2_behaviors (Spin, BackUp, DriveOnHeading, Wait)

**Poin bahasan:**
- Planner, controller, costmap, BT, lifecycle
- Konsistensi format plugin :: vs /

**⚠️ Bukti yang perlu disiapkan:** Log lifecycle 'Managed nodes are active'

### 2.14.2 Penyesuaian Nav2 untuk Ackermann

**Data acuan:**
- **planner:**
  - **plugin:** nav2_smac_planner/SmacPlannerHybrid
  - **motion_model:** DUBIN (Ackermann maju)
  - **minimum_turning_radius:** 0.9
  - **reverse_penalty:** 2.0
  - **angle_quantization_bins:** 72
  - **allow_unknown:** true
- **controller:**
  - **plugin:** nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController
  - **desired_linear_vel:** 0.3
  - **lookahead_dist:** 0.6
  - **use_rotate_to_heading:** false (Ackermann tak bisa putar di tempat)
  - **allow_reversing:** true

**Poin bahasan:**
- SmacPlannerHybrid DUBIN, min turning radius 0,90 m
- RegulatedPurePursuit, use_rotate_to_heading=false

**⚠️ Bukti yang perlu disiapkan:** Screenshot global plan menghormati radius putar

### 2.14.3 Pengujian Mode Demo Navigasi

**Data acuan:**
- **gerbang_terakhir:**
  - **no:** 8
  - **gejala:** Robot tetap diam walau /cmd_vel != 0
  - **akar:** autonomous_enabled default false (safety gate)
  - **fix:** ros2 param set /stm32_bridge autonomous_enabled true (runtime)
- **mode:** Tanpa failover; Nav2 -> /cmd_vel langsung; rem darurat R1 wajib.

**Poin bahasan:**
- Kirim goal navigate_to_pose; robot bergerak otonom
- Rantai 8 gerbang sebagai catatan debugging sah

**⚠️ Bukti yang perlu disiapkan:** WAJIB: video navigasi + log /cmd_vel + screenshot RViz path (bukti runtime)

---
## Lampiran: Rantai 8 Gerbang Nav2

| # | Gejala | Akar Masalah | Perbaikan |
|---|--------|--------------|-----------|
| 1 | VoxelLayer does not exist | Format plugin '/' vs '::' campur di nav2_params.yaml | Seragamkan format per package |
| 2 | ID [RemovePassedGoals] already registered (crash) | Blok plugin_lib_names eksplisit -> registrasi ganda | Hapus blok -> Nav2 auto-load via pluginlib |
| 3 | Node not recognized: RateController | Turunan #2 | Terselesaikan bersama #2 |
| 4 | Action server spin not available | Behavior 'spin' tak terdaftar, padahal BT default memanggilnya | Daftarkan nav2_behaviors/Spin di behavior_plugins |
| 5 | Couldn't open input XML file | default_nav_to_pose_bt_xml bukan path absolut | Pakai path absolut /opt/ros/humble/share/nav2_bt_navigator/... |
| 6 | collision ahead / lethal terus | depth_scan salah baca lantai sebagai obstacle hantu | Matikan depth_scan di costmap (LiDAR saja); robot_radius 0,35->0,28; inflation_radius 0,45->0,25 |
| 7 | Nav2 kirim cmd_vel tapi robot diam (Failed to make progress) | Remap /cmd_vel->/cmd_vel_nav, bridge dengar /cmd_vel | Hapus remap di nav2.launch.py (mode demo tanpa failover) |
| 8 | Robot tetap diam walau /cmd_vel != 0 | autonomous_enabled default false (safety gate) | ros2 param set /stm32_bridge autonomous_enabled true (runtime) |

## Lampiran: Kendala & Solusi

| Kendala | Penyebab | Dampak | Solusi |
|---------|----------|--------|--------|
| Visual odometry terpengaruh cahaya | Sensitivitas RealSense terhadap pencahayaan & tekstur | VO drift, kualitas peta menurun area minim fitur | Tuning exposure/gain, andalkan LiDAR, re-mapping bersih |
| Database rusak/malformed | Proses perekaman terputus saat penulisan .db | 2 berkas tidak dapat dianalisis | Tutup sesi mapping dengan benar; backup berkala |
| File database duplikat | Penyalinan/backup manual sesi yang sama | Agregat membengkak, klaim bisa menyesatkan | Deduplikasi; peta tunggal acuan; SOP penamaan |
| Konfigurasi Nav2 plugin tidak konsisten | Campuran format :: dan / pada ROS2 Humble | Lifecycle bringup gagal | Seragamkan format + selesaikan rantai 8 gerbang |
| Ackermann butuh tuning khusus | Radius putar minimum & sifat nonholonomic | Planner/controller default kurang sesuai | SmacPlannerHybrid + RegulatedPurePursuit (sadar-kinematika) |
| Loop rejection saat lokalisasi | Ambang localization lebih ketat dari mapping | Robot tak pernah lock ke peta | Samakan ambang localization = mapping |
| Brownout NUC saat motor inrush | Lonjakan arus PG45 -> voltage sag | Sistem freeze saat akselerasi | PWM software ramping + e-stop bypass |
| Layout ruangan berubah | Tata ruang lab tidak tetap | Lokalisasi melemah, planner no valid path | Re-mapping saat layout berubah signifikan |

## Lampiran: Perbaikan Hardware

- **Brownout power-rail saat motor start** (15 Juni 2026, Selesai): Inrush motor PG45 -> tegangan NUC sag (SSH freeze, RealSense timeout) — terkonfirmasi uji EMI → Software PWM ramping (batas delta 400/call); e-stop bypass ramp
- **Odometry over-report 2,58×** (14 Juni 2026, Selesai): PPR teoretis (1496) tidak sesuai realita gear/quadrature → Kalibrasi empiris -> PPR 3858 (R²=0,998)
- **Arah kemudi otonom terbalik** (20 Juni 2026, Diterapkan; menunggu verifikasi hardware penulis): Tanda kemudi pada formula Ackermann terbalik (bench test). Velocity maju/mundur sudah benar (kabel motor ditukar lab). → Negasi steer_rad = -atan(L*omega/v) di cmd_vel_callback

## Lampiran: Tabel Ambang Mapping vs Localization

| Parameter | Mapping | Localization (sblm fix) | Setelah fix |
|-----------|---------|--------------------------|-------------|
| Rtabmap/LoopThr | 0,05 | 0,11 (2x ketat) | 0,05 |
| Vis/MinInliers | 8 | 10 | 8 |
| Rtabmap/DetectionRate | 2,0 | 1,0 Hz | 2,0 |
| Kp/MaxFeatures | 400 | (hilang) | 400 |
| Kp/DetectorStrategy | 8 | (hilang) | 8 |
| RGBD/LoopClosureReextractFeatures | true | (hilang) | true |
| RGBD/OptimizeMaxError | 5,0 | 3,0 (default) | 5,0 |
| Mem/STMSize | 10 | (hilang) | 10 |