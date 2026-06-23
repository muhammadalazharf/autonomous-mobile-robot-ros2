# GUIDEBOOK MANUAL — AMR 4WD Ackermann Indoor (ROS 2 Humble)

**Proyek:** Autonomous Mobile Robot — Platform Ackermann Indoor
**Penyusun:** Muhammad Al Azhar Faradis (NRP 2040241017), Teknik Fisika ITS
**Platform:** Intel NUC13ANHi7 · Ubuntu 22.04 LTS · ROS 2 Humble Hawksbill
**Workspace NUC:** `~/amr_starter`
**Cakupan:** Penyiapan environment lokal NUC → build → verifikasi → menjalankan → pengujian otonom → pengumpulan bukti.

> Dokumen ini adalah **bahan baku Guidebook**. Setiap blok perintah disertai *apa yang dilakukan* dan *kenapa*. Semua perintah dan parameter diverifikasi dari kode aktual di repository (bukan asumsi).

---

## DAFTAR ISI

1. [Arsitektur Sistem AMR](#1-arsitektur-sistem-amr)
2. [Hierarki Proyek (Struktur Paket)](#2-hierarki-proyek-struktur-paket)
3. [Aliran Data & TF Tree](#3-aliran-data--tf-tree)
4. [Spesifikasi Hardware](#4-spesifikasi-hardware)
5. [Penyiapan Environment Lokal NUC (First-Time)](#5-penyiapan-environment-lokal-nuc-first-time)
6. [Build Workspace](#6-build-workspace)
7. [Verifikasi Pra-Jalan (Preflight)](#7-verifikasi-pra-jalan-preflight)
8. [Menjalankan Sistem](#8-menjalankan-sistem)
9. [Pengujian Manual (Joystick)](#9-pengujian-manual-joystick)
10. [Pengujian Navigasi Otonom (Nav2)](#10-pengujian-navigasi-otonom-nav2)
11. [Pengumpulan Bukti (Evidence)](#11-pengumpulan-bukti-evidence)
12. [Troubleshooting](#12-troubleshooting)
13. [Lampiran: Tabel Parameter Kritis](#13-lampiran-tabel-parameter-kritis)

---

## 1. Arsitektur Sistem AMR

AMR ini adalah robot **4WD dengan kemudi Ackermann** (steering depan, penggerak roda), dirancang untuk navigasi **indoor** tanpa GPS. Lokalisasi mengandalkan **Visual-Inertial Odometry (VIO)** dari kamera RGB-D + IMU, dengan LiDAR 2D untuk deteksi rintangan.

### 1.1 Tiga Lapisan Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│  LAPISAN 3 — PERENCANAAN & NAVIGASI (Nav2)                        │
│  SmacPlannerHybrid (DUBIN) → RegulatedPurePursuit → /cmd_vel      │
│  Beroperasi di frame: odom                                        │
├─────────────────────────────────────────────────────────────────┤
│  LAPISAN 2 — PERSEPSI & LOKALISASI                                │
│  RTAB-Map VIO (rgbd_odometry) → /rtabmap/odom + TF odom→base_link │
│  RTAB-Map SLAM → loop closure + peta 3D/2D grid                   │
│  RPLIDAR C1 → /scan (obstacle costmap)                            │
├─────────────────────────────────────────────────────────────────┤
│  LAPISAN 1 — KONTROL & AKTUASI (low-level)                        │
│  joy_node → stm32_bridge → Serial → STM32 → Motor + Servo         │
│  Encoder → odometry_publisher → /odom (wheel odometry sekunder)   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Prinsip Desain Kunci

| Prinsip | Implementasi | Alasan |
|---------|-------------|--------|
| **Navigasi di frame `odom`** | Nav2 `global_frame: odom` | VIO mulus & kontinu; lock map-frame RTAB-Map masih berkedip di layout uji |
| **VIO = sumber pose utama** | `rgbd_odometry` publish TF `odom→base_link` | Lebih akurat dari wheel odom untuk Ackermann (slip roda) |
| **Wheel odom = sekunder** | `odometry_publisher.py`, `publish_tf` hanya saat VIO mati | Hindari konflik TF (dua publisher `odom→base_link`) |
| **Keselamatan berlapis** | R1 deadman + runtime cap + PWM ramping + cmd_vel timeout | Anti-runaway, anti-brownout NUC, rem darurat manual |
| **Ackermann motion model** | SmacPlannerHybrid `DUBIN` (forward-only) | Robot tidak bisa berputar di tempat; jalur harus feasible |

---

## 2. Hierarki Proyek (Struktur Paket)

Workspace berisi **7 paket ROS 2** di bawah `~/amr_starter/src/`:

```
amr_starter/
├── src/
│   ├── amr_bringup/          ← ORKESTRATOR: master launch + sensor + driver
│   │   ├── launch/
│   │   │   ├── amr_full.launch.py    ← master (semua komponen, toggle via arg)
│   │   │   ├── amr_launch.py         ← joy_node + stm32_bridge
│   │   │   └── sensors_launch.py     ← RPLIDAR C1 + RealSense D455 + static TF
│   │   └── config/joy_params.yaml
│   │
│   ├── amr_controller/       ← KONTROL LOW-LEVEL (jembatan ke hardware)
│   │   ├── src/stm32_bridge.cpp           ← /cmd_vel & /joy → Serial STM32 (C++)
│   │   └── scripts/
│   │       ├── odometry_publisher.py      ← encoder → /odom (Ackermann inverse)
│   │       └── imu_merger_node.py         ← accel+gyro → /imu/data
│   │
│   ├── amr_description/      ← MODEL ROBOT (URDF)
│   │   └── urdf/amr_description.urdf.xacro ← geometri, TF statis, frame
│   │
│   ├── amr_3d_mapping/       ← PERSEPSI 3D (RTAB-Map VIO + SLAM)
│   │   ├── launch/
│   │   │   ├── vio_only.launch.py             ← VIO + SLAM (dipakai demo odom-frame)
│   │   │   ├── rtabmap_mapping.launch.py      ← bangun peta baru
│   │   │   └── rtabmap_localization.launch.py ← lokalisasi di peta tersimpan
│   │   └── config/rtabmap_mapping.yaml, rtabmap_localization.yaml
│   │
│   ├── amr_slam/             ← NAVIGASI & SLAM 2D
│   │   ├── launch/nav2.launch.py             ← Nav2 stack
│   │   ├── config/nav2_params.yaml           ← parameter planner/controller/costmap
│   │   └── scripts/goal_sender.py            ← kirim goal Nav2 dari terminal
│   │
│   ├── amr_failover/         ← FAILOVER CONTROLLER (default OFF saat demo)
│   │   └── launch/failover.launch.py
│   │
│   └── amr_visual_regression/ ← REGRESI VISUAL (line segments LiDAR, depth CNN-less)
│       └── launch/line_segments.launch.py, vr_inference.launch.py
│
└── scripts/                  ← HELPER OPERASIONAL (bash/python)
    ├── 00_preflight_check.sh      ← cek environment & hardware sebelum kerja
    ├── 01_setup_workspaces.sh     ← first-time setup (deps + build + udev)
    ├── install_deps.sh            ← install paket ROS 2 + Python
    ├── install_rtabmap_deps.sh    ← install RTAB-Map ROS 2
    ├── 02_quick_test.sh           ← uji bertahap tiap komponen
    ├── setup_network.sh           ← auto-reconnect WiFi/Bluetooth
    ├── fresh_mapping.sh           ← backup + reset DB untuk remap
    └── calibrate_wheel.py         ← kalibrasi PPR encoder
```

### 2.1 Tanggung Jawab Tiap Paket

| Paket | Peran | Output Utama |
|-------|-------|-------------|
| `amr_bringup` | Menyalakan semua node (driver, sensor, orkestrasi) | `/joy`, `/scan`, `/camera/camera/*` |
| `amr_controller` | Terjemahkan perintah → sinyal motor; baca encoder | Serial ke STM32, `/odom` |
| `amr_description` | Definisi geometri & TF statis robot | `/robot_description`, TF |
| `amr_3d_mapping` | VIO + SLAM visual-inersia | `/rtabmap/odom`, TF `odom→base_link`, peta |
| `amr_slam` | Perencanaan jalur & kontrol gerak otonom | `/cmd_vel`, `/plan` |
| `amr_failover` | Cadangan controller (produksi) | (nonaktif saat demo) |
| `amr_visual_regression` | Eksperimen regresi visual | overlay, inferensi depth |

---

## 3. Aliran Data & TF Tree

### 3.1 Rantai Kontrol (perintah → gerak)

```
[Otonom]  Nav2 controller ─┐
                            ├─→ /cmd_vel ─→ velocity_smoother ─→ stm32_bridge ─→ Serial ─→ STM32 ─→ Motor+Servo
[Manual]  joy_node ─/joy ──┘                                          │
                                                                       │  (gate: autonomous_enabled + R1 deadman)
Encoder ─→ odometry_publisher ─→ /odom  (Ackermann inverse, PPR=3858)
```

### 3.2 Rantai Persepsi/VIO (sensor → pose)

```
RealSense D455 ┬─ /camera/camera/color/image_raw ─┐
               ├─ /camera/camera/depth/...        ├─→ rgbd_sync ─→ /rgbd_image ─┐
               ├─ /camera/camera/color/camera_info┘                             │
               ├─ /camera/camera/accel/sample (100Hz) ┐                         ├─→ rgbd_odometry ─→ /rtabmap/odom
               └─ /camera/camera/gyro/sample  (200Hz) ┴─→ imu_merger ─/imu/data ┘        │            + TF odom→base_link
                                                                                          ↓
RPLIDAR C1 ─→ /scan ──────────────────────────────────────────────────────→ rtabmap (SLAM: loop closure, peta)
```

### 3.3 TF Tree (rantai transform)

```
map                         (RTAB-Map SLAM; opsional saat localization)
 └─ odom                    (rgbd_odometry / VIO — sumber pose Nav2)
     └─ base_footprint
         └─ base_link       (pusat robot, robot_base_frame Nav2)
             ├─ chassis
             ├─ laser_frame                 (RPLIDAR)
             ├─ camera_link
             │   ├─ color_optical_frame ↔ camera_color_optical_frame  (static bridge)
             │   └─ depth_optical_frame ↔ camera_depth_optical_frame  (static bridge)
             └─ {fl,fr,rl,rr}_steering_link → _wheel  (roda + steering Ackermann)
```

> **CATATAN PENTING:** Saat demo odom-frame, `odom→base_link` di-publish oleh **VIO** (`rgbd_odometry`), bukan wheel odom. Pose yang dibaca Nav2 = TF ini, **bukan** topik `/rtabmap/odom`. (Lihat Troubleshooting Temuan #2.)

---

## 4. Spesifikasi Hardware

| Komponen | Spesifikasi | Catatan |
|----------|-------------|---------|
| Compute | Intel NUC13ANHi7 | Ubuntu 22.04, ROS 2 Humble |
| LiDAR | RPLIDAR C1 | Serial CP2102N, baud **460800**, `frame_id: laser_frame`, scan Standard |
| Kamera | Intel RealSense D455 | RGB **848×480×30**, Depth **848×480×30**, IMU (gyro 200Hz / accel 100Hz), `align_depth: true`, `publish_tf: false` |
| Penggerak | 4WD + servo Ackermann | `wheelbase: 0.50 m`, `wheel_radius: 0.0775 m` |
| MCU | STM32 (via Serial) | Terima PWM dari `stm32_bridge` |
| Encoder | Quadrature | **PPR efektif = 3858** (kalibrasi empiris, R²=0.998) |
| Input | Joystick (joy_node) | `device_id: 0`, `deadzone: 0.05`, **R1 = deadman/rem darurat** |
| GPS | — | **Dicopot fisik** (platform indoor only) |

> ⚠️ **JANGAN ubah resolusi RealSense dari `848×480×30`** (RGB & Depth). Tuning exposure (gain 64, exposure 156) sudah disetel untuk pencahayaan lab tidak konsisten.

---

## 5. Penyiapan Environment Lokal NUC (First-Time)

> Lakukan **sekali** saat deploy ke NUC baru, atau setelah re-flash OS.

### 5.1 Prasyarat: ROS 2 Humble

```bash
# Cek apakah ROS 2 Humble sudah terpasang
printenv ROS_DISTRO     # harus mengembalikan: humble
```
*Apa:* memastikan ROS 2 Humble ada. *Kenapa:* seluruh skrip menolak jalan kalau `ROS_DISTRO` bukan `humble`.

Jika kosong, source dulu (atau install ROS 2 Humble sesuai dokumen resmi):
```bash
source /opt/ros/humble/setup.bash
```

### 5.2 Clone Repository

```bash
# Workspace standar di NUC: ~/amr_starter
cd ~
git clone <URL_REPO> amr_starter
cd ~/amr_starter
git checkout claude/zealous-darwin-6l4bs5    # branch kerja aktif
```
*Apa:* ambil source code. *Kenapa:* branch `claude/zealous-darwin-6l4bs5` berisi audit fixes & konfigurasi demo terbaru.

### 5.3 Install Dependencies

```bash
# 1. Dependencies inti ROS 2 + Python
source /opt/ros/humble/setup.bash
bash ~/amr_starter/scripts/install_deps.sh
```
*Apa:* install paket ROS 2 (nav2, joy, realsense2_camera, dst) + Python. *Kenapa:* node tidak akan ditemukan tanpa ini.

```bash
# 2. Dependencies RTAB-Map (terpisah, ~500 MB, 5–10 menit)
bash ~/amr_starter/scripts/install_rtabmap_deps.sh
```
*Apa:* install `rtabmap_ros` (rgbd_sync, rgbd_odometry, rtabmap, rtabmap_slam). *Kenapa:* paket `amr_3d_mapping` butuh ini untuk VIO.

### 5.4 Setup Otomatis (deps + build + udev)

```bash
# Skrip all-in-one first-time (deps sistem, build underlay+overlay, .bashrc, udev)
bash ~/amr_starter/scripts/01_setup_workspaces.sh
```
*Apa:* setup dual-workspace (underlay driver + overlay amr_starter), auto-source `.bashrc`, pasang udev rules hardware. *Kenapa:* memastikan port serial stabil (`/dev/serial/by-id/...`) dan workspace ter-source otomatis tiap buka terminal.

### 5.5 Setup Jaringan (untuk demo)

```bash
# Auto-reconnect WiFi/Bluetooth setelah reboot (butuh sudo)
sudo bash ~/amr_starter/scripts/setup_network.sh "WiFi-Kampus-ITS"
```
*Apa:* konfigurasi NetworkManager autoconnect. *Kenapa:* NUC harus reconnect sendiri saat demo tanpa intervensi manual.

---

## 6. Build Workspace

```bash
cd ~/amr_starter
source /opt/ros/humble/setup.bash

# Build SELURUH workspace (hanya saat first-time atau perubahan besar)
colcon build --symlink-install
```
*Apa:* kompilasi semua paket. *Kenapa:* `--symlink-install` membuat perubahan file Python/YAML langsung berlaku **tanpa rebuild**.

> ⚠️ **Aturan operasional:** Setelah first-time, **JANGAN** rebuild full. Build per-paket saja:

```bash
# Build hanya paket yang berubah (mis. setelah edit stm32_bridge.cpp)
colcon build --packages-select amr_controller
```
*Apa:* build satu paket. *Kenapa:* full rebuild lambat & berisiko; per-paket cukup.

```bash
# Source hasil build (WAJIB tiap buka terminal baru sebelum ros2 launch)
source ~/amr_starter/install/setup.bash
```
*Apa:* daftarkan paket ke environment. *Kenapa:* tanpa source, `ros2 launch amr_*` → "package not found".

> **Catatan file:**
> - `*.yaml` (config) & `*.py` (script) → cukup edit, **tanpa rebuild** (berkat symlink).
> - `*.cpp` (stm32_bridge) → **wajib** `colcon build --packages-select amr_controller`.

---

## 7. Verifikasi Pra-Jalan (Preflight)

> Jalankan **setiap kali** setelah reboot NUC, sebelum demo.

```bash
bash ~/amr_starter/scripts/00_preflight_check.sh
```
*Apa:* cek environment + hardware (port serial, LiDAR, kamera, ROS env). *Kenapa:* mendeteksi masalah sebelum demo. Exit code: `0`=hijau, `1`=kritis, `2`=warning.

```bash
# Verifikasi hardware terdeteksi di port serial
ls -l /dev/serial/by-id/
```
*Apa:* lihat device serial. *Kenapa:* RPLIDAR (`CP2102N`) & STM32 harus muncul; jika tidak, cek kabel/udev.

```bash
# Uji komponen bertahap (interaktif: joystick, bridge, odom, lidar, kamera)
bash ~/amr_starter/scripts/02_quick_test.sh
```
*Apa:* uji tiap subsistem satu per satu. *Kenapa:* isolasi masalah per komponen sebelum integrasi penuh.

---

## 8. Menjalankan Sistem

Demo otonom butuh **3 terminal**. Tiap terminal **wajib** `source ~/amr_starter/install/setup.bash` dulu.

### 8.1 Terminal 1 — Robot Base (driver + sensor + odometry)

```bash
source ~/amr_starter/install/setup.bash
ros2 launch amr_bringup amr_full.launch.py
```
*Apa:* nyalakan URDF + robot_state_publisher + joy_node + stm32_bridge + RPLIDAR + RealSense + odometry_publisher. *Kenapa:* fondasi semua — tanpa ini tak ada sensor/aktuator. (SLAM/Nav2 default OFF di sini, dijalankan terpisah.)

**Verifikasi:** tunggu log RPLIDAR `RPLidar health status : OK` dan kamera mulai publish.

### 8.2 Terminal 2 — VIO + SLAM (RTAB-Map)

```bash
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping vio_only.launch.py
```
*Apa:* jalankan `imu_merger` → `rgbd_sync` → `rgbd_odometry` (VIO) → `rtabmap` (SLAM). *Kenapa:* menghasilkan `/rtabmap/odom` + TF `odom→base_link` yang dibaca Nav2 sebagai pose robot.

**Verifikasi:** VIO publish dengan benar:
```bash
ros2 topic hz /rtabmap/odom        # harus ~15–30 Hz
```
> Error `VWDictionary.cpp: Not found word` dari node `rtabmap` = **bukan kritis** (loop closure DB lama). VIO tetap jalan. Abaikan untuk demo odom-frame.

### 8.3 Terminal 3 — Nav2 Stack

```bash
source ~/amr_starter/install/setup.bash
ros2 launch amr_slam nav2.launch.py
```
*Apa:* jalankan controller_server, planner_server (SmacPlannerHybrid), bt_navigator, behavior_server, dll. *Kenapa:* mesin perencanaan + kontrol gerak otonom.

**Verifikasi:** tunggu log:
```
[lifecycle_manager_navigation]: Managed nodes are active
```

---

## 9. Pengujian Manual (Joystick)

Sebelum otonom, pastikan kontrol low-level benar.

```bash
# Lihat input joystick mentah
ros2 topic echo /joy
```
*Apa:* tampilkan axes & buttons. *Kenapa:* verifikasi stick & tombol R1 terbaca.

**Prosedur uji kemudi (Ackermann):**
1. Tahan **R1** (deadman) — robot standby, roda depan lurus.
2. Dorong analog kanan ke **KIRI** → roda depan harus belok **KIRI**.
3. Dorong ke **KANAN** → roda depan belok **KANAN**.

*Kenapa:* memverifikasi tanda kemudi (`steer_rad = -atan(L·ω/v)` di `stm32_bridge.cpp`) benar di hardware. Jika terbalik, jangan ubah kode tanpa diskusi — catat dulu.

```bash
# Verifikasi wheel odometry naik saat robot maju
ros2 topic echo /odom --field pose.pose.position
```
*Apa:* lihat posisi x dari encoder. *Kenapa:* pastikan x **naik** saat robot maju (arah benar) — fondasi sebelum otonom.

---

## 10. Pengujian Navigasi Otonom (Nav2)

> Urutan ini **TERBUKTI BERHASIL** (2 run SUCCEEDED, terverifikasi runtime).

### 10.1 Set Parameter Keselamatan (SEBELUM kirim goal)

```bash
# Naikkan runtime cap supaya motor tidak auto-stop di tengah jalan
ros2 param set /stm32_bridge autonomous_max_runtime_s 60.0

# Buka gate autonomous (cmd_vel baru diteruskan ke motor jika true)
ros2 param set /stm32_bridge autonomous_enabled true
```
*Apa:* atur batas runtime & buka gerbang otonom. *Kenapa:* default cap 10s bisa hentikan motor sebelum Nav2 menyatakan SUCCEEDED (lihat Temuan #4). Gate `autonomous_enabled` default `false` (keselamatan).

### 10.2 Cek & Reset Posisi Awal

```bash
# Cek posisi robot menurut TF (INI yang dibaca Nav2, bukan topik)
ros2 run tf2_ros tf2_echo odom base_link
```
*Apa:* lihat translasi `odom→base_link`. *Kenapa:* goal absolut harus relatif posisi TF ini. Jika x sudah jauh dari 0, reset dengan **restart Terminal 2 (VIO)** agar TF mulai dari (0,0).

### 10.3 Kirim Goal (frame `odom`, jarak ≥ 1 m)

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'odom'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}" \
  --feedback
```
*Apa:* kirim goal 1 m ke depan dalam frame `odom`, tampilkan feedback real-time. *Kenapa:*
- **`frame_id: 'odom'`** wajib — frame `base_link` membuat goal "mengejar" robot (Temuan #1).
- **jarak ≥ 1 m** — goal < `xy_goal_tolerance` (0.25 m) langsung SUCCEEDED tanpa gerak (Temuan #3).
- **`--feedback`** — pantau `distance_remaining` turun menuju goal.

**Hasil yang benar:**
```
Goal finished with status: SUCCEEDED
```
Robot bergerak ~0.7 m lalu berhenti (sisa 0.25 m masuk toleransi = normal). Servo goyang kiri-kanan di akhir = alignment RegulatedPurePursuit (normal, bukan bug).

### 10.4 Alternatif: goal via skrip atau RViz

```bash
# Via goal_sender.py (parameter)
ros2 run amr_slam goal_sender.py --ros-args \
  -p goal_x:=1.0 -p goal_y:=0.0 -p goal_yaw:=0.0 -p send_on_start:=true
```

```bash
# Via RViz (dari NoMachine, BUKAN SSH)
export DISPLAY=:0
export LIBGL_ALWAYS_SOFTWARE=1
source ~/amr_starter/install/setup.bash
rviz2
# Set Fixed Frame → odom, klik "2D Goal Pose", klik ~1.5 m di depan robot
```
*Kenapa `DISPLAY=:0` + `LIBGL_ALWAYS_SOFTWARE=1`:* RViz butuh display NoMachine; software rendering hindari crash GL di remote desktop.

---

## 11. Pengumpulan Bukti (Evidence)

Untuk laporan & sidang, rekam bukti saat run berhasil.

```bash
# 1. Rekam topik kunci selama navigasi (terminal terpisah, JALANKAN SEBELUM goal)
mkdir -p ~/amr_starter/bags
ros2 bag record /cmd_vel /odom /rtabmap/odom -o ~/amr_starter/bags/demo_$(date +%H%M)
```
*Apa:* rekam perintah & odometri. *Kenapa:* bukti kuantitatif gerak robot (bisa diputar ulang & diplot).

```bash
# 2. Screenshot node graph (dari NoMachine)
export DISPLAY=:0
source ~/amr_starter/install/setup.bash
rqt_graph
```
*Apa:* visualisasi koneksi node. *Kenapa:* bukti arsitektur runtime (rantai cmd_vel & VIO terlihat).

```bash
# 3. Export TF tree ke PDF
ros2 run tf2_tools view_frames
```
*Apa:* hasilkan `frames.pdf`. *Kenapa:* bukti TF tree lengkap & tanpa konflik.

```bash
# 4. Rekam bukti sensor (skrip helper)
bash ~/amr_starter/scripts/record_sensor_evidence.sh
```
*Apa:* rekam paket bukti sensor. *Kenapa:* dokumentasi sensor aktif.

**Checklist bukti:** video gerak (HP) · bag `/cmd_vel`+`/odom` · log `SUCCEEDED` · rqt_graph · TF PDF · RViz screenshot.

---

## 12. Troubleshooting

> Empat temuan operasional dari uji lapangan 22–23 Jun. **Wajib paham sebelum demo.**

### Temuan #1 🔴 — Robot jalan terus tak berhenti
**Gejala:** robot melewati goal, tidak ada SUCCEEDED.
**Sebab:** goal dikirim di frame `base_link` → titik tujuan dihitung ulang relatif robot tiap replan → goal "mengejar" robot selamanya.
**Solusi:** selalu pakai `frame_id: 'odom'`.

### Temuan #2 🔴 — Robot diam, mengira sudah sampai
**Gejala:** `/rtabmap/odom` x≈0 setelah reset, tapi robot tak gerak saat goal dikirim.
**Sebab:** `reset_odom` hanya reset **topik**, **bukan TF**. Nav2 baca pose dari TF `odom→base_link` (mis. masih x=0.758).
**Solusi:** restart Terminal 2 (VIO) agar TF mulai (0,0), ATAU kirim goal = posisi TF sekarang + jarak.
```bash
ros2 run tf2_ros tf2_echo odom base_link   # baca x sekarang, mis. 0.758
# goal x = 0.758 + 1.0 = 1.758
```

### Temuan #3 🟡 — Goal langsung SUCCEEDED tanpa gerak
**Gejala:** `Reached the goal!` instan, robot diam.
**Sebab:** jarak goal < `xy_goal_tolerance` (0.25 m).
**Solusi:** selalu goal ≥ 1.0 m dari posisi robot.

### Temuan #4 🟠 — Stuck di `distance_remaining: 0.25`, servo goyang ~10s lalu macet
**Gejala:** feedback macet, motor berhenti, Nav2 tak menyatakan SUCCEEDED.
**Sebab:** runtime cap 10s menghentikan motor sementara Nav2 masih di approach phase.
**Solusi:** naikkan cap sebelum goal:
```bash
ros2 param set /stm32_bridge autonomous_max_runtime_s 60.0
```

### Masalah Display (RViz/rqt)
**Gejala:** `could not connect to display`.
**Sebab:** dijalankan dari SSH (tanpa display).
**Solusi:** jalankan dari terminal **NoMachine** dengan `export DISPLAY=:0` (+ `LIBGL_ALWAYS_SOFTWARE=1` untuk RViz).

### Error VWDictionary
**Gejala:** spam `Not found word XXXX` dari node `rtabmap`.
**Status:** **bukan kritis**. VIO (`rgbd_odometry`) jalan terpisah. Abaikan untuk demo odom-frame.

---

## 13. Lampiran: Tabel Parameter Kritis

### 13.1 `stm32_bridge.cpp` (kontrol low-level)

| Parameter | Default | Fungsi |
|-----------|---------|--------|
| `autonomous_enabled` | `false` | Gate: cmd_vel diteruskan ke motor hanya jika `true` |
| `max_speed_mps` | `1.0` | Skala kecepatan → PWM |
| `cmd_vel_timeout_ms` | `500` | Watchdog: stop bila cmd_vel hilang |
| `autonomous_max_runtime_s` | `10.0` | Runtime cap anti-runaway (naikkan ke 60 saat demo) |
| `MAX_PWM` | `4000` | PWM maksimum |
| `MAX_PWM_STEP` | `400` | Ramping PWM/step (anti-brownout NUC) |
| `WHEELBASE` | `0.5` m | Jarak sumbu, untuk `steer = -atan(L·ω/v)` |

> **Aturan keselamatan:** R1 (deadman) **selalu** menang atas otonom.

### 13.2 `odometry_publisher.py` (wheel odometry)

| Parameter | Nilai | Catatan |
|-----------|-------|---------|
| `wheel_radius` | `0.0775` m | |
| `wheelbase` | `0.50` m | |
| `pulses_per_revolution` | `3858` | Kalibrasi empiris (R²=0.998) |
| `publish_rate` | `50.0` Hz | |
| `publish_tf` | kondisional | `true` hanya saat VIO mati (hindari konflik TF) |

### 13.3 `nav2_params.yaml` (navigasi)

| Parameter | Nilai | Catatan |
|-----------|-------|---------|
| `global_frame` | `odom` | Navigasi di frame odom |
| `robot_base_frame` | `base_link` | |
| Planner | `SmacPlannerHybrid` (DUBIN) | Ackermann forward-only |
| Controller | `RegulatedPurePursuitController` | |
| `desired_linear_vel` | `0.3` m/s | |
| `lookahead_dist` | `0.6` m | |
| `xy_goal_tolerance` | `0.25` m | Robot berhenti ~0.25 m dari goal |
| `yaw_goal_tolerance` | `0.25` rad | |
| `robot_radius` | `0.22` m | Audit 48h (dari 0.28) |
| `inflation_radius` | `0.10` m | Audit 48h (dari 0.25) |
| `obstacle/raytrace_min_range` | `0.3` m | Filter self-scan (chassis jadi obstacle hantu) |
| `rolling_window` | `true` | Costmap ikut robot (odom-frame) |

### 13.4 Sensor (`sensors_launch.py`)

| Sensor | Parameter | Nilai |
|--------|-----------|-------|
| RPLIDAR C1 | baud / frame | `460800` / `laser_frame` |
| RealSense D455 | RGB/Depth profile | `848×480×30` (JANGAN diubah) |
| RealSense D455 | gain / exposure | `64` / `156` (tuning lab) |
| RealSense D455 | `publish_tf` | `false` (TF dari URDF + static bridge) |

---

**Akhir Guidebook.** Untuk SOP mapping & lokalisasi map-frame, lihat `docs/SOP_MAPPING_DAN_AUTONOMOUS.md`. Untuk catatan uji lapangan terbaru, lihat `docs/HANDOVER_22JUN2026.md` §6c.
