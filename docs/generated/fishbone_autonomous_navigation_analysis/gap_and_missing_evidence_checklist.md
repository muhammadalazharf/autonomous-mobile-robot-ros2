# Gap & Missing Evidence Checklist

Bukti yang HARUS ditambahkan manual (di luar ekstraksi repo):

- [ ] Screenshot RViz /scan (LaserScan)
- [ ] Screenshot RealSense RGB-D (image + pointcloud)
- [ ] Screenshot RTAB-Map database (DatabaseViewer graph view)
- [ ] Output rtabmap-info lab_demo_18jun.db (verifikasi metrik)
- [ ] Screenshot/log localization pose (/localization_pose atau loop closure hijau)
- [ ] Screenshot Nav2 lifecycle active ('Managed nodes are active')
- [ ] Screenshot global path (RViz Path dari planner)
- [ ] Screenshot local costmap (dengan obstacle)
- [ ] Log /cmd_vel saat goal aktif (linear.x != 0)
- [ ] Video robot bergerak menuju goal (point-to-point)
- [ ] Bukti obstacle avoidance (robot belok menghindar)
- [ ] Bukti STM32 menerima command (log serial / motor bergerak)
- [ ] Bukti encoder feedback (plot /encoder atau /odom)
- [ ] Foto fisik robot + wiring + penempatan komponen
- [ ] Konfirmasi hardware: BTS7960, buck converter, push button/e-stop fisik

## Prioritas untuk klaim autonomous
1. Log /cmd_vel saat goal + video robot bergerak (Bone H,I,J).
2. Screenshot loop closure hijau / log localization (Bone G).
3. Screenshot global plan + local costmap (Bone H,I).
4. rtabmap-info DB acuan (Bone F).
