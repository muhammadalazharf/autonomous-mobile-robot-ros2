# Deploy AMR ke NUC — Checklist Lengkap

## TAHAP 0: Transfer Workspace ke NUC

```bash
# Di WINDOWS — zip workspace (tanpa build/install/log)
# Masuk ke folder C:\Users\alazh\Downloads\AMR\amr_ws\
# Hapus dulu folder build/, install/, log/ kalau ada
# Zip folder src/ saja

# Di NUC — terima file dan extract
mkdir -p ~/amr_ws
# Copy zip via USB / scp / git
# Extract ke ~/amr_ws/src/

# Pastikan struktur:
# ~/amr_ws/src/amr_sensors/
# ~/amr_ws/src/amr_pose/
# ~/amr_ws/src/amr_mapping/
# ~/amr_ws/src/amr_navigation/
# ~/amr_ws/src/amr_brain/
# ~/amr_ws/src/amr_startup/
# ~/amr_ws/src/amr_body/
# ~/amr_ws/src/amr_motor/
```

### Build di NUC

```bash
cd ~/amr_ws
source /opt/ros/humble/setup.bash

# Build SATU PER SATU — JANGAN colcon build tanpa --packages-select!
colcon build --symlink-install --packages-select amr_sensors
colcon build --symlink-install --packages-select amr_pose
colcon build --symlink-install --packages-select amr_mapping
colcon build --symlink-install --packages-select amr_navigation
colcon build --symlink-install --packages-select amr_brain
colcon build --symlink-install --packages-select amr_startup

source install/setup.bash
```

### Cek device terhubung

```bash
# LiDAR — harus ada /dev/rplidar atau /dev/ttyUSBx
ls /dev/ttyUSB*
# Kalau tidak ada /dev/rplidar, buat udev rule:
# sudo cp src/amr_sensors/udev/rplidar.rules /etc/udev/rules.d/
# sudo udevadm control --reload-rules && sudo udevadm trigger

# RealSense — harus terdeteksi
rs-enumerate-devices | head -5

# Encoder — tergantung setup STM32 (serial / rosserial)
ls /dev/ttyACM*
```

---

## TAHAP 1: Uji Layer 1 — Sensor (Modul 1)

### Terminal 1: Nyalakan sensor

```bash
cd ~/amr_ws && source install/setup.bash
ros2 launch amr_startup amr_sensors_only.launch.py
```

### Terminal 2: Gerbang uji

```bash
source ~/amr_ws/install/setup.bash

# 1A. Health Check — SEMUA harus PASS
ros2 topic echo /health_check
# Tunggu 3 siklus. Kalau ada FAIL → perbaiki dulu, JANGAN lanjut.

# 1B. Cek setiap sensor hidup
ros2 topic hz /scan                                # LiDAR: ≥ 5 Hz
ros2 topic hz /camera/camera/color/image_raw       # Color:  ≥ 15 Hz
ros2 topic hz /camera/camera/depth/image_rect_raw  # Depth:  ≥ 15 Hz
ros2 topic hz /imu/data                            # IMU:    ≥ 30 Hz
ros2 topic hz /encoder                             # Encoder: ≥ 1 Hz

# 1C. Integration Check — verifikasi QoS + frekuensi + latency
ros2 run amr_sensors integration_check
# Tunggu 5 siklus sampai hierarki muncul.

# 1D. RViz2 — visual check
rviz2
# Add LaserScan (/scan), Image (/camera/camera/color/image_raw)
# Fixed Frame: base_footprint
# LiDAR harus membentuk kontur ruangan
# Kamera harus menampilkan gambar real-time
```

### Gerbang PASS Layer 1:
- [ ] Health check: 5/5 PASS
- [ ] Semua Hz di atas minimum
- [ ] Integration check: tidak ada QoS mismatch
- [ ] Visual: LiDAR kontur benar, kamera gambar benar

---

## TAHAP 2: Pengukuran Fisik (SEBELUM Layer 2)

### 2A. Verifikasi arah encoder

```bash
# Buka terminal baru
ros2 topic echo /encoder

# DORONG robot MAJU dengan tangan
# Lihat angka encoder:
#   Naik (positif) → BENAR ✓
#   Turun (negatif) → SALAH → balik tanda di encoder_odom_node.py
```

### 2B. Verifikasi PPR encoder

```bash
ros2 topic echo /encoder

# Tandai posisi awal roda (spidol/selotip)
# Putar roda TEPAT 1 putaran penuh
# Catat selisih angka encoder
# Hasilnya harus ≈ 3858
# Kalau BEDA JAUH → update encoder.yaml: pulses_per_revolution
```

### 2C. Ukur radius putar minimum

```bash
# 1. Taruh robot di lantai luas
# 2. Tempel spidol di roda belakang
# 3. Joystick: belok FULL ke kanan, gas pelan
# 4. Biarkan robot jalan MELINGKAR sampai 1 putaran penuh
# 5. Ukur DIAMETER lingkaran dengan meteran
# 6. Radius = diameter / 2
# 7. Tulis hasilnya ke: src/amr_navigation/config/nav2_params.yaml
#    → minimum_turning_radius: [HASIL UKUR]
#
# Ulangi belok FULL ke kiri — ambil yang LEBIH BESAR dari dua hasil
```

### 2D. Ukur dimensi fisik robot (footprint)

```bash
# 1. Meteran: ukur PANJANG robot dari ujung depan ke ujung belakang (termasuk sensor menonjol)
# 2. Meteran: ukur LEBAR robot dari sisi kiri ke sisi kanan
# 3. Hitung: setengah_panjang = panjang / 2, setengah_lebar = lebar / 2
# 4. Tulis ke: src/amr_navigation/config/nav2_params.yaml
#    → footprint: [[setengah_panjang, -setengah_lebar],
#                  [setengah_panjang, setengah_lebar],
#                  [-setengah_panjang, setengah_lebar],
#                  [-setengah_panjang, -setengah_lebar]]
#    (tulis di KEDUA tempat: local_costmap DAN global_costmap)
#
# Contoh: robot 50cm × 40cm → [[0.25, -0.20], [0.25, 0.20], [-0.25, 0.20], [-0.25, -0.20]]
```

### Gerbang PASS Pengukuran:
- [ ] Encoder sign: maju = positif
- [ ] Encoder PPR: ≈ 3858 (atau sudah diupdate)
- [ ] Radius putar: _____ meter (sudah ditulis ke nav2_params.yaml)
- [ ] Footprint robot: ___cm × ___cm (sudah ditulis ke nav2_params.yaml)

---

## TAHAP 3: Uji Layer 2 — Pose/EKF (Modul 2)

### Terminal 1: Nyalakan sensor + pose

```bash
ros2 launch amr_startup layer2_pose.launch.py
```

### Terminal 2: Gerbang uji

```bash
# 3A. Encoder odom hidup
ros2 topic hz /encoder_odom    # harus > 0 Hz

# 3B. EKF output hidup (belum ada VIO, jadi hanya dari encoder)
ros2 topic hz /odometry/filtered    # harus > 0 Hz

# 3C. TF tree — pastikan rantai lengkap
ros2 run tf2_tools view_frames
# Buka frames.pdf — harus ada: odom → base_footprint
# (map → odom belum ada, itu dari RTAB-Map nanti)

# 3D. Dorong robot maju lurus 1 meter
ros2 topic echo /odometry/filtered --once
# Catat x awal
# Dorong maju 1 meter (ukur pakai meteran)
ros2 topic echo /odometry/filtered --once
# Selisih x harus ≈ 1.0 (± 0.3 OK untuk encoder saja)
```

### Gerbang PASS Layer 2:
- [ ] /encoder_odom aktif
- [ ] /odometry/filtered aktif
- [ ] TF: odom → base_footprint ada
- [ ] Dorong 1m → EKF baca ≈ 1m (kasar OK)

---

## TAHAP 4: Uji Layer 3 — Mapping (Modul 4)

### Terminal 1: Nyalakan sensor + pose + mapping

```bash
ros2 launch amr_startup layer3_mapping.launch.py
```

### Terminal 2: Gerbang uji

```bash
# 4A. KRITIS — rgbd_image harus hidup (fix QoS!)
ros2 topic hz /rgbd_image    # HARUS > 0 Hz
# Kalau 0 Hz → QoS masih salah, STOP, jangan lanjut!

# 4B. VIO hidup
ros2 topic hz /rtabmap/odom    # harus > 0 Hz

# 4C. TF tree lengkap
ros2 run tf2_tools view_frames
# Harus ada: map → odom → base_footprint

# 4D. RViz2 — lihat peta terbentuk
rviz2
# Add: Map (/grid_map), PointCloud2 (/cloud_map), LaserScan (/scan)
# Fixed Frame: map
# Jalan keliling ruangan — peta harus terbentuk real-time
```

### Terminal 3: Rekam data (BERSAMAAN dengan mapping)

```bash
ros2 launch amr_startup record_sensors.launch.py
# Biarkan jalan selama mapping. Ctrl+C setelah selesai.
# Data tersimpan di ~/amr_bags/[timestamp]/
```

### 4E. Uji loop closure

```bash
# Jalan keliling ruangan, KEMBALI ke titik awal
# Cek apakah RTAB-Map mengenali tempat yang sudah dikunjungi:
ros2 topic echo /rtabmap/info --field loop_closure_id
# Harus muncul angka > 0 saat kembali ke tempat awal
# Kalau selalu 0 → loop closure GAGAL (sama seperti sistem lama)
```

### 4F. Simpan peta

```bash
# Setelah mapping selesai, Ctrl+C launch.
# Peta otomatis tersimpan di: ~/.ros/rtabmap.db
# Backup:
mkdir -p ~/maps
cp ~/.ros/rtabmap.db ~/maps/lab_$(date +%Y%m%d).db
```

### Gerbang PASS Layer 3:
- [ ] /rgbd_image > 0 Hz (FIX UTAMA!)
- [ ] /rtabmap/odom > 0 Hz
- [ ] TF: map → odom → base_footprint
- [ ] Peta 2D terbentuk di RViz2
- [ ] Loop closure terpicu (loop_closure_id > 0)
- [ ] Peta .db tersimpan

---

## TAHAP 5: Uji Layer 4 — Navigation (Modul 5)

### Terminal 1: Nyalakan full navigation (pakai peta)

```bash
ros2 launch amr_startup layer4_navigation.launch.py \
    database_path:=/home/azhar/maps/lab_[tanggal].db
```

### Terminal 2: Gerbang uji

```bash
# 5A. Nav2 lifecycle semua aktif
ros2 lifecycle list controller_server    # harus: active
ros2 lifecycle list planner_server       # harus: active

# 5B. Costmap terlihat di RViz2
rviz2
# Add: Map (/map), Costmap (/local_costmap/costmap), Path (/plan)
# Fixed Frame: map
# Costmap harus menunjukkan obstacle + inflation di sekitar dinding

# 5C. Kirim goal navigasi
# Di RViz2: klik "Nav2 Goal" → klik titik tujuan di peta
# Robot HARUS:
#   - Bikin jalur yang MASUK AKAL (tidak S-curve berlebihan)
#   - Bergerak mengikuti jalur
#   - Berhenti di tujuan

# 5D. Uji obstacle avoidance
# Taruh kardus di jalur robot
# Robot harus belok menghindari, bukan tabrak
```

### Gerbang PASS Layer 4:
- [ ] Nav2 lifecycle: semua active
- [ ] Costmap visible, inflation terlihat
- [ ] Goal → jalur masuk akal (tidak berbelit)
- [ ] Robot sampai di tujuan
- [ ] Obstacle avoidance bekerja

---

## TAHAP 6: Uji Layer 5 — Brain (Modul 6)

### Terminal 1: Nyalakan full system

```bash
ros2 launch amr_startup full_system.launch.py \
    database_path:=/home/azhar/maps/lab_[tanggal].db
```

### Terminal 2: Gerbang uji

```bash
# 6A. Brain state awal
ros2 topic echo /brain/state    # harus: IDLE

# 6B. Kirim goal → cek transisi NAVIGATING
# Di RViz2: Nav2 Goal → klik tujuan
ros2 topic echo /brain/state    # harus: NAVIGATING

# 6C. Tunggu sampai → cek transisi IDLE
ros2 topic echo /brain/state    # harus: IDLE (setelah sampai)

# 6D. Uji sensor mati → ERROR
# CABUT KABEL LiDAR
ros2 topic echo /brain/state    # harus: ERROR dalam 3 detik
# PASANG KEMBALI
ros2 topic echo /brain/state    # harus: kembali ke IDLE

# 6E. Uji stuck detection
# Kirim goal navigasi → TAHAN robot fisik (jangan biarkan bergerak)
# Setelah 15 detik:
ros2 topic echo /brain/state    # harus: STUCK
# Robot harus MUNDUR otomatis
# Setelah mundur:
ros2 topic echo /brain/state    # harus: NAVIGATING (lanjut)
```

### Gerbang PASS Layer 5:
- [ ] State awal: IDLE
- [ ] Goal diterima → NAVIGATING
- [ ] Goal tercapai → IDLE
- [ ] LiDAR cabut → ERROR → pasang → IDLE
- [ ] Stuck → mundur → lanjut navigasi

---

## TAHAP 7: Pengambilan Data Lengkap

### 7A. Rekam saat mapping (data mentah)

```bash
# Terminal 1: mapping
ros2 launch amr_startup layer3_mapping.launch.py

# Terminal 2: rekam
ros2 launch amr_startup record_sensors.launch.py

# Jalan keliling ruangan 2-3 putaran
# Ctrl+C kedua terminal setelah selesai
```

### 7B. Rekam saat navigasi (data operasional)

```bash
# Terminal 1: full system
ros2 launch amr_startup full_system.launch.py \
    database_path:=/home/azhar/maps/lab_[tanggal].db

# Terminal 2: rekam
ros2 launch amr_startup record_sensors.launch.py

# Kirim beberapa goal navigasi dari RViz2
# Biarkan robot jalan otonom
# Ctrl+C setelah selesai
```

### 7C. Data LiDAR khusus (untuk dosen)

```bash
# Nyalakan sensor + LiDAR XY visualizer
ros2 launch amr_sensors lidar_study.launch.py record:=true

# Arahkan robot ke berbagai objek (tembok, meja, kursi)
# Data CSV tersimpan otomatis
# Di RViz2: lihat titik-titik LiDAR berwarna (merah=dekat, hijau=jauh)
```

### 7D. Replay data di Windows (opsional)

```bash
# Copy folder ~/amr_bags/[timestamp]/ ke Windows via USB
# Di Windows:
cd C:\Users\alazh\Downloads\AMR\amr_ws
ros2 bag play [path_ke_folder_bag]
# Bisa buka RViz2 di Windows untuk analisis tanpa robot fisik
```

---

## Troubleshooting Cepat

| Gejala | Kemungkinan | Fix |
|---|---|---|
| Health check: LiDAR FAIL | Port serial salah | Cek `ls /dev/ttyUSB*`, update sensors.yaml |
| Health check: Kamera FAIL | USB bandwidth | Pindahkan ke port USB 3.0 yang beda |
| /rgbd_image 0 Hz | QoS mismatch | Pastikan rtabmap.yaml: qos_image: 1 |
| VIO langsung lost | Tembok polos, minim fitur | Tempel poster/gambar di tembok |
| Loop closure selalu 0 | Ruangan terlalu kecil/monoton | Tambah objek visual yang unik |
| Nav2 jalur berbelit | minimum_turning_radius salah | Ukur ulang radius putar fisik |
| Robot jalan mundur | Encoder sign terbalik | Balik tanda di encoder_odom_node.py |
| Brain tidak ke ERROR | Timeout terlalu lama | Kurangi sensor_timeout di brain.yaml |
