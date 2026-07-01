# HANDOVER: Rebuild Arsitektur AMR Ackermann

**Penulis:** Muhammad Al Azhar Faradis (NRP 2040241017)  
**Program Studi:** Teknik Elektro Otomasi — ITS Surabaya  
**Tanggal:** 30 Juni 2026  
**Deadline:** Akhir Juli 2026 (~30 hari)  
**Status:** Kode selesai di Windows, BELUM deploy ke NUC

---

## 1. Konteks Proyek

### 1.1 Apa yang terjadi

Sistem AMR sebelumnya dinyatakan **GAGAL** oleh dosen pembimbing. Dokumen analisis kegagalan tercatat di `HANDOVER_ARSITEKTUR_AMR_GAGAL.md` yang mengidentifikasi **7 titik kegagalan** fatal pada kode lama.

Diputuskan untuk **membangun ulang dari nol** — bukan patch, tapi arsitektur baru yang memperbaiki setiap kegagalan secara sistematis.

### 1.2 Hardware robot

| Komponen | Spesifikasi |
|---|---|
| Komputer | Intel NUC13, Ubuntu 22.04, ROS 2 Humble |
| Kamera | Intel RealSense D455 (color + depth + IMU) |
| LiDAR | RPLIDAR C1 (single-ring 2D, ~360°) |
| Mikrokontroler | STM32 (bridge encoder + motor) |
| Steering | **Ackermann** (4WD, seperti mobil — TIDAK bisa putar di tempat) |
| Resolusi kamera | 848×480×30 (RGB & Depth) — JANGAN DIUBAH |

### 1.3 Lingkungan kerja

- **Pengembangan:** Windows 11, folder `C:\Users\alazh\Downloads\AMR\amr_ws\`
- **Deploy:** NUC Ubuntu 22.04, folder `~/amr_ws/`
- **ROS 2:** Humble Hawksbill

---

## 2. Arsitektur Sistem — 5 Layer

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
│  Layer 1: SENSE — amr_sensors                        │
│  LiDAR + RealSense + IMU merger + Health Check       │
└──────────────────────────────────────────────────────┘
```

Setiap layer **bergantung pada layer di bawahnya.** Deploy dan uji harus **berurutan dari bawah ke atas.** Kalau Layer 1 gagal, Layer 2–5 pasti ikut gagal.

---

## 3. Peta Perbaikan — 7 Kegagalan Lama → 7 Fix

| # | Kegagalan Sistem Lama | Root Cause | Fix di Sistem Baru | Lokasi Fix |
|---|---|---|---|---|
| 7.1 | Sensor terputus tanpa error | QoS mismatch (publisher BestEffort, subscriber Reliable) | **Kontrak QoS:** semua sensor BestEffort, cmd_vel Reliable | `sensors.yaml`, `rtabmap.yaml` |
| 7.2 | Parameter saling overwrite | Parameter ditulis inline di launch + YAML + code | **Single source of truth:** hanya YAML, launch tanpa inline | Semua `config/*.yaml` |
| 7.3 | Odometry jalan mundur | Encoder sign terbalik + encoder dijadikan sumber utama | **Encoder input lemah** (kov besar), VIO sumber utama | `ekf.yaml`, `encoder_odom_node.py` |
| 7.4 | LiDAR dipakai dangkal | ICP PointToPlane untuk LiDAR single-ring | **ICP PointToPoint** + VoxelSize 0 | `rtabmap.yaml` |
| 7.5 | Loop closure tidak pernah terpicu | rgbd_sync tidak terima gambar (QoS mismatch) | **qos_image: 1** (BestEffort) di rgbd_sync | `rtabmap.yaml` |
| 7.6 | Tidak ada hierarki perilaku | Hanya saklar failover, bukan FSM/BT | **Brain FSM** dengan 5 state + transisi | `brain_node.py` |
| 7.7 | Jalur navigasi berbelit | turning_radius terlalu besar, inflation terlalu kecil, ada spin recovery | **Ackermann-aware Nav2:** no spin, inflation 0.25, Reeds-Shepp | `nav2_params.yaml` |

---

## 4. Keputusan Desain yang Sudah Dikunci

### 4.1 Odometry: VIO sebagai sumber utama

**Keputusan:** Visual-Inertial Odometry (VIO) dari RTAB-Map `rgbd_odometry` + IMU D455 adalah sumber pose utama. Encoder HANYA input tambahan di EKF dengan kovarians BESAR.

**Alasan:** Fisik mekanis robot penuh slip, roda sedikit miring → encoder selalu melenceng. VIO menggunakan kamera + IMU yang tidak terpengaruh slip roda.

**Implementasi:**
- EKF `odom0`: `/rtabmap/odom` (VIO) — trust penuh, x/y/yaw/vx/vyaw
- EKF `odom1`: `/encoder_odom` — HANYA vx, kovarians 1.0 (besar = tidak dipercaya)

### 4.2 Kontrak QoS

| Topic | QoS | Alasan |
|---|---|---|
| `/scan` (LiDAR) | BestEffort | High-frequency, data terbaru lebih penting |
| `/camera/*/color/image_raw` | BestEffort | 30 fps, frame terlewat tidak fatal |
| `/camera/*/depth/image_rect_raw` | BestEffort | Sama dengan color |
| `/imu/data` | BestEffort | 200+ Hz, data terbaru yang penting |
| `/encoder` | BestEffort | High-frequency |
| `/cmd_vel` | **Reliable** | Perintah motor kritis, tidak boleh hilang |

**KRITIS:** `rgbd_sync` di RTAB-Map HARUS subscribe dengan `qos_image: 1` (BestEffort). Ini yang membunuh sistem lama — gambar tidak pernah sampai karena QoS mismatch.

### 4.3 Ackermann constraints

Robot menggunakan steering Ackermann (seperti mobil):
- **TIDAK BISA** putar di tempat (no spin)
- **BISA** mundur
- Memiliki radius putar minimum (BELUM DIUKUR — lihat Bagian 8)

Dampak pada Nav2:
- Recovery behavior: hanya `backup` + `wait`, **TIDAK ADA `spin`**
- Planner: `SmacPlannerHybrid` dengan `REEDS_SHEPP` (maju + mundur)
- Controller: `use_rotate_to_heading: false`

### 4.4 Parameter management

**Aturan Modul 3:** Semua parameter HANYA ditulis di file YAML di folder `config/`. Launch file TIDAK BOLEH menulis parameter inline. `--symlink-install` WAJIB saat build.

### 4.5 Referensi RAISA

Repo dosen (`github.com/ismarintan98/Mobile_Robot_RAISA`) dipakai HANYA untuk pola arsitektur berlapis (FSM) di Brain. TIDAK dipakai untuk odometry/lokalisasi karena RAISA menggunakan UWB (domain berbeda).

---

## 5. Inventaris File Lengkap

### 5.1 amr_sensors (Layer 1 — SENSE)

| File | Fungsi |
|---|---|
| `config/sensors.yaml` | Parameter LiDAR, RealSense, LiDAR XY (single source of truth) |
| `amr_sensors/health_check_node.py` | Subscribe 5 sensor, lapor PASS/FAIL tiap 2 detik |
| `amr_sensors/imu_merger_node.py` | Gabung D455 accel + gyro → `/imu/data` (BestEffort) |
| `amr_sensors/lidar_xy_node.py` | Konversi polar→kartesian, visualisasi RViz2, CSV recording |
| `amr_sensors/integration_check_node.py` | Verifikasi QoS compatibility, frekuensi, latency |
| `launch/sensors.launch.py` | Launch rplidar + realsense + imu_merger + health_check |
| `launch/lidar_study.launch.py` | Launch rplidar + lidar_xy + rviz2 (untuk pengambilan data dosen) |
| `package.xml` | Deps: rclpy, sensor_msgs, diagnostic_msgs, rplidar_ros, realsense2_camera |
| `setup.py` | Entry points: health_check, imu_merger, lidar_xy, integration_check |

### 5.2 amr_pose (Layer 2 — POSE)

| File | Fungsi |
|---|---|
| `config/ekf.yaml` | EKF config: VIO (odom0, trust) + encoder (odom1, suspek) |
| `config/encoder.yaml` | wheel_radius=0.0775, pulses_per_revolution=3858, publish_rate=20 |
| `amr_pose/encoder_odom_node.py` | Konversi encoder Int32 → Odometry. Hanya vx. Kov besar. |
| `launch/pose.launch.py` | Launch encoder_odom + EKF |
| `package.xml` | Deps: rclpy, nav_msgs, robot_localization |
| `setup.py` | Entry point: encoder_odom |

### 5.3 amr_mapping (Layer 3 — MAP)

| File | Fungsi |
|---|---|
| `config/rtabmap.yaml` | Parameter rgbd_sync (qos_image:1 ✓), VIO, RTAB-Map SLAM, ICP |
| `launch/mapping.launch.py` | rgbd_sync → VIO → rtabmap → peta baru |
| `launch/localization.launch.py` | Pakai peta .db yang sudah ada |
| `package.xml` | Deps: rtabmap_slam, rtabmap_odom, rtabmap_sync |
| `setup.py` | Tidak ada entry points (semua dari rtabmap_ros) |

### 5.4 amr_navigation (Layer 4 — ACT)

| File | Fungsi |
|---|---|
| `config/nav2_params.yaml` | Nav2 lengkap: planner, controller, costmap, recovery, smoother |
| `launch/nav2.launch.py` | Launch semua Nav2 lifecycle nodes |
| `package.xml` | Deps: nav2_bringup |
| `setup.py` | Tidak ada entry points (semua dari nav2) |

### 5.5 amr_brain (Layer 5 — THINK)

| File | Fungsi |
|---|---|
| `config/brain.yaml` | Sensor kritis/warning, timeout stuck, recovery params |
| `amr_brain/brain_node.py` | FSM: IDLE/MAPPING/NAVIGATING/STUCK/ERROR + transisi |
| `launch/brain.launch.py` | Launch brain node |
| `package.xml` | Deps: rclpy, geometry_msgs, sensor_msgs, diagnostic_msgs |
| `setup.py` | Entry point: brain |

### 5.6 amr_startup (Master Launch)

| File | Fungsi |
|---|---|
| `launch/amr_sensors_only.launch.py` | Tahap 1: sensor saja |
| `launch/layer2_pose.launch.py` | Tahap 3: sensor + pose |
| `launch/layer3_mapping.launch.py` | Tahap 4: sensor + pose + mapping |
| `launch/layer4_navigation.launch.py` | Tahap 5: sensor + pose + localization + nav2 |
| `launch/full_system.launch.py` | Tahap 6: SEMUA layer + brain |
| `launch/record_sensors.launch.py` | Rekam semua topic ke rosbag |
| `launch/save_map.launch.py` | Simpan peta .pgm + .yaml + backup .db ke ~/maps/ |

### 5.7 amr_body & amr_motor (Kerangka — belum diisi)

| Package | Status | Keterangan |
|---|---|---|
| `amr_body` | Kerangka CMake | Untuk URDF/xacro nanti (robot_state_publisher) |
| `amr_motor` | Kerangka CMake | Untuk STM32 bridge nanti (rclcpp) |

### 5.8 File root workspace

| File | Fungsi |
|---|---|
| `amr_ws/deploy.bash` | Script deploy otomatis ke NUC (7 langkah) |
| `amr_ws/DEPLOY_NUC.md` | Checklist uji coba per tahap (copy-paste di terminal) |
| `amr_ws/ATURAN_PARAMETER.md` | Aturan Modul 3 (single source of truth) |

---

## 6. Dependencies (apt packages di NUC)

```bash
# ROS 2 packages
ros-humble-rtabmap-ros              # RTAB-Map SLAM + VIO
ros-humble-navigation2              # Nav2 full stack
ros-humble-nav2-bringup             # Nav2 launch helpers
ros-humble-robot-localization       # EKF
ros-humble-rplidar-ros              # RPLIDAR driver
ros-humble-realsense2-camera        # RealSense driver
ros-humble-realsense2-description   # RealSense URDF
ros-humble-depthimage-to-laserscan  # Depth → fake scan
ros-humble-robot-state-publisher    # TF dari URDF
ros-humble-joint-state-publisher    # Joint states
ros-humble-xacro                    # URDF macros
ros-humble-diagnostic-msgs          # Diagnostics
ros-humble-tf2-tools                # view_frames

# Build tools
python3-colcon-common-extensions
python3-rosdep
```

Semua di-install otomatis oleh `deploy.bash`.

---

## 7. Progress per Modul

| Modul | Judul | Konsep | Kode | Deploy NUC | Uji PASS |
|---|---|---|---|---|---|
| 1 | Sensor + QoS | ✅ | ✅ | ❌ | ❌ |
| 2 | Pose: VIO + EKF | ✅ | ✅ | ❌ | ❌ |
| 3 | Parameter management | ✅ | ✅ | ❌ | ❌ |
| 4 | RTAB-Map SLAM + loop closure | ✅ | ✅ | ❌ | ❌ |
| 5 | Nav2 Ackermann navigation | ✅ | ✅ | ❌ | ❌ |
| 6 | Brain FSM (hierarki perilaku) | ✅ | ✅ | ❌ | ❌ |

**Status keseluruhan:** Semua kode tertulis. Belum ada yang diuji di hardware fisik.

---

## 8. Parameter yang BELUM TERVERIFIKASI (KRITIS)

Tiga parameter ini **TEBAKAN**, bukan data. HARUS diukur di NUC sebelum robot boleh jalan otonom:

### 8.1 Radius putar minimum

- **Nilai sekarang:** `minimum_turning_radius: 0.55` (PLACEHOLDER)
- **File:** `amr_navigation/config/nav2_params.yaml` baris 71
- **Cara ukur:** Belok full → spidol di roda belakang → ukur diameter lingkaran → radius = diameter/2
- **Dampak kalau salah:** Jalur berbelit (kebesaran) atau tabrak dinding (kekecilan)

### 8.2 Arah encoder (sign)

- **Asumsi sekarang:** Maju = positif
- **File:** `amr_pose/amr_pose/encoder_odom_node.py`
- **Cara verifikasi:** Dorong robot maju → `/encoder` harus naik (positif)
- **Dampak kalau salah:** Robot "berpikir" jalan mundur padahal maju

### 8.3 Footprint robot (panjang × lebar)

- **Nilai sekarang:** `footprint: [[0.25, -0.20], [0.25, 0.20], [-0.25, 0.20], [-0.25, -0.20]]` (PLACEHOLDER 50cm × 40cm)
- **File:** `amr_navigation/config/nav2_params.yaml` (local_costmap DAN global_costmap)
- **Cara ukur:** Meteran dari ujung terluar robot (termasuk sensor yang menonjol). Panjang = depan-belakang, lebar = kiri-kanan.
- **Format:** `[[depan/2, -lebar/2], [depan/2, lebar/2], [-belakang/2, lebar/2], [-belakang/2, -lebar/2]]`
- **Dampak kalau salah:** Terlalu kecil = tabrak tembok. Terlalu besar = tidak bisa lewat lorong yang seharusnya cukup.

### 8.4 Encoder PPR (pulses per revolution)

- **Nilai sekarang:** `pulses_per_revolution: 3858`
- **File:** `amr_pose/config/encoder.yaml`
- **Cara verifikasi:** Putar roda tepat 1 putaran → hitung selisih pulsa
- **Dampak kalau salah:** Kecepatan yang dilaporkan encoder tidak akurat

---

## 9. Konsep yang Dipahami Mahasiswa

Berikut konsep yang sudah diajarkan dan dipahami melalui analogi:

| Konsep | Analogi yang dipakai | Status pemahaman |
|---|---|---|
| Frame `odom` vs `map` | Langkah kaki (drift) vs GPS (lompat tapi akurat) | ✅ Paham |
| QoS BestEffort vs Reliable | Teriak (tidak peduli dengar) vs telepon (pastikan dengar) | ✅ Paham |
| QoS mismatch = silent death | Teriak ke orang yang pakai headset = tidak pernah dengar | ✅ Paham |
| VIO (Visual-Inertial Odometry) | Mata + telinga dalam (keseimbangan) | ✅ Paham |
| EKF sensor fusion | Menggabungkan 2 saksi: yang terpercaya vs yang mencurigakan | ✅ Paham |
| Kovarians besar = tidak dipercaya | "Aku curiga kamu bohong, jadi aku lebih percaya saksi lain" | ✅ Paham |
| Ackermann vs differential | Mobil vs kursi roda | ✅ Paham |
| Single source of truth (YAML) | Buku resep (1 tempat) vs catatan tempel (bertebaran) | ✅ Paham |
| Brain FSM | Bos di kursi belakang yang memutuskan supir harus kemana | ✅ Paham |
| Loop closure | Buka mata, lihat kulkas → "Oh aku pernah di sini!" | ✅ Paham |
| Sense → Think → Act | Indera → Otak → Otot (dari SKC M1) | ✅ Paham |

---

## 10. Alur Deploy ke NUC

```
TAHAP 0: Transfer src/ ke NUC → deploy.bash
    ↓
TAHAP 1: Layer 1 Sensor → health check 5/5 PASS?
    ↓ PASS
TAHAP 2: Pengukuran fisik → encoder sign, PPR, radius putar
    ↓ Data ditulis ke YAML
TAHAP 3: Layer 2 Pose → EKF aktif, TF: odom→base_footprint?
    ↓ PASS
TAHAP 4: Layer 3 Mapping → /rgbd_image > 0 Hz? loop closure terpicu?
    ↓ PASS + simpan peta .db
TAHAP 5: Layer 4 Navigation → jalur lurus? sampai tujuan?
    ↓ PASS
TAHAP 6: Layer 5 Brain → FSM transisi benar? sensor mati → ERROR?
    ↓ PASS
AMR SIAP DEMO KE DOSEN
```

Detail lengkap ada di `DEPLOY_NUC.md`.

---

## 11. Hard Rules (DILARANG DILANGGAR)

1. JANGAN push ke `main` — selalu branch feature; tiap push butuh approval eksplisit.
2. JANGAN ubah resolusi RealSense dari 848×480×30 (RGB & Depth).
3. JANGAN ubah URDF (`amr_body/`) kecuali diminta eksplisit.
4. JANGAN install package baru tanpa menyatakan dulu apa & kenapa.
5. JANGAN rebuild full workspace (`colcon build` tanpa `--packages-select`).
6. JANGAN hapus file/folder tanpa konfirmasi eksplisit.
7. JANGAN klaim "sudah jalan" tanpa output command sebagai bukti.
8. JANGAN fabrikasi spec hardware / parameter yang tidak ada.
9. JANGAN ganti algoritma fundamental tanpa diskusi panjang.
10. Selalu cek update repo sebelum eksekusi.

---

## 12. Pengambilan Data

### 12.1 Rosbag recording (semua sensor)

```bash
ros2 launch amr_startup record_sensors.launch.py
```

Topic yang direkam:
- Layer 1: `/scan`, `/camera/*/color/image_raw`, `/camera/*/depth/image_rect_raw`, `/camera/*/accel/sample`, `/camera/*/gyro/sample`, `/imu/data`, `/encoder`
- Layer 2: `/encoder_odom`, `/odometry/filtered`
- Layer 3: `/rtabmap/odom`, `/rgbd_image`, `/rtabmap/info`
- Layer 5: `/brain/state`
- TF: `/tf`, `/tf_static`

Output: `~/amr_bags/[timestamp]/`

### 12.2 Data LiDAR XY (permintaan dosen)

```bash
ros2 launch amr_sensors lidar_study.launch.py record:=true
```

- Konversi polar (angle, range) → kartesian (x, y) per laser beam
- Visualisasi di RViz2: warna merah (dekat) → hijau (jauh)
- CSV output untuk analisis jarak

### 12.3 Simpan peta dan mapping baru

```bash
# SIMPAN peta saat ini (SAAT mapping masih jalan)
ros2 launch amr_startup save_map.launch.py map_name:=lab_lantai1

# Hasil tersimpan di:
# ~/maps/lab_lantai1/
#   ├── lab_lantai1.pgm     ← peta 2D (gambar hitam-putih)
#   ├── lab_lantai1.yaml    ← metadata peta
#   └── rtabmap.db          ← database 3D RTAB-Map

# MAPPING BARU — langsung jalankan mapping lagi
# (--delete_db_on_start otomatis menghapus db lama)
ros2 launch amr_startup layer3_mapping.launch.py

# PAKAI PETA LAMA untuk navigasi
ros2 launch amr_startup layer4_navigation.launch.py \
    database_path:=~/maps/lab_lantai1/rtabmap.db
```

### 12.4 Replay data di Windows (tanpa robot)

```bash
# Copy ~/amr_bags/[timestamp]/ ke Windows
ros2 bag play [path_ke_bag]
# Buka RViz2 untuk analisis
```

---

## 13. Apa yang BELUM Dibangun

| Item | Status | Keterangan |
|---|---|---|
| `amr_body` (URDF) | Kerangka saja | Perlu model 3D robot untuk TF lengkap |
| `amr_motor` (STM32 bridge) | Kerangka saja | Perlu protokol komunikasi STM32 |
| Custom Behavior Tree XML | Belum | Pakai default Nav2 BT dulu |
| Obstacle detection khusus | Belum | LiDAR + costmap sudah cukup untuk awal |
| GitHub repo | Belum setup | Semua masih lokal |
| Multi-floor navigation | Tidak ada rencana | Tidak dibutuhkan untuk TA |

---

## 14. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| VIO gagal di tembok polos | Robot kehilangan posisi | Tempel poster/gambar di tembok lab |
| Encoder PPR salah | Kecepatan EKF tidak akurat | Verifikasi PPR (Tahap 2), encoder hanya input lemah |
| RTAB-Map terlalu berat untuk NUC | Frame drop, mapping lambat | Resolusi 848×480 (bukan 1280×720), VoxelSize 0.03 |
| Loop closure gagal | Peta drift, tidak menutup | Pastikan ruangan punya fitur visual unik |
| STM32 komunikasi putus | Motor mati tiba-tiba | Brain → ERROR → STOP |
| Radius putar ternyata > 0.55m | Jalur tabrak dinding | Ukur fisik dulu (Tahap 2), update YAML |

---

## 15. Kontak & Referensi

- **Mahasiswa:** Muhammad Al Azhar Faradis — malazharfaradis@gmail.com
- **Repo referensi dosen (RAISA):** `github.com/ismarintan98/Mobile_Robot_RAISA`
- **Materi kuliah:** SKC M1–M5 (Sistem Kendaraan Cerdas)
- **Handover sistem lama:** `HANDOVER_ARSITEKTUR_AMR_GAGAL.md`

---

*Dokumen ini dibuat sebagai serah terima pengetahuan agar siapapun yang melanjutkan proyek ini — termasuk diri sendiri di masa depan — dapat memahami MENGAPA setiap keputusan diambil, bukan hanya APA yang dibangun.*
