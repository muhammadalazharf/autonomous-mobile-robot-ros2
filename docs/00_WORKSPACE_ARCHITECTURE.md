# 00 — Arsitektur Workspace

Dokumen ini menjelaskan struktur workspace, peran tiap package, aliran data
antar-node, dan kontrak komunikasi yang berlaku di sistem AMR.

---

## 1. Struktur Workspace

```
amr_ws/
├── src/
│   ├── amr_description/        Model robot (URDF/Xacro) + TF tree
│   ├── amr_controller/         Jembatan STM32, IMU merger, odometry
│   ├── amr_bringup/            Orkestrasi launch + konfigurasi RViz
│   ├── amr_3d_mapping/         RTAB-Map: VIO, mapping, localization
│   ├── amr_slam/               Nav2 + behavior tree + skrip navigasi
│   ├── amr_visual_regression/  Navigasi cadangan berbasis visual
│   └── amr_failover/           Arbiter keselamatan
├── build/                      (hasil build — tidak masuk Git)
├── install/                    (hasil build — tidak masuk Git)
└── log/                        (hasil build — tidak masuk Git)
```

## 2. Peran Tiap Package

| Package | Bahasa | Tanggung jawab |
|---|---|---|
| `amr_description` | XML/Xacro | Definisi geometri robot, kerangka koordinat (TF), posisi sensor |
| `amr_controller` | C++ / Python | `stm32_bridge` (serial), `imu_merger_node`, `odometry_publisher` |
| `amr_bringup` | Python | Launch file gabungan: sensor, sistem penuh, konfigurasi joystick |
| `amr_3d_mapping` | Python | Konfigurasi & launch RTAB-Map (mapping, localization, VIO) |
| `amr_slam` | Python | Nav2 (planner, controller, costmap), behavior tree, goal sender |
| `amr_visual_regression` | Python | Pengumpulan dataset, ekstraksi fitur, inferensi navigasi cadangan |
| `amr_failover` | Python | Pemilihan sumber kendali & penghentian darurat |

## 3. Aliran Data

```
                    ┌─────────────────────────────┐
                    │   amr_failover (arbiter)     │
                    │  SLAM / Visual / Joy / STOP  │
                    └──────────────┬───────────────┘
                                   │ memilih sumber /cmd_vel
                                   ▼
 SENSOR              PEMROSESAN                    AKTUATOR
 ──────              ──────────                    ────────
 RPLIDAR ──/scan──┐
                  ├──► amr_3d_mapping ──► amr_slam ──/cmd_vel──► STM32 ──► Motor
 RealSense ──RGBD─┤     (RTAB-Map)         (Nav2)                          + Servo
           ──IMU──┤          ▲
                  │          │ /odom
 Encoder ─────────┴──► amr_controller ◄──/encoder──────────────────────────┘
                        (stm32_bridge)
```

**Penjelasan alur:**

1. **Sensor** mengirim data mentah: LiDAR (`/scan`), kamera RGB-D + IMU, encoder.
2. **`amr_controller`** mengubah pulsa encoder menjadi odometry, dan
   menggabungkan accel+gyro menjadi `/imu/data`.
3. **`amr_3d_mapping`** (RTAB-Map) membangun peta dan memperkirakan posisi robot
   menggunakan data visual + LiDAR + odometry.
4. **`amr_slam`** (Nav2) merencanakan lintasan menuju target dan menghasilkan
   perintah gerak `/cmd_vel`.
5. **`amr_failover`** menentukan sumber `/cmd_vel` mana yang diteruskan
   (otonom, visual, joystick, atau berhenti).
6. **`stm32_bridge`** menerjemahkan `/cmd_vel` menjadi perintah serial ke STM32.

## 4. Kerangka Koordinat (TF Tree)

```
map                     ← RTAB-Map (global, dapat "melompat" saat loop closure)
 └── odom               ← odometry (halus & kontinu, tetapi mengalami drift)
      └── base_footprint    ← titik acuan robot di lantai
           ├── base_link
           ├── camera_link  ← RealSense D455
           └── laser_frame  ← RPLIDAR C1
```

**Mengapa `map` dan `odom` dipisah** (mengikuti REP-105):

- `odom` bersifat **halus dan kontinu** — cocok untuk kendali gerak jangka
  pendek, tetapi posisinya makin melenceng seiring waktu (*drift*).
- `map` bersifat **akurat dalam jangka panjang** — namun posisinya dapat
  melompat tiba-tiba ketika sistem mengenali kembali tempat yang pernah
  dilewati (*loop closure*).

Analogi: `odom` seperti menghitung langkah kaki (mulus, tapi makin lama makin
meleset); `map` seperti GPS (kadang melompat, tetapi tidak menyimpang jauh).

## 5. Kontrak QoS

Kesalahan konfigurasi QoS di ROS 2 **tidak memunculkan pesan error** — koneksi
hanya diam-diam tidak terbentuk. Karena itu, seluruh sistem mengikuti satu
kontrak yang seragam:

| Topic | Reliability | Alasan |
|---|---|---|
| `/scan` | BestEffort | Frekuensi tinggi; data terbaru lebih penting |
| `/camera/*/color/image_raw` | BestEffort | 30 fps; kehilangan satu frame tidak fatal |
| `/camera/*/depth/image_rect_raw` | BestEffort | Sama seperti color |
| `/imu/data` | BestEffort | 100–200 Hz |
| `/encoder` | BestEffort | Frekuensi tinggi |
| `/cmd_vel` | **Reliable** | Perintah gerak kritis — tidak boleh hilang |

**Aturan:** publisher dan subscriber **harus** memakai reliability yang sama.
Bila berbeda, data tidak akan pernah sampai.

## 6. Daftar Topic Utama

| Topic | Tipe Pesan | Penerbit |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | rplidar_node |
| `/camera/camera/color/image_raw` | `sensor_msgs/Image` | realsense2_camera |
| `/camera/camera/depth/image_rect_raw` | `sensor_msgs/Image` | realsense2_camera |
| `/imu/data` | `sensor_msgs/Imu` | imu_merger_node |
| `/encoder` | `std_msgs/Int32` | stm32_bridge |
| `/odom` | `nav_msgs/Odometry` | odometry_publisher |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 / joystick / failover |
| `/joy` | `sensor_msgs/Joy` | joy_node |
| `/map`, `/cloud_map` | `OccupancyGrid`, `PointCloud2` | rtabmap |

## 7. Prinsip Tata Kelola Parameter

Seluruh parameter ditulis **hanya di satu tempat** — berkas YAML di folder
`config/` masing-masing package.

**Alasan:** pada sistem sebelumnya, parameter yang sama tertulis di launch file,
YAML, dan kode sekaligus. Ketiganya saling menimpa, sehingga nilai yang benar-benar
aktif menjadi sulit dilacak.

**Cara memverifikasi nilai yang aktif:**
```bash
ros2 param get /nama_node nama_parameter
```

---

**Lanjut:** [01_USER_MANUAL.md](01_USER_MANUAL.md) untuk panduan pengoperasian.
