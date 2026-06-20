# MISSING EVIDENCE CHECKLIST

Bukti yang HARUS ditambahkan manual (di luar kemampuan ekstraksi repo).

## Foto / Hardware
- [ ] Foto keseluruhan robot terakit
- [ ] Foto kerangka & penggerak 4WD + kemudi Ackermann
- [ ] Foto penempatan NUC/STM32/driver/baterai
- [ ] Wiring diagram / skema kelistrikan
- [ ] Konfirmasi spec: driver BTS7960, buck converter, push button/e-stop fisik

## Sensor (RViz)
- [ ] Screenshot RViz /scan (LaserScan)
- [ ] Screenshot RViz point cloud RGB-D
- [ ] Output `ros2 topic hz` tiap sensor

## Mapping / Database
- [ ] Screenshot rtabmap_viz saat mapping
- [ ] Screenshot DatabaseViewer graph view
- [ ] Output `rtabmap-info lab_demo_18jun.db` (verifikasi metrik)
- [ ] Plot trajektori (x-y)

## Localization
- [ ] Screenshot loop closure hijau (mode localization)
- [ ] Log /localization_pose atau /rtabmap pose
- [ ] (Opsional) RMSE pose vs ground truth

## Navigation2
- [ ] Video robot bergerak otonom dari goal
- [ ] Log `/cmd_vel` saat goal aktif (linear.x != 0)
- [ ] Screenshot RViz global plan + local plan + costmap
- [ ] Log 'Managed nodes are active'

## Kalibrasi (perkuat)
- [ ] Plot regresi real vs odom (dari data_euler_odom.csv / jalan_maju)
- [ ] Foto pengukuran meteran saat uji jarak
