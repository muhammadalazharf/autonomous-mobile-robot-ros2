# 15 — Matriks Bukti per Subbab Laporan

Menghubungkan data raw ke subbab 2.1-2.16. Kolom status_bukti menandai kekuatan bukti; gambar yang perlu ditambah manual disebut eksplisit.

| subbab | data_pendukung | bentuk_bukti | file_sumber | status_bukti | tabel_disarankan | gambar_disarankan | catatan |
|---|---|---|---|---|---|---|---|
| 2.1 Konsep AMR | identitas proyek, target | narasi + spec | 00_project_identity | Kuat | perbandingan AMR vs AGV | konsep robot | definisi & cakupan |
| 2.2 Perancangan Hardware | inventaris hardware | tabel komponen | 01_hardware_inventory | Kuat (sebagian perlu konfirmasi) | spec komponen | foto komponen, wiring | BTS7960/buck perlu validasi |
| 2.3 Perakitan Platform | geometri, penempatan sensor | foto + dimensi | 05_robot_model_urdf_xacro | Sedang | posisi sensor | foto robot terakit | FOTO perlu ditambah |
| 2.4 Setup ROS2 | env, workspace, deps | daftar + screenshot | 03_ros2_package_inventory | Kuat | daftar package | ros2 node list | screenshot terminal |
| 2.5 Pembagian Package | 7 package | tabel package | 03_ros2_package_inventory | Kuat | fungsi package | diagram dependency | - |
| 2.6 STM32/Joystick/Motor/Servo/Encoder | protokol serial | tabel protokol | 06_stm32_serial_communication | Kuat | format pesan TX/RX | foto wiring STM32 | video uji manual |
| 2.7 RPLIDAR & RealSense | data sensor | tabel sensor + scan params | 02_sensor_raw_data | Kuat | spec sensor | RViz scan + pointcloud | scan params dari data nyata |
| 2.8 URDF/TF | link/joint/frame | tabel + diagram TF | 05_robot_model_urdf_xacro | Kuat | parameter geometri | frames_*.pdf (ADA), RViz RobotModel | TF diagram tersedia |
| 2.9 Kalibrasi Odometry | uji 5 jarak, regresi | tabel + plot | 07_odometry_calibration | Kuat | jarak nyata vs odom | plot regresi R2 | data CSV upload tersedia |
| 2.10 Mapping RTAB-Map | pipeline, params | tabel param + screenshot | 08_rtabmap_database_inventory | Sedang | param mapping | rtabmap_viz, graph view | screenshot perlu |
| 2.11 Analisis Database | inventaris 24 DB | tabel + ringkasan | 08_rtabmap_database_summary | Kuat (di laporan) | metrik per DB | bar chart node/LC | verifikasi ulang via rtabmap-info |
| 2.12 Remapping & Peta Acuan | lab_demo_18jun.db | tabel metrik | 08_rtabmap_database_inventory | Sedang | peta lama vs bersih | loop closure hijau, cloud | screenshot perlu |
| 2.13 Localization | params, root cause | tabel ambang | 09_localization_evidence | Sedang (bukti runtime kurang) | mapping vs localization | screenshot localization, log pose | BUKTI RUNTIME perlu |
| 2.14 Navigation2 | config, 8 gerbang | tabel config + kronologi | 10_nav2_configuration_and_evidence | Sedang (bukti runtime kurang) | plugin & param | RViz path, video navigasi | VIDEO/LOG runtime perlu |
| 2.15 Safety/Failover/Kendala | failover, kendala | tabel state + kendala | 12_safety_failover_manual_control | Kuat | state machine, kendala-solusi | marker RViz failover | - |
| 2.16 Project Terselesaikan | status capaian | tabel ketercapaian | 00_project_identity | Kuat | target vs realisasi | - | jaga kejujuran teknis |
