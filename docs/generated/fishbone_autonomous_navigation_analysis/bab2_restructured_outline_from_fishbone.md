# BAB II REALISASI PROJECT — Kerangka dari Fishbone

Disusun mengikuti rantai sebab-akibat fishbone menuju autonomous navigation point-to-point + obstacle avoidance.

## 2.1 Penentuan Target Autonomous Navigation AMR
Target akhir: AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.

## 2.2 Platform Hardware dan Aktuator
- Dari Bone A. Robot memiliki platform fisik 4WD Ackermann yang mampu mengeksekusi gerak translasi & kemudi sesuai perintah navigasi.
- Status bukti: Berdasarkan catatan progress

## 2.3 Sensor dan Persepsi Lingkungan
- Dari Bone B. Robot membaca lingkungan (jarak, citra, gerak) sebagai masukan mapping, costmap, odometry, dan localization.
- Status bukti: Terverifikasi dari file repo

## 2.4 ROS 2 Middleware dan Arsitektur Software
- Dari Bone C. ROS 2 menghubungkan seluruh subsistem secara modular (7 package) via topic/service/action/TF.
- Status bukti: Terverifikasi dari file repo

## 2.5 Model Robot, URDF/Xacro, dan TF Tree
- Dari Bone D. Representasi geometris benar agar transform map->odom->base_link ->sensor konsisten untuk mapping, localization, navigation.
- Status bukti: Terverifikasi dari file repo

## 2.6 Odometry dan Estimasi Gerak
- Dari Bone E. Robot mengestimasi perubahan posisi (odometry) sebagai motion prior untuk SLAM & Nav2.
- Status bukti: Terverifikasi dari file repo

## 2.7 Mapping Lingkungan (RTAB-Map)
- Dari Bone F. Robot membangun peta lingkungan (pose graph + occupancy grid) yang valid sebagai basis localization & global costmap.
- Status bukti: Berdasarkan catatan progress

## 2.8 Localization terhadap Peta
- Dari Bone G. Robot menentukan posisinya terhadap peta acuan (lock) sebelum menerima goal navigasi.
- Status bukti: Berdasarkan catatan progress

## 2.9 Navigation2 Global Planner — Point-to-Point
- Dari Bone H. Robot menerima goal dan menghitung lintasan global dari pose saat ini menuju target (point-to-point), Ackermann-aware.
- Status bukti: Berdasarkan catatan progress

## 2.10 Navigation2 Local Planner — Obstacle Avoidant
- Dari Bone I. Robot mengikuti lintasan global sambil menghasilkan /cmd_vel yang menghindari rintangan dari costmap lokal.
- Status bukti: Berdasarkan catatan progress

## 2.11 Eksekusi Perintah ke STM32 dan Aktuator
- Dari Bone J. Hasil planner (/cmd_vel) diteruskan ke STM32 dan menjadi gerak motor + servo kemudi.
- Status bukti: Terverifikasi dari file repo

## 2.12 Safety, Failover, dan Manual Override
- Dari Bone K. Sistem aman saat autonomous: e-stop, deadman, arbitrasi sumber gerak.
- Status bukti: Terverifikasi dari file repo

## 2.13 Evidence, Testing, dan Gap Validasi
- Dari Bone L. Klaim autonomous didukung bukti yang dapat diaudit; gap dinyatakan jujur.
- Status bukti: Berdasarkan catatan progress

## 2.14 Project yang Terselesaikan
- Ringkasan capaian per bone + status kejujuran teknis (mana yang terbukti file, mana yang masih perlu bukti runtime).
