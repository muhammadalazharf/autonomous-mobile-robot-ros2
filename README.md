<!--
  README bergaya RAISA (repo dosen: github.com/ismarintan98/Mobile_Robot_RAISA)
  Proyek PJBL TIM. Ganti gambar di images/ dengan diagram & screenshot milik tim.

  >>> PENTING: Bagian "6. Kontribusi Tim" WAJIB kamu sunting sendiri <<<
  Isi dengan pembagian kerja yang SEBENARNYA. Jangan klaim bagian teman.
-->

# Autonomous Mobile Robot (Ackermann) — ROS 2

Platform **Autonomous Mobile Robot** berkemudi **Ackermann (4WD, mirip mobil)**
untuk navigasi otonom, SLAM, dan penghindaran rintangan di lingkungan indoor.
Dikembangkan sebagai **Proyek PjBL (Project-Based Learning)** di Teknik Elektro
Otomasi, Institut Teknologi Sepuluh Nopember (ITS) Surabaya.

![ROS 2](https://img.shields.io/badge/ROS%202-Humble-blue)
![Language](https://img.shields.io/badge/Python%20%7C%20C++-informational)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 1. Arsitektur Sistem

<!-- Taruh diagram arsitektur di images/architecture.png -->
![Arsitektur Sistem](images/architecture.png)

Sistem berjalan di atas ROS 2 Humble pada Intel NUC, dengan STM32 sebagai
pengendali tingkat rendah. Alur besar: **Sensor → Pemetaan/Lokalisasi →
Navigasi → Aktuator**, dengan lapisan keselamatan (failover) di atasnya.

## 2. Paket ROS 2

| Package | Peran |
|---|---|
| `amr_description` | Model robot (URDF/Xacro), TF tree |
| `amr_controller` | Jembatan STM32 (C++), IMU merger, publikasi odometry |
| `amr_bringup` | Orkestrasi launch (sensor, sistem penuh) |
| `amr_3d_mapping` | RTAB-Map: mapping, localization, Visual-Inertial Odometry |
| `amr_slam` | Nav2 + SLAM + behavior tree + skrip patroli/goal |
| `amr_visual_regression` | Navigasi cadangan berbasis visual (fallback) |
| `amr_failover` | Arbiter keselamatan (SLAM / Visual / Joystick / E-Stop) |

## 3. Perangkat Keras

| Komponen | Model |
|---|---|
| Komputasi | Intel NUC13 (Ubuntu 22.04, ROS 2 Humble) |
| Kamera | Intel RealSense D455 (RGB-D + IMU) |
| LiDAR | RPLIDAR C1 (2D, 360°) |
| Mikrokontroler | STM32F407 |
| Motor / Kemudi | Motor DC + driver BTS7960, servo kemudi DS3225 |
| Kemudi | Ackermann, roda depan (2WS), wheelbase 0.5 m |
| Daya | Baterai LiPo + manajemen daya |

## 4. Mode Operasi

| Mode | Deskripsi |
|---|---|
| Foundation | Kendali manual via joystick |
| SLAM Mapping | Membangun peta lingkungan (RTAB-Map) |
| SLAM Localization | Menentukan posisi pada peta yang sudah ada |
| Full Autonomous | Navigasi otonom menuju target (Nav2) |

## 5. Akses NUC

```bash
# SSH ke NUC (contoh via Tailscale)
ssh <user>@<ip-nuc>

# Sumber environment tiap terminal baru
source /opt/ros/humble/setup.bash
source ~/amr_ws/install/setup.bash
```

## 6. Tim & Kontribusi

Proyek PjBL ini dikerjakan oleh **tim beranggotakan tiga orang**. Dokumen dan
sebagian besar basis kode terpelihara di repositori tim (kredit di bawah).

**Anggota tim:**
- **Mararevi Subagyo** (NRP 2040241036)
- **Muhammad Al Azhar Faradis** (NRP 2040241017)
- **Anwar Rifa'i** (NRP 2040241021)

**Dosen pembimbing:** Moh. Ismarintan Zazuli

### Kontribusi Saya (Muhammad Al Azhar Faradis)

Rincian lengkap — setup & dependensi, pembuatan node, perancangan
publisher–subscriber, pengujian, debugging, dan iterasi perbaikan — ada di
**[docs/KONTRIBUSI_AZHAR.md](docs/KONTRIBUSI_PROYEK.md)**.

Ringkasnya:

| Bidang | Kontribusi |
|---|---|
| **Setup & Dependensi** | Deployment workspace ke NUC, skrip `deploy.bash` 7 tahap, instalasi 15 paket ROS 2, udev rules (`/dev/rplidar`, `/dev/stm32`), akses remote SSH/Tailscale |
| **Pembuatan Node** | 7 node: health check, IMU merger, LiDAR XY, integration check, encoder odometry, brain FSM, STM32 bridge (C++) |
| **Publisher–Subscriber** | Perancangan kontrak QoS menyeluruh (sensor BestEffort, `/cmd_vel` Reliable), sinkronisasi accel+gyro, protokol serial NUC ↔ STM32 |
| **Pengujian** | Verifikasi berlapis di perangkat keras — Lapisan 1: 5/5 sensor PASS, Lapisan 2: EKF ~45 Hz; analisis presisi LiDAR (σ 1,6–4,5 mm) |
| **Debugging** | 6 akar masalah ditemukan & diperbaiki, termasuk *motor plugging* (lonjakan arus → EMI → chip Wi-Fi/BT reset) |
| **Trial & Error** | Iterasi terdokumentasi: bridge Python→C++, parameter RealSense, watchdog yang dilumpuhkan `autorepeat` |

## 7. Getting Started

```bash
# 1. Clone
git clone https://github.com/muhammadalazharf/autonomous-mobile-robot-ros2.git ~/amr_ws
cd ~/amr_ws

# 2. Install dependency
./scripts/install_deps.sh

# 3. Build
colcon build --symlink-install
source install/setup.bash

# 4. Jalankan (contoh)
ros2 launch amr_bringup sensors_launch.py      # sensor
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py   # mapping
ros2 launch amr_slam nav2.launch.py            # navigasi otonom
```

## 8. Dokumentasi Lengkap

Panduan detail ada di folder `docs/`:

- `00_WORKSPACE_ARCHITECTURE.md` — arsitektur workspace
- `01_USER_MANUAL.md` — panduan pengguna
- `02_DEVELOPMENT_GUIDE.md` — panduan pengembangan
- `03_HARDWARE_GUIDE.md` — panduan perangkat keras
- `05_SLAM_NAV2_GUIDE.md` — SLAM & navigasi
- `06_FAILOVER_GUIDE.md` — sistem keselamatan
- `07_TROUBLESHOOTING.md` — pemecahan masalah

## 9. Troubleshooting Singkat

| Gejala | Penyebab | Solusi |
|---|---|---|
| Sensor tak nyambung tanpa error | QoS mismatch | samakan QoS publisher & subscriber |
| RTAB-Map tak jalan | TF tree belum lengkap | pastikan static TF sensor → base |
| Robot menabrak saat mundur | tuning Nav2 Ackermann | sesuaikan turning radius & inflation |
| RViz2 gagal via remote | X11 tak ter-forward | jalankan dari layar NUC |

## 10. Status & Roadmap

Proyek mencapai tahap navigasi otonom terpandu dengan peta hasil SLAM. Pekerjaan
lanjutan mencakup penguatan lokalisasi, tuning navigasi Ackermann, dan integrasi
lapisan keselamatan secara penuh.

## 11. Acknowledgments & Lisensi

- Terima kasih kepada dosen pembimbing dan tim PjBL.
- Dibangun di atas: ROS 2, Nav2, RTAB-Map, SLAM Toolbox, rplidar_ros, realsense2.
- Lisensi: **MIT** — lihat [LICENSE](LICENSE).

## 12. Kredit Repositori

Basis kode dan dokumentasi tim dipelihara bersama. Repositori rujukan tim
(oleh Mararevi Subagyo): `github.com/Mervs111/autonomous-mobile-robot-ros2-PJBL-4-24`.
Struktur dokumentasi terinspirasi repositori dosen (RAISA):
`github.com/ismarintan98/Mobile_Robot_RAISA`.
