# Fishbone Analysis — AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.

Effect (kepala ikan): **AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.**

Dianalisis melalui 12 tulang (bone). Tiap bone: Requirement -> Implementation evidence -> Dependency -> Risk/Gap -> Report placement.


## Bone A. Platform Hardware dan Aktuator  ->  BAB II 2.2

**Requirement:** Robot memiliki platform fisik 4WD Ackermann yang mampu mengeksekusi gerak translasi & kemudi sesuai perintah navigasi.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Sasis 4WD + 4 roda + 2 steering link | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| Motor PG45 (4WD: 1 motor + 2 diferensial + shaft) | `src/amr_description/urdf/amr_description.urdf.xacro (komentar)` | [VF] |
| Servo kemudi DSSERVO D25, MAX_STEER 45, STEER_TRIM -5 | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| STM32F407 (USB Virtual COM 115200) | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Encoder pada PG45 -> /encoder | `src/amr_controller/src/stm32_bridge.cpp, src/amr_controller/scripts/odometry_publisher.py` | [VF] |
| Geometri: wheelbase 0.5 m, track 0.4 m, wheel_radius 0.0775 m | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| Baterai LiPo Ovonic 5300 mAh 6S (>22 V) | `laporan/progress` | [PG] |
| Driver motor BTS7960 | `Tidak ditemukan di repo saat ini (rancangan)` | [PG] |
| Buck converter / power management | `Tidak ditemukan di repo saat ini` | [BT] |
| Emergency stop FISIK / push button | `Tidak ditemukan di repo (e-stop SOFTWARE ada)` | [BT] |

**Dependency:** Catu daya stabil; firmware STM32; PWM ramping anti-brownout.

**Risk/Gap:** BTS7960/buck/push button tak terbukti di repo; foto fisik belum ada; Ackermann tak bisa rotate-in-place (min turning radius 0.90 m) -> goal sempit gagal; brownout inrush PG45 (dimitigasi PWM ramping).

**Report placement:** BAB II 2.2 Platform Hardware dan Aktuator

## Bone B. Sensor dan Persepsi Lingkungan  ->  BAB II 2.3

**Requirement:** Robot membaca lingkungan (jarak, citra, gerak) sebagai masukan mapping, costmap, odometry, dan localization.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| RPLIDAR C1 -> /scan, frame laser_frame, baud 460800, ~10 Hz | `src/amr_bringup/launch/sensors_launch.py` | [VF] |
| Parameter scan nyata: range 0.15-16 m, ~720 titik | `data_lidar_*.txt (upload)` | [VL] |
| RealSense D455 RGB+Depth 848x480x30, align_depth | `src/amr_bringup/launch/sensors_launch.py` | [VF] |
| IMU D455 accel+gyro -> /imu/data (imu_merger, slop 50 ms) | `src/amr_controller/scripts/imu_merger_node.py` | [VF] |
| LiDAR /scan = sumber utama costmap (depth_scan dimatikan di costmap) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| RGB+Depth+Scan+IMU = input mapping/VIO RTAB-Map | `src/amr_3d_mapping/launch/rtabmap_mapping.launch.py` | [VF] |
| Encoder = sumber odometry | `src/amr_controller/scripts/odometry_publisher.py` | [VF] |
| depth_scan diproduksi depthimage_to_laserscan_node -> /depth_scan | `src/amr_3d_mapping/launch/rtabmap_localization.launch.py` | [VF] |

**Dependency:** TF sensor benar (URDF); sinkronisasi RGB-D-Scan-IMU (approx 0.05 s).

**Risk/Gap:** VIO drift pada area minim tekstur/cahaya tidak konsisten; depth_scan salah baca lantai (obstacle hantu) -> dimatikan di costmap; LiDAR 1 bidang horizontal -> obstacle sangat rendah/tinggi bisa terlewat.

**Report placement:** BAB II 2.3 Sensor dan Persepsi Lingkungan

## Bone C. ROS 2 Middleware dan Arsitektur Software  ->  BAB II 2.4

**Requirement:** ROS 2 menghubungkan seluruh subsistem secara modular (7 package) via topic/service/action/TF.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| amr_description (URDF/TF) | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| amr_controller (stm32_bridge, odometry, imu_merger) | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| amr_bringup (master launch + sensor + joy) | `src/amr_bringup/launch/amr_full.launch.py` | [VF] |
| amr_3d_mapping (RTAB-Map mapping/localization, VIO) | `src/amr_3d_mapping/config/rtabmap_mapping.yaml` | [VF] |
| amr_slam (Nav2 + SLAM Toolbox) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| amr_visual_regression (fallback depth-regression + line segments) | `src/amr_visual_regression/` | [VF] |
| amr_failover (arbiter cmd_vel) | `src/amr_failover/amr_failover/failover_controller.py` | [VF] |
| Env: ROS2 Humble, CycloneDDS, DOMAIN_ID 42 | `SOP/launch` | [PG] |

**Dependency:** colcon --symlink-install; urutan launch sensor->localization->Nav2.

**Risk/Gap:** Konflik TF map->odom bila SLAM Toolbox & RTAB-Map jalan bersamaan (dicegah: gunakan salah satu).

**Report placement:** BAB II 2.4 ROS 2 Middleware dan Arsitektur Software

## Bone D. Model Robot, URDF/Xacro, dan TF Tree  ->  BAB II 2.5

**Requirement:** Representasi geometris benar agar transform map->odom->base_link ->sensor konsisten untuk mapping, localization, navigation.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| TF tree: base_footprint->base_link->{chassis,roda,steering,laser,camera} | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| laser_frame z=0.25; camera x=0.35 z=0.20; optical frame REP-103 | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| Geometri wheelbase 0.5 / track 0.4 / wheel_radius 0.0775 / steer ±45 | `src/amr_description/urdf/amr_description.urdf.xacro` | [VF] |
| Diagram TF runtime (view_frames) | `frames_2026-06-09_22.09.38.pdf` | [VL] |
| robot_state_publisher load xacro | `src/amr_bringup/launch/amr_full.launch.py` | [VF] |

**Dependency:** xacro ter-parse; static TF bridge ke frame RealSense.

**Risk/Gap:** Diagram frames_*.pdf bertanggal 9 Jun (mungkin belum mencerminkan TF terbaru); TF salah -> mapping/localization/costmap meleset.

**Report placement:** BAB II 2.5 Model Robot, URDF/Xacro, dan TF Tree

## Bone E. Odometry dan Estimasi Gerak  ->  BAB II 2.6

**Requirement:** Robot mengestimasi perubahan posisi (odometry) sebagai motion prior untuk SLAM & Nav2.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| odometry_publisher (bicycle model Ackermann), 50 Hz | `src/amr_controller/scripts/odometry_publisher.py` | [VF] |
| Rumus dist_per_tick=2*pi*r/PPR; theta+=(vx/L)tan(delta)dt | `src/amr_controller/scripts/odometry_publisher.py` | [VF] |
| PPR awal 1496 -> kalibrasi 3858; dist_per_tick 0.3255->0.1262 mm | `src/amr_bringup/launch/amr_full.launch.py` | [VF] |
| Uji 5 jarak: real=0.3877*odom; R2=0.998; over-report 2.58x | `src/amr_bringup/launch/amr_full.launch.py (komentar) + data upload` | [VL] |
| Data eksperimen odom CSV (442 baris + 8 run jalan_maju) | `upload (di luar repo)` | [VL] |
| publish_tf kondisional (True hanya saat VIO mati) | `src/amr_bringup/launch/amr_full.launch.py` | [VF] |

**Dependency:** Encoder /encoder valid; wheel_radius & PPR akurat.

**Risk/Gap:** Sudut setir odometry dibaca dari /joy, bukan /cmd_vel -> saat autonomous murni yaw odom tak update (dikoreksi RTAB-Map); tanpa IMU eksternal yaw drift (dikoreksi scan-matching/loop closure).

**Report placement:** BAB II 2.6 Odometry dan Estimasi Gerak

## Bone F. Mapping Lingkungan (RTAB-Map)  ->  BAB II 2.7

**Requirement:** Robot membangun peta lingkungan (pose graph + occupancy grid) yang valid sebagai basis localization & global costmap.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Config mapping: Reg/Strategy 2, LoopThr 0.05, MinInliers 8 | `src/amr_3d_mapping/config/rtabmap_mapping.yaml` | [VF] |
| Launch mapping (RGB-D+Scan+IMU sync, VIO) | `src/amr_3d_mapping/launch/rtabmap_mapping.launch.py` | [VF] |
| Peta acuan lab_demo_18jun.db: 448 pose, 125 global + 648 proximity LC, 28.9 m | `rtabmap-info (.db di ~/maps/ NUC, tidak di repo)` | [PG] |
| Analisis agregat 24 DB (19 valid, 2 rusak, 3 kosong) | `laporan .docx BAB IV` | [PG] |
| DB terpadat: mapping_20260611_MASTER.db (1526 node, 754 LC) | `laporan .docx` | [PG] |

**Dependency:** Odometry/VIO stabil; sensor sinkron; loop closure cukup.

**Risk/Gap:** File .db TIDAK ada di repo (di NUC) -> metrik perlu verifikasi ulang rtabmap-info; peta lama ghosting/near-static (sebagian tak layak bukti); screenshot rtabmap_viz/graph belum ada.

**Report placement:** BAB II 2.7 Mapping Lingkungan (RTAB-Map)

## Bone G. Localization terhadap Peta  ->  BAB II 2.8

**Requirement:** Robot menentukan posisinya terhadap peta acuan (lock) sebelum menerima goal navigasi.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Config localization: Mem/IncrementalMemory=false, InitWMWithAllNodes=true | `src/amr_3d_mapping/config/rtabmap_localization.yaml` | [VF] |
| Launch localization (rtabmap mode localization + depth_to_scan) | `src/amr_3d_mapping/launch/rtabmap_localization.launch.py` | [VF] |
| Ambang disamakan dgn mapping (LoopThr 0.05, MinInliers 8, DetectionRate 2.0) | `src/amr_3d_mapping/config/rtabmap_localization.yaml` | [VF] |
| Root cause loop rejection (ambang localization > mapping) + fix | `docs/root_cause_analysis_nav_lokalisasi.md` | [VF] |
| Bukti lock (loop closure hijau) 18 Jun | `handover/progress` | [PG] |
| Topic /localization_pose | `tidak di-remap eksplisit (rtabmap default mode loc)` | [BT] |

**Dependency:** Peta .db valid; TF benar; ambang localization = mapping.

**Risk/Gap:** Bukti runtime lock belum lengkap (screenshot/log /localization_pose, RMSE vs ground truth belum ada); lock tipis bila layout berubah.

**Report placement:** BAB II 2.8 Localization terhadap Peta

## Bone H. Navigation2 Global Planner — Point-to-Point  ->  BAB II 2.9

**Requirement:** Robot menerima goal dan menghitung lintasan global dari pose saat ini menuju target (point-to-point), Ackermann-aware.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Planner SmacPlannerHybrid (DUBIN, min turning radius 0.90, reverse_penalty 2.0) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Global costmap (static+obstacle+inflation, res 0.05) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Action navigate_to_pose (server bt_navigator) | `src/amr_slam/launch/nav2.launch.py` | [VF] |
| goal_sender.py (klien NavigateToPose dari terminal) | `src/amr_slam/scripts/goal_sender.py` | [VF] |
| BT XML path absolut; lifecycle autostart | `src/amr_slam/config/nav2_params.yaml, src/amr_slam/launch/nav2.launch.py` | [VF] |
| Bringup sukses (8 gerbang) -> lifecycle active | `docs/root_cause_analysis_nav_lokalisasi.md + handover` | [PG] |
| Bukti path runtime (screenshot global plan / log) | `belum ada` | [BT] |

**Dependency:** Peta valid + localization lock + TF map->odom->base_link + lifecycle active.

**Risk/Gap:** Bukti runtime path belum ada (screenshot RViz plan/log action); area sempit -> no valid path (radius putar 0.90 m).

**Report placement:** BAB II 2.9 Navigation2 Global Planner — Point-to-Point

## Bone I. Navigation2 Local Planner — Obstacle Avoidant  ->  BAB II 2.10

**Requirement:** Robot mengikuti lintasan global sambil menghasilkan /cmd_vel yang menghindari rintangan dari costmap lokal.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Controller RegulatedPurePursuit (desired_linear_vel 0.3, use_rotate_to_heading false) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Local costmap 4x4 rolling: voxel_layer + inflation_layer | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Obstacle source = LiDAR /scan; depth_scan DIMATIKAN di costmap | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| robot_radius 0.28; inflation_radius 0.25; cost_scaling 3.0 | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Output /cmd_vel (velocity_smoother max 0.3) | `src/amr_slam/config/nav2_params.yaml` | [VF] |
| Fix obstacle hantu (matikan depth_scan, kecilkan radius) | `docs/root_cause_analysis_nav_lokalisasi.md` | [VF] |
| Bukti avoidance runtime (robot belok hindar obstacle) | `belum ada` | [BT] |

**Dependency:** LiDAR /scan masuk costmap; controller server lifecycle active.

**Risk/Gap:** Bukti runtime obstacle avoidance belum ada (video/log); depth_scan off -> obstacle sangat rendah/tinggi bisa terlewat (single-plane LiDAR).

**Report placement:** BAB II 2.10 Navigation2 Local Planner — Obstacle Avoidant

## Bone J. Eksekusi Perintah ke STM32 dan Aktuator  ->  BAB II 2.11

**Requirement:** Hasil planner (/cmd_vel) diteruskan ke STM32 dan menjadi gerak motor + servo kemudi.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| stm32_bridge subscribe /cmd_vel -> serial V:{pwm},S:{sudut} | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Baudrate 115200; konversi steer=-atan(L*w/v) | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Gate autonomous_enabled (default false -> set true runtime) | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Remap /cmd_vel->/cmd_vel_nav DIHAPUS (mode demo) | `src/amr_slam/launch/nav2.launch.py` | [VF] |
| Feedback encoder E:{delta} -> /encoder | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| PWM ramping (400/call) + watchdog 500 ms | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Bukti aktuator bergerak saat goal (log /cmd_vel != 0) | `progress (19 Jun) / belum ada log` | [PG] |

**Dependency:** Port serial terbuka; autonomous_enabled true; R1 tak ditekan.

**Risk/Gap:** Masalah historis: remap salah & autonomous_enabled false -> robot diam (sudah diperbaiki); bukti log /cmd_vel saat goal belum dilampirkan.

**Report placement:** BAB II 2.11 Eksekusi Perintah ke STM32 dan Aktuator

## Bone K. Safety, Failover, dan Manual Override  ->  BAB II 2.12

**Requirement:** Sistem aman saat autonomous: e-stop, deadman, arbitrasi sumber gerak.

**Status bone:** [VF] Terverifikasi dari file repo

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Failover state machine (SLAM/VISUAL/JOY/E-STOP) | `src/amr_failover/amr_failover/failover_controller.py` | [VF] |
| E-stop software: min /scan < 0.30 m -> cmd_vel (0,0) | `src/amr_failover/amr_failover/failover_controller.py` | [VF] |
| Deadman R1 (button 5); watchdog cmd_vel 500 ms | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| autonomous_enabled gate | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| PWM ramping anti-brownout | `src/amr_controller/src/stm32_bridge.cpp` | [VF] |
| Mode demo: failover DIBYPASS (Nav2->/cmd_vel langsung) | `src/amr_slam/launch/nav2.launch.py` | [VF] |
| E-stop FISIK | `Tidak ditemukan di repo (perlu validasi)` | [BT] |

**Dependency:** failover node aktif (mode lengkap); joystick terhubung.

**Risk/Gap:** Mode demo tanpa failover = tanpa auto e-stop (R1 rem manual wajib); uji failover runtime belum terdokumentasi; e-stop fisik perlu validasi.

**Report placement:** BAB II 2.12 Safety, Failover, dan Manual Override

## Bone L. Evidence, Testing, dan Gap Validasi  ->  BAB II 2.13

**Requirement:** Klaim autonomous didukung bukti yang dapat diaudit; gap dinyatakan jujur.

**Status bone:** [PG] Berdasarkan catatan progress

**Implementation evidence:**

| Faktor teknis | Sumber | Status |
|---|---|---|
| Konfigurasi sistem (semua YAML/launch/source) | `src/ (file-verified)` | [VF] |
| Kalibrasi odometry numerik + R2=0.998 | `src/amr_bringup/launch/amr_full.launch.py + data upload` | [VL] |
| Diagram TF (frames_*.pdf) | `frames_2026-06-09_22.09.38.pdf` | [VL] |
| Rantai 8 gerbang Nav2 (kronologi debugging) | `docs/root_cause_analysis_nav_lokalisasi.md` | [VF] |
| Analisis 24 DB mapping | `laporan .docx + evidence package` | [PG] |
| Screenshot RViz/rtabmap/Nav2, video navigasi, log runtime | `belum ada` | [BT] |

**Dependency:** Sesi lab untuk merekam bukti runtime.

**Risk/Gap:** Bukti runtime (lokalisasi, global path, obstacle avoidance, /cmd_vel saat goal, encoder feedback) belum dilampirkan -> gap utama laporan.

**Report placement:** BAB II 2.13 Evidence, Testing, dan Gap Validasi
