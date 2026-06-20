# Laporan Teknis Final — Autonomous Mobile Robot (AMR) Ackermann Indoor

**Proyek:** PjBL Autonomous Mobile Robot — Kelompok 4-24
**Penyusun utama:** Muhammad Al Azhar Faradis (NRP 2040241017)
**Kolaborator:** Mararevi Subagyo (NRP 2040241036)
**Institusi:** Departemen Teknik Elektro Otomasi, Institut Teknologi Sepuluh Nopember (ITS) Surabaya
**Platform:** ROS 2 Humble · Ubuntu 22.04 · Intel NUC13ANHi7

> Dokumen ini merekap **praktik, teori, metode, konfigurasi, dan plugin** yang dipakai
> sepanjang pembangunan proyek, sebagai bahan dasar penyusunan laporan final PjBL.
> Semua parameter dikutip langsung dari source code repository (bukan asumsi).

---

## 1. Ringkasan Proyek

AMR ini adalah robot **4WD bergaya kemudi Ackermann** (2 roda depan berbelok via servo,
penggerak 4 roda dari 1 motor) untuk navigasi otonom **indoor**. Sistem mampu:

1. **Mapping 3D** lingkungan (RGB-D + LiDAR) menghasilkan peta `.db` RTAB-Map.
2. **Lokalisasi** robot terhadap peta yang sudah dibuat (mode frame-to-map).
3. **Navigasi otonom** (Nav2): kirim goal → perencanaan jalur Ackermann-aware → eksekusi gerak.
4. **Teleoperasi manual** via joystick PS4/PS5 dengan tombol deadman (R1).
5. **Failover / arbitrasi** antara sumber `cmd_vel` (Nav2, visual regression, joystick, e-stop).

Tujuan akhir demo: **robot bergerak sendiri dari goal Nav2 di atas peta indoor**.

---

## 2. Arsitektur Perangkat Keras

| Komponen | Spesifikasi | Catatan |
|----------|-------------|---------|
| Compute | Intel NUC13ANHi7, Ubuntu 22.04 | Host ROS 2 Humble |
| Mikrokontroler | STM32 (USB Virtual COM Port, 115200 baud) | Driver motor + servo + encoder |
| Penggerak | 1× Motor PG45 + 2 differential + shaft (4WD) | Single drive motor |
| Kemudi | Servo tunggal, Ackermann 2WS (2 roda depan tersinkron mekanis) | `MAX_STEER = 45°`, `STEER_TRIM = -5°` |
| LiDAR | RPLIDAR C1 (2D 360°), 460800 baud | Topik `/scan`, frame `laser_frame` |
| Kamera | Intel RealSense D455 (RGB-D + IMU internal) | RGB & Depth `848×480×30` |
| IMU | IMU internal RealSense D455 (gyro + accel) | Dipakai untuk VIO + gravity constraint |
| GPS | **Dicopot** (platform indoor) | Antena GNSS tidak terpasang |

**Geometri robot (dari URDF & odometry):**
- Wheelbase: **0.50 m**
- Wheel radius: **0.0775 m** (diameter 155 mm)
- PPR efektif (kalibrasi empiris): **3858** (lihat §8)

---

## 3. Arsitektur Perangkat Lunak (7 Package ROS 2)

| Package | Peran | Isi utama |
|---------|-------|-----------|
| `amr_description` | Model robot | URDF/Xacro: chassis, 4 roda, 2 steering link, LiDAR, kamera |
| `amr_controller` | Jembatan HW + odometry | `stm32_bridge` (C++), `odometry_publisher` (Py), `imu_merger_node` (Py) |
| `amr_bringup` | Orkestrasi launch | `amr_full.launch.py` (master), `sensors_launch.py`, `amr_launch.py`, `joy_params.yaml` |
| `amr_3d_mapping` | SLAM 3D | RTAB-Map config + launch (mapping & localization, VIO) |
| `amr_slam` | SLAM 2D + Nav2 | SLAM Toolbox config + `nav2_params.yaml` + `nav2.launch.py` |
| `amr_visual_regression` | Path B (fallback) | Regresi depth-statistic (scikit-learn, tanpa CNN), LiDAR line segments |
| `amr_failover` | Arbiter cmd_vel | State machine SLAM/Visual/Joy/E-Stop |

### 3.1 Diagram Aliran Data (pipeline autonomous)

```
[HARDWARE]                  [SOFTWARE]                         [OUTPUT]
STM32 + Motor ◄── UART ──── stm32_bridge ◄──────────────────── /cmd_vel
                             (autonomous_enabled=true,             ▲
                              R1 tidak ditekan)                    │
Encoder ────────────────────► /encoder ──► odometry_publisher ──► /odom
RPLIDAR C1 ─────────────────► /scan ──────────────► Nav2 ─────────┤
RealSense D455                                       (Controller +  │
  RGB+Depth ──► rgbd_sync ──► /rgbd_image            Planner)       │
  IMU       ──┘                  │                                  │
                                 ├─► rgbd_odometry (VIO) ─► /odom   │
                                 └─► RTAB-Map ─► /map, /cloud_map ──┘
                                     (localization)
```

---

## 4. Teori & Metode yang Diterapkan

### 4.1 Kinematika Ackermann (Bicycle Model)

Odometry roda memakai model sepeda (bicycle kinematic):

```
distance_per_tick = 2·π·wheel_radius / PPR
vx     = Δdistance / dt
θ̇      = (vx / wheelbase) · tan(δ)         ; δ = sudut kemudi
x     += Δdistance · cos(θ + Δθ/2)
y     += Δdistance · sin(θ + Δθ/2)
θ     += θ̇ · dt
```

Untuk Nav2, konversi `Twist` → kemudi memakai:
```
δ = atan(wheelbase · ω / v)               ; ω = angular.z, v = linear.x
```

Keterbatasan Ackermann tercermin di konfigurasi Nav2:
- **Tidak bisa rotate-in-place** → `use_rotate_to_heading: false`
- **Radius belok minimum** `minimum_turning_radius: 0.90 m` (≈ L/tan(30°) + margin)
- Planner memakai model gerak **DUBIN** (maju saja, Ackermann-aware)

### 4.2 Visual-Inertial Odometry (VIO)

`rgbd_odometry` (RTAB-Map) menggantikan wheel odometry saat mapping 3D:
- Strategi **Frame-to-Map** (`Odom/Strategy: 0`) — lebih robust daripada frame-to-frame.
- IMU RealSense membantu prediksi gerak (`Odom/GuessMotion: true`) + gravity constraint.
- Anti-divergence: `Odom/MaxVariance` (buang frame saat tracking tidak yakin),
  `Odom/ResetCountdown: 5` (toleran motion blur).

### 4.3 SLAM & Loop Closure (RTAB-Map)

- **Registrasi `Reg/Strategy: 2` (Vis + ICP):** visual feature untuk initial estimate,
  ICP LiDAR untuk koreksi halus (menyelamatkan area minim tekstur).
- **Loop closure** via Bag-of-Words (BoW): `Kp/*` membangun vocabulary, `Rtabmap/LoopThr`
  ambang penerimaan, proximity loop closure (`RGBD/ProximityBySpace`) untuk koreksi drift.
- **Force 3DoF** (`Reg/Force3DoF: true`): robot lantai → hanya x, y, yaw.

### 4.4 Depth-to-LaserScan & Visual Regression (Path B)

- Kamera depth dapat dipakai sebagai sumber obstacle tambahan (`/depth_scan`).
- **Visual Regression** = pendekatan klasik (Random Forest Regressor, scikit-learn) yang
  memetakan statistik depth → perintah gerak `/cmd_vel_visual` **tanpa CNN**.
  Pipeline: `data_collector_node` → `train.py` (offline) → `vr_inference_node` (real-time).
- **LiDAR line segments** (RANSAC) sebagai overlay deteksi dinding/koridor.

---

## 5. Konfigurasi Nav2 (Stack Navigasi)

File: `src/amr_slam/config/nav2_params.yaml`

### 5.1 Plugin yang dipakai

| Server | Plugin | Format namespace |
|--------|--------|------------------|
| Controller | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController` | `::` |
| Progress checker | `nav2_controller::SimpleProgressChecker` | `::` |
| Goal checker | `nav2_controller::SimpleGoalChecker` | `::` |
| Planner | `nav2_smac_planner/SmacPlannerHybrid` | `/` |
| Smoother | `nav2_smoother::SimpleSmoother` | `::` |
| Costmap layers | `nav2_costmap_2d::{Voxel,Obstacle,Static,Inflation}Layer` | `::` |
| Behaviors | `nav2_behaviors/{Spin,BackUp,DriveOnHeading,Wait}` | `/` |
| Waypoint | `nav2_waypoint_follower::WaitAtWaypoint` | `::` |

> **Pelajaran penting:** Nav2 Humble pakai campuran `::` (costmap/controller/smoother/waypoint)
> dan `/` (smac_planner/behaviors). Salah format → plugin gagal load.

### 5.2 Parameter kunci

- **Controller (RPP):** `desired_linear_vel: 0.3` (diturunkan dari 0.4 supaya VIO tidak lost),
  `allow_reversing: true`, `use_rotate_to_heading: false`.
- **Planner (Smac Hybrid):** `motion_model_for_search: DUBIN`, `minimum_turning_radius: 0.90`,
  `reverse_penalty: 2.0`, `angle_quantization_bins: 72`.
- **Costmap:** `robot_radius: 0.28`, `inflation_radius: 0.25`, resolusi `0.05 m`.
  Observasi obstacle **hanya dari LiDAR `/scan`** (depth_scan dimatikan — lihat §7 fix #6).
- **Velocity smoother:** `max_velocity: [0.3, 0.0, 0.5]`, akselerasi dihaluskan
  (`max_accel: [1.0, 0.0, 1.5]`) agar start/stop tidak bikin IMU spike → VIO confused.

---

## 6. Konfigurasi RTAB-Map (Mapping & Localization)

### 6.1 Prinsip kunci: ambang localization HARUS = ambang mapping

Parameter loop closure yang dipakai saat mapping **ter-baked di dalam `.db`**. Saat
localization, ambang **tidak boleh lebih ketat** — kalau tidak, loop closure valid selalu
ditolak walau peta sehat.

| Parameter | Mapping (`.db`) | Localization (setelah fix) |
|-----------|-----------------|----------------------------|
| `Rtabmap/LoopThr` | 0.05 | 0.05 |
| `Vis/MinInliers` | 8 | 8 |
| `Rtabmap/DetectionRate` | 2.0 Hz | 2.0 Hz |
| `Kp/MaxFeatures` | 400 | 400 |
| `Kp/DetectorStrategy` | 8 (GFTT/BRIEF) | 8 |
| `RGBD/LoopClosureReextractFeatures` | true | true |
| `RGBD/OptimizeMaxError` | 5.0 | 5.0 |
| `Mem/STMSize` | 10 | 10 |

### 6.2 Parameter mapping lain yang signifikan

- `Vis/FeatureType: 8` (GFTT/BRIEF, ringan), `Vis/MaxFeatures: 1000`
- `GFTT/QualityLevel: 0.001` (sensitif untuk area minim tekstur)
- `Grid/CellSize: 0.05` (match Nav2), `Grid/RangeMax: 5.0`
- `Optimizer/GravitySigma: 0.3` (IMU gravity constraint aktif)
- `Mem/STMSize: 10` (fix pola "double-room" di lab sempit)
- Mode sinkronisasi: `approx_sync` slop **0.05 s** untuk RGB+Depth+Scan+IMU

### 6.3 RealSense (sumber RGB-D + IMU)

- Profil **848×480×30** untuk RGB dan Depth (TIDAK diubah — konsisten dgn kalibrasi).
- `align_depth.enable: true`, IMU gyro+accel aktif (`unite_imu_method: 2`).
- Filter: temporal + spatial ON, decimation OFF.
- Exposure tuning: auto-exposure ON + gain dinaikkan untuk area gelap (VIO tracking).

---

## 7. Kronologi Penyelesaian Masalah (Root Cause → Fix)

Bagian ini merekam masalah nyata yang ditemukan & diperbaiki selama proyek.

### 7.1 Rantai 8 Gerbang Nav2 (berurutan memblokir bringup)

| # | Gejala | Akar masalah | Fix |
|---|--------|--------------|-----|
| 1 | `VoxelLayer does not exist` | Format plugin `/` vs `::` campur | Samakan format per package |
| 2 | `ID [RemovePassedGoals] already registered` (crash) | Blok `plugin_lib_names` eksplisit → double-registration | Hapus blok → Nav2 auto-load |
| 3 | `Node not recognized: RateController` | Turunan #2 | Terselesaikan bersama #2 |
| 4 | `Action server spin not available` | `spin` tak terdaftar, padahal BT default memanggilnya | Tambah `spin: nav2_behaviors/Spin` |
| 5 | `Couldn't open input XML file` | `default_nav_to_pose_bt_xml` bukan path absolut | Pakai path absolut `/opt/ros/humble/share/...` |
| 6 | `collision ahead` / lethal terus | `depth_scan` salah baca lantai = obstacle hantu | Matikan depth_scan di costmap (LiDAR saja), kecilkan radius |
| 7 | Nav2 kirim cmd_vel, robot diam (`Failed to make progress`) | Remap `/cmd_vel`→`/cmd_vel_nav`, bridge dengar `/cmd_vel` | Hapus remap di `nav2.launch.py` |
| 8 | Robot tetap diam walau `/cmd_vel`≠0 | `autonomous_enabled` default `false` (safety gate) | `ros2 param set /stm32_bridge autonomous_enabled true` (runtime) |

### 7.2 Lokalisasi: loop rejection

- **Gejala:** RTAB-Map log `Loop closure rejected` terus → robot tak pernah lock.
- **Akar masalah:** config localization 2× lebih ketat dari ambang mapping + 3 parameter hilang
  (`Kp/*`, `RGBD/LoopClosureReextractFeatures`).
- **Fix:** samakan semua ambang ke nilai mapping (tabel §6.1).

### 7.3 Kualitas peta: mapping "menjalar" / ghosting

- **Gejala:** peta 17 Juni (1224 pose, ~175 m) 3D cloud menjalar karena drift VIO akumulatif.
- **Fix metode:** **mapping ulang 1 loop pendek & bersih** → `lab_demo_18jun.db`
  (448 pose, 28.9 m). Prinsip: **kualitas > kuantitas**.

### 7.4 Arah motor / kemudi terbalik

- **Gejala (autonomous):** perintah belok kiri → roda depan belok kanan (kebalik).
- **Akar masalah (bench test):** tanda kemudi pada formula Ackermann terbalik. Velocity
  maju/mundur sudah benar (kabel motor sudah ditukar fisik oleh setup lab).
- **Fix:** negasi `steer_rad` → `steer_rad = -atan(wheelbase·ω/v)` di `cmd_vel_callback`.
  *(Status: menunggu verifikasi hardware sebelum final.)*

### 7.5 Brownout power-rail saat motor inrush

- **Gejala:** SSH freeze + RealSense timeout saat motor start (uji EMI).
- **Akar masalah:** lonjakan arus inrush motor PG45 bikin tegangan NUC sag.
- **Fix:** software ramping PWM (`MAX_PWM_STEP = 400`/call), e-stop bypass ramp untuk safety.

---

## 8. Kalibrasi Empiris

### 8.1 PPR Encoder (odometry)

- **Metode:** uji odom-vs-meteran 5 jarak (0.5/1.0/1.5/2.0/2.5 m → 22/41/61/81/96 cm).
- **Hasil:** faktor over-report **2.58×**, regresi proporsional **real = 0.3877·odom**, **R² = 0.998**.
- **Koreksi:** PPR efektif = 1496 / 0.3877 = **3858** (dist_per_tick 0.3255 → 0.1262 mm).

### 8.2 Validasi peta produksi `lab_demo_18jun.db`

| Metrik | Nilai |
|--------|-------|
| Sessions | 1 (single coherent run) |
| Durasi mapping | ~17 menit (1012 s) |
| Panjang trajektori | 28.9 m |
| Pose (optimized graph) | 448 |
| Nodes (LTM) | 1846, 126.506 words |
| Global loop closures | 125 |
| Proximity loop closures | 648 |
| Jarak antar-keyframe | 0.06 m |
| Ukuran database | 743 MB (Depth 56% · RGB 25% · Features 10% · Grid 5%) |

---

## 9. Failover Controller (Arbitrasi cmd_vel)

State machine (`amr_failover`):

| State | Output `/cmd_vel` | Trigger |
|-------|-------------------|---------|
| `SLAM_ACTIVE` (default) | `/cmd_vel_nav` | Nav2 sehat |
| `VISUAL_FALLBACK` | `/cmd_vel_visual` | SLAM/Nav2 gagal → regresi visual |
| `JOY_OVERRIDE` | `/cmd_vel_joy` | Deadman R1 ditekan |
| `EMERGENCY_STOP` | `(0, 0)` | Kondisi bahaya |

> **Catatan demo:** untuk demo saat ini failover **dibypass** (Nav2 → `/cmd_vel` langsung).
> Konsekuensi: tidak ada auto e-stop → joystick R1 = rem darurat manual wajib siap.

---

## 10. Standard Operating Procedure (SOP Demo Autonomous)

Setiap terminal diawali:
```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/humble/setup.bash
cd ~/amr_starter && source install/setup.bash
```

| Terminal | Perintah |
|----------|----------|
| 1 — Sensor (tanpa failover) | `ros2 launch amr_bringup amr_full.launch.py use_slam:=false use_nav2:=false use_rtabmap:=false use_failover:=false` |
| 2 — Localization | `ros2 launch amr_3d_mapping rtabmap_localization.launch.py database_path:=$HOME/maps/lab_demo_18jun.db` |
| 3 — Nav2 | `ros2 launch amr_slam nav2.launch.py` (tunggu `Managed nodes are active`) |
| 4 — Gerbang + Goal | `ros2 param set /stm32_bridge autonomous_enabled true` lalu kirim goal `/navigate_to_pose` |

---

## 11. Known Issues & Batasan

1. **Peta vs layout:** lokalisasi melemah jika layout ruangan berubah → solusi: mapping ulang.
2. **Ackermann butuh ruang manuver** (radius belok 0.90 m) → goal di area sempit gagal (`no valid path`).
3. **Tanpa failover = tanpa auto e-stop** → R1 wajib di tangan.
4. **depth_scan dimatikan di costmap** → obstacle sangat rendah/tinggi bisa terlewat (LiDAR 1 bidang).
5. **Odometry membaca setir hanya dari `/joy`** (`odometry_publisher.py`) → saat autonomous murni
   yaw odom tidak terupdate dari `/cmd_vel`; dikoreksi oleh RTAB-Map. (Fix sinkron `/cmd_vel`
   tersedia di repo kolaborator, belum diadopsi.)
6. **Hardware:** jaga LiPo > 22 V (servo brownout), charge joystick (input drift saat lowbat).

---

## 12. Pelajaran Kunci (untuk laporan)

1. **Konsistensi ambang mapping↔localization** menentukan keberhasilan lokalisasi RTAB-Map.
2. **Kualitas peta > kuantitas:** 1 loop bersih (28.9 m) > banyak lap panjang (175 m).
3. **Pipeline autonomous = rantai gerbang berurutan;** satu gerbang gagal memblokir semua,
   sehingga debugging harus sistematis (symptom → root cause → fix → verifikasi).
4. **Verifikasi empiris menang atas teori:** masalah arah terbukti bench test (kemudi), bukan
   asumsi motor terbalik.
5. **Kalibrasi empiris wajib:** PPR teoretis (1496) meleset 2.58× dari realita (3858).
6. **Safety by design:** `autonomous_enabled` default false, deadman R1, PWM ramping anti-brownout.

---

## 13. Daftar File Konfigurasi Acuan

| Fungsi | File |
|--------|------|
| Master launch | `src/amr_bringup/launch/amr_full.launch.py` |
| Sensor | `src/amr_bringup/launch/sensors_launch.py` |
| Nav2 params | `src/amr_slam/config/nav2_params.yaml` |
| RTAB-Map mapping | `src/amr_3d_mapping/config/rtabmap_mapping.yaml` |
| RTAB-Map localization | `src/amr_3d_mapping/config/rtabmap_localization.yaml` |
| Bridge HW | `src/amr_controller/src/stm32_bridge.cpp` |
| Odometry | `src/amr_controller/scripts/odometry_publisher.py` |
| Analisis akar masalah | `docs/root_cause_analysis_nav_lokalisasi.md` |
| SOP | `docs/SOP_MAPPING_DAN_AUTONOMOUS.md` |
