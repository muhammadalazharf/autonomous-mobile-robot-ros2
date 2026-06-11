# HANDOVER: AMR Ackermann — Dari Claude Code ke Gemini

**Tanggal:** 11 Juni 2026, ~20:00 WIB
**Pemilik:** Muhammad Al Azhar Faradis (NRP 2040241017, ITS Surabaya)
**Repo:** https://github.com/muhammadalazharf/autonomous-mobile-robot-ros2
**Branch aktif:** `claude/zealous-darwin-6l4bs5`

---

## 1. APA INI?

Robot mobile otonom (AMR) bergerak roda 4 dengan steering Ackermann (belok depan, mirip mobil). Dipakai untuk:
- **Tugas Akhir (TA):** mapping 3D + navigasi otonom indoor
- **Korelasi mata kuliah:** Metode Numerik, DCS SCADA, Pengolahan Citra Digital (PCD)

**Deadline sangat ketat — target malam ini: satu sesi mapping berhasil.**

---

## 2. HARDWARE

| Komponen | Detail |
|----------|--------|
| Komputer | Intel NUC13ANHi7 (i7, Ubuntu 22.04, ROS 2 Humble) |
| Kamera | Intel RealSense D455 (RGB+Depth 848x480x30, Accel 100Hz, Gyro 200Hz) |
| LiDAR | RPLIDAR C1 (2D, 360 derajat, 10Hz, max 16m) |
| Mikrokontroler | STM32F407 (serial bridge: menerima V:{pwm},S:{sudut}, mengirim E:{delta_encoder}) |
| Steering | Ackermann 2WS (roda depan saja), wheelbase 0.5m, radius putar min 0.90m |
| Joystick | PS4/PS5 DualShock via Bluetooth, R1 = deadman switch |
| USB | D455 di USB 3.2 (port 4-3), LiDAR + STM32 via USB serial |

---

## 3. ARSITEKTUR SOFTWARE

```
Terminal 1: amr_full.launch.py (sensor + driver)
  robot_state_publisher (URDF → TF)
  joy_node (joystick Bluetooth)
  stm32_bridge (joystick → STM32 serial, encoder → /encoder)
  rplidar_node (/scan, 10Hz, QoS BestEffort)
  realsense2_camera_node (RGB, Depth, Accel, Gyro)
  static_tf_color_bridge + static_tf_depth_bridge
  odometry_publisher.py (/odom wheel, publish_tf=False saat RTAB-Map aktif)

Terminal 2: rtabmap_mapping.launch.py (SLAM 3D)
  imu_merger_node.py (accel + gyro → /imu/data)
  rgbd_sync (RGB + Depth → /rgbd_image)
  rgbd_odometry (VIO: /rgbd_image + /imu/data → /rtabmap/odom + TF odom→base_link)
  rtabmap (SLAM: /rgbd_image + /scan + /rtabmap/odom → peta 3D + loop closure)
  depth_to_laserscan (/depth_scan untuk Nav2, terpisah dari /scan LiDAR)

Terminal 3 (nanti): Nav2 stack (navigasi otonom)
Terminal 4 (opsional): record_sensor_evidence.sh (rekam data untuk laporan)
```

### Alur Data Kunci

```
RealSense D455 ──RGB+Depth──→ rgbd_sync ──/rgbd_image──→ rgbd_odometry ──/rtabmap/odom──→ rtabmap SLAM
                ──Accel+Gyro──→ imu_merger ──/imu/data──→ rgbd_odometry                      ↑
RPLIDAR C1 ─────────/scan────────────────────────────────────────────────────────────────────→─┘
                                                                                      ↓
                                                                          /rtabmap/mapData (graph SLAM)
                                                                          /rtabmap/cloud_map (3D)
                                                                          /rtabmap/grid_map (2D occupancy)
```

---

## 4. STATUS SAAT HANDOVER

### Yang Sudah Jalan (Verified)
- Semua sensor sehat: RealSense D455 (Depth+Color+Accel+Gyro), RPLIDAR C1 (10Hz), joystick
- VIO (Visual-Inertial Odometry) menghasilkan /rtabmap/odom ~30Hz
- /rgbd_image ~29Hz dari rgbd_sync
- /scan ~10Hz dari rplidar
- TF chain: map → odom → base_link → laser_frame lengkap
- Script rekaman sensor (`scripts/record_sensor_evidence.sh`) sudah siap

### Fix Terakhir Yang Baru Diterapkan (KRITIS)
**QoS Mismatch Fix (commit `b17e8fb`):**
- rplidar publish `/scan` dengan QoS **BestEffort**
- rtabmap default subscribe dengan QoS **Reliable**
- Di ROS 2 DDS: Reliable subscriber TIDAK BISA menerima dari BestEffort publisher
- **Akibat:** rtabmap tidak pernah menerima data /scan → sync gagal → "Did not receive data since 5 seconds" → tidak ada mapData/cloud_map/grid_map
- **Fix:** tambah `'qos': 1` (SensorDataQoS = BestEffort) di parameter inline rtabmap SLAM node
- **Status:** sudah di-commit dan push, BELUM DITEST di NUC (user sedang apply manual)

### Yang Belum Ditest
- Standby test ulang setelah QoS fix (apakah /rtabmap/mapData muncul)
- Mapping run sesungguhnya (robot bergerak, loop closure, cloud_map akumulasi)
- Sensor evidence recording saat mapping

### Yang Belum Dikerjakan
- Nav2 params untuk Ackermann (nav2_params.yaml masih banyak yang salah):
  - `minimum_turning_radius`: 0.5 → harus 0.90m
  - `allow_reversing`: true → harus false
  - `min_y_velocity_threshold`: 0.5 → harus 0.001
  - `inflation_radius`: 0.45 → harus 0.55
  - Plugin `Spin` harus dihapus (Ackermann tidak bisa spin in-place)
- Firmware STM32: PWM tidak boleh menerima nilai negatif (butuh if-else di main.c)
- Integrasi PCD node (pcd_prototype/) ke pipeline ROS 2 utama

---

## 5. FILE PENTING DAN LOKASINYA

| File | Fungsi | Catatan |
|------|--------|---------|
| `src/amr_bringup/launch/amr_full.launch.py` | Master launch | Flag: use_rtabmap, use_nav2, use_slam, dll |
| `src/amr_3d_mapping/launch/rtabmap_mapping.launch.py` | SLAM 3D mapping | 5 node, semua param inline |
| `src/amr_3d_mapping/launch/rtabmap_localization.launch.py` | Lokalisasi di peta fixed | Mem/IncrementalMemory=false |
| `src/amr_3d_mapping/config/rtabmap_mapping.yaml` | YAML config (secondary) | Inline di launch override ini |
| `src/amr_3d_mapping/config/rtabmap_localization.yaml` | YAML config lokalisasi | Idem |
| `src/amr_controller/src/stm32_bridge.cpp` | Serial bridge joystick→STM32 | V:{pwm},S:{sudut}\n |
| `src/amr_controller/scripts/odometry_publisher.py` | Wheel odometry (backup) | publish_tf HARUS False |
| `src/amr_controller/scripts/imu_merger_node.py` | Merge accel+gyro→/imu/data | ApproximateTimeSynchronizer |
| `src/amr_slam/config/nav2_params.yaml` | Nav2 config | BANYAK YANG SALAH, lihat Seksi 4 |
| `scripts/record_sensor_evidence.sh` | Rekam data sensor saat mapping | ros2 bag record -a minus berat |
| `scripts/analyze_sensor_bag.py` | Analisis bag → CSV + summary | Dispatch by message type |
| `pcd_prototype/amr_pcd_prototype.py` | Pipeline PCD standalone | OpenCV, TIDAK boleh bareng kamera ROS |
| `docs/SOP_MAPPING_DAN_AUTONOMOUS.md` | SOP operasional | Urutan terminal, checklist |

---

## 6. PARAMETER KRITIS RTAB-Map (JANGAN UBAH TANPA ALASAN)

### VIO (rgbd_odometry node)
```
Odom/Strategy: '0'           # Frame-to-Map (lebih robust)
Odom/MaxVariance: '0.05'     # Batas variance — 0.01 terlalu ketat untuk textureless
Odom/ResetCountdown: '5'     # Toleransi motion blur sebelum reset
Vis/MinInliers: '8'          # PnP butuh min 8 inlier (2 = penyebab scattered cloud)
Vis/MaxFeatures: '1000'      # Fitur tracking
Reg/Force3DoF: 'true'        # Ground vehicle: x, y, yaw saja
```

### SLAM (rtabmap node)
```
Reg/Strategy: '2'            # Vis+ICP: visual initial + LiDAR fine correction
Rtabmap/LoopThr: '0.05'      # Agresif loop closure (fix double-room)
Rtabmap/DetectionRate: '2.0'  # Deteksi 2x per detik
RGBD/OptimizeMaxError: '5.0'  # Terima koreksi besar saat loop closure
RGBD/ProximityBySpace: 'true' # Proximity-based loop closure aktif
RGBD/LoopClosureReextractFeatures: 'true' # Re-extract fitur saat verifikasi
Mem/STMSize: '10'            # Node cepat pindah ke WM (fix double-room)
Optimizer/GravitySigma: '0.3' # IMU gravity constraint aktif
qos: 1                       # WAJIB: BestEffort untuk terima /scan dari rplidar
subscribe_rgb: False          # WAJIB: cegah konflik dengan subscribe_rgbd
topic_queue_size: 30          # Samakan dengan sync_queue_size
```

---

## 7. HARD RULES (DILARANG DILANGGAR)

1. **JANGAN push ke branch `main`** — selalu kerja di branch feature
2. **JANGAN ubah resolusi RealSense** dari 848x480x30 (RGB dan Depth)
3. **JANGAN set `publish_tf=True` di odometry_publisher.py** — TF conflict dengan VIO
4. **JANGAN ubah URDF** (`src/amr_description/`) kecuali diminta eksplisit
5. **JANGAN install package baru** tanpa menyatakan dulu apa dan kenapa
6. **JANGAN rebuild full workspace** (`colcon build` tanpa `--packages-select`)
7. **JANGAN hapus file/folder** tanpa konfirmasi eksplisit dari owner
8. **JANGAN klaim "sudah jalan"** tanpa output command sebagai bukti
9. **JANGAN fabricate spec hardware** atau parameter yang tidak ada
10. **JANGAN ganti algoritma fundamental** (misal VIO → wheel odom) tanpa diskusi panjang

### 7 Patch Yang TIDAK BOLEH Di-Revert
1. `odometry_publisher.py`: `publish_tf=False` (cegah TF conflict)
2. `CMakeLists.txt`: install `imu_merger_node.py`
3. `sensors_launch.py`: `respawn=True` untuk LiDAR + RealSense
4. `nav2_params.yaml`: `motion_model: DUBIN` (Ackermann)
5. `stm32_bridge.cpp`: trim steering + format encoder
6. `imu_merger_node.py`: node merger accel+gyro
7. `rtabmap_mapping.launch.py`: VIO chain lengkap

---

## 8. CARA MENJALANKAN

### Mapping (target malam ini)
```bash
# Terminal 1: Sensor + driver
ros2 launch amr_bringup amr_full.launch.py use_slam:=false use_nav2:=false use_rtabmap:=false

# Terminal 2: SLAM 3D (tunggu Terminal 1 stabil ~5 detik)
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py

# Terminal 3 (opsional): Rekam data sensor untuk laporan
bash scripts/record_sensor_evidence.sh run1

# Terminal 4: Verifikasi
ros2 topic list | grep rtabmap
ros2 topic hz /rtabmap/odom
```

### Rebuild setelah edit file
```bash
cd ~/amr_starter
colcon build --packages-select amr_3d_mapping --symlink-install
source install/setup.bash
```

### Analisis data setelah mapping
```bash
python3 scripts/analyze_sensor_bag.py ~/mapping_evidence/run1_YYYYMMDD_HHMMSS
```

---

## 9. MASALAH YANG PERNAH TERJADI DAN SOLUSINYA

| Masalah | Akar Penyebab | Solusi |
|---------|---------------|--------|
| "Did not receive data since 5 seconds" | QoS mismatch: rplidar BestEffort vs rtabmap Reliable | `qos: 1` di parameter rtabmap |
| "subscribe_rgb and subscribe_rgbd cannot be true" | Default subscribe_rgb=true di rtabmap internal | `subscribe_rgb: False` eksplisit |
| Cloud 3D scattered/fraktal | Vis/MinInliers=2 (PnP terima pose random) | Naikkan ke 8 |
| VIO reset terus-menerus | Odom/MaxVariance=0.01 terlalu ketat | Naikkan ke 0.05 |
| Double-room pattern (ruangan terduplikasi di peta) | Loop closure gagal match di area sempit | LoopThr turun ke 0.05, STMSize turun ke 10 |
| mapData/grid_map tidak muncul | YAML namespace mismatch (rtabmap_slam vs rtabmap) | Pindahkan semua param ke inline di launch |
| IR stream start failure (RealSense) | USB initialization glitch | Cabut-colok USB, atau `sudo usbreset` |
| TF conflict odom→base_link | Dua node publish TF sama (VIO + wheel odom) | publish_tf=False di odometry_publisher |
| Encoder sign terbalik | Arah putaran motor vs konvensi firmware | Negate delta di stm32_bridge (lokal NUC) |

---

## 10. PRIORITAS KERJA (URUTAN)

1. **[SEKARANG] Verifikasi QoS fix** — ulangi standby test, pastikan /rtabmap/mapData muncul
2. **[MALAM INI] Mapping run** — gerakkan robot, dapatkan satu .db yang bersih
3. **[MALAM INI] Rekam evidence** — jalankan record_sensor_evidence.sh bersamaan mapping
4. **[BESOK] Nav2 Ackermann fix** — perbaiki nav2_params.yaml (9 parameter salah)
5. **[BESOK] Localization test** — load .db hasil mapping, test navigasi otonom
6. **[NANTI] Integrasi PCD** — gabungkan pcd_prototype ke pipeline ROS 2

---

## 11. KONTAK DAN KOLABORATOR

- **Owner:** Muhammad Al Azhar Faradis (malazharfaradis@gmail.com)
- **Teammate:** Mervi — repo fork: https://github.com/Mervs111/autonomous-mobile-robot-ros2
  - Kontribusi: PCD prototype, SOP docs, RViz config (sudah di-cherry-pick)
  - **HELD commit:** Mervi punya cmd_vel subscriber di stm32_bridge (commit 6c37fd9) — JANGAN merge tanpa diskusi, butuh firmware fix dulu

---

## 12. ENVIRONMENT

```bash
# ROS 2
ROS_DISTRO=humble
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=42

# Workspace
~/amr_starter/                    # workspace path di NUC
~/amr_starter/src/                # source packages
~/amr_starter/install/            # built artifacts

# Database RTAB-Map
~/.ros/rtabmap.db                 # default mapping output
/tmp/standby_test.db              # test database (temporary)

# Evidence recording output
~/mapping_evidence/               # bag files dari record_sensor_evidence.sh
```
