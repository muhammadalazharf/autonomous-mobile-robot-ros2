# HANDOVER: Sesi Deploy Rebuild AMR ke NUC — 1 Juli 2026

**Pemilik:** Muhammad Al Azhar Faradis (NRP 2040241017, ITS Surabaya)
**Repo:** `github.com/muhammadalazharf/autonomous-mobile-robot-ros2`
**Branch:** `claude/markdown-file-review-rokxcl`
**Tanggal:** 1 Juli 2026
**Tujuan sesi:** Deploy arsitektur rebuild 5-layer dari laptop ke NUC + uji Layer 1

---

## 1. Konteks Awal Sesi

Sesi dimulai dari user attach `HANDOVER_REBUILD_AMR.md` — dokumen serah terima arsitektur baru AMR Ackermann yang memperbaiki 7 kegagalan sistem lama. Kode rebuild ada di laptop Windows/Linux user, belum ter-deploy ke NUC.

**Status awal:**
- Repo GitHub berisi arsitektur LAMA (`amr_bringup`, `amr_3d_mapping`, dll)
- Kode rebuild (`amr_sensors`, `amr_pose`, `amr_mapping`, `amr_navigation`, `amr_brain`, `amr_startup`, `amr_body`, `amr_motor`) belum ada di repo
- NUC belum menerima kode rebuild

---

## 2. Eksekusi yang Sudah Dilakukan

### 2.1 Transfer Kode Rebuild ke Repo GitHub

**Masalah:** Container cloud Claude tidak bisa akses filesystem laptop user.

**Solusi yang dipilih:** Push langsung dari laptop Linux user ke GitHub.

**Rangkaian error yang muncul:**
1. `git push` via HTTPS → gagal karena GitHub tidak lagi terima password (harus PAT/SSH)
2. User pilih setup SSH → generate ed25519 key
3. User daftarkan key ke GitHub Settings
4. `git remote set-url` ganti HTTPS → SSH
5. `git push -u origin claude/rebuild-amr` → **berhasil push 61.67 MiB kode rebuild**

**Hasil:** Branch `claude/rebuild-amr` di GitHub berisi seluruh `amr_ws/` rebuild.

### 2.2 Verifikasi Kode Rebuild di Container Claude

Kode rebuild diperiksa:
- Semua 8 package lengkap (`amr_body`, `amr_brain`, `amr_mapping`, `amr_motor`, `amr_navigation`, `amr_pose`, `amr_sensors`, `amr_startup`)
- Kontrak QoS ✓ (`qos_image: 1` di rgbd_sync)
- EKF: VIO odom0 trust, encoder odom1 kovarians besar ✓
- Nav2 Ackermann: no spin, Reeds-Shepp, `use_rotate_to_heading: false` ✓
- Single source of truth: parameter hanya di YAML ✓

**Hard Rule #9 dipatuhi:** kontradiksi antara REBUILD vs GEMINI (radius putar 0.55 vs 0.90, allow_reversing) di-flag tapi tidak diubah tanpa persetujuan user.

### 2.3 Merge ke Branch Kerja

Kode dari `origin/claude/rebuild-amr` di-checkout ke branch `claude/markdown-file-review-rokxcl`, commit dan push.
File tidak relevan (dokumen MOOC, pptx, docx) di-unstage. Hanya kode workspace yang masuk.

### 2.4 Backup Workspace Lama di NUC

**Perintah eksekusi user (di NUC):**
```bash
mkdir -p ~/WORKSPACE_1
mv ~/amr_starter     ~/WORKSPACE_1/
mv ~/amr_underlay_ws ~/WORKSPACE_1/
mv ~/rtabmap_vio_pkg ~/WORKSPACE_1/
zip -r ~/WORKSPACE_1.zip ~/WORKSPACE_1
```

**Hasil:** `WORKSPACE_1.zip` 11 MB tersimpan di `~/`.

### 2.5 Deploy Workspace Baru ke NUC

User zip `amr_ws/` di laptop, transfer via flashdisk, extract di NUC ke `~/AMR/amr_ws/`.
User memilih tidak meletakkan di `~/amr_ws` supaya home directory bersih.

**Modifikasi `deploy.bash`:**
```bash
sed -i 's|WS_DIR="$HOME/amr_ws"|WS_DIR="$HOME/AMR/amr_ws"|' ~/AMR/amr_ws/deploy.bash
```

### 2.6 Deploy Bash Script

`./deploy.bash` dijalankan 7 langkah:

| Langkah | Status |
|---|---|
| 0/7 Cek prasyarat (ROS 2 Humble) | ✓ |
| 1/7 Install system dependencies | ✓ (rplidar_ros + realsense2_description) |
| 2/7 Resolve rosdep | ✓ All required rosdeps installed |
| 3/7 Bersihkan build lama | ✓ |
| 4/7 Build 8 packages | ✓ (semua < 1.1 detik) |
| 5/7 Setup udev rules | ✓ `/dev/rplidar` + `/dev/stm32` |
| 6/7 Setup bashrc + folder | ✓ |
| 7/7 Verifikasi | ✓ Semua 6 package terdeteksi ROS 2 |

**Hasil:** DEPLOY BERHASIL.

---

## 3. Proses Debug & Perbaikan

### 3.1 Problem #1: Encoder FAIL (0.0 Hz) — Layer 1

**Gejala:** Health check menunjukkan 4/5 sensor PASS (LiDAR, Color, Depth, IMU), tapi Encoder FAIL 0 Hz.

**Diagnosis:**
- `ros2 topic info /encoder` → "Unknown topic"
- `ls /dev/stm32` → `/dev/stm32 -> ttyACM0` (hardware STM32 fisik tersambung)
- Root cause: package `amr_motor` hanya kerangka kosong (CMakeLists + package.xml), tidak ada node publisher `/encoder`

**Fix Iterasi #1 (SALAH — self-correction):**
Claude membuat `stm32_bridge_node.py` (Python) berdasarkan tebakan protokol dari handover. User memprotes: *"kamu menyusun stm_bridge dari sumber apa? kan kamu tidak punya data dimana stm32 tersambung di port mana"*

**Fix Iterasi #2 (BENAR):**
- Ambil `stm32_bridge.cpp` **asli** dari branch `main` (`src/amr_controller/src/stm32_bridge.cpp`) — kode yang **sudah terbukti jalan di hardware**
- Parameter kritis yang benar dari kode asli:
  - Serial port: `/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_206833894152-if00`
  - `MAX_PWM = 4000` (bukan 255)
  - `MAX_STEER = 45` dengan `STEER_TRIM = -5`
  - Baud rate `B115200`
  - Dual-mode: joystick (R1 deadman) + cmd_vel autonomous
  - Watchdog: timeout cmd_vel → motor stop
- Convert `amr_motor` dari kerangka kosong → C++ ament_cmake package fungsional
- Update `sensors.launch.py` include `motor.launch.py`

**Hasil setelah rebuild + relaunch:** Encoder PASS 20 Hz — **Layer 1 5/5 PASS**.

### 3.2 Problem #2: Resolusi Kamera Color 1280x720 (Melanggar Hard Rule #2)

**Gejala:** `ros2 topic echo /camera/camera/color/image_raw` menunjukkan `height: 720, width: 1280`, seharusnya 848x480.

**Diagnosis:**
- Cek `ros2 param get /camera/camera rgb_camera.color_profile` → `1280x720x30` (nilai default RealSense driver, YAML tidak terbaca)
- `ros2 param get /camera/camera depth_module.depth_profile` → `848x480x30` (kebetulan default depth D455 memang cocok)
- Root cause: parameter dari `sensors.yaml` tidak diterapkan node RealSense (kemungkinan namespace matching issue: `name='camera'` + `namespace='camera'`)

**Fix Iterasi #1 (SALAH):**
Rename `rgb_camera.color_profile` → `rgb_camera.profile` (tanpa `color_`). Ternyata driver mengharapkan nama dengan `color_`, bukan tanpa.

**Fix Iterasi #2 (BENAR — dikonfirmasi web research):**
- Revert nama parameter ke `rgb_camera.color_profile` dan `depth_module.depth_profile`
- Tambah parameter dict langsung di `sensors.launch.py` sebagai override yang terjamin masuk:
```python
parameters=[config, {
    'rgb_camera.color_profile': '848x480x30',
    'depth_module.depth_profile': '848x480x30',
}]
```

**Hasil:** Color resolution jadi 848x480 — **Hard Rule #2 terpenuhi**.

### 3.3 Problem #3: `lidar_xy_node` PermissionError

**Gejala:** Saat launch `lidar_study.launch.py record:=true`:
```
PermissionError: [Errno 13] Permission denied: '/home/azhar'
```

**Diagnosis:**
- `sensors.yaml` line 34: `record_dir: '/home/azhar/lidar_data'` (path LAPTOP, bukan NUC)
- Node coba buat folder `/home/azhar/` di NUC → ditolak karena user tidak ada

**Fix:**
- Ganti `record_dir` → `~/lidar_data` (portable)
- Tambah `os.path.expanduser()` di `lidar_xy_node.py` agar `~` di-expand

### 3.4 Problem #4: RViz2 Display Error (Bukan Fix, Workaround)

**Gejala:** RViz2 gagal load Qt platform "xcb" — NoMachine remote tidak forward display X11.

**Solusi:** Jalankan node tanpa RViz2:
```bash
ros2 run amr_sensors lidar_xy --ros-args -p record:=true -p record_dir:=$HOME/lidar_data
```

---

## 4. Ringkasan Commit

| Commit | Deskripsi |
|---|---|
| `7602367` | Add rebuild AMR 5-layer architecture (push awal dari laptop) |
| `7d675e9` | Add AMR rebuild workspace ke branch kerja |
| `c433a2a` | Implement amr_motor STM32 bridge (Python, salah — di-revert berikutnya) |
| `8ea44b2` | Replace amr_motor Python → C++ stm32_bridge dari main branch |
| `c943ca7` | Fix RealSense param name (salah — di-revert berikutnya) |
| `21aff88` | Fix RealSense: revert param names + launch override 848x480 |
| `27feabb` | Fix lidar_xy PermissionError: record_dir + expanduser |

---

## 5. Status Sistem Saat Ini

### 5.1 Layer 1 SENSE — VERIFIED PASS

Terverifikasi dari `ros2 topic echo`:

| Sensor | Topic | Data | Freq | Status |
|---|---|---|---|---|
| LiDAR RPLIDAR C1 | `/scan` | Range data, `laser_frame`, min 0.15m, max 16m | 10 Hz | PASS |
| Kamera Color | `/camera/camera/color/image_raw` | **848x480** RGB8 | 17-27 Hz | PASS |
| Kamera Depth | `/camera/camera/depth/image_rect_raw` | **848x480** 16UC1 | 20-30 Hz | PASS |
| IMU merged | `/imu/data` | accel + gyro dari D455 | 100 Hz | PASS |
| Encoder | `/encoder` | Int32 delta ticks dari STM32 | 20 Hz | PASS |

### 5.2 Pengambilan Data LiDAR — DONE

CSV pertama tersimpan di NUC:
```
/home/itssurabaya/lidar_data/lidar_20260701_171017.csv
```
Kolom: `scan_id, beam_index, sudut_rad, sudut_deg, jarak_m, x_m, y_m`

### 5.3 Layer 2–5 — BELUM DIUJI

Deploy sudah, code build OK, tapi belum ada test run:
- Layer 2 (Pose/EKF) — belum
- Layer 3 (Mapping RTAB-Map) — belum
- Layer 4 (Nav2 Ackermann) — belum
- Layer 5 (Brain FSM) — belum

---

## 6. Parameter yang MASIH BELUM Diukur di NUC

Sesuai handover Bagian 8, empat parameter masih placeholder:

| Parameter | File | Nilai sekarang | Aksi |
|---|---|---|---|
| `minimum_turning_radius` | `nav2_params.yaml:71` | `0.55` (placeholder) | Belok full, ukur diameter lingkaran ÷ 2 |
| `pulses_per_revolution` | `encoder.yaml` | `3858` | Putar roda 1x, hitung selisih pulsa |
| Encoder sign | `stm32_bridge.cpp` | Asumsi maju = positif | Dorong maju, cek `/encoder` naik atau turun |
| `footprint` robot | `nav2_params.yaml` | `50cm × 40cm` | Meteran dari ujung terluar |

**Note:** Bridge C++ dari main branch sudah pakai konvensi "V positif = maju" (dicatat di komentar file), jadi encoder sign kemungkinan sudah benar. Tapi tetap perlu verifikasi fisik.

---

## 7. Problem yang Masih Perlu Perhatian

### 7.1 RViz2 Tidak Bisa di NoMachine

Setiap kali butuh visualisasi (RViz2), harus dijalankan langsung dari layar NUC atau setup X11 forwarding.

### 7.2 Kontradiksi Dokumen (Belum Diputuskan)

- **HANDOVER_REBUILD**: `minimum_turning_radius: 0.55` (placeholder), `allow_reversing: true`, motion model `REEDS_SHEPP`
- **HANDOVER_GEMINI**: `0.90` (terukur), `allow_reversing: false`, motion `DUBIN`

User instruksikan **hiraukan HANDOVER_GEMINI** untuk konteks desain. Tapi keputusan final untuk parameter nyata (radius putar, reversing) belum diambil.

### 7.3 Firmware STM32 (Info Latar)

Handover GEMINI mencatat: "Firmware STM32: PWM tidak boleh menerima nilai negatif (butuh if-else di main.c)". Perlu verifikasi apakah kondisi ini masih berlaku sebelum aktifkan mode autonomous dengan reversing.

---

## 8. Prioritas Kerja Berikutnya

1. **[SEKARANG]** Transfer CSV LiDAR dari NUC → laptop (proses berlangsung):
   ```bash
   scp itssurabaya@<IP_NUC>:~/lidar_data/lidar_20260701_171017.csv ~/Documents/
   ```
   Butuh: cek IP NUC + laptop dulu (`hostname -I`)

2. **[SELANJUTNYA]** Pengukuran fisik 4 parameter (Bagian 6 di atas)

3. **[SELANJUTNYA]** Uji Layer 2 (Pose/EKF):
   ```bash
   ros2 launch amr_startup layer2_pose.launch.py
   ```
   Verify: `/odometry/filtered` publish, TF `odom → base_footprint` benar

4. **[SELANJUTNYA]** Uji Layer 3 (Mapping RTAB-Map):
   ```bash
   ros2 launch amr_startup layer3_mapping.launch.py
   ```
   Verify: `/rgbd_image` > 0 Hz, loop closure terpicu saat robot lewati area yang sama

5. **[BELAKANGAN]** Uji Layer 4 (Nav2) + Layer 5 (Brain FSM)

6. **[BELAKANGAN]** Handle firmware STM32 kalau reversing dibutuhkan Nav2

---

## 9. Kontak & Referensi

- **Owner:** Muhammad Al Azhar Faradis (malazharfaradis@gmail.com)
- **Repo:** github.com/muhammadalazharf/autonomous-mobile-robot-ros2
- **Branch aktif:** `claude/markdown-file-review-rokxcl`
- **Handover induk:** `HANDOVER_REBUILD_AMR.md`
- **Workspace lokasi NUC:** `~/AMR/amr_ws/`
- **Backup workspace lama NUC:** `~/WORKSPACE_1/` + `~/WORKSPACE_1.zip`
- **Data LiDAR NUC:** `~/lidar_data/`

---

*Dokumen ini dibuat pada 1 Juli 2026 sebagai record sesi deploy pertama arsitektur rebuild ke NUC. Tujuannya agar siapapun yang melanjutkan (termasuk diri sendiri di sesi berikutnya) tahu persis apa yang sudah bekerja, apa yang di-fix, dan apa yang belum.*
