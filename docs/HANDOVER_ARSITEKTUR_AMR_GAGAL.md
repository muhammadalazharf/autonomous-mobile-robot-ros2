# HANDOVER ARSITEKTUR AMR — Dokumentasi Sistem yang Dinyatakan GAGAL

> **Dokumen ini untuk di-handover ke AI/engineer berikutnya.** Tujuannya: menjelaskan
> SELURUH arsitektur sistem AMR yang sudah dibangun, **di mana letak akar kegagalannya**
> (dipetakan ke baris kode nyata), supaya workspace baru bisa dibangun ulang tanpa
> mengulang kesalahan yang sama.

**Tanggal handover:** 27 Juni 2026
**Pemilik:** Muhammad Al Azhar Faradis (NRP 2040241017, Teknik — ITS Surabaya)
**Repo:** https://github.com/muhammadalazharf/autonomous-mobile-robot-ros2
**Branch:** `claude/zealous-darwin-6l4bs5`
**Status proyek:** Dinyatakan GAGAL oleh dosen — diberi waktu 1 bulan untuk menyelesaikan.
**Rencana pemilik:** Backup workspace lama, bangun workspace baru dari awal.

> ⚠️ **CARA BACA DOKUMEN INI:** Bagian 1–6 = peta arsitektur "apa yang ada".
> **Bagian 7 = inti dokumen** — 7 titik kegagalan dipetakan ke akar masalah di kode.
> Bagian 8–11 = referensi parameter, jebakan, dan rekomendasi rebuild.

---

## 1. APA INI?

Robot mobile otonom (AMR), penggerak 4 roda, **steering Ackermann** (belok roda depan
seperti mobil — **TIDAK bisa berputar di tempat**). Untuk Tugas Akhir: **mapping 3D
indoor + navigasi otonom**. Korelasi mata kuliah: Metode Numerik, DCS/SCADA, Pengolahan
Citra Digital.

**Kemampuan fisik kunci (ground-truth dari kode):**
- Wheelbase = 0.50 m, track width = 0.40 m, jari-jari roda = 0.0775 m
- Sudut steer maksimum = 45° (firmware `MAX_STEER`), → radius putar minimum fisik = `0.5 / tan(45°)` = **0.50 m**
- Encoder: 3858 pulsa per revolusi

---

## 2. HARDWARE

| Komponen | Detail |
|----------|--------|
| Komputer | Intel NUC13ANHi7 (i7, Ubuntu 22.04, ROS 2 Humble) |
| Kamera | Intel RealSense D455 (RGB+Depth 848x480x30, Accel ~100Hz, Gyro ~200Hz) |
| LiDAR | RPLIDAR C1 (2D, 360°, 10Hz, max 16m, **single-ring**) |
| Mikrokontroler | STM32 (serial Virtual ComPort, B115200) |
| Steering | Ackermann 2WS (roda depan), wheelbase 0.50m, radius putar fisik ~0.50m |
| Joystick | DualShock via Bluetooth, R1 = deadman switch (button index 5) |

**Catatan hardware penting (dari komentar kode `stm32_bridge.cpp:30-34, 207`):**
Kabel motor **ditukar secara fisik** agar perintah "maju" = robot maju. **TAPI arah hitung
encoder belum tentu ikut ditukar** — lihat Bagian 7.3 (akar masalah odometry terbalik).

---

## 3. STRUKTUR WORKSPACE (7 package)

```
src/
├── amr_bringup/          # Master launch: sensor + driver + odometry. Launch/config only (ament_python, tanpa node)
├── amr_controller/       # stm32_bridge (C++), odometry_publisher.py, imu_merger_node.py
├── amr_description/      # URDF/xacro robot, TF statis. (SEHAT — bukan sumber bug)
├── amr_3d_mapping/       # RTAB-Map SLAM 3D + VIO + localization
├── amr_slam/             # Nav2 stack (nama membingungkan: ini NAV2, bukan SLAM)
├── amr_failover/         # Arbiter cmd_vel 4-state (SLAM/visual/joy/e-stop)
└── amr_visual_regression/# Depth→(steer,vel) Random Forest + LiDAR line-segment node
```

> ⚠️ **Penamaan menyesatkan:** `amr_slam` berisi **Nav2** (navigasi), BUKAN SLAM. SLAM
> sesungguhnya ada di `amr_3d_mapping`. Di workspace baru, rename agar jelas.

---

## 4. ARSITEKTUR DATA & NODE GRAPH

### 4.1 Pipeline mapping (kondisi "lengkap")

```
RealSense D455 ─RGB+Depth─→ rgbd_sync ──/rgbd_image──→ rgbd_odometry (VIO) ──/rtabmap/odom──→ rtabmap (SLAM)
               ─Accel─┐                                      ↑                                     ↑
               ─Gyro──┴→ imu_merger ──/imu/data──────────────┘                                     │
RPLIDAR C1 ────────────────────────/scan──────────────────────────────────────────────────────────┘
STM32 ──E:{delta}──→ stm32_bridge ──/encoder──→ odometry_publisher ──/odom──→ (Nav2 / backup)
                                                                              ↓
                                                          rtabmap → /cloud_map (3D), /grid_map (2D), TF map→odom
```

### 4.2 Urutan terminal yang dipakai saat pengujian

| Terminal | Perintah | Fungsi |
|---|---|---|
| 1 | `ros2 launch amr_bringup amr_full.launch.py use_slam:=false use_nav2:=false use_rtabmap:=false use_vr:=false use_failover:=false` | Sensor + driver + wheel odometry |
| 2 | `ros2 launch amr_3d_mapping rtabmap_mapping.launch.py` | SLAM 3D (mapping) |
| 2' | `ros2 launch amr_3d_mapping rtabmap_localization.launch.py database_path:=...` | Localization (pakai peta .db) |
| 3 | `ros2 launch amr_slam nav2.launch.py` | Nav2 (navigasi otonom) |

### 4.3 TF Tree (dari URDF — INI SEHAT)

```
odom ──(dinamis: odometry_publisher ATAU VIO)──→ base_footprint
base_footprint ─[fixed, xyz 0 0 0.0775, rpy 0 0 0]→ base_link
  ├─ chassis            [fixed, rpy 0 0 0]
  ├─ rear_left/right_wheel   [continuous, axis 0 1 0]
  ├─ front_left/right_steering_link [revolute, axis 0 0 1, ±0.785 rad]
  │    └─ front wheel   [continuous]
  ├─ laser_frame        [fixed, xyz 0 0 0.250, rpy 0 0 0]   ← LiDAR, TIDAK diputar
  └─ camera_link        [fixed, xyz 0.350 0 0.200, rpy 0 0 0]  ← kamera, TIDAK diputar
       ├─ color_optical_frame [fixed, rpy -pi/2 0 -pi/2]  ← standar REP-103, BENAR
       └─ depth_optical_frame [fixed, rpy -pi/2 0 -pi/2]  ← standar REP-103, BENAR
```

**+x = depan** secara konsisten di seluruh URDF (front steering & kamera di +x, roda
belakang di −x). **TIDAK ada joint dengan yaw = π atau axis terbalik.** Verifikasi:
`amr_description/urdf/amr_description.urdf.xacro:36-213`.

---

## 5. RINGKASAN TIAP PACKAGE

### 5.1 `amr_bringup` — launch & config
- `launch/amr_full.launch.py` — master launch, semua sub-stack di-gate dengan argumen (`use_slam`, `use_nav2`, `use_rtabmap`, `use_vr`, `use_failover`).
  - Node `odometry_publisher` param di-override di sini: `wheel_radius=0.0775`, `wheelbase=0.50`, `pulses_per_revolution=3858`, `publish_rate=50.0`.
  - **`publish_tf = PythonExpression("'<use_rtabmap>' != 'true'")`** (`amr_full.launch.py:155-157`) — jadi saat `use_rtabmap:=false` (default), wheel odom **broadcast TF** `odom→base_footprint`; saat RTAB-Map aktif, VIO yang pegang TF.
- `launch/sensors_launch.py` — `rplidar_node` (→`/scan`), `camera` (RealSense, `publish_tf=False`, 848x480x30), 2 static_tf bridge (identity, hanya rename frame).
- `launch/amr_launch.py` — `joy_node` + `stm32_bridge`.
- ⚠️ `config/joy_params.yaml` menargetkan `teleop_node` (teleop_twist_joy) yang **tidak pernah di-launch** → file yatim. Jalur joystick→gerak lewat `stm32_bridge`, bukan teleop_twist_joy.

### 5.2 `amr_controller` — kontrol & odometry
- `src/stm32_bridge.cpp` (C++):
  - Serial by-id, B115200. **TX:** `"V:%d,S:%d\n"` (PWM ±4000, steer ±45° + trim −5°). **RX:** `"E:%d\n"` → republish `/encoder` (`std_msgs/Int32`, Reliable).
  - Velocity **tidak dinegasi** (kabel motor sudah ditukar). Steering **dinegasi** (`steer_rad = -atan(L*ω/v)`, `stm32_bridge.cpp:208`). Autonomous butuh `|v|>0.05` agar steering aktif (`:204`).
- `scripts/odometry_publisher.py` (Python):
  - Sub `/encoder`, `/joy`, `/cmd_vel` (semua **Reliable**); pub `/odom` (Reliable).
  - Model sepeda (bicycle): `delta_dist = last_delta * dist_per_tick` (`:218`); `theta += (vx/L)*tan(steering)*dt` (`:231`).
  - **Default `publish_tf=False` di script (`:76`)** — TAPI di-override jadi True oleh master launch saat non-RTAB-Map.
  - ⚠️ Tanda steering di sini **berlawanan** dengan `stm32_bridge`: joy callback negasi (`:151`), tapi `cmd_vel_cb` **tidak** negasi (`:162`).
- `scripts/imu_merger_node.py` (Python):
  - Gabung `/camera/camera/accel/sample` + `/gyro/sample` (ApproximateTimeSync, slop 0.05) → `/imu/data` (**BestEffort**).
  - Orientation di-set tak tersedia (`orientation_covariance[0] = -1.0`) — hanya accel+gyro, tanpa AHRS.
  - ⚠️ **TIDAK di-launch oleh `amr_bringup` mana pun.** Hanya dipanggil oleh launch `amr_3d_mapping`. Jadi di bringup default, IMU tidak terintegrasi sama sekali.

### 5.3 `amr_description` — URDF/TF — **SEHAT, BUKAN SUMBER BUG**
Lihat Bagian 4.3. Semua joint struktural `rpy 0 0 0`, +x konsisten ke depan,
`base_footprint→base_link` ada. Satu-satunya rotasi = optical frame standar REP-103.

### 5.4 `amr_3d_mapping` — RTAB-Map SLAM 3D
- `launch/rtabmap_mapping.launch.py` — **launch nyata** (410 baris, param inline lengkap). 5 node: imu_merger → rgbd_sync → rgbd_odometry (VIO) → rtabmap → depth_to_laserscan.
- `launch/rtabmap_localization.launch.py` — mode localization (`Mem/IncrementalMemory=false`).
- ⚠️ `launch/vio_only.launch.py` — **DUPLIKAT USANG** dari mapping launch (docstring salah, depth topic tak teralign, param rtabmap nyaris kosong). **JEBAKAN** — jangan dipakai.
- `qos=1` (BestEffort) di node rtabmap agar bisa terima `/scan` BestEffort dari rplidar.

### 5.5 `amr_slam` — **Nav2** (bukan SLAM)
- `config/nav2_params.yaml` (260 baris) + `launch/nav2.launch.py` + `scripts/goal_sender.py`.
- Planner: `SmacPlannerHybrid` (Ackermann-aware, BENAR). Controller: `RegulatedPurePursuitController` (BENAR, `use_rotate_to_heading:false`).
- Detail & masalah parameter → Bagian 7.7.

### 5.6 `amr_failover` — arbiter cmd_vel
- `failover_controller.py`: state machine 4-state (`SLAM_ACTIVE`, `VISUAL_FALLBACK`, `JOY_OVERRIDE`, `EMERGENCY_STOP`).
- Pilih sumber dari `/cmd_vel_nav`, `/cmd_vel_visual`, `/cmd_vel_joy` → publish `/cmd_vel` @20Hz. E-stop bila `/scan` min range < 0.30 m. Output status `/failover_status` + marker RViz.

### 5.7 `amr_visual_regression` — regresi citra (Path B, klasik)
- `data_collector_node.py` → rekam dataset (depth.npy + color.jpg + labels.csv).
- `scripts/train.py` → latih Random Forest Regressor.
- `vr_inference_node.py` → depth → 36 fitur → RF → `[steer, vel]` → `/cmd_vel_visual`. Safety: min depth <0.4m → vel=0. Model default di `/home/azhar/models/`.
- `lidar_line_segments_node.py` → `/scan` → RANSAC + PCA → segmen garis dinding → `/amr/line_segments`.

---

## 6. ENVIRONMENT

```bash
ROS_DISTRO=humble
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=42

~/amr_starter/          # workspace path di NUC
~/amr_starter/src/      # source packages
~/amr_starter/install/  # build artifacts
~/maps/                 # database .db hasil mapping (mis. lab_demo_18jun.db)
~/.ros/rtabmap.db       # default output mapping
```

---

## 7. ⭐ INTI DOKUMEN — 7 TITIK KEGAGALAN DIPETAKAN KE AKAR MASALAH

> Tiap titik = keluhan pemilik/dosen → akar masalah teknis nyata → referensi file:line →
> cara perbaikan di workspace baru. **Semua berbasis pembacaan kode aktual, bukan asumsi.**

---

### 7.1 — "Tidak dilihat integrasi sensor sudah tersambung atau belum"

**Akar masalah: tidak ada verifikasi liveness sensor, dan ada QoS mismatch yang
memutus aliran data secara DIAM-DIAM (tanpa error/crash).**

1. **`stm32_bridge` hanya cek "port terbuka", bukan "data masuk".** Log `[OK] STM32
   connected!` muncul saat serial berhasil dibuka (`stm32_bridge.cpp:52-61`), TAPI tidak
   ada cek bahwa byte encoder benar-benar mengalir. STM32 yang "tersambung tapi diam"
   tetap terlihat OK.

2. **QoS mismatch paling berbahaya — `rgbd_sync` tanpa `qos_image`.** RealSense publish
   image **BestEffort**, tapi `rgbd_sync` tidak set `qos`/`qos_image` → default **Reliable
   (2)** (`rtabmap_mapping.yaml:187-192`). Reliable-subscriber vs BestEffort-publisher =
   **QoS incompatible → TIDAK ada data terkirim**, tanpa error. Akibatnya `/rgbd_image`
   kosong → VIO mati → rtabmap tak dapat frame. **Ini bisa jadi penyebab utama mapping &
   loop closure tidak pernah jalan** (lihat 7.5).

3. **`/imu/data` BestEffort** (`imu_merger_node.py:83-88`) sementara konsumen Reliable
   (mis. robot_localization default) tak akan terima → IMU "diam".

4. **`odometry_publisher` subscribe `/cmd_vel` & `/joy` sebagai Reliable** (`:107-119`).
   Jika ada publisher cmd_vel BestEffort, koneksi gagal diam-diam → steering odom beku.

**Perbaikan di workspace baru:**
- Buat **health-check node / script** yang cek `ros2 topic hz` untuk tiap sensor wajib
  (`/scan`, `/camera/.../color`, `/camera/.../depth`, `/encoder`, `/imu/data`) dan tampilkan
  PASS/FAIL sebelum mapping. (Catatan: `scripts/amr_test_tools/scripts/topic_snapshot.py`
  sudah jadi cikal-bakal alat ini.)
- **Samakan QoS secara eksplisit di SEMUA subscriber sensor** → BestEffort (`qos:1`,
  `qos_image:1`, `qos_scan:1`) agar cocok dengan sensor.

---

### 7.2 — "Tidak tahu dependensi parameter yang dibutuhkan untuk membangun sistem AMR"

**Akar masalah: parameter tersebar di banyak tempat dengan prioritas yang saling
menimpa, sehingga "sudah di-set" di satu file ternyata ditimpa file lain.**

Fakta konkret yang ditemukan:
- **Inline launch override YAML.** Banyak parameter ada DUA kali (di `.launch.py` inline
  dan di `config/*.yaml`). Di ROS 2, **inline launch menang**. Contoh paling merusak:
  localization YAML diperbaiki ke `STMSize=10, LoopThr=0.05`, tapi
  `rtabmap_localization.launch.py:165,178` meng-inline `STMSize=30, LoopThr=0.11` →
  **perbaikan YAML diam-diam dibatalkan**.
- **Duplicate key dalam satu YAML.** `Odom/MaxVariance` di-set `0.05` (baris 169) lalu
  `0.01` lagi (baris 175) di `rtabmap_mapping.yaml` → YAML last-key-wins = `0.01`
  (nilai terlalu ketat yang dikomentari sendiri sebagai penyebab "cloud kosong").
- **CMake tanpa symlink-install untuk config** → edit YAML **tidak sampai ke `install/`**
  tanpa rebuild. Jadi user kira sudah ganti param, padahal runtime baca versi lama.

**Perbaikan di workspace baru:**
- **Satu sumber kebenaran (single source of truth) per parameter.** Pilih: SEMUA inline
  ATAU semua YAML. Jangan campur. Rekomendasi: semua di YAML + `--symlink-install`.
- Buat **tabel dependensi parameter** (Bagian 8) jadi dokumen hidup.
- Tambah langkah `colcon build --symlink-install` + verifikasi `ros2 param get` setelah edit.

---

### 7.3 — "Odometry menghadap ke belakang padahal robot menghadap ke depan"

**Akar masalah: BUKAN di URDF (URDF sehat). Ada di tanda (sign) encoder & steering di
`amr_controller`.**

URDF sudah diverifikasi BENAR: +x ke depan, tak ada yaw π, sensor tak diputar
(`amr_description.urdf.xacro:36-213`). Jadi 180° error TIDAK berasal dari frame statis.

**Dua sumber sebenarnya:**

1. **Tanda encoder (paling mungkin).** Arah gerak odom **sepenuhnya** bergantung tanda
   `last_delta` dari `/encoder`: `delta_dist = last_delta * dist_per_tick`
   (`odometry_publisher.py:218`). Kabel motor **ditukar fisik** agar perintah maju = maju
   (`stm32_bridge.cpp:30-34, 207`), **TAPI arah hitung encoder tidak ikut dibalik**. Jika
   encoder melaporkan delta negatif saat robot maju, maka `x` berkurang → pose odom jalan
   mundur sementara robot maju. **Odometry tidak punya referensi silang** ke tanda
   `cmd_vel` untuk mengoreksi ini.

2. **Asimetri tanda steering.** `stm32_bridge` negasi steering (`:208`), tapi
   `odometry_publisher.cmd_vel_cb` **tidak** negasi (`:162`) sedangkan joy callback negasi
   (`:151`). Akibatnya di mode autonomous, yaw odom melengkung ke arah berlawanan dari
   belokan fisik → heading makin lama makin salah.

**Perbaikan di workspace baru:**
- **Verifikasi tanda encoder dulu** (paling penting): dorong robot maju manual, lihat
  apakah `/encoder` naik positif. Jika negatif → balik tanda di firmware STM32 ATAU negasi
  `last_delta` di `odometry_publisher.py:218`.
- **Samakan konvensi steering** di kedua node (kontrol & odometry) — satu tempat saja yang
  menentukan tanda.
- Tambah uji kalibrasi: maju 1 m → cek `/odom` x naik ~+1.0 (uji ini sudah dibuat:
  `scripts/amr_test_tools/scripts/odom_trial_logger.py`).

---

### 7.4 — "Tidak mendalami x,y dari deteksi LiDAR"

**Akar masalah: LiDAR x,y dipakai sangat dangkal — hanya untuk grid 2D & koreksi ICP
pose, TIDAK pernah masuk ke cloud 3D, dan ICP-nya disetel buruk untuk LiDAR single-ring.**

Fakta:
- `subscribe_scan=true`, `qos=1`, remap `scan→/scan` — scan **diterima**.
- Grid 2D **memang** dari LiDAR (`Grid/FromDepth=false`, `rtabmap_mapping.yaml:86`). BAGUS.
- TAPI **cloud 3D (`cloud_map`) dibangun murni dari depth image** (`publish_cloud_map` +
  `cloud_*` params). **Titik LiDAR tidak pernah dimasukkan ke 3D.**
- **ICP disetel buruk untuk single-ring 2D:** `Icp/PointToPlane=true`
  (`rtabmap_mapping.launch.py:269`). Untuk scan 2D garis-tipis, estimasi normal tak andal —
  seharusnya point-to-point. `Icp/VoxelSize=0.05` lagi-lagi men-decimate scan yang sudah sparse.
- `/depth_scan` dari `depth_to_laserscan` hanya dikirim ke **Nav2**, tidak difusikan ke rtabmap.

**Perbaikan di workspace baru:**
- Pahami peran LiDAR: untuk robot 2D-indoor, **scan-to-scan ICP / LiDAR odometry** sering
  lebih akurat daripada VIO untuk x,y. Pertimbangkan jadikan LiDAR sumber utama x,y.
- Ganti `Icp/PointToPlane=false` (point-to-point) untuk single-ring.
- Pelajari `lidar_line_segments_node.py` (sudah ada RANSAC+PCA dinding) untuk fitur
  geometris x,y yang lebih dalam.

---

### 7.5 — "Loop Closure tidak bekerja menyimpan frame — ada parameter belum di-setup & masih disconnected, tapi dikira sudah"

**Akar masalah: parameter loop closure ADA & masuk akal, tapi feed kamera kemungkinan
TERPUTUS diam-diam karena QoS (7.1), jadi rtabmap tak pernah akumulasi node → loop
closure mustahil terpicu.**

Ini persis gejala "sudah di-setup tapi disconnected":
1. **`rgbd_sync` QoS mismatch (lihat 7.1.2)** → `/rgbd_image` kosong → rtabmap tak daftar
   node sama sekali → loop closure tak pernah jalan. Tidak ada yang crash, jadi terlihat
   "seperti sudah jalan".
2. **Riwayat `loop_closure_id selalu 0`** (komentar `rtabmap_mapping.yaml:56-59`) konsisten
   dengan loop closure tak pernah terpicu.
3. **Komentar parameter TERBALIK:** komentar di `rtabmap_mapping.launch.py:303-304` bilang
   "LoopThr lebih TINGGI = lebih sulit accept" — ini **salah**. `Rtabmap/LoopThr` =
   probabilitas minimum untuk **menerima** loop closure; **menurunkannya = lebih mudah**.
   Nilai diturunkan 0.11→0.08→0.05 mengejar "selalu rejected" — padahal masalah
   sebenarnya kemungkinan di hulu (tak ada frame karena QoS), bukan threshold.
4. **Mode localization:** inline `LoopThr=0.11`/`STMSize=30` menimpa perbaikan YAML
   `0.05`/`10` (lihat 7.2).
5. `subscribe_odom_info=False` → info loop closure berkurang.

**Perbaikan di workspace baru:**
- **Perbaiki QoS `rgbd_sync` dulu** (`qos_image:1`) — ini kemungkinan kunci utama.
- Verifikasi `ros2 topic hz /rgbd_image` > 0 SEBELUM menyalahkan parameter loop closure.
- Setel ulang `LoopThr` dari nilai default RTAB-Map (0.11) setelah feed dipastikan hidup.
- Pahami alur: node → STM (Short-Term Mem) → setelah `STMSize` node → WM (eligible loop
  target) → BoW place recognition @`DetectionRate` → verifikasi geometris → optimize graph.

---

### 7.6 — "Tidak membuat sistem Hierarki (seperti teman dgn robot arm + kamera)"

**Akar masalah: arsitektur ada (TF tree benar, frame sensor terpasang), tapi TIDAK ada
"hierarki tugas/perilaku" yang mengoordinasikan persepsi → keputusan → aksi. Yang ada
hanya pipeline data datar.**

Konteks: teman pemilik membuat robot arm dengan **hierarki**: kamera disamakan posisinya
(frame) ke arm → deteksi objek → arm ambil. Itu hierarki **TF + task/behavior** yang jelas.

Yang ADA di sistem ini:
- **Hierarki TF sudah benar** (`base_footprint→base_link→sensor frames`, Bagian 4.3) —
  jadi fondasi "menyamakan posisi kamera/LiDAR ke robot" SUDAH ada, tinggal dimanfaatkan.
- `amr_failover` adalah satu-satunya "koordinator" (arbiter cmd_vel), tapi ia hanya
  memilih sumber kecepatan, bukan hierarki tugas.

Yang TIDAK ada:
- **Tidak ada Behavior Tree / state machine tingkat misi** (selain BT bawaan Nav2). Tidak
  ada lapisan "perception → world model → planning → action" yang eksplisit.
- Persepsi (`amr_visual_regression`, `lidar_line_segments`) berdiri sendiri, **tidak
  ter-feed** ke pengambilan keputusan navigasi.

**Perbaikan di workspace baru:**
- Rancang **hierarki eksplisit**: (1) Layer sensor/TF, (2) Layer persepsi (peta, objek,
  dinding), (3) Layer world-model/lokalisasi, (4) Layer planning (Nav2), (5) Layer
  behavior/misi (BT). Definisikan kontrak topik antar-layer.
- Manfaatkan TF tree yang sudah benar untuk transform deteksi ke `base_link`/`map`.

---

### 7.7 — "Kenapa robot mencari jalur rumit untuk menuju titik yang di-set?"

**Akar masalah: pilihan plugin Nav2 sudah BENAR (dosen keliru soal "salah planner"),
tapi NILAI parameter membuat jalur berbelit. 3 penyebab utama:**

> Plugin sudah tepat: `SmacPlannerHybrid` (Ackermann-aware) + `RegulatedPurePursuit`
> (`use_rotate_to_heading:false`). Masalahnya di **nilai**, bukan pilihan.

| # | File:line | Param | Nilai skrg | Masalah | Saran |
|---|---|---|---|---|---|
| **A** | `nav2_params.yaml:185` | `minimum_turning_radius` | **0.90** | ~80% lebih besar dari kemampuan fisik (0.50m). Planner dipaksa bikin busur lebar → S-curve & detour | ~0.60 |
| **B** | `nav2_params.yaml:104,162` | `inflation_radius` | **0.10** | Terlalu KECIL (bukan terlalu besar). Tak ada gradien koridor → robot nempel-lepas dinding (zig-zag) | ~0.20–0.30 |
| **C** | `nav2_params.yaml:131-137,158` | global costmap `rolling_window`, tanpa static map, frame `odom` | rolling, odom | Planner global hanya "lihat" window 10×10m tanpa peta → replan terus → lintasan kumulatif zig-zag | pakai static map di frame `map` |
| **D** | `nav2_params.yaml:215; :28` | behavior `spin` + recovery BT bawaan | ada `spin` | Ackermann **tak bisa putar di tempat** → recovery Spin gagal/twitch → gerakan makin kacau | buang `spin`, BT custom |
| **E** | `nav2_params.yaml:252` | velocity_smoother angular max | 0.5 | Membatasi kurvatur di bawah kemampuan kinematik | naikkan sesuai radius |
| **F** | `goal_sender.py:66` vs `nav2_params.yaml:23` | goal frame vs global_frame | map vs odom | TF map→odom drift → goal bergeser → jalur ngelantur | samakan frame / stabilkan map→odom |

**Tiga yang paling kelihatan efeknya: A, B, D.**

**Perbaikan di workspace baru:**
- Set `minimum_turning_radius` sesuai fisik (0.5m + margin).
- Naikkan `inflation_radius` agar ada gradien tengah-koridor.
- Buang `spin` dari behavior; pakai static map untuk planning global.

---

## 8. REFERENSI PARAMETER KRITIS (tabel dependensi)

### 8.1 RTAB-Map VIO (`rgbd_odometry`)
| Param | Nilai | Catatan |
|---|---|---|
| `Odom/Strategy` | 0 | Frame-to-Map |
| `Odom/MaxVariance` | 0.05 | (YAML duplikat ke 0.01 — JEBAKAN, perbaiki) |
| `Odom/ResetCountdown` | 5 | toleransi motion blur |
| `Vis/MinInliers` | 8 | <8 = pose acak (cloud scattered) |
| `Reg/Force3DoF` | true | ground vehicle x,y,yaw |

### 8.2 RTAB-Map SLAM (`rtabmap`)
| Param | Nilai | Catatan |
|---|---|---|
| `Reg/Strategy` | 2 | Vis+ICP |
| `Rtabmap/LoopThr` | 0.05 | **komentar terbalik di kode**; default RTAB-Map 0.11 |
| `Rtabmap/DetectionRate` | 2.0 | deteksi 2×/detik |
| `Mem/STMSize` | 10 | node cepat ke WM |
| `Mem/IncrementalMemory` | true (map) / false (loc) | switch mode |
| `Grid/FromDepth` | false | grid dari LiDAR |
| `Icp/PointToPlane` | true | **buruk utk single-ring 2D**, ganti false |
| `qos` | 1 | BestEffort utk /scan |
| `subscribe_rgb` | false | cegah konflik subscribe_rgbd |

### 8.3 rgbd_sync (SUMBER QoS BUG)
| Param | Nilai skrg | Seharusnya |
|---|---|---|
| `qos`/`qos_image` | **tidak di-set → Reliable** | **1 (BestEffort)** agar cocok RealSense |
| `approx_sync` | false | hardware-synced |

### 8.4 Nav2 — lihat tabel Bagian 7.7.

---

## 9. JEBAKAN & DEFECT TERDOKUMENTASI (jangan terulang)

1. **`vio_only.launch.py`** = duplikat usang mapping launch (depth tak teralign, param kosong). Jangan dipakai.
2. **Inline launch menimpa YAML** — perbaikan YAML bisa "hilang" saat runtime.
3. **Duplicate key `Odom/MaxVariance`** (0.05 lalu 0.01) di `rtabmap_mapping.yaml`.
4. **`cloud_voxel_size`** beda: inline 0.05 vs YAML 0.03.
5. **CMake config tanpa symlink-install** → wajib rebuild agar YAML sampai `install/`.
6. **`joy_params.yaml` yatim** (target `teleop_node` yang tak di-launch).
7. **`imu_merger` tak di-launch di bringup** — IMU mati di mode default.
8. **Komentar `LoopThr` terbalik** — jangan ikuti arah tuning lama.
9. **Nama `amr_slam` = Nav2**, bukan SLAM.
10. **Banyak file `.bak`** sisa trial-error — file aktif = yang non-`.bak`.

---

## 10. HARD RULES (dari pemilik — DILARANG DILANGGAR)

1. JANGAN push ke `main` — selalu branch feature; tiap push butuh approval eksplisit ("ya push").
2. JANGAN ubah resolusi RealSense dari 848x480x30 (RGB & Depth).
3. JANGAN ubah URDF (`amr_description/`) kecuali diminta eksplisit "ubah URDF".
4. JANGAN install package baru tanpa menyatakan dulu apa & kenapa.
5. JANGAN rebuild full workspace (`colcon build` tanpa `--packages-select`).
6. JANGAN hapus file/folder tanpa konfirmasi eksplisit.
7. JANGAN klaim "sudah jalan" tanpa output command sebagai bukti.
8. JANGAN fabrikasi spec hardware / parameter yang tidak ada.
9. JANGAN ganti algoritma fundamental tanpa diskusi panjang.
10. Selalu cek update repo (termasuk fork Mervi) sebelum eksekusi.

---

## 11. REKOMENDASI URUTAN REBUILD (workspace baru)

Prioritas berbasis dependensi (fondasi dulu):

1. **[Fondasi] Verifikasi & integrasi sensor** (atasi 7.1): health-check node, samakan
   semua QoS ke BestEffort. Pastikan `ros2 topic hz` semua sensor > 0.
2. **[Fondasi] Kalibrasi odometry** (atasi 7.3): perbaiki tanda encoder & steering, uji
   maju 1m = +1.0 di /odom. Tegaskan satu konvensi tanda.
3. **[Parameter] Single source of truth** (atasi 7.2): pilih YAML-only + symlink-install,
   buang inline ganda, hapus duplicate key.
4. **[Mapping] Perbaiki feed RGB-D + loop closure** (atasi 7.5): `qos_image:1` di
   rgbd_sync, verifikasi `/rgbd_image` hidup, baru tuning LoopThr.
5. **[Mapping] Perdalam pemakaian LiDAR** (atasi 7.4): ICP point-to-point, pertimbangkan
   LiDAR sebagai sumber x,y utama.
6. **[Navigasi] Perbaiki nilai Nav2** (atasi 7.7): turunkan `minimum_turning_radius`,
   naikkan `inflation_radius`, buang `spin`, pakai static map.
7. **[Arsitektur] Bangun hierarki eksplisit** (atasi 7.6): definisikan layer
   perception→world-model→planning→behavior + kontrak topik.

---

## 12. KONTAK & KOLABORATOR

- **Owner:** Muhammad Al Azhar Faradis (malazharfaradis@gmail.com)
- **Teammate:** Mervi — fork: https://github.com/Mervs111/autonomous-mobile-robot-ros2
  (kontribusi PCD prototype, SOP, RViz config). **Selalu cek update fork Mervi sebelum eksekusi.**

---

## 13. LAMPIRAN — Dokumen & alat pendukung yang sudah ada

- `HANDOVER_GEMINI.md` — handover sebelumnya (11 Jun 2026), fokus QoS fix mapping.
- `docs/SOP_MAPPING_DAN_AUTONOMOUS.md` — SOP operasional.
- `scripts/amr_test_tools/` — alat uji odometry/localization/navigation + rekap Excel
  (sudah dipakai untuk pengambilan data pengujian).
- `scripts/export_rtabmap_db.py`, `analyze_rtabmap_excel.py`, `extract_rtabmap_*.py` —
  ekstraksi & analisis database .db (trajectory, loop closure, sensor RGBD/LiDAR).
- File `frames_*.pdf` — snapshot TF tree historis.

> **Pesan untuk AI/engineer berikutnya:** Sistem ini GAGAL bukan karena pilihan
> arsitektur fundamental yang salah (URDF benar, plugin Nav2 benar, pipeline RTAB-Map
> wajar). Ia gagal karena **akumulasi masalah integrasi**: QoS mismatch yang memutus
> data diam-diam, tanda encoder/steering yang tak dikalibrasi, parameter yang saling
> menimpa antar-file, dan nilai parameter Nav2 yang tak sesuai kemampuan fisik robot.
> Bangun ulang dengan disiplin: **verifikasi tiap koneksi sebelum naik ke layer
> berikutnya.**
