# 00 — Identitas Proyek AMR

- **Nama:** Autonomous Mobile Robot (AMR) 4WD Ackermann Indoor
- **Deskripsi:** Robot bergerak otonom 4WD kemudi Ackermann untuk indoor, berbasis ROS 2 Humble; mapping & localization RTAB-Map, navigasi Navigation2, kendali via STM32 serial.
- **Jenis robot:** Mobile robot 4WD, kemudi Ackermann (2 roda depan)
- **Lingkungan:** Indoor / laboratorium (E105 ITS)
- **Target utama:** Robot bergerak otonom dari goal Nav2 di atas peta indoor

## Tim
- **Mararevi Subagyo** (2040241036): Integrasi sistem, dokumentasi, analisis DB, Nav2, lokalisasi
- **Muhammad Al Azhar Faradis** (2040241017): ROS2, RTAB-Map, Nav2, kalibrasi odometry, debugging
- **Anwar Rifa'i** (2040241021): Hardware, wiring, STM32, aktuator, pengujian

## Status Capaian Umum
- platform_4wd_ackermann: **Tercapai**
- integrasi_ros2: **Tercapai**
- integrasi_sensor: **Tercapai (LiDAR C1 + RealSense D455)**
- kalibrasi_odometry: **Tercapai (PPR 3858, R2=0.998)**
- mapping_rtabmap: **Tercapai (lab_demo_18jun.db)**
- localization: **Tercapai; bukti runtime perlu dilengkapi**
- navigasi_nav2: **Tercapai mode demo; bukti runtime perlu dilengkapi**
- failover: **Diimplementasi; dibypass saat demo**

> Catatan sumber: Catatan/progress (perlu validasi sumber) (identitas tim & status dari laporan .docx + progress; spec hardware terverifikasi dari URDF/launch)
