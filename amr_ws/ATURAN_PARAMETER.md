# ATURAN PARAMETER — Workspace AMR Baru

## Satu resep, satu tempat. Tidak ada pengecualian.

### BOLEH:
- Parameter ditulis di `config/*.yaml` dalam package masing-masing
- Launch file menunjuk ke file YAML: `parameters=[config_path]`
- Launch argument untuk input user runtime (misal `record:=true`)

### DILARANG:
- ❌ Menulis parameter inline di launch file: `parameters=[{'key': 'value'}]`
- ❌ Menulis parameter yang sama di dua file berbeda
- ❌ Edit YAML tanpa rebuild (kecuali pakai `--symlink-install`)

### Cara build yang benar:
```bash
colcon build --symlink-install --packages-select <nama_package>
```
`--symlink-install` membuat link dari install/ ke src/ — jadi edit YAML
langsung berlaku tanpa rebuild. WAJIB dipakai setiap kali build.

### Cara verifikasi parameter benar sampai ke runtime:
```bash
ros2 param get <nama_node> <nama_parameter>
```
Hasil harus SAMA dengan isi file YAML. Kalau beda → ada yang menimpa.

### Peta parameter per package:
| Package        | File YAML                  | Isi                          |
|----------------|----------------------------|------------------------------|
| amr_sensors    | config/sensors.yaml        | RPLIDAR, RealSense, LiDAR XY|
| amr_pose       | config/encoder.yaml        | wheel_radius, PPR, rate      |
| amr_pose       | config/ekf.yaml            | EKF sumber, kovarians        |
| amr_mapping    | config/rtabmap.yaml        | (Modul 4, belum dibuat)      |
| amr_navigation | config/nav2_params.yaml    | (Modul 5, belum dibuat)      |
