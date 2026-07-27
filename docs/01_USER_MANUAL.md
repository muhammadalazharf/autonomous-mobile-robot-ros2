# 01 — Panduan Pengguna

Panduan pengoperasian robot AMR sehari-hari: mengakses komputer robot,
menjalankan tiap mode, hingga mematikan sistem dengan aman.

---

## 1. Mengakses Komputer Robot (NUC)

Robot dikendalikan oleh **Intel NUC13** yang menjalankan Ubuntu 22.04 dan
ROS 2 Humble. Ada dua cara mengaksesnya dari laptop.

### 1.1 SSH (terminal)

```bash
ssh <user>@<ip-nuc>
```

Bila alamat IP berubah-ubah (jaringan kampus), gunakan **Tailscale** yang
memberikan alamat tetap:

```bash
tailscale ip -4      # jalankan di NUC untuk melihat alamat tetapnya
```

### 1.2 NoMachine (tampilan grafis)

Diperlukan bila ingin membuka **RViz2**, karena RViz butuh tampilan grafis.

> **Catatan:** RViz2 sering gagal berjalan melalui NoMachine dengan pesan
> kegagalan platform Qt "xcb". Bila terjadi, jalankan RViz langsung dari layar
> yang terhubung ke NUC.

### 1.3 Menyiapkan environment (wajib tiap terminal baru)

```bash
source /opt/ros/humble/setup.bash
source ~/amr_ws/install/setup.bash
```

Agar otomatis, tambahkan kedua baris tersebut ke `~/.bashrc`.

---

## 2. Mode Operasi

| Mode | Kegunaan | Prasyarat |
|---|---|---|
| **Foundation** | Kendali manual via joystick | Sensor aktif |
| **SLAM Mapping** | Membuat peta lingkungan baru | Sensor aktif |
| **SLAM Localization** | Menentukan posisi pada peta yang sudah ada | Peta tersedia |
| **Full Autonomous** | Navigasi otonom menuju target | Peta + lokalisasi aktif |

---

## 3. Mode Foundation — Kendali Manual

### Langkah

```bash
# Terminal 1 — nyalakan sensor dan jembatan motor
ros2 launch amr_bringup sensors_launch.py
```

### Tata letak joystick (PS4/PS5)

| Kontrol | Fungsi |
|---|---|
| **R1** | **Deadman switch** — WAJIB ditahan agar robot mau bergerak |
| Stik kiri (atas/bawah) | Maju / mundur |
| Stik kanan (kiri/kanan) | Belok |

> **Deadman switch** adalah pengaman: begitu R1 dilepas, robot langsung berhenti.
> Ini mencegah robot terus melaju bila pengendali terjatuh atau koneksi terputus.

### Verifikasi sensor sebelum menjalankan

```bash
ros2 topic hz /scan          # LiDAR      ~10 Hz
ros2 topic hz /imu/data      # IMU        ~100 Hz
ros2 topic hz /encoder       # Encoder    ~20 Hz
ros2 topic echo /joy         # Joystick   harus muncul saat tombol ditekan
```

---

## 4. Mode SLAM Mapping — Membuat Peta

### Langkah

```bash
# Terminal 1 — sensor
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 — mapping
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py

# Terminal 3 (opsional) — visualisasi
rviz2 -d ~/amr_ws/src/amr_bringup/config/rviz_3d_mapping.rviz
```

### Cara memetakan yang baik

1. **Berjalan perlahan.** Gerakan cepat menyebabkan citra kabur (*motion blur*)
   dan membuat estimasi posisi visual kehilangan acuan.
2. **Kelilingi ruangan, lalu kembali ke titik awal.** Ini memicu *loop closure*,
   yaitu koreksi peta ketika sistem mengenali kembali tempat yang pernah dilewati.
3. **Hindari dinding polos tanpa corak.** Odometri visual membutuhkan tekstur
   sebagai acuan; bila perlu, tempelkan poster atau objek bercorak.
4. **Perhatikan indikator loop closure** di RViz — garis hijau menandakan sistem
   berhasil mengenali kembali suatu lokasi.

### Menyimpan peta

Peta tersimpan otomatis dalam berkas basis data RTAB-Map:

```bash
# Lokasi bawaan
~/.ros/rtabmap.db

# Salin sebagai arsip
mkdir -p ~/maps
cp ~/.ros/rtabmap.db ~/maps/lab_$(date +%Y%m%d).db
```

---

## 5. Mode SLAM Localization — Menggunakan Peta yang Ada

```bash
# Terminal 1 — sensor
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 — localization
ros2 launch amr_3d_mapping rtabmap_localization.launch.py
```

**Penting:** tempatkan robot pada posisi yang **dikenali** dalam peta (idealnya
titik awal saat pemetaan dilakukan). Sistem membutuhkan acuan visual yang cocok
untuk menentukan posisinya.

Verifikasi bahwa lokalisasi berhasil:
```bash
ros2 run tf2_ros tf2_echo map base_footprint
```
Bila muncul nilai translasi yang wajar, robot berhasil menemukan posisinya.

---

## 6. Mode Full Autonomous — Navigasi Otonom

```bash
# Terminal 1 — sensor
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 — localization
ros2 launch amr_3d_mapping rtabmap_localization.launch.py

# Terminal 3 — navigasi
ros2 launch amr_slam nav2.launch.py

# Terminal 4 — RViz untuk memberi target
rviz2
```

### Memberi target navigasi

**Melalui RViz:** klik tombol **`2D Goal Pose`** (atau `Nav2 Goal`), lalu klik
titik tujuan pada peta. Arah panah menentukan orientasi akhir robot.

**Melalui terminal:**
```bash
ros2 run amr_slam goal_sender.py
```

### Yang perlu diperhatikan saat robot berjalan otonom

- **Siapkan joystick.** Tekan R1 kapan saja untuk mengambil alih kendali manual.
- **Robot tidak dapat berputar di tempat.** Kemudi Ackermann membutuhkan ruang
  untuk bermanuver, seperti mobil.
- **Amati lintasan di RViz.** Lintasan yang berbelit menandakan parameter
  navigasi belum sesuai — lihat [05_SLAM_NAV2_GUIDE.md](05_SLAM_NAV2_GUIDE.md).

---

## 7. Mematikan Sistem

```bash
# Hentikan tiap terminal dengan Ctrl+C, atau hentikan semuanya sekaligus:
pkill -f "ros2 launch"

# Matikan NUC dengan benar
sudo shutdown -h now
```

> **Jangan** langsung memutus daya saat pemetaan sedang berjalan — basis data
> peta berisiko rusak dan tidak dapat dibuka kembali.

---

## 8. Pemeriksaan Cepat Sebelum Beroperasi

| Pemeriksaan | Perintah | Nilai yang diharapkan |
|---|---|---|
| LiDAR | `ros2 topic hz /scan` | ~10 Hz |
| Kamera | `ros2 topic hz /camera/camera/color/image_raw` | 15–30 Hz |
| IMU | `ros2 topic hz /imu/data` | ~100 Hz |
| Encoder | `ros2 topic hz /encoder` | ~20 Hz |
| Joystick | `ros2 topic echo /joy` | Ada keluaran saat tombol ditekan |
| TF tree | `ros2 run tf2_tools view_frames` | Rantai frame lengkap |

Bila salah satu pemeriksaan gagal, lihat
[07_TROUBLESHOOTING.md](07_TROUBLESHOOTING.md).

---

**Lanjut:** [02_DEVELOPMENT_GUIDE.md](02_DEVELOPMENT_GUIDE.md) untuk
pengembangan kode.
