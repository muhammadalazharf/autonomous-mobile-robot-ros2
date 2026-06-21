# Ringkasan Fishbone untuk Laporan

BAB II Realisasi Project disusun menggunakan **Fishbone (Ishikawa) Analysis** terhadap effect utama: _AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan._

Analisis memecah sistem menjadi **12 tulang (bone)** yang saling bergantung: (A) platform hardware & aktuator, (B) sensor & persepsi, (C) arsitektur ROS 2, (D) model robot & TF, (E) odometry, (F) mapping RTAB-Map, (G) localization, (H) global planner point-to-point, (I) local planner obstacle-avoidant, (J) eksekusi STM32, (K) safety/failover, (L) bukti & gap.

Setiap bone menjadi satu subbab BAB II (2.2-2.13), diapit penetapan target (2.1) dan ringkasan capaian (2.14). Pendekatan ini menampilkan hubungan **sebab-akibat**: hardware->sensor->ROS2->TF->odometry->mapping->localization menjadi prasyarat global & local planner, yang keluarannya (/cmd_vel) dieksekusi STM32 di bawah pengawasan safety.

Dari 12 bone, **6 bone terverifikasi dari file** (config/hardware/sensor/odometry/eksekusi/safety) dan **6 bone berstatus catatan progress** (mapping, localization, global/local planner, bukti) yang **masih memerlukan bukti runtime** (screenshot/log/video). Penyajian ini menjaga kejujuran teknis: capaian yang terbukti dinyatakan tegas, sedangkan rantai autonomous end-to-end ditandai sebagai gap yang harus dilengkapi.
