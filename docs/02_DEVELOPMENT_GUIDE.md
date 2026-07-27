# 02 — Panduan Pengembangan

Panduan bagi siapa pun yang akan mengembangkan, memodifikasi, atau menambah
fitur pada sistem AMR ini.

---

## 1. Menyiapkan Lingkungan Pengembangan

### 1.1 Prasyarat

- Ubuntu 22.04 LTS
- ROS 2 Humble
- Python 3.10, `colcon`, `rosdep`

### 1.2 Instalasi otomatis

```bash
cd ~/amr_ws
./scripts/install_deps.sh
```

### 1.3 Instalasi manual

```bash
sudo apt install -y \
  ros-humble-rtabmap-ros ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-robot-localization ros-humble-rplidar-ros \
  ros-humble-realsense2-camera ros-humble-realsense2-description \
  ros-humble-depthimage-to-laserscan ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher ros-humble-xacro \
  ros-humble-diagnostic-msgs ros-humble-tf2-tools \
  python3-colcon-common-extensions python3-rosdep

rosdep install --from-paths src --ignore-src -y -r
```

---

## 2. Build

### 2.1 Build seluruh workspace

```bash
cd ~/amr_ws
colcon build --symlink-install
source install/setup.bash
```

### 2.2 Build satu package saja (disarankan)

```bash
colcon build --symlink-install --packages-select amr_controller
source install/setup.bash
```

**Mengapa per-package:** bila terjadi kegagalan kompilasi, penyebabnya langsung
terlihat pada package mana. Build menyeluruh membuat pesan error bercampur dan
sulit ditelusuri.

### 2.3 Arti `--symlink-install`

Opsi ini membuat *tautan* ke berkas sumber, bukan menyalinnya. Akibatnya,
perubahan pada berkas **Python** dan **YAML** langsung berlaku tanpa perlu build
ulang. Berkas C++ tetap harus di-build ulang karena perlu dikompilasi.

### 2.4 Build bersih (bila terjadi kejanggalan)

```bash
rm -rf build/ install/ log/
colcon build --symlink-install
```

---

## 3. Menambahkan Node Baru

### 3.1 Node Python

**Langkah 1 — buat berkas node** di `src/<package>/<package>/nama_node.py`:

```python
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# Profil QoS untuk sensor — WAJIB BestEffort (lihat kontrak QoS)
SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)


class NamaNode(Node):
    def __init__(self):
        super().__init__('nama_node')
        self.declare_parameter('contoh_parameter', 1.0)
        # ... subscriber / publisher / timer


def main(args=None):
    rclpy.init(args=args)
    node = NamaNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

**Langkah 2 — daftarkan di `setup.py`:**

```python
entry_points={'console_scripts': [
    'nama_node = nama_package.nama_node:main',
]},
```

**Langkah 3 — build dan jalankan:**

```bash
colcon build --symlink-install --packages-select nama_package
source install/setup.bash
ros2 run nama_package nama_node
```

### 3.2 Node C++

Tambahkan target pada `CMakeLists.txt`:

```cmake
add_executable(nama_node src/nama_node.cpp)
ament_target_dependencies(nama_node rclcpp std_msgs)
install(TARGETS nama_node DESTINATION lib/${PROJECT_NAME})
```

---

## 4. Aturan Tata Kelola Parameter

### 4.1 Prinsip: satu sumber kebenaran

Seluruh parameter ditulis **hanya** pada berkas YAML di `config/`.

❌ **Jangan** menulis parameter langsung di launch file:
```python
Node(package='x', executable='y', parameters=[{'kecepatan': 0.5}])   # SALAH
```

✅ **Gunakan** berkas YAML:
```python
Node(package='x', executable='y', parameters=[config_path])          # BENAR
```

**Alasan:** pada sistem sebelumnya, nilai parameter yang sama tertulis di
beberapa tempat dan saling menimpa. Akibatnya nilai yang benar-benar aktif tidak
dapat dipastikan tanpa membaca seluruh berkas.

### 4.2 Memverifikasi nilai yang aktif

```bash
ros2 param list                              # daftar seluruh parameter
ros2 param get /nama_node nama_parameter     # nilai yang benar-benar dipakai
```

> **Kasus nyata:** parameter resolusi kamera pernah ditulis di YAML, tetapi
> `ros2 param get` menunjukkan nilai bawaan driver (1280×720) — YAML tidak
> terbaca karena persoalan namespace. **Selalu verifikasi, jangan berasumsi.**

---

## 5. Aturan QoS

Saat membuat publisher atau subscriber baru, ikuti kontrak berikut:

| Jenis data | Reliability |
|---|---|
| Data sensor (LiDAR, kamera, IMU, encoder) | `BEST_EFFORT` |
| Perintah gerak (`/cmd_vel`) | `RELIABLE` |

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)
self.create_subscription(LaserScan, '/scan', self.callback, SENSOR_QOS)
```

**Memeriksa kecocokan QoS:**
```bash
ros2 topic info /scan --verbose
```
Bandingkan bagian *Reliability* pada publisher dan subscriber. Bila berbeda,
data **tidak akan pernah sampai** — dan tidak ada pesan error yang muncul.

---

## 6. Alur Kerja Git

### 6.1 Aturan dasar

- **Jangan** melakukan commit langsung ke `main`.
- Buat branch untuk tiap fitur atau perbaikan.
- Tulis pesan commit yang menjelaskan **alasan**, bukan sekadar apa yang diubah.

```bash
git checkout -b fix/nama-perbaikan
# ... lakukan perubahan ...
git add <berkas>
git commit -m "Fix: watchdog joystick tidak aktif karena autorepeat"
git push origin fix/nama-perbaikan
```

### 6.2 Berkas yang tidak boleh masuk Git

Pastikan `.gitignore` memuat:
```gitignore
build/
install/
log/
__pycache__/
*.pyc
*.db          # basis data peta RTAB-Map (berukuran besar)
frames*.pdf   # keluaran view_frames
frames*.gv
*.bag
```

---

## 7. Kebiasaan Menulis Kode

- **Komentar menjelaskan alasan, bukan cara.**
  ✅ `# BestEffort — harus cocok dengan publisher RealSense`
  ❌ `# membuat subscriber`
- **Beri nama yang menjelaskan diri sendiri.** `imu_merger_node` lebih baik
  daripada `node2`.
- **Beri tanda pada nilai yang belum terverifikasi:**
  ```python
  WHEEL_RADIUS = 0.0775   # PERLU DIUKUR ULANG di robot fisik
  ```
- **Jangan menebak parameter perangkat keras.** Ukur, atau ambil dari kode yang
  sudah terbukti berjalan.

---

## 8. Menguji Perubahan

Selalu uji **berurutan dari lapisan terbawah**:

```bash
# 1. Sensor berfungsi?
ros2 launch amr_bringup sensors_launch.py
ros2 topic hz /scan

# 2. Kerangka koordinat benar?
ros2 run tf2_tools view_frames

# 3. Baru lanjut ke mapping / navigasi
```

Menguji navigasi sementara sensor belum terverifikasi hanya akan menghasilkan
kebingungan — kegagalan di lapisan bawah selalu merambat ke atas.

---

## 9. Kesalahan yang Sering Terjadi

| Kesalahan | Akibat | Pencegahan |
|---|---|---|
| Lupa `source install/setup.bash` | Node tidak ditemukan | Tambahkan ke `.bashrc` |
| QoS tidak cocok | Data tidak sampai, **tanpa error** | Periksa `ros2 topic info --verbose` |
| Parameter ditulis di dua tempat | Nilai aktif tidak dapat dipastikan | Satu sumber di YAML |
| Path di-*hardcode* (`/home/nama`) | Gagal di komputer lain | Gunakan `os.path.expanduser('~')` |
| Menebak parameter perangkat keras | Perilaku tidak sesuai | Ukur langsung atau ambil dari kode terverifikasi |

---

**Lanjut:** [03_HARDWARE_GUIDE.md](03_HARDWARE_GUIDE.md) untuk detail perangkat
keras.
