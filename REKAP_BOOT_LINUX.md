# REKAP AMR — Untuk Chat Baru di Boot Linux (NUC)

> **Cara pakai file ini:** Saat kamu buka chat Claude baru di NUC Ubuntu, lampirkan file ini
> sebagai konteks. Isinya rangkuman SEMUA yang sudah dikerjakan di Windows, plus perintah
> siap-jalan untuk deploy dan uji. Tidak perlu jelaskan ulang dari nol.

---

## 0. SIAPA AKU & APA PROYEKNYA

- **Nama:** Muhammad Al Azhar Faradis (NRP 2040241017), Teknik Elektro Otomasi ITS.
- **Proyek:** Rebuild Autonomous Mobile Robot (AMR) dari NOL. Sistem lama dinyatakan GAGAL oleh dosen.
- **Deadline:** akhir Juli 2026.
- **Gaya belajar:** satu konsep per langkah, analogi dulu baru istilah teknis. Jangan dibanjiri banyak pertanyaan sekaligus.
- **Hardware:** NUC13 (Ubuntu 22.04, ROS 2 Humble) + RealSense D455 + RPLIDAR C1 + STM32.
- **Steering:** Ackermann (seperti mobil, TIDAK bisa putar di tempat).

---

## 1. ARSITEKTUR — 5 LAYER (semua kode SUDAH jadi)

```
Layer 5 THINK  → amr_brain       FSM: IDLE→MAPPING→NAVIGATING→STUCK→ERROR
Layer 4 ACT    → amr_navigation  Nav2 (SmacPlannerHybrid + RegulatedPurePursuit)
Layer 3 MAP    → amr_mapping     rgbd_sync → VIO → RTAB-Map SLAM + loop closure
Layer 2 POSE   → amr_pose        Encoder Odom (lemah) + EKF (robot_localization)
Layer 1 SENSE  → amr_sensors     LiDAR + RealSense + IMU merger + Health Check
```

Deploy & uji WAJIB berurutan dari Layer 1 ke atas. Kalau Layer 1 gagal, atasnya pasti gagal.

---

## 2. KEPUTUSAN DESAIN YANG DIKUNCI (jangan diubah tanpa diskusi)

1. **VIO sumber pose utama** (bukan encoder). Encoder slip + roda miring → tidak dipercaya.
   Encoder cuma input lemah di EKF (kovarians BESAR).
2. **Kontrak QoS:** semua 5 sensor = BestEffort. `/cmd_vel` = Reliable.
   `rgbd_sync` WAJIB `qos_image: 1` (BestEffort) — ini yang membunuh sistem lama.
3. **Ackermann:** tidak ada recovery `spin`. Planner Reeds-Shepp (maju+mundur). `use_rotate_to_heading: false`.
4. **Single source of truth:** semua parameter HANYA di file YAML `config/`. Launch tanpa parameter inline.
   Build WAJIB `--symlink-install`.

---

## 3. 7 KEGAGALAN LAMA → 7 FIX

| # | Gagal lama | Fix baru |
|---|---|---|
| 7.1 | Sensor putus diam-diam | Kontrak QoS BestEffort semua sensor |
| 7.2 | Parameter saling timpa | Single source YAML |
| 7.3 | Odometry jalan mundur | Encoder input lemah, VIO utama |
| 7.4 | LiDAR dipakai dangkal | ICP PointToPoint (bukan PointToPlane) |
| 7.5 | Loop closure mati | `qos_image: 1` di rgbd_sync |
| 7.6 | Tak ada hierarki | Brain FSM 5 state |
| 7.7 | Jalur berbelit | Nav2 Ackermann-aware |

---

## 4. ⚠️ 4 PARAMETER YANG BELUM TERVERIFIKASI — UKUR DI NUC DULU

| # | Parameter | File | Cara ukur |
|---|---|---|---|
| 1 | `minimum_turning_radius` (skrg 0.55) | `nav2_params.yaml:71` | Belok full → ukur diameter lingkaran → radius = diameter/2 |
| 2 | Arah encoder (sign) | `encoder_odom_node.py` | Dorong maju → `/encoder` harus NAIK |
| 3 | `pulses_per_revolution` (skrg 3858) | `encoder.yaml` | Putar roda 1x → hitung selisih pulsa |
| 4 | `footprint` (skrg 50×40cm) | `nav2_params.yaml` (local + global costmap) | Meteran panjang × lebar robot |

Catatan footprint: yang diberi bantalan itu TEMBOK-nya (inflation), bukan robot. Robot dianggap titik.
`inflation_radius: 0.10` = bantalan 10cm DI LUAR footprint. Jarak aman total = ½ lebar robot + 10cm.

---

## 5. DEPLOY — LANGKAH PERTAMA DI NUC

```bash
# 1. Pastikan folder src/ sudah tersalin ke ~/amr_ws/src/
ls ~/amr_ws/src/
# harus ada: amr_sensors amr_pose amr_mapping amr_navigation amr_brain amr_startup amr_body amr_motor

# 2. Jalankan deploy otomatis (install deps + build per paket + udev + bashrc)
cd ~/amr_ws
chmod +x deploy.bash
./deploy.bash

# 3. Buka terminal BARU supaya bashrc ter-source
```

`deploy.bash` melakukan: install apt deps, rosdep, bersihkan build lama, build 8 paket satu-per-satu
dengan `--symlink-install`, setup udev (`/dev/rplidar`, `/dev/stm32`), auto-source bashrc,
buat folder `~/amr_bags/` dan `~/maps/`, lalu verifikasi.

---

## 6. UJI BERTAHAP — PERINTAH SIAP JALAN

### Tahap 1 — Layer 1 Sensor
```bash
ros2 launch amr_startup amr_sensors_only.launch.py       # Terminal 1
ros2 topic echo /health_check                            # Terminal 2 — harus 5/5 PASS
ros2 run amr_sensors integration_check                   # cek QoS + Hz + latency
```
Hz minimum: /scan ≥5, color ≥15, depth ≥15, /imu/data ≥30, /encoder ≥1.

### Tahap 2 — Pengukuran fisik (lihat Bagian 4). Tulis hasil ke YAML.

### Tahap 3 — Layer 2 Pose
```bash
ros2 launch amr_startup layer2_pose.launch.py
ros2 topic hz /odometry/filtered                         # > 0 Hz
ros2 run tf2_tools view_frames                           # cek odom → base_footprint
```

### Tahap 4 — Layer 3 Mapping
```bash
ros2 launch amr_startup layer3_mapping.launch.py
ros2 topic hz /rgbd_image                                # KRITIS: harus > 0 Hz (fix QoS!)
ros2 topic hz /rtabmap/odom                              # VIO hidup
ros2 topic echo /rtabmap/info --field loop_closure_id    # kembali ke titik awal → harus > 0
```

### Tahap 5 — Layer 4 Navigation
```bash
ros2 launch amr_startup layer4_navigation.launch.py database_path:=~/maps/lab_lt1/rtabmap.db
# RViz2: Nav2 Goal → klik tujuan → jalur harus LURUS, bukan zig-zag
```

### Tahap 6 — Layer 5 Brain (full system)
```bash
ros2 launch amr_startup full_system.launch.py database_path:=~/maps/lab_lt1/rtabmap.db
ros2 topic echo /brain/state                             # IDLE → NAVIGATING → IDLE
# Cabut kabel LiDAR → harus ke ERROR dalam 3 detik → pasang → kembali IDLE
```

---

## 7. PENGAMBILAN DATA (LiDAR, RGBD, IMU)

```bash
# Rekam SEMUA sensor ke rosbag (jalankan bersamaan dengan mapping/navigasi)
ros2 launch amr_startup record_sensors.launch.py         # → ~/amr_bags/[timestamp]/

# Data LiDAR XY khusus (permintaan dosen) + visualisasi RViz2 + CSV
ros2 launch amr_sensors lidar_study.launch.py record:=true
```

Topic yang direkam: /scan, color, depth, accel, gyro, /imu/data, /encoder,
/encoder_odom, /odometry/filtered, /rtabmap/odom, /rgbd_image, /rtabmap/info, /brain/state, /tf, /tf_static.

---

## 8. SIMPAN PETA & MAPPING ULANG

```bash
# Simpan peta saat ini (SAAT mapping masih jalan)
ros2 launch amr_startup save_map.launch.py map_name:=lab_lt1
# → ~/maps/lab_lt1/  berisi: .pgm (gambar) + .yaml (metadata) + rtabmap.db (database 3D)

# Mapping BARU → jalankan mapping lagi, db lama terhapus otomatis (--delete_db_on_start)
ros2 launch amr_startup layer3_mapping.launch.py

# Pakai peta lama untuk navigasi
ros2 launch amr_startup layer4_navigation.launch.py database_path:=~/maps/lab_lt1/rtabmap.db
```

Format peta RTAB-Map = `.db` (bukan .pgm mentah). `.pgm` + `.yaml` dihasilkan oleh `save_map` untuk kompatibilitas Nav2 standar.

---

## 9. HARD RULES (DILARANG DILANGGAR)

1. JANGAN push ke `main` — selalu branch, tiap push butuh approval eksplisit.
2. JANGAN ubah resolusi RealSense dari 848×480×30.
3. JANGAN ubah URDF (`amr_body/`) kecuali diminta eksplisit.
4. JANGAN install paket baru tanpa menyatakan apa & kenapa.
5. JANGAN `colcon build` tanpa `--packages-select`.
6. JANGAN hapus file/folder tanpa konfirmasi.
7. JANGAN klaim "sudah jalan" tanpa output command sebagai bukti.
8. JANGAN fabrikasi spec hardware / parameter.
9. JANGAN ganti algoritma fundamental tanpa diskusi.
10. Selalu cek update repo sebelum eksekusi.

---

## 10. DOKUMEN TERKAIT (di folder yang sama)

| File | Isi |
|---|---|
| `HANDOVER_REBUILD_AMR.md` | Handover lengkap 15 bagian (arsitektur, semua file, risiko) |
| `DEPLOY_NUC.md` | Checklist deploy super-detail per tahap (copy-paste) |
| `deploy.bash` | Script deploy otomatis |
| `ATURAN_PARAMETER.md` | Aturan Modul 3 (single source of truth) |
| `HANDOVER_ARSITEKTUR_AMR_GAGAL.md` | Analisis 7 kegagalan sistem lama |

---

## 11. STATUS SAAT INI

- ✅ Semua kode 6 modul selesai (Windows).
- ❌ Belum ada satupun yang di-deploy / diuji di hardware NUC.
- ⏳ Langkah berikutnya: transfer `src/` ke NUC → `./deploy.bash` → uji Tahap 1.
- ⚠️ 4 parameter fisik (Bagian 4) HARUS diukur sebelum robot jalan otonom.
- `amr_body` (URDF) & `amr_motor` (STM32 bridge) masih kerangka — belum diisi.
```
