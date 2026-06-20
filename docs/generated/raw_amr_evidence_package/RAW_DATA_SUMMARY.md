# RAW DATA SUMMARY

## Data yang BERHASIL dikumpulkan (terverifikasi dari file)

- Spesifikasi hardware terkonfigurasi (URDF, sensors_launch, bridge).
- Parameter sensor LiDAR & RealSense (termasuk scan params dari data nyata).
- 7 package ROS2 + topic/node/service/action/TF.
- Model robot URDF (geometri, link, joint, TF tree) + diagram frames_*.pdf.
- Protokol serial STM32 lengkap (TX/RX, PWM, servo, gate, ramping).
- Kalibrasi odometry: 5 titik uji, regresi R2=0.998, PPR 3858.
- Konfigurasi RTAB-Map mapping & localization (+ tabel ambang).
- Konfigurasi Nav2 lengkap + rantai 8 gerbang debugging.
- Ackermann steering (parameter, rumus, fix arah).
- Failover state machine + safety + PWM ramping.
- Visual regression + line segments.
- 14 kendala lintas subsistem dengan solusi.

## Data KUAT sebagai bukti

1. Kalibrasi odometry (data numerik + R2=0.998) — paling kuat & auditable.
2. Konfigurasi sistem (semua YAML/launch/source) — 100% file-verified.
3. Rantai 8 gerbang Nav2 (kronologi debugging dengan akar masalah).
4. Parameter sensor LiDAR dari scan nyata (data_lidar_*.txt).

## Data yang MASIH KURANG

- File `.db` TIDAK ada di repo (di `~/maps/` NUC) — metrik dari laporan .docx; verifikasi ulang `rtabmap-info` di NUC.
- Bukti RUNTIME lokalisasi (screenshot loop closure hijau, log /localization_pose).
- Bukti RUNTIME navigasi (video, log /cmd_vel saat goal, RViz path).
- Foto fisik robot, wiring diagram, screenshot RViz/rtabmap_viz.
- Konfirmasi hardware: BTS7960, buck converter, push button/e-stop fisik.

## Bagian laporan dengan bukti KUAT

2.2, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.15 — sudah didukung data file.

## Bagian laporan yang MASIH butuh bukti tambahan

2.3 (foto), 2.10/2.11/2.12 (screenshot mapping/DB), 2.13 (bukti lokalisasi runtime), 2.14 (video/log navigasi runtime).

## Rekomendasi urutan penggunaan data

1. Mulai dari yang file-verified (2.4-2.9) untuk fondasi kuat.
2. Lengkapi 2.10-2.14 dengan screenshot/log saat sesi lab berikutnya.
3. Tambah foto hardware (2.2-2.3) dari dokumentasi tim.
4. Jaga kejujuran: tandai klaim yang belum ada bukti runtime.
