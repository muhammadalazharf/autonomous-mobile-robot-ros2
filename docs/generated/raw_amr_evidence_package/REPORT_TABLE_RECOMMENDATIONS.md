# REPORT TABLE RECOMMENDATIONS

Tabel siap-pakai per subbab (sumber CSV ada di paket ini).

| Subbab | Tabel disarankan | Sumber CSV |
|---|---|---|
| 2.2 Hardware | Spesifikasi komponen | 01_hardware_inventory.csv |
| 2.5 Package | Fungsi 7 package | 03_ros2_package_inventory.csv |
| 2.6 STM32 | Format pesan TX/RX & parameter | 06_stm32_serial_communication.csv |
| 2.7 Sensor | Spec & parameter sensor | 02_sensor_raw_data.csv |
| 2.8 URDF/TF | Parameter geometri | 05_robot_model_urdf_xacro.csv |
| 2.9 Odometry | Jarak nyata vs odom + regresi | 07_odometry_calibration.csv |
| 2.10 Mapping | Parameter RTAB-Map | (lihat 08 + bank data) |
| 2.11 Database | Metrik per DB + ringkasan | 08_rtabmap_database_*.csv |
| 2.13 Localization | Ambang mapping vs localization | 09_localization_evidence.csv |
| 2.14 Nav2 | Plugin & parameter + 8 gerbang | 10_nav2_*.csv, 14_issues_*.csv |
| 2.15 Safety | State machine + kendala-solusi | 12_*.csv, 14_*.csv |
| 2.16 Capaian | Target vs realisasi | 00_project_identity.json |

## Catatan
- CSV dapat langsung di-import ke Word/Excel/Sheets lalu diformat.
- JSON untuk pemrosesan lanjut / generate ulang.
- Selalu cantumkan sumber & jaga kejujuran teknis (tandai bukti runtime yang belum ada).
