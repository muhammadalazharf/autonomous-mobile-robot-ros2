# 05 — Panduan SLAM & Navigasi

Konfigurasi RTAB-Map (pemetaan & lokalisasi) dan Nav2 (navigasi otonom), khusus
untuk robot berkemudi **Ackermann**.

---

## 1. Konsep SLAM

**SLAM** (*Simultaneous Localization and Mapping*) memungkinkan robot membangun
peta lingkungan sekaligus menentukan posisinya di dalam peta tersebut.

**RTAB-Map** menyimpan lingkungan dalam bentuk *pose graph*:

| Elemen | Arti |
|---|---|
| **Node** | Rekaman pengamatan robot pada satu waktu (citra RGB, depth, laser scan, pose) |
| **Link** | Hubungan antar-node — dari odometry atau pencocokan fitur visual |
| **Loop closure** | Sistem mengenali kembali tempat yang pernah dilewati |

### Mengapa loop closure penting

Estimasi posisi selalu mengalami penyimpangan (*drift*) yang menumpuk seiring
waktu. Ketika robot kembali ke tempat yang pernah dikunjungi dan sistem
mengenalinya, seluruh peta dikoreksi sekaligus.

Analogi: seperti berjalan sambil menghitung langkah dengan mata tertutup —
perkiraan posisi makin melenceng. Loop closure adalah momen membuka mata dan
berkata *"saya pernah di sini"*, lalu membetulkan seluruh perkiraan sebelumnya.

---

## 2. Komponen RTAB-Map

| Node | Fungsi |
|---|---|
| `rgbd_sync` | Menggabungkan citra RGB + depth menjadi satu paket tersinkronisasi |
| `rgbd_odometry` (VIO) | Memperkirakan gerak robot dari citra + IMU |
| `rtabmap` | Membangun peta, mendeteksi loop closure, menerbitkan TF `map → odom` |

### ⚠️ Konfigurasi QoS — penyebab kegagalan tersering

`rgbd_sync` **harus** berlangganan dengan QoS **BestEffort**, karena driver
RealSense menerbitkan dengan BestEffort.

```yaml
rgbd_sync:
  ros__parameters:
    qos: 1          # 1 = BestEffort
    qos_image: 1    # 1 = BestEffort
```

**Bila salah:** citra kamera **tidak akan pernah sampai** ke RTAB-Map. Tidak ada
pesan error yang muncul — peta hanya tidak terbentuk dan loop closure tidak
pernah terpicu.

**Cara memverifikasi:**
```bash
ros2 topic hz /rgbd_image     # harus > 0 Hz
```
Bila hasilnya 0 Hz, hentikan proses dan perbaiki QoS terlebih dahulu.

---

## 3. Parameter Penting RTAB-Map

### 3.1 Visual-Inertial Odometry

```yaml
Odom/Strategy: 0            # Frame-to-Map — lebih stabil dibanding Frame-to-Frame
Odom/ResetCountdown: 5      # toleransi 5 frame gagal sebelum reset
Vis/FeatureType: 6          # ORB — cepat, memadai untuk indoor
Vis/MaxFeatures: 1000       # makin banyak fitur, makin tahan pada dinding polos
Reg/Force3DoF: true         # robot bergerak di bidang datar: x, y, yaw saja
wait_imu_to_init: true      # tunggu data IMU sebelum memulai
```

### 3.2 ICP untuk LiDAR *single-ring*

```yaml
Icp/PointToPlane: false     # PENTING: LiDAR 2D tidak memiliki informasi bidang
Icp/VoxelSize: 0.0          # jangan menipiskan data yang memang sudah jarang
Icp/MaxCorrespondenceDistance: 0.15
```

**Alasan:** metode *point-to-plane* membutuhkan estimasi normal permukaan, yang
memerlukan data 3D dari LiDAR multi-lapis. RPLIDAR C1 hanya memindai satu bidang
datar, sehingga metode *point-to-point* yang sesuai.

### 3.3 Deteksi loop closure

```yaml
Rtabmap/DetectionRate: 2.0  # memeriksa 2× per detik
Rtabmap/LoopThr: 0.11       # ambang batas bawaan RTAB-Map
Mem/STMSize: 10
Reg/Strategy: 2             # gabungan visual + ICP
```

### 3.4 Peta grid 2D

```yaml
Grid/FromDepth: false       # grid dibentuk dari LiDAR, bukan citra depth
Grid/RangeMax: 12.0
Grid/CellSize: 0.05         # resolusi 5 cm per sel
```

---

## 4. Prosedur Pemetaan

```bash
# Terminal 1 — sensor
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 — mapping
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py

# Terminal 3 — visualisasi
rviz2 -d ~/amr_ws/src/amr_bringup/config/rviz_3d_mapping.rviz
```

### Verifikasi sebelum mulai berjalan

```bash
ros2 topic hz /rgbd_image      # harus > 0 Hz  ← paling penting
ros2 topic hz /odom            # VIO aktif
ros2 run tf2_tools view_frames # TF map → odom → base_footprint harus lengkap
```

### Cara memetakan yang baik

1. **Berjalan perlahan** — gerakan cepat menyebabkan citra kabur dan VIO
   kehilangan acuan.
2. **Kelilingi ruangan, kembali ke titik awal** — untuk memicu loop closure.
3. **Hindari dinding polos** — VIO membutuhkan tekstur visual sebagai acuan.
4. **Jangan berbelok terlalu tajam** — sudut pandang berubah drastis dan fitur
   visual hilang seketika.

### Memastikan loop closure terpicu

```bash
ros2 topic echo /rtabmap/info --field loop_closure_id
```
Nilai selain `0` menandakan loop closure berhasil. Di RViz, hal ini terlihat
sebagai garis hijau yang menghubungkan dua posisi.

### Menyimpan peta

```bash
# Berkas peta tersimpan otomatis di:
~/.ros/rtabmap.db

# Salin sebagai arsip
mkdir -p ~/maps
cp ~/.ros/rtabmap.db ~/maps/lab_$(date +%Y%m%d).db
```

Untuk menghasilkan format peta 2D standar Nav2 (`.pgm` + `.yaml`):
```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/lab_map
```

---

## 5. Prosedur Lokalisasi

```bash
ros2 launch amr_3d_mapping rtabmap_localization.launch.py
```

Perbedaan mendasar dengan mode mapping: `Mem/IncrementalMemory: false` — peta
tidak lagi diperbarui, sistem hanya mencari posisi robot di dalam peta yang ada.

**Penting:** tempatkan robot pada posisi yang **dikenali** dalam peta, idealnya
titik awal ketika pemetaan dilakukan.

Verifikasi:
```bash
ros2 run tf2_ros tf2_echo map base_footprint
```

---

## 6. Nav2 untuk Robot Ackermann

### 6.1 Perbedaan mendasar dari differential drive

| Aspek | Differential drive | **Ackermann** |
|---|---|---|
| Berputar di tempat | Bisa | **Tidak bisa** |
| Radius putar minimum | 0 | Ditentukan mekanik |
| Recovery `spin` | Dapat digunakan | **Harus dinonaktifkan** |
| Gerak menyamping | Tidak bisa | Tidak bisa |

Sebagian besar contoh konfigurasi Nav2 di internet ditujukan untuk differential
drive. Menyalinnya begitu saja akan menghasilkan lintasan yang **mustahil
diikuti** oleh robot ini.

### 6.2 Planner

```yaml
planner_server:
  ros__parameters:
    GridBased:
      plugin: nav2_smac_planner/SmacPlannerHybrid
      minimum_turning_radius: 0.55        # ⚠️ WAJIB diukur di robot fisik
      motion_model_for_search: REEDS_SHEPP # memungkinkan maju + mundur
      angle_quantization_bins: 72
      smooth_path: true
```

**`SmacPlannerHybrid`** dipilih karena mempertimbangkan batasan kinematik
kendaraan, tidak sekadar mencari jalur terpendek.

**`REEDS_SHEPP`** memungkinkan manuver mundur (seperti parkir paralel).
Alternatifnya `DUBIN` bila robot hanya boleh bergerak maju.

### 6.3 Controller

```yaml
FollowPath:
  plugin: nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController
  desired_linear_vel: 0.3
  lookahead_dist: 0.6
  use_rotate_to_heading: false        # WAJIB false untuk Ackermann
  allow_reversing: true
  regulated_linear_scaling_min_radius: 0.5
```

`use_rotate_to_heading: false` bersifat **wajib** — bila `true`, controller akan
meminta robot berputar di tempat, yang secara mekanik tidak mungkin dilakukan.

### 6.4 Recovery behavior

```yaml
behavior_server:
  ros__parameters:
    behavior_plugins: [backup, wait]    # TIDAK ADA spin
```

Perilaku `spin` harus dihilangkan sepenuhnya. Bila tetap ada, robot akan
tersangkut selamanya saat mencoba manuver yang tidak dapat dilakukannya.

### 6.5 Costmap

```yaml
footprint: [[0.25, -0.20], [0.25, 0.20], [-0.25, 0.20], [-0.25, -0.20]]
inflation_layer:
  inflation_radius: 0.10      # bantalan tambahan di luar footprint
  cost_scaling_factor: 5.0
```

**Cara kerja:** Nav2 memperlakukan robot sebagai satu titik, lalu "menebalkan"
seluruh rintangan sebesar ukuran robot ditambah bantalan. Jarak aman total =
setengah lebar robot + `inflation_radius`.

⚠️ Nilai `footprint` di atas masih perkiraan — **wajib diukur** pada robot fisik.

---

## 7. Menjalankan Navigasi Otonom

```bash
# Terminal 1 — sensor
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 — lokalisasi
ros2 launch amr_3d_mapping rtabmap_localization.launch.py

# Terminal 3 — Nav2
ros2 launch amr_slam nav2.launch.py

# Terminal 4 — RViz
rviz2
```

Memberi target: klik **`2D Goal Pose`** di RViz, lalu klik titik tujuan.

Memeriksa status Nav2:
```bash
ros2 lifecycle list controller_server    # harus: active
ros2 lifecycle list planner_server       # harus: active
ros2 topic echo /plan                    # lintasan yang direncanakan
```

---

## 8. Penyetelan Parameter

| Gejala | Kemungkinan penyebab | Perbaikan |
|---|---|---|
| Lintasan berbelit / zig-zag | `minimum_turning_radius` terlalu besar | Ukur radius putar sebenarnya |
| Robot menabrak dinding | `inflation_radius` terlalu kecil | Perbesar bantalan |
| Robot tidak mau lewat lorong sempit | `inflation_radius` terlalu besar | Perkecil bantalan |
| Robot tersangkut, berusaha berputar | `spin` masih aktif | Hapus dari `behavior_plugins` |
| Robot bergerak terlalu cepat | `desired_linear_vel` terlalu tinggi | Kurangi nilainya |

**Prinsip penyetelan:** ubah **satu parameter** dalam satu waktu, lalu uji.
Mengubah beberapa parameter sekaligus membuat penyebab perubahan perilaku tidak
dapat diketahui.

---

**Lanjut:** [06_FAILOVER_GUIDE.md](06_FAILOVER_GUIDE.md) untuk sistem
keselamatan.
