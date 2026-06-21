# Prompt Penulisan per Subbab BAB II

Salin prompt ke AI untuk menulis narasi tiap subbab. Lampirkan data dari evidence package & file sumber terkait.

## 2.1 Penentuan Target Autonomous Navigation AMR
> Tulis subbab yang menetapkan target sistem: 'AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.'. Jelaskan definisi global planner point-to-point & local planner obstacle-avoidant. Data: konsep AMR vs AGV. Hindari klaim hasil; ini penetapan target.

## 2.2 Platform Hardware dan Aktuator
> **Tujuan:** jelaskan Robot memiliki platform fisik 4WD Ackermann yang mampu mengeksekusi gerak translasi & kemudi sesuai perintah navigasi.
>
> **Data yang dimasukkan:** Sasis 4WD + 4 roda + 2 steering link; Motor PG45 (4WD: 1 motor + 2 diferensial + shaft); Servo kemudi DSSERVO D25, MAX_STEER 45, STEER_TRIM -5; STM32F407 (USB Virtual COM 115200); Encoder pada PG45 -> /encoder
>
> **Bukti yang disebut (kuat):** Sasis 4WD + 4 roda + 2 steering link; Motor PG45 (4WD: 1 motor + 2 diferensial + shaft); Servo kemudi DSSERVO D25, MAX_STEER 45, STEER_TRIM -5; STM32F407 (USB Virtual COM 115200); Encoder pada PG45 -> /encoder; Geometri: wheelbase 0.5 m, track 0.4 m, wheel_radius 0.0775 m
>
> **Gambar/tabel:** Foto robot, wiring; tabel spec hardware
>
> **Hindari klaim:** BTS7960/buck/push button tak terbukti di repo; foto fisik belum ada; Ackermann tak bisa rotate-in-place (min turning radius 0.90 m) -> goal sempit gagal; brownout inrush PG45 (dimitigasi PWM ramping).
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.3 Sensor dan Persepsi Lingkungan
> **Tujuan:** jelaskan Robot membaca lingkungan (jarak, citra, gerak) sebagai masukan mapping, costmap, odometry, dan localization.
>
> **Data yang dimasukkan:** RPLIDAR C1 -> /scan, frame laser_frame, baud 460800, ~10 Hz; Parameter scan nyata: range 0.15-16 m, ~720 titik; RealSense D455 RGB+Depth 848x480x30, align_depth; IMU D455 accel+gyro -> /imu/data (imu_merger, slop 50 ms); LiDAR /scan = sumber utama costmap (depth_scan dimatikan di costmap)
>
> **Bukti yang disebut (kuat):** RPLIDAR C1 -> /scan, frame laser_frame, baud 460800, ~10 Hz; Parameter scan nyata: range 0.15-16 m, ~720 titik; RealSense D455 RGB+Depth 848x480x30, align_depth; IMU D455 accel+gyro -> /imu/data (imu_merger, slop 50 ms); LiDAR /scan = sumber utama costmap (depth_scan dimatikan di costmap); RGB+Depth
>
> **Gambar/tabel:** Screenshot RViz /scan + pointcloud; tabel sensor
>
> **Hindari klaim:** VIO drift pada area minim tekstur/cahaya tidak konsisten; depth_scan salah baca lantai (obstacle hantu) -> dimatikan di costmap; LiDAR 1 bidang horizontal -> obstacle sangat rendah/tinggi bisa terlewa
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.4 ROS 2 Middleware dan Arsitektur Software
> **Tujuan:** jelaskan ROS 2 menghubungkan seluruh subsistem secara modular (7 package) via topic/service/action/TF.
>
> **Data yang dimasukkan:** amr_description (URDF/TF); amr_controller (stm32_bridge, odometry, imu_merger); amr_bringup (master launch + sensor + joy); amr_3d_mapping (RTAB-Map mapping/localization, VIO); amr_slam (Nav2 + SLAM Toolbox)
>
> **Bukti yang disebut (kuat):** amr_description (URDF/TF); amr_controller (stm32_bridge, odometry, imu_merger); amr_bringup (master launch + sensor + joy); amr_3d_mapping (RTAB-Map mapping/localization, VIO); amr_slam (Nav2 + SLAM Toolbox); amr_visual_regression (fallback depth-regression + line segments); amr_failover (arbiter cm
>
> **Gambar/tabel:** Diagram arsitektur package; tabel package
>
> **Hindari klaim:** Konflik TF map->odom bila SLAM Toolbox & RTAB-Map jalan bersamaan (dicegah: gunakan salah satu).
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.5 Model Robot, URDF/Xacro, dan TF Tree
> **Tujuan:** jelaskan Representasi geometris benar agar transform map->odom->base_link ->sensor konsisten untuk mapping, localization, navigation.
>
> **Data yang dimasukkan:** TF tree: base_footprint->base_link->{chassis,roda,steering,laser,camera}; laser_frame z=0.25; camera x=0.35 z=0.20; optical frame REP-103; Geometri wheelbase 0.5 / track 0.4 / wheel_radius 0.0775 / steer ±45; Diagram TF runtime (view_frames); robot_state_publisher load xacro
>
> **Bukti yang disebut (kuat):** TF tree: base_footprint->base_link->{chassis,roda,steering,laser,camera}; laser_frame z=0.25; camera x=0.35 z=0.20; optical frame REP-103; Geometri wheelbase 0.5 / track 0.4 / wheel_radius 0.0775 / steer ±45; Diagram TF runtime (view_frames); robot_state_publisher load xacro
>
> **Gambar/tabel:** frames_*.pdf, RViz RobotModel; tabel geometri
>
> **Hindari klaim:** Diagram frames_*.pdf bertanggal 9 Jun (mungkin belum mencerminkan TF terbaru); TF salah -> mapping/localization/costmap meleset.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.6 Odometry dan Estimasi Gerak
> **Tujuan:** jelaskan Robot mengestimasi perubahan posisi (odometry) sebagai motion prior untuk SLAM & Nav2.
>
> **Data yang dimasukkan:** odometry_publisher (bicycle model Ackermann), 50 Hz; Rumus dist_per_tick=2*pi*r/PPR; theta+=(vx/L)tan(delta)dt; PPR awal 1496 -> kalibrasi 3858; dist_per_tick 0.3255->0.1262 mm; Uji 5 jarak: real=0.3877*odom; R2=0.998; over-report 2.58x; Data eksperimen odom CSV (442 baris + 8 run jalan_maju)
>
> **Bukti yang disebut (kuat):** odometry_publisher (bicycle model Ackermann), 50 Hz; Rumus dist_per_tick=2*pi*r/PPR; theta+=(vx/L)tan(delta)dt; PPR awal 1496 -> kalibrasi 3858; dist_per_tick 0.3255->0.1262 mm; Uji 5 jarak: real=0.3877*odom; R2=0.998; over-report 2.58x; Data eksperimen odom CSV (442 baris + 8 run jalan_maju); publi
>
> **Gambar/tabel:** Plot regresi R2; tabel jarak nyata vs odom
>
> **Hindari klaim:** Sudut setir odometry dibaca dari /joy, bukan /cmd_vel -> saat autonomous murni yaw odom tak update (dikoreksi RTAB-Map); tanpa IMU eksternal yaw drift (dikoreksi scan-matching/loop closure).
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.7 Mapping Lingkungan (RTAB-Map)
> **Tujuan:** jelaskan Robot membangun peta lingkungan (pose graph + occupancy grid) yang valid sebagai basis localization & global costmap.
>
> **Data yang dimasukkan:** Config mapping: Reg/Strategy 2, LoopThr 0.05, MinInliers 8; Launch mapping (RGB-D+Scan+IMU sync, VIO); Peta acuan lab_demo_18jun.db: 448 pose, 125 global + 648 proximity LC, 28.9 m; Analisis agregat 24 DB (19 valid, 2 rusak, 3 kosong); DB terpadat: mapping_20260611_MASTER.db (1526 node, 754 LC)
>
> **Bukti yang disebut (kuat):** Config mapping: Reg/Strategy 2, LoopThr 0.05, MinInliers 8; Launch mapping (RGB-D+Scan+IMU sync, VIO)
>
> **Gambar/tabel:** rtabmap_viz/graph view; tabel metrik DB
>
> **Hindari klaim:** File .db TIDAK ada di repo (di NUC) -> metrik perlu verifikasi ulang rtabmap-info; peta lama ghosting/near-static (sebagian tak layak bukti); screenshot rtabmap_viz/graph belum ada.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.8 Localization terhadap Peta
> **Tujuan:** jelaskan Robot menentukan posisinya terhadap peta acuan (lock) sebelum menerima goal navigasi.
>
> **Data yang dimasukkan:** Config localization: Mem/IncrementalMemory=false, InitWMWithAllNodes=true; Launch localization (rtabmap mode localization + depth_to_scan); Ambang disamakan dgn mapping (LoopThr 0.05, MinInliers 8, DetectionRate 2.0); Root cause loop rejection (ambang localization > mapping) + fix; Bukti lock (loop closure hijau) 18 Jun
>
> **Bukti yang disebut (kuat):** Config localization: Mem/IncrementalMemory=false, InitWMWithAllNodes=true; Launch localization (rtabmap mode localization + depth_to_scan); Ambang disamakan dgn mapping (LoopThr 0.05, MinInliers 8, DetectionRate 2.0); Root cause loop rejection (ambang localization > mapping) + fix
>
> **Gambar/tabel:** Screenshot loop closure hijau; tabel ambang map vs loc
>
> **Hindari klaim:** Bukti runtime lock belum lengkap (screenshot/log /localization_pose, RMSE vs ground truth belum ada); lock tipis bila layout berubah.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.9 Navigation2 Global Planner — Point-to-Point
> **Tujuan:** jelaskan Robot menerima goal dan menghitung lintasan global dari pose saat ini menuju target (point-to-point), Ackermann-aware.
>
> **Data yang dimasukkan:** Planner SmacPlannerHybrid (DUBIN, min turning radius 0.90, reverse_penalty 2.0); Global costmap (static+obstacle+inflation, res 0.05); Action navigate_to_pose (server bt_navigator); goal_sender.py (klien NavigateToPose dari terminal); BT XML path absolut; lifecycle autostart
>
> **Bukti yang disebut (kuat):** Planner SmacPlannerHybrid (DUBIN, min turning radius 0.90, reverse_penalty 2.0); Global costmap (static+obstacle+inflation, res 0.05); Action navigate_to_pose (server bt_navigator); goal_sender.py (klien NavigateToPose dari terminal); BT XML path absolut; lifecycle autostart
>
> **Gambar/tabel:** Screenshot global plan; tabel param planner
>
> **Hindari klaim:** Bukti runtime path belum ada (screenshot RViz plan/log action); area sempit -> no valid path (radius putar 0.90 m).
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.10 Navigation2 Local Planner — Obstacle Avoidant
> **Tujuan:** jelaskan Robot mengikuti lintasan global sambil menghasilkan /cmd_vel yang menghindari rintangan dari costmap lokal.
>
> **Data yang dimasukkan:** Controller RegulatedPurePursuit (desired_linear_vel 0.3, use_rotate_to_heading false); Local costmap 4x4 rolling: voxel_layer + inflation_layer; Obstacle source = LiDAR /scan; depth_scan DIMATIKAN di costmap; robot_radius 0.28; inflation_radius 0.25; cost_scaling 3.0; Output /cmd_vel (velocity_smoother max 0.3)
>
> **Bukti yang disebut (kuat):** Controller RegulatedPurePursuit (desired_linear_vel 0.3, use_rotate_to_heading false); Local costmap 4x4 rolling: voxel_layer + inflation_layer; Obstacle source = LiDAR /scan; depth_scan DIMATIKAN di costmap; robot_radius 0.28; inflation_radius 0.25; cost_scaling 3.0; Output /cmd_vel (velocity_smoot
>
> **Gambar/tabel:** Screenshot local costmap + path; tabel param controller
>
> **Hindari klaim:** Bukti runtime obstacle avoidance belum ada (video/log); depth_scan off -> obstacle sangat rendah/tinggi bisa terlewat (single-plane LiDAR).
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.11 Eksekusi Perintah ke STM32 dan Aktuator
> **Tujuan:** jelaskan Hasil planner (/cmd_vel) diteruskan ke STM32 dan menjadi gerak motor + servo kemudi.
>
> **Data yang dimasukkan:** stm32_bridge subscribe /cmd_vel -> serial V:{pwm},S:{sudut}; Baudrate 115200; konversi steer=-atan(L*w/v); Gate autonomous_enabled (default false -> set true runtime); Remap /cmd_vel->/cmd_vel_nav DIHAPUS (mode demo); Feedback encoder E:{delta} -> /encoder
>
> **Bukti yang disebut (kuat):** stm32_bridge subscribe /cmd_vel -> serial V:{pwm},S:{sudut}; Baudrate 115200; konversi steer=-atan(L*w/v); Gate autonomous_enabled (default false -> set true runtime); Remap /cmd_vel->/cmd_vel_nav DIHAPUS (mode demo); Feedback encoder E:{delta} -> /encoder; PWM ramping (400/call) + watchdog 500 ms
>
> **Gambar/tabel:** Log /cmd_vel; tabel protokol serial
>
> **Hindari klaim:** Masalah historis: remap salah & autonomous_enabled false -> robot diam (sudah diperbaiki); bukti log /cmd_vel saat goal belum dilampirkan.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.12 Safety, Failover, dan Manual Override
> **Tujuan:** jelaskan Sistem aman saat autonomous: e-stop, deadman, arbitrasi sumber gerak.
>
> **Data yang dimasukkan:** Failover state machine (SLAM/VISUAL/JOY/E-STOP); E-stop software: min /scan < 0.30 m -> cmd_vel (0,0); Deadman R1 (button 5); watchdog cmd_vel 500 ms; autonomous_enabled gate; PWM ramping anti-brownout
>
> **Bukti yang disebut (kuat):** Failover state machine (SLAM/VISUAL/JOY/E-STOP); E-stop software: min /scan < 0.30 m -> cmd_vel (0,0); Deadman R1 (button 5); watchdog cmd_vel 500 ms; autonomous_enabled gate; PWM ramping anti-brownout; Mode demo: failover DIBYPASS (Nav2->/cmd_vel langsung)
>
> **Gambar/tabel:** Marker failover RViz; tabel state machine
>
> **Hindari klaim:** Mode demo tanpa failover = tanpa auto e-stop (R1 rem manual wajib); uji failover runtime belum terdokumentasi; e-stop fisik perlu validasi.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.13 Evidence, Testing, dan Gap Validasi
> **Tujuan:** jelaskan Klaim autonomous didukung bukti yang dapat diaudit; gap dinyatakan jujur.
>
> **Data yang dimasukkan:** Konfigurasi sistem (semua YAML/launch/source); Kalibrasi odometry numerik + R2=0.998; Diagram TF (frames_*.pdf); Rantai 8 gerbang Nav2 (kronologi debugging); Analisis 24 DB mapping
>
> **Bukti yang disebut (kuat):** Konfigurasi sistem (semua YAML/launch/source); Kalibrasi odometry numerik + R2=0.998; Diagram TF (frames_*.pdf); Rantai 8 gerbang Nav2 (kronologi debugging)
>
> **Gambar/tabel:** Galeri bukti; checklist gap
>
> **Hindari klaim:** Bukti runtime (lokalisasi, global path, obstacle avoidance, /cmd_vel saat goal, encoder feedback) belum dilampirkan -> gap utama laporan.
>
> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.

## 2.14 Project yang Terselesaikan
> Ringkas capaian per bone dengan status jujur (terbukti file vs perlu bukti runtime). Hindari klaim 'autonomous penuh' tanpa video/log.
