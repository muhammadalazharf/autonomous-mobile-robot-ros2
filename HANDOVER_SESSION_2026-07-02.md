# HANDOVER: Sesi Deploy + Debug AMR — 1–2 Juli 2026

**Pemilik:** Muhammad Al Azhar Faradis (NRP 2040241017, ITS Surabaya)
**Email:** malazharfaradis@gmail.com
**Repo:** `github.com/muhammadalazharf/autonomous-mobile-robot-ros2`
**Branch:** `claude/markdown-file-review-rokxcl`
**Tanggal mulai:** 1 Juli 2026
**Tanggal update terakhir:** 2 Juli 2026
**Konteks:** Deploy arsitektur rebuild 5-layer AMR Ackermann ke NUC13 + debug hardware + persiapan exhibition

---

## 1. Konteks Proyek

### 1.1 Latar Belakang

Robot mobile otonom (AMR) dengan steering Ackermann (4WD, belok depan mirip mobil) untuk Tugas Akhir mahasiswa Teknik Elektro Otomasi ITS Surabaya. Sistem sebelumnya dinyatakan **GAGAL** (7 titik kegagalan fatal), lalu dibangun ulang dari nol dengan arsitektur 5-layer.

### 1.2 Hardware

| Komponen | Spesifikasi |
|---|---|
| Komputer | Intel NUC13ANHi7, Ubuntu 22.04, ROS 2 Humble |
| Kamera | Intel RealSense D455 (color+depth 848x480x30, accel 100Hz, gyro 200Hz) |
| LiDAR | RPLIDAR C1 (2D, 360°, 10Hz, max 16m) |
| Mikrokontroler | STM32F407 (serial bridge: TX `V:{pwm},S:{sudut}\n`, RX `E:{delta}\n`) |
| Steering | Ackermann 2WS (roda depan saja), wheelbase 0.5m |
| Joystick | PS4/PS5 DualShock via Bluetooth, R1 = deadman switch |
| Wi-Fi/BT | Intel AX211 (Wi-Fi + Bluetooth dalam satu chip) |
| Daya | Baterai lithium (shared NUC + motor) ATAU PSU 25V terpisah |

### 1.3 Arsitektur 5-Layer

```
┌──────────────────────────────────────────────────────┐
│  Layer 5: THINK — amr_brain                          │
│  FSM: IDLE → MAPPING → NAVIGATING → STUCK → ERROR   │
├──────────────────────────────────────────────────────┤
│  Layer 4: ACT — amr_navigation                       │
│  SmacPlannerHybrid + RegulatedPurePursuit (Nav2)     │
├──────────────────────────────────────────────────────┤
│  Layer 3: MAP — amr_mapping                          │
│  rgbd_sync → VIO → RTAB-Map SLAM + loop closure     │
├──────────────────────────────────────────────────────┤
│  Layer 2: POSE — amr_pose                            │
│  Encoder Odom (lemah) + EKF (robot_localization)     │
├──────────────────────────────────────────────────────┤
│  Layer 1: SENSE — amr_sensors + amr_motor            │
│  LiDAR + RealSense + IMU merger + STM32 Bridge       │
└──────────────────────────────────────────────────────┘
```

Setiap layer bergantung pada layer di bawahnya. Deploy dan uji **berurutan dari bawah ke atas.**

### 1.4 Lingkungan Kerja

- **NUC workspace:** `~/AMR/amr_ws/` (bukan `~/amr_ws/`)
- **Git repo root:** Container cloud, path `amr_ws/src/...`
- **Build command:** `colcon build --symlink-install`
- **Source tiap terminal:** `source /opt/ros/humble/setup.bash && source ~/AMR/amr_ws/install/setup.bash`
- **Remote access NUC:** SSH via Tailscale CGNAT (IP `100.85.144.92`) + NoMachine
- **Joystick:** Bluetooth ke NUC (via Intel AX211)

### 1.5 Instruksi User yang Harus Dipatuhi

- "hiraukan HANDOVER_GEMINI sebelum sebelumnya" — abaikan HANDOVER_GEMINI.md untuk desain, tapi info hardware tetap relevan
- "jangan langsung main fix dan ubah sebelum aku tau konteksnya kenapa dan mengapa" — selalu jelaskan sebelum fix
- "/debug cari root causenya" — cari akar masalah, jangan workaround
- **Hard Rule:** Lihat `HANDOVER_REBUILD_AMR.md` Bagian 11 untuk 10 aturan yang DILARANG dilanggar

---

## 2. Kronologi Kerja Lengkap

### Fase 1: Transfer Kode ke NUC (1 Juli 2026)

1. **Push kode rebuild ke GitHub** — dari laptop Linux via SSH (HTTPS gagal karena GitHub tidak terima password, harus PAT/SSH). Branch `claude/rebuild-amr`, 61.67 MiB.
2. **Merge ke branch kerja** `claude/markdown-file-review-rokxcl`.
3. **Backup workspace lama NUC** → `~/WORKSPACE_1/` + `~/WORKSPACE_1.zip` (11 MB).
4. **Transfer via flashdisk** → extract ke `~/AMR/amr_ws/`.
5. **Jalankan `deploy.bash`** — 7 langkah semua PASS (install deps, rosdep, build 8 package, udev, bashrc).

### Fase 2: Layer 1 Sensor — Debug & Verifikasi (1 Juli 2026)

#### Problem #1: Encoder FAIL (0 Hz)

- **Gejala:** Health check 4/5 PASS, Encoder FAIL.
- **Root cause:** Package `amr_motor` hanya kerangka kosong (CMakeLists + package.xml), tidak ada node.
- **Fix salah (iterasi 1):** Claude bikin `stm32_bridge_node.py` (Python) dari tebakan — user protes karena Claude mengarang parameter.
- **Fix benar (iterasi 2):** Ambil `stm32_bridge.cpp` **asli** dari branch `main` (kode C++ yang sudah terbukti jalan di hardware). Convert `amr_motor` dari kerangka → C++ ament_cmake package fungsional.
- **Parameter kritis dari kode asli:**
  - Serial port: `/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_206833894152-if00`
  - `MAX_PWM = 4000` (bukan 255 seperti di motor.yaml — file YAML ini SALAH/outdated)
  - `MAX_STEER = 45`, `STEER_TRIM = -5`
  - Baud rate B115200
  - Dual-mode: joystick (R1 deadman) + cmd_vel autonomous
- **Hasil:** Encoder PASS 20 Hz. **Layer 1: 5/5 PASS.**
- **Commit:** `c433a2a`, `8ea44b2`

#### Problem #2: Resolusi Kamera Color 1280x720

- **Root cause:** Parameter `sensors.yaml` tidak terbaca oleh RealSense node (namespace issue).
- **Fix:** Tambah parameter dict langsung di `sensors.launch.py` sebagai override:
  ```python
  parameters=[config, {'rgb_camera.color_profile': '848x480x30', 'depth_module.depth_profile': '848x480x30'}]
  ```
- **Commit:** `21aff88`

#### Problem #3: LiDAR XY PermissionError

- **Root cause:** `record_dir` hardcode `/home/azhar` (path laptop, bukan NUC).
- **Fix:** Ganti ke `~/lidar_data` + `os.path.expanduser()`.
- **Commit:** `27feabb`

#### Problem #4: CSV LiDAR Kosong

- **Root cause:** Filter `scan_count % 10` skip hampir semua data + tidak ada `flush()`.
- **Fix:** Hapus filter, tambah flush per scan, tambah try/finally.
- **Commit:** `c939591`

#### Hasil Layer 1:

| Sensor | Topic | Freq | Status |
|---|---|---|---|
| LiDAR RPLIDAR C1 | `/scan` | 10 Hz | PASS |
| Kamera Color | `/camera/camera/color/image_raw` | 17-27 Hz | PASS |
| Kamera Depth | `/camera/camera/depth/image_rect_raw` | 20-30 Hz | PASS |
| IMU merged | `/imu/data` | 100 Hz | PASS |
| Encoder | `/encoder` | 20 Hz | PASS |
| Joystick | `/joy` | ~variabel | PASS |
| Motor cmd | `/cmd_vel` | on-demand | PASS |

**Data LiDAR CSV** tersimpan di NUC: `~/lidar_data/lidar_20260701_171017.csv` — 92,744 baris.

### Fase 3: Layer 2 Pose/EKF — Verifikasi (1 Juli 2026)

- **Launch:** `ros2 launch amr_startup layer2_pose.launch.py`
- **Hasil:** `/odometry/filtered` publish di ~45 Hz, TF `odom → base_footprint` benar (identity saat idle — normal karena belum ada input gerakan).
- **Status: PASS.**

### Fase 4: Joystick Control — Debug & Fix (1 Juli 2026)

#### Problem #5: Joystick Tidak Bisa Kontrol Robot

- **Gejala:** `ros2 topic echo /joy` — tidak ada output.
- **Root cause:** `joy_node` tidak pernah di-include di launch file manapun.
- **Fix:** Tambah `joy_node` ke `motor.launch.py` dengan `dev: /dev/input/js0`.
- **Commit:** `e49637c`

### Fase 5: Motor Plugging — Root Cause & Safety (1-2 Juli 2026)

#### Problem #6: NUC Mati/Disconnect Saat Motor Mundur

**Ini masalah terbesar sesi ini.** Debugging intensif dilakukan untuk menemukan root cause.

**Gejala:**
- Kontrol joystick maju → normal.
- Kontrol joystick mundur → NUC mati (baterai) atau SSH+BT disconnect (PSU).
- Terjadi HANYA saat motor bergerak, bukan saat perintah PWM negatif tanpa motor tersambung.

**Debug Sistematis:**

| Test | Kondisi | Hasil |
|---|---|---|
| V:-3900, kabel motor LEPAS | PWM negatif, motor tidak connected | NUC aman, tidak mati |
| V:-3900, kabel motor SAMBUNG, baterai | Motor mundur fisik | NUC MATI total |
| V:-3900, kabel motor SAMBUNG, PSU 25V | Motor mundur fisik | NUC hidup, tapi Wi-Fi+BT DISCONNECT semua |
| Maju→mundur (banting stick) | Transisi cepat | Disconnect pada titik perubahan arah |

**Root Cause: Motor Plugging**

Saat PWM berubah mendadak dari maju→mundur (atau sebaliknya), motor mengalami **plugging**:
1. Motor yang masih berputar ke arah A tiba-tiba diberi tegangan arah B
2. Back-EMF dari putaran lama + tegangan baru = lonjakan arus ~2x normal
3. Arus besar → transien EMI pada power rail yang dibagi NUC + motor
4. Intel AX211 chip (Wi-Fi + Bluetooth SATU chip) sangat sensitif → reset
5. Pada baterai: brownout → NUC mati total
6. Pada PSU 25V: NUC survive tapi AX211 reset → Wi-Fi+BT disconnect bersamaan

**Bukti di log:**
- Disconnect selalu terjadi saat PWM berubah tanda (positif→negatif)
- Motor cables off → tidak disconnect walau PWM negatif
- PSU → NUC survive tapi wireless reset
- SSH, NoMachine, Bluetooth (joystick) disconnect **bersamaan** → satu chip (AX211)

#### Fix #1: Joystick Watchdog (commit `5826e20`)

Tujuan: Deteksi jika `/joy` berhenti publish (BT disconnect) → paksa motor stop.

```cpp
// Di watchdog_check():
if (manual_override_) {
  int joy_timeout_ms = this->get_parameter("joy_timeout_ms").as_int();
  auto joy_elapsed_ms = (now - last_joy_time_).nanoseconds() / 1000000;
  if (joy_elapsed_ms > joy_timeout_ms) {
    manual_override_ = false;
    last_velocity_ = 0;
    send_command(0, STEER_TRIM);
    RCLCPP_WARN(..., "[WATCHDOG] /joy timeout...");
  }
  return;
}
```

**Masalah tambahan:** Watchdog awalnya tidak bekerja karena `autorepeat_rate: 20.0` di joy_node. Autorepeat membuat joy_node terus publish pesan terakhir walau controller sudah putus → watchdog tidak pernah fire.

#### Fix #2: Disable Autorepeat (commit `916b163`)

```python
# motor.launch.py
'autorepeat_rate': 0.0,  # HARUS 0 — lihat komentar panjang
```

**KRITIS:** Autorepeat HARUS 0. Kalau >0, saat Bluetooth putus, joy_node terus kirim perintah terakhir → watchdog tidak fire → motor terus jalan tanpa kontrol.

#### Fix #3: Slew-Rate Limiter (commit `0e0299f`)

Tujuan: Batasi perubahan PWM per pesan supaya transisi maju→mundur gradual (lewat nol), mengurangi lonjakan arus.

```cpp
#define MAX_PWM_STEP 250

int apply_slew(int target) {
  int delta = target - last_velocity_;
  if (delta >  MAX_PWM_STEP) delta =  MAX_PWM_STEP;
  if (delta < -MAX_PWM_STEP) delta = -MAX_PWM_STEP;
  last_velocity_ += delta;
  return last_velocity_;
}
```

Applied di `joy_callback()` dan `cmd_vel_callback()`. Semua stop path reset `last_velocity_ = 0`.

**Hasil test:**
- Log menunjukkan slew limiter BEKERJA: PWM naik bertahap `V:0→250→500→...→4000→3750→...→0→-250→...→-4000`
- **TAPI disconnect MASIH TERJADI.** Transien EMI masih cukup kuat walau sudah di-ramp.

#### Status Masalah Motor Plugging:

**Software safety sudah diterapkan (3 fix), tapi belum cukup menghilangkan disconnect sepenuhnya.**

Opsi yang belum dicoba (untuk exhibition):
1. **Joystick via USB cable** — bypass Bluetooth, tidak tergantung AX211
2. **SSH via Ethernet** — bypass Wi-Fi, tidak terpengaruh transien
3. **Kurangi MAX_PWM** — misal cap 2000 (setengah kecepatan), arus lebih kecil
4. **Jalan pelan saat demo** — mapping indoor tidak perlu kecepatan tinggi
5. **Hardware fix (jangka panjang):** ferrite beads, kapasitor decoupling, pisahkan power rail NUC dan motor

---

## 3. Status Layer per 2 Juli 2026

| Layer | Package | Status | Catatan |
|---|---|---|---|
| 1 SENSE | amr_sensors, amr_motor | **PASS** | 7 topic aktif, semua sensor verified |
| 2 POSE | amr_pose | **PASS** | /odometry/filtered ~45Hz, TF benar |
| 3 MAP | amr_mapping | **BELUM** | Config lengkap, belum dijalankan |
| 4 ACT | amr_navigation | **BELUM** | Nav2 params lengkap, belum deploy |
| 5 THINK | amr_brain | **BELUM** | FSM lengkap, belum deploy |

---

## 4. Blocker Layer 3 — TF Tree Belum Ada

RTAB-Map **tidak akan jalan** tanpa TF (transform) dari `base_footprint` ke frame sensor. Saat ini:

### 4.1 Yang Hilang

1. **`amr_body` kosong** — Package sudah ada (CMakeLists.txt + package.xml), tapi folder `urdf/` dan `launch/` belum dibuat. Seharusnya berisi URDF robot + robot_state_publisher + static TF.

2. **RealSense `publish_tf: false`** — TF internal kamera (camera_link → camera_color_optical_frame, dll.) tidak di-publish. Harus diganti `true`.

3. **Tidak ada static transform:**
   - `base_footprint` → `camera_link` (posisi fisik kamera di robot)
   - `base_footprint` → `laser_frame` (posisi fisik LiDAR di robot)

### 4.2 Yang Dibutuhkan

TF tree lengkap untuk RTAB-Map:

```
map (rtabmap)
 └── odom (EKF)
      └── base_footprint
           ├── camera_link → camera_color_optical_frame (RealSense publish_tf)
           │                → camera_depth_optical_frame
           │                → camera_accel_optical_frame
           │                → camera_gyro_optical_frame
           └── laser_frame
```

### 4.3 Aksi yang Perlu Dilakukan

1. Set `publish_tf: true` di `sensors.yaml` untuk RealSense
2. Buat URDF/launch di `amr_body` dengan static transforms (atau minimal static_transform_publisher nodes)
3. Include `amr_body` launch di `layer3_mapping.launch.py` atau `sensors.launch.py`
4. Posisi fisik sensor perlu diukur (atau pakai estimasi dulu, tune nanti)

---

## 5. File-File Kritis & Perannya

### 5.1 amr_motor (Layer 1 — STM32 Bridge)

| File | Status | Fungsi |
|---|---|---|
| `src/stm32_bridge.cpp` | **MODIFIKASI BERAT** | Node C++ utama: joystick+autonomous dual-mode, serial TX/RX, watchdog, slew limiter |
| `launch/motor.launch.py` | **MODIFIKASI** | Launch joy_node (autorepeat=0) + stm32_bridge |
| `config/motor.yaml` | Tidak terpakai | **PERINGATAN:** Parameter di file ini SALAH (max_pwm:255, baud:115200 melalui parameter). Kode C++ pakai hardcode `#define` yang benar (MAX_PWM=4000). File ini di-load tapi stm32_bridge tidak membaca parameter darinya — semua di-hardcode di cpp. |
| `CMakeLists.txt` | OK | Build target stm32_bridge executable |
| `package.xml` | OK | Deps: rclcpp, sensor_msgs, geometry_msgs, std_msgs |

**Detail `stm32_bridge.cpp`:**

```
Defines:
  SERIAL_PORT = /dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_206833894152-if00
  BAUD_RATE   = B115200
  MAX_PWM     = 4000
  MAX_PWM_STEP = 250   (slew limiter)
  MAX_STEER   = 45
  STEER_TRIM  = -5
  DEADMAN_BTN = 5      (R1 pada PS4/PS5)
  AXIS_VEL    = 1      (Left stick up/down)
  AXIS_STEER  = 3      (Right stick left/right)
  WHEELBASE   = 0.5f   (meter)

ROS Parameters (declare_parameter):
  autonomous_enabled  = false
  max_speed_mps       = 1.0
  cmd_vel_timeout_ms  = 500
  joy_timeout_ms      = 500

Subscriptions:
  /joy     → joy_callback (manual mode, R1 deadman)
  /cmd_vel → cmd_vel_callback (autonomous mode, Nav2)

Publisher:
  /encoder → Int32 (delta ticks dari STM32)

Serial Protocol:
  TX: "V:{pwm},S:{sudut}\n"   (pwm bisa negatif = mundur)
  RX: "E:{delta}\n"           (encoder delta ticks)

Konvensi tanda (setelah kabel motor ditukar):
  V positif  = robot maju fisik
  V negatif  = robot mundur fisik
  Stick maju = axes[1] = +1.0 → V positif → maju ✓
  Nav2 linear.x > 0            → V positif → maju ✓
```

### 5.2 amr_sensors (Layer 1 — Sensor)

| File | Status | Fungsi |
|---|---|---|
| `config/sensors.yaml` | OK | Parameter LiDAR, RealSense, lidar_xy. **publish_tf: false perlu diganti true** |
| `launch/sensors.launch.py` | OK | Launch rplidar + realsense + imu_merger + health_check + motor.launch.py |
| `amr_sensors/imu_merger_node.py` | OK | Gabung D455 accel + gyro → /imu/data |
| `amr_sensors/health_check_node.py` | OK | Subscribe 5 sensor, lapor PASS/FAIL tiap 2 detik |
| `amr_sensors/lidar_xy_node.py` | **FIXED** | Polar→kartesian, CSV recording. Fix: flush per scan + no filter |

### 5.3 amr_pose (Layer 2 — Pose/EKF)

| File | Status | Fungsi |
|---|---|---|
| `config/ekf.yaml` | OK | EKF: VIO (odom0, trust) + encoder (odom1, suspek). `two_d_mode: true` |
| `config/encoder.yaml` | OK | wheel_radius=0.0775, PPR=3858, rate=20Hz |
| `amr_pose/encoder_odom_node.py` | OK | Encoder Int32 → Odometry. Hanya vx. Kovarians besar. |
| `launch/pose.launch.py` | OK | Launch encoder_odom + EKF |

### 5.4 amr_mapping (Layer 3 — SLAM)

| File | Status | Fungsi |
|---|---|---|
| `config/rtabmap.yaml` | OK | Parameter lengkap: rgbd_sync (qos_image:1), VIO (ORB, F2M, Reg/Force3DoF), RTAB-Map (vis+icp, grid 2D dari LiDAR) |
| `launch/mapping.launch.py` | OK | 4 node: rgbd_sync, VIO, rtabmap, depth_to_laserscan. Args: localization, database_path |
| `launch/localization.launch.py` | OK | Mode localization (pakai peta .db yang sudah ada) |

**RTAB-Map Config Highlights:**
- `rgbd_sync`: `qos: 1`, `qos_image: 1` (BestEffort — FIX dari sistem lama)
- VIO: `Odom/Strategy: 0` (Frame-to-Map), `Vis/FeatureType: 6` (ORB), `Reg/Force3DoF: true`
- SLAM: `Reg/Strategy: 2` (visual+ICP), `Icp/PointToPlane: false` (FIX untuk single-ring LiDAR)
- Grid: `Grid/FromDepth: false` (dari LiDAR), `Grid/CellSize: 0.05`

### 5.5 amr_body (TF/URDF — BELUM DIBUAT)

| File | Status | Fungsi |
|---|---|---|
| `CMakeLists.txt` | Ada | Install `urdf/` dan `launch/` directories |
| `package.xml` | Ada | Deps: robot_state_publisher, joint_state_publisher, xacro |
| `urdf/` | **KOSONG** | Perlu URDF/xacro robot model |
| `launch/` | **KOSONG** | Perlu launch file untuk robot_state_publisher + static TF |

### 5.6 amr_navigation (Layer 4 — Nav2) & amr_brain (Layer 5 — FSM)

Belum diuji. Config sudah lengkap. Lihat `HANDOVER_REBUILD_AMR.md` untuk detail.

### 5.7 amr_startup (Master Launch)

| File | Fungsi |
|---|---|
| `launch/amr_sensors_only.launch.py` | Layer 1 saja |
| `launch/layer2_pose.launch.py` | L1 + L2 |
| `launch/layer3_mapping.launch.py` | L1 + L2 + L3 |
| `launch/layer4_navigation.launch.py` | L1 + L2 + localization + Nav2 |
| `launch/full_system.launch.py` | Semua layer + brain |
| `launch/save_map.launch.py` | Simpan peta |
| `launch/record_sensors.launch.py` | Rekam rosbag |

---

## 6. Daftar Commit Lengkap (Sesi Ini)

| Commit | Deskripsi | Status |
|---|---|---|
| `7d675e9` | Add AMR rebuild workspace — arsitektur 5-layer baru | OK |
| `c433a2a` | Implement amr_motor STM32 bridge (Python, SALAH) | Superseded |
| `8ea44b2` | Replace amr_motor Python → C++ stm32_bridge dari main branch | OK |
| `c943ca7` | Fix RealSense param name (SALAH) | Superseded |
| `21aff88` | Fix RealSense: revert param names + launch override 848x480 | OK |
| `27feabb` | Fix lidar_xy PermissionError: record_dir + expanduser | OK |
| `c939591` | Fix lidar_xy CSV kosong: flush per scan + try/finally | OK |
| `53e740b` | Add HANDOVER_SESSION_2026-07-01.md | OK |
| `e49637c` | Add joy_node to motor.launch.py — auto-launch joystick | OK |
| `5826e20` | Add joystick watchdog: stop motor if /joy lost (BT drop safety) | OK |
| `916b163` | Disable joy autorepeat: it defeated the joystick watchdog | OK |
| `0e0299f` | Add slew-rate limiter to prevent motor plugging transient | OK |

---

## 7. Inkonsistensi yang Diketahui

### 7.1 `motor.yaml` vs `stm32_bridge.cpp`

File `amr_motor/config/motor.yaml` berisi parameter yang **TIDAK DIPAKAI** oleh kode C++:

| Parameter di YAML | Nilai YAML | Nilai aktual di C++ | Status |
|---|---|---|---|
| `max_pwm` | 255 | 4000 (`#define MAX_PWM`) | **SALAH di YAML** |
| `serial_port` | `/dev/stm32` | `/dev/serial/by-id/usb-STMicro...` | **SALAH di YAML** |
| `max_steering_angle` | 30.0 | 45 (`#define MAX_STEER`) | **SALAH di YAML** |
| `max_speed` | 0.5 | 1.0 (ROS param `max_speed_mps`) | **Berbeda** |

Kode C++ menggunakan `#define` hardcode, bukan parameter dari YAML. File `motor.yaml` di-load oleh launch tapi parameter-nya tidak dibaca oleh node (kecuali `autonomous_enabled`, `max_speed_mps`, `cmd_vel_timeout_ms`, `joy_timeout_ms` yang di-declare via `declare_parameter`).

**Rekomendasi:** Hapus atau update `motor.yaml` supaya sesuai kode aktual. Tapi ini bukan blocker.

### 7.2 HANDOVER_GEMINI vs HANDOVER_REBUILD

| Parameter | GEMINI | REBUILD | Status |
|---|---|---|---|
| `minimum_turning_radius` | 0.90m (terukur) | 0.55m (placeholder) | Belum diputuskan |
| `allow_reversing` | false | true (Reeds-Shepp) | Belum diputuskan |
| Motion model | DUBIN | REEDS_SHEPP | Belum diputuskan |

User instruksikan abaikan GEMINI untuk desain. Parameter nyata belum diukur.

### 7.3 Firmware STM32

HANDOVER_GEMINI mencatat: "Firmware STM32: PWM tidak boleh menerima nilai negatif (butuh if-else di main.c)". **TAPI** kode C++ stm32_bridge mengirim V negatif dan motor fisik mundur → artinya firmware SUDAH di-update atau catatan GEMINI salah. Perlu verifikasi.

---

## 8. Parameter yang BELUM Diukur di NUC

| Parameter | File | Nilai sekarang | Cara ukur |
|---|---|---|---|
| `minimum_turning_radius` | `nav2_params.yaml` | 0.55 (placeholder) | Belok full, ukur diameter lingkaran ÷ 2 |
| `pulses_per_revolution` | `encoder.yaml` | 3858 | Putar roda 1x, hitung selisih pulsa |
| Encoder sign | `encoder_odom_node.py:72` | Asumsi maju = positif | Dorong maju, cek `/encoder` naik/turun |
| `footprint` robot | `nav2_params.yaml` | 50cm × 40cm (placeholder) | Meteran ujung terluar robot |
| Posisi kamera di robot | Belum ada file | Belum ada | Ukur x,y,z dari base_footprint ke camera_link |
| Posisi LiDAR di robot | Belum ada file | Belum ada | Ukur x,y,z dari base_footprint ke laser_frame |

---

## 9. Prioritas Kerja Selanjutnya

### 9.1 URGENT — Untuk Exhibition

1. **Buat TF tree (amr_body):**
   - Set RealSense `publish_tf: true`
   - Buat static transforms base_footprint → camera_link dan base_footprint → laser_frame
   - Include di launch

2. **Test Layer 3 RTAB-Map:**
   ```bash
   ros2 launch amr_startup layer3_mapping.launch.py
   ```
   Verifikasi: `/rgbd_image` > 0 Hz, VIO output, peta terbentuk saat robot jalan

3. **Mitigasi disconnect untuk demo:**
   - Joystick via USB cable (bypass Bluetooth)
   - SSH via Ethernet (bypass Wi-Fi)
   - Jalan pelan saat mapping

### 9.2 Setelah Exhibition

4. Ukur parameter fisik (radius putar, PPR, encoder sign, footprint, posisi sensor)
5. Update motor.yaml atau hapus (sesuaikan dengan kode C++)
6. Test Layer 4 Nav2 + Layer 5 Brain
7. Hardware fix: ferrite beads, kapasitor, pisahkan power rail

---

## 10. Perintah-Perintah Penting

### Launch per layer:
```bash
# Layer 1 saja
ros2 launch amr_sensors sensors.launch.py

# Layer 1 + 2
ros2 launch amr_startup layer2_pose.launch.py

# Layer 1 + 2 + 3 (mapping)
ros2 launch amr_startup layer3_mapping.launch.py

# Layer 1 + 2 + localization + Nav2
ros2 launch amr_startup layer4_navigation.launch.py database_path:=~/maps/lab.db

# Full system
ros2 launch amr_startup full_system.launch.py
```

### Verifikasi:
```bash
# Cek semua topic
ros2 topic list

# Cek frekuensi
ros2 topic hz /scan
ros2 topic hz /odometry/filtered
ros2 topic hz /rgbd_image

# Cek TF tree
ros2 run tf2_tools view_frames

# Health check
ros2 topic echo /health_check
```

### Simpan peta:
```bash
ros2 launch amr_startup save_map.launch.py map_name:=nama_peta
# Hasil di ~/maps/nama_peta/
```

### Build setelah edit:
```bash
cd ~/AMR/amr_ws
colcon build --symlink-install --packages-select amr_motor
source install/setup.bash
```

### Pull update dari GitHub:
```bash
cd ~/AMR/amr_ws
git fetch origin claude/markdown-file-review-rokxcl
git checkout origin/claude/markdown-file-review-rokxcl -- amr_ws/src/PACKAGE/FILE
cp amr_ws/src/PACKAGE/FILE src/PACKAGE/FILE
# Lalu rebuild
```

---

## 11. Konsep yang Dipahami Mahasiswa

| Konsep | Analogi | Status |
|---|---|---|
| Frame `odom` vs `map` | Langkah kaki (drift) vs GPS (lompat tapi akurat) | Paham |
| QoS BestEffort vs Reliable | Teriak vs telepon | Paham |
| QoS mismatch = silent death | Teriak ke orang pakai headset | Paham |
| VIO (Visual-Inertial Odometry) | Mata + telinga dalam | Paham |
| EKF sensor fusion | 2 saksi: terpercaya vs mencurigakan | Paham |
| Kovarians besar = tidak dipercaya | "Aku curiga kamu bohong" | Paham |
| Ackermann vs differential | Mobil vs kursi roda | Paham |
| Single source of truth | Buku resep (1 tempat) | Paham |
| Motor plugging | Rem mendadak + gas terbalik = lonjakan arus | Paham |
| Slew-rate limiter | Gas/rem gradual, bukan banting setir | Paham |
| Watchdog timer | Alarm kalau tidak ada kabar | Paham |

---

## 12. Kontak & Referensi

- **Owner:** Muhammad Al Azhar Faradis (malazharfaradis@gmail.com, NRP 2040241017)
- **Repo:** github.com/muhammadalazharf/autonomous-mobile-robot-ros2
- **Branch aktif:** `claude/markdown-file-review-rokxcl`
- **Handover arsitektur:** `HANDOVER_REBUILD_AMR.md`
- **Handover sesi 1 Juli:** `HANDOVER_SESSION_2026-07-01.md`
- **Handover Gemini (legacy):** `HANDOVER_GEMINI.md`
- **Workspace NUC:** `~/AMR/amr_ws/`
- **Backup workspace lama:** `~/WORKSPACE_1/` + `~/WORKSPACE_1.zip`
- **Data LiDAR:** `~/lidar_data/`

---

*Dokumen ini mencakup SELURUH riwayat kerja dari deploy pertama (1 Juli 2026) hingga status terkini (2 Juli 2026). Tujuannya agar siapapun yang melanjutkan — termasuk AI assistant lain atau diri sendiri — tahu persis: apa yang sudah jalan, apa yang di-fix (dan kenapa), apa yang belum, dan apa yang masih bermasalah.*
