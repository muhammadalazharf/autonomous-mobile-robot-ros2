# Kontribusi — Muhammad Al Azhar Faradis

**NRP:** 2040241017 · Teknologi Rekayasa Otomasi, ITS Surabaya
**Proyek:** Autonomous Mobile Robot (Ackermann) — ROS 2 Humble
**Periode:** Juni – Juli 2026

> Dokumen ini merinci peran dan kegiatan teknis saya pada proyek AMR, mulai dari
> penyiapan lingkungan kerja, pembuatan node ROS 2, perancangan komunikasi
> publisher–subscriber, pengujian di perangkat keras, hingga proses debugging dan
> iterasi perbaikan. Seluruh angka dan gejala error yang disebutkan berasal dari
> catatan sesi kerja di robot, bukan estimasi.

---

## 1. Setup & Instalasi Dependensi

### 1.1 Penyiapan lingkungan kerja

Menyiapkan workspace ROS 2 dari nol pada komputer onboard **Intel NUC13**
(Ubuntu 22.04, ROS 2 Humble), termasuk migrasi kode dari laptop pengembangan.

**Kegiatan:**
- Transfer kode workspace dari laptop ke NUC (via flashdisk dan repositori Git).
- Konfigurasi autentikasi Git — mengatasi kegagalan `git push` via HTTPS
  (GitHub tidak lagi menerima password) dengan membuat **SSH key ed25519** dan
  mendaftarkannya ke akun GitHub, lalu mengganti remote HTTPS → SSH.
- **Backup workspace lama** sebelum deploy versi baru, agar pekerjaan
  sebelumnya tidak hilang:
  ```bash
  mkdir -p ~/WORKSPACE_1
  mv ~/amr_starter ~/amr_underlay_ws ~/rtabmap_vio_pkg ~/WORKSPACE_1/
  zip -r ~/WORKSPACE_1.zip ~/WORKSPACE_1     # hasil: arsip 11 MB
  ```
- Menyiapkan akses remote ke robot: **SSH via Tailscale** (IP tetap, tembus
  CGNAT kampus) dan **NoMachine** untuk akses grafis (RViz2).

### 1.2 Otomatisasi instalasi (`deploy.bash`)

Menyusun dan menjalankan skrip deployment **7 tahap** agar proses pemasangan
dapat diulang (*reproducible*) dan tidak bergantung pada ingatan:

| Tahap | Kegiatan |
|---|---|
| 0 | Verifikasi prasyarat (ROS 2 Humble terpasang, seluruh package tersedia) |
| 1 | Instalasi dependensi sistem via `apt` |
| 2 | Resolusi dependensi ROS via `rosdep` |
| 3 | Pembersihan artefak build lama (`build/`, `install/`, `log/`) |
| 4 | Build package **satu per satu** dengan `--symlink-install` |
| 5 | Konfigurasi **udev rules** untuk penamaan device yang konsisten |
| 6 | Konfigurasi `.bashrc` (auto-source) dan pembuatan folder data |
| 7 | Verifikasi akhir — memastikan seluruh package terdeteksi ROS 2 |

**Dependensi yang dipasang:**
```
ros-humble-rtabmap-ros            ros-humble-navigation2
ros-humble-nav2-bringup           ros-humble-robot-localization
ros-humble-rplidar-ros            ros-humble-realsense2-camera
ros-humble-realsense2-description ros-humble-depthimage-to-laserscan
ros-humble-robot-state-publisher  ros-humble-joint-state-publisher
ros-humble-xacro                  ros-humble-diagnostic-msgs
ros-humble-tf2-tools              python3-colcon-common-extensions
python3-rosdep
```

**Alasan build per-package** (`--packages-select`), bukan sekaligus: bila terjadi
kegagalan kompilasi, penyebabnya langsung terlihat pada package mana, sehingga
proses debugging jauh lebih cepat.

### 1.3 Konfigurasi udev — mengatasi port yang berpindah

**Masalah:** penamaan device Linux (`/dev/ttyUSB0`, `/dev/ttyUSB1`) berubah-ubah
tergantung urutan colok, sehingga konfigurasi sensor sering gagal terbaca.

**Solusi:** membuat aturan udev berbasis Vendor/Product ID agar setiap perangkat
memperoleh nama tetap:
```bash
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="stm32"
```
Hasil: LiDAR selalu berada di `/dev/rplidar` dan mikrokontroler di `/dev/stm32`,
terlepas dari urutan pemasangan kabel.

---

## 2. Pembuatan Node ROS 2

Merancang dan mengimplementasikan node-node berikut (Python dan C++):

| Node | Bahasa | Fungsi |
|---|---|---|
| `health_check_node` | Python | Memantau 5 sensor, melaporkan status PASS/FAIL tiap 2 detik |
| `imu_merger_node` | Python | Menggabungkan data accelerometer + gyroscope D455 menjadi satu pesan IMU |
| `lidar_xy_node` | Python | Konversi data LiDAR polar → kartesian, visualisasi RViz2, perekaman CSV |
| `integration_check_node` | Python | Verifikasi kompatibilitas QoS, frekuensi, dan latensi antar-node |
| `encoder_odom_node` | Python | Konversi pulsa encoder menjadi pesan Odometry |
| `brain_node` | Python | Finite State Machine koordinator perilaku robot |
| `stm32_bridge` | C++ | Jembatan serial ke mikrokontroler: kendali motor, kemudi, umpan balik encoder |

### 2.1 `imu_merger_node` — menyatukan dua aliran data

Kamera RealSense D455 memublikasikan accelerometer (100 Hz) dan gyroscope
(200 Hz) sebagai **dua topic terpisah**, sedangkan algoritma odometri
membutuhkan satu pesan IMU utuh.

Solusi: menggunakan `ApproximateTimeSynchronizer` untuk memasangkan kedua aliran
berdasarkan kedekatan *timestamp*, lalu menerbitkannya sebagai `sensor_msgs/Imu`.
Nilai `orientation_covariance[0] = -1.0` diisi secara eksplisit untuk menyatakan
bahwa sensor tidak menyediakan data orientasi absolut (tidak ada AHRS) — agar
node hilir tidak salah menafsirkan data.

### 2.2 `lidar_xy_node` — mengubah sudut menjadi koordinat

Node ini dibuat atas permintaan dosen untuk membuktikan pemahaman terhadap cara
kerja LiDAR. Data mentah LiDAR berbentuk **polar** (sudut, jarak); node
mengubahnya menjadi **kartesian**:

```
x = jarak × cos(sudut)
y = jarak × sin(sudut)
```

Keluaran: `MarkerArray` untuk RViz2 (berwarna sesuai jarak — merah dekat, hijau
jauh) dan berkas CSV berkolom
`scan_id, beam_index, sudut_rad, sudut_deg, jarak_m, x_m, y_m` untuk analisis.

### 2.3 `health_check_node` — membuat kegagalan menjadi terlihat

Node ini dibuat karena pengalaman pada sistem sebelumnya: **sensor dapat terputus
tanpa memunculkan pesan error apa pun**. Node berlangganan kelima topic sensor
dan mencetak status PASS/FAIL beserta frekuensi setiap 2 detik, sehingga
kegagalan yang semula senyap menjadi kasatmata sejak awal.

### 2.4 `brain_node` — koordinasi perilaku (FSM)

Finite State Machine dengan lima keadaan:
`IDLE → MAPPING → NAVIGATING → STUCK → ERROR`, lengkap dengan aturan transisi:
sensor kritis mati → `ERROR` (motor dihentikan); robot tidak bergerak selama
15 detik → `STUCK` (manuver mundur otomatis); pemulihan gagal 3× → `ERROR`.

---

## 3. Perancangan Publisher–Subscriber & Kontrak QoS

### 3.1 Kontrak QoS

Kegagalan terbesar pada sistem sebelumnya adalah **QoS mismatch**: publisher
mengirim dengan `BestEffort`, subscriber meminta `Reliable`. Dalam ROS 2, kondisi
ini **tidak menimbulkan error** — koneksi hanya diam-diam tidak terbentuk.

Untuk menutup celah tersebut, saya menetapkan satu kontrak QoS yang berlaku
menyeluruh:

| Topic | QoS | Alasan |
|---|---|---|
| `/scan` (LiDAR) | BestEffort | Frekuensi tinggi; data terbaru lebih penting daripada data lengkap |
| `/camera/*/color/image_raw` | BestEffort | 30 fps; kehilangan satu frame tidak fatal |
| `/camera/*/depth/image_rect_raw` | BestEffort | Sama seperti color |
| `/imu/data` | BestEffort | 100–200 Hz |
| `/encoder` | BestEffort | Frekuensi tinggi |
| `/cmd_vel` | **Reliable** | Perintah gerak bersifat kritis — tidak boleh hilang |

Analogi yang saya gunakan untuk menjelaskan konsep ini: *BestEffort* seperti
berteriak (tidak peduli apakah terdengar), *Reliable* seperti menelepon
(memastikan lawan bicara menerima).

### 3.2 Peta publisher & subscriber

**Subscriber:** `/scan`, `/camera/*/color/image_raw`,
`/camera/*/depth/image_rect_raw`, `/camera/*/accel/sample`,
`/camera/*/gyro/sample`, `/imu/data`, `/encoder`, `/joy`, `/cmd_vel`,
`/odometry/filtered`, `/navigate_to_pose/_action/status`

**Publisher:** `/imu/data`, `/encoder`, `/encoder_odom`, `/health_check`,
`/brain/state`, `/brain/status`, `/cmd_vel`, `visualization_marker_array`

### 3.3 Protokol komunikasi serial (NUC ↔ STM32)

Protokol ASCII sederhana melalui USB CDC:
```
TX (NUC → STM32):  "V:{pwm},S:{sudut}\n"     pwm negatif = mundur
RX (STM32 → NUC):  "E:{delta}\n"             delta pulsa encoder
```
Parameter aktual: `MAX_PWM = 4000`, `MAX_STEER = 45°`, `STEER_TRIM = -5°`,
baud rate `115200`, wheelbase `0.5 m`.

---

## 4. Pengujian & Verifikasi di Perangkat Keras

### 4.1 Strategi pengujian berlapis

Pengujian dilakukan **bertahap dari lapisan terbawah**, karena setiap lapisan
bergantung pada lapisan di bawahnya. Menguji navigasi sementara sensor belum
terverifikasi hanya akan menghasilkan kebingungan.

| Tahap | Yang diuji | Kriteria lulus |
|---|---|---|
| 1 | Sensor | 5/5 PASS, frekuensi di atas ambang minimum |
| 2 | Estimasi pose | `/odometry/filtered` aktif, TF `odom → base_footprint` benar |
| 3 | Pemetaan | `/rgbd_image` > 0 Hz, loop closure terpicu |
| 4 | Navigasi | Lintasan wajar, robot mencapai target |
| 5 | Perilaku | Transisi FSM sesuai rancangan |

### 4.2 Hasil verifikasi Lapisan 1 (Sensor)

| Sensor | Topic | Frekuensi | Status |
|---|---|---|---|
| RPLIDAR C1 | `/scan` | 10 Hz | ✅ PASS |
| Kamera Color | `/camera/camera/color/image_raw` | 17–27 Hz | ✅ PASS |
| Kamera Depth | `/camera/camera/depth/image_rect_raw` | 20–30 Hz | ✅ PASS |
| IMU (hasil merge) | `/imu/data` | 100 Hz | ✅ PASS |
| Encoder | `/encoder` | 20 Hz | ✅ PASS |
| Joystick | `/joy` | variabel | ✅ PASS |

### 4.3 Hasil verifikasi Lapisan 2 (Estimasi Pose)

`/odometry/filtered` terbit pada **~45 Hz**, TF `odom → base_footprint`
terverifikasi benar melalui `ros2 run tf2_tools view_frames`.

### 4.4 Perintah verifikasi yang digunakan

```bash
ros2 topic hz /scan                  # memastikan frekuensi sensor
ros2 topic echo /health_check        # status keseluruhan sensor
ros2 topic info /encoder --verbose   # memeriksa profil QoS
ros2 param get /camera/camera rgb_camera.color_profile   # verifikasi parameter aktif
ros2 run tf2_tools view_frames       # memeriksa struktur TF tree
ros2 run amr_sensors integration_check   # verifikasi QoS, frekuensi, latensi
```

### 4.5 Pengambilan & analisis data LiDAR

Merekam dan menganalisis data LiDAR untuk mengukur kualitas sensor:

| Parameter | Nilai |
|---|---|
| Total data | 92.743 beam |
| Jumlah scan | 190 putaran |
| Rentang jarak | 0,15 – 11,52 m |
| **Standar deviasi (permukaan stabil)** | **1,6 – 4,5 mm** |
| Presisi relatif terbaik | 0,06 % |
| Spesifikasi pabrikan | ± 30 mm |

Kesimpulan: presisi sensor berada **jauh di dalam** spesifikasi pabrikan.

Saya juga merancang dua protokol validasi lanjutan:
- **Uji sumbu LiDAR** — menempatkan objek pada posisi terukur (depan/kiri/kanan/
  belakang) untuk membuktikan arah sumbu X dan Y secara fisik, bukan asumsi.
- **Uji ATE (Absolute Trajectory Error)** — membandingkan posisi hasil SLAM
  dengan pengukuran meteran sebagai *ground truth*.

---

## 5. Debugging

Enam permasalahan yang berhasil ditemukan akar penyebabnya dan diperbaiki:

### Masalah 1 — Encoder tidak terbaca (0 Hz)

| Aspek | Keterangan |
|---|---|
| **Gejala** | Health check menunjukkan 4/5 sensor PASS; encoder FAIL |
| **Penelusuran** | `ros2 topic info /encoder` → "Unknown topic"; `ls /dev/stm32` → perangkat fisik **terdeteksi** |
| **Akar masalah** | Package `amr_motor` masih berupa kerangka kosong — belum ada node yang memublikasikan `/encoder` |
| **Perbaikan** | Mengintegrasikan `stm32_bridge.cpp` (C++) yang sudah terbukti berjalan di perangkat keras |
| **Hasil** | Encoder PASS 20 Hz → **Lapisan 1 lengkap 5/5** |

### Masalah 2 — Resolusi kamera tidak sesuai (1280×720, seharusnya 848×480)

| Aspek | Keterangan |
|---|---|
| **Gejala** | `ros2 topic echo` menampilkan `height: 720, width: 1280` |
| **Penelusuran** | `ros2 param get` menunjukkan nilai **default driver**, bukan nilai dari berkas YAML |
| **Akar masalah** | Parameter pada `sensors.yaml` tidak terbaca oleh node RealSense (masalah pencocokan namespace) |
| **Perbaikan** | Menambahkan override parameter langsung pada launch file |
| **Hasil** | Resolusi menjadi 848×480 sesuai spesifikasi |

### Masalah 3 — `PermissionError` saat merekam data LiDAR

| Aspek | Keterangan |
|---|---|
| **Gejala** | `PermissionError: [Errno 13] Permission denied: '/home/azhar'` |
| **Akar masalah** | Path direktori di-*hardcode* mengikuti nama pengguna **laptop**, sedangkan pengguna di NUC berbeda |
| **Perbaikan** | Mengganti ke path relatif `~/lidar_data` disertai `os.path.expanduser()` |

### Masalah 4 — Berkas CSV LiDAR kosong

| Aspek | Keterangan |
|---|---|
| **Gejala** | Berkas CSV terbentuk, tetapi tidak berisi data |
| **Akar masalah** | Filter `scan_count % 10` membuang hampir seluruh data, dan buffer tidak pernah di-*flush* ke disk |
| **Perbaikan** | Menghapus filter, menambahkan `flush()` setiap scan, serta blok `try/finally` agar berkas tetap tertutup rapi saat program dihentikan |
| **Hasil** | Terekam 92.743 baris data valid |

### Masalah 5 — Joystick tidak berfungsi

| Aspek | Keterangan |
|---|---|
| **Gejala** | `ros2 topic echo /joy` tidak menghasilkan keluaran apa pun |
| **Akar masalah** | `joy_node` tidak pernah disertakan pada launch file mana pun |
| **Perbaikan** | Menambahkan `joy_node` ke `motor.launch.py` dengan device `/dev/input/js0` |

### Masalah 6 — Komputer mati saat motor bergerak mundur ⭐

Ini permasalahan tersulit dan paling menarik pada proyek ini.

**Gejala:** NUC mati total (saat memakai baterai) atau seluruh koneksi Wi-Fi dan
Bluetooth terputus bersamaan (saat memakai PSU) — **hanya ketika motor
diperintahkan mundur.**

**Matriks pengujian yang saya susun untuk mengisolasi penyebab:**

| Kondisi pengujian | Hasil |
|---|---|
| PWM negatif, kabel motor **dilepas** | NUC aman |
| PWM negatif, kabel motor **tersambung**, catu baterai | NUC **mati total** |
| PWM negatif, kabel motor **tersambung**, catu PSU 25 V | NUC hidup, tetapi Wi-Fi + Bluetooth **putus bersamaan** |
| Transisi maju → mundur mendadak | Putus tepat pada saat perubahan arah |

**Akar masalah — *motor plugging*:** ketika PWM berubah mendadak dari maju ke
mundur, motor yang masih berputar menghasilkan *back-EMF* yang berlawanan dengan
tegangan baru. Keduanya bertumpuk dan menimbulkan lonjakan arus sekitar dua kali
lipat. Lonjakan tersebut memunculkan **transien EMI** pada jalur daya yang
dipakai bersama oleh NUC dan motor.

**Petunjuk kunci:** SSH, NoMachine, dan Bluetooth terputus **pada saat yang sama
persis**. Ketiganya bergantung pada satu chip — Intel AX211, yang menempatkan
Wi-Fi dan Bluetooth dalam satu paket. Ini menunjukkan persoalan berada pada ranah
kelistrikan/RF, bukan perangkat lunak.

**Mitigasi perangkat lunak yang diterapkan:**
1. **Slew-rate limiter** — membatasi perubahan PWM maksimum 250 per pesan,
   sehingga transisi maju → mundur melewati nol secara bertahap.
2. **Watchdog `/joy`** — menghentikan motor bila data joystick hilang.
3. **Menonaktifkan `autorepeat_rate`** — lihat bagian 6.3.

**Kejujuran hasil:** ketiga mitigasi mengurangi frekuensi kejadian, tetapi
**belum menghilangkannya sepenuhnya**. Solusi tuntas berada di ranah perangkat
keras: pemasangan ferrite bead, kapasitor decoupling, dan pemisahan jalur daya
antara komputasi dan motor. Hal ini telah saya dokumentasikan sebagai pekerjaan
lanjutan.

---

## 6. Trial and Error (Iterasi Perbaikan)

Beberapa perbaikan tidak berhasil pada percobaan pertama. Bagian ini mencatat
iterasi tersebut secara terbuka, karena justru di sinilah proses belajar terjadi.

### 6.1 Jembatan STM32: Python → C++

| Iterasi | Tindakan | Hasil |
|---|---|---|
| 1 | Menulis ulang `stm32_bridge` dalam Python berdasarkan perkiraan protokol | **Ditolak** — parameter (port serial, `MAX_PWM`) hanya asumsi, bukan data aktual |
| 2 | Mengambil `stm32_bridge.cpp` yang **sudah terbukti berjalan** di perangkat keras | **Berhasil** — encoder aktif 20 Hz |

**Pelajaran:** kode yang sudah terverifikasi pada perangkat keras lebih berharga
daripada kode baru yang ditulis berdasarkan asumsi. Parameter seperti
`MAX_PWM = 4000` dan `STEER_TRIM = -5` mustahil ditebak dengan benar.

### 6.2 Parameter RealSense: dua kali percobaan

| Iterasi | Tindakan | Hasil |
|---|---|---|
| 1 | Mengubah nama parameter `rgb_camera.color_profile` → `rgb_camera.profile` | **Gagal** — driver memang mengharapkan nama dengan awalan `color_` |
| 2 | Mengembalikan nama semula, lalu menambahkan override pada launch file | **Berhasil** — resolusi 848×480 tercapai |

**Pelajaran:** memverifikasi nama parameter melalui dokumentasi resmi lebih cepat
daripada menebak. Perbaikan yang keliru menghabiskan waktu dua kali lipat.

### 6.3 Watchdog yang tidak pernah aktif

Setelah watchdog `/joy` dipasang, motor **tetap** berjalan ketika Bluetooth
terputus. Penelusuran menemukan penyebabnya: parameter `autorepeat_rate: 20.0`
pada `joy_node` membuat node terus mengulang pesan terakhir walaupun perangkat
sudah terputus — sehingga watchdog tidak pernah mendeteksi hilangnya data.

**Perbaikan:** menetapkan `autorepeat_rate: 0.0`.

**Pelajaran:** sebuah mekanisme pengaman dapat dilumpuhkan oleh konfigurasi lain
yang tampak tidak berhubungan. Fitur keselamatan harus **diuji dalam kondisi
gagal yang sesungguhnya** — dalam hal ini, benar-benar memutus koneksi Bluetooth,
bukan sekadar mengasumsikan watchdog bekerja.

### 6.4 Slew limiter: berhasil sebagian

Log menunjukkan pembatas laju bekerja sebagaimana dirancang
(`V:0 → 250 → 500 → … → 4000 → … → 0 → -250 → … → -4000`), namun gangguan
koneksi **masih terjadi**. Transien EMI ternyata tetap cukup kuat meskipun
perubahan PWM sudah dilandaikan.

**Pelajaran:** tidak semua persoalan perangkat keras dapat diselesaikan dari sisi
perangkat lunak. Mengetahui **batas** suatu pendekatan sama pentingnya dengan
mengetahui cara menerapkannya.

---

## 7. Ringkasan Keterampilan

| Bidang | Penerapan konkret |
|---|---|
| **ROS 2** | Node, topic, QoS, TF, launch file, parameter, lifecycle |
| **Python** | 6 node (sensor, odometri, FSM, perkakas analisis) |
| **C++** | Jembatan serial STM32, watchdog, slew limiter |
| **Linux** | udev rules, systemd, SSH, izin akses, manajemen paket |
| **Git** | Autentikasi SSH, branching, penelusuran riwayat commit |
| **Debugging** | Isolasi akar masalah melalui matriks pengujian terkontrol |
| **Elektronika** | Analisis *back-EMF*, transien EMI, integritas jalur daya |
| **Analisis data** | Statistik presisi sensor, perancangan protokol validasi |
| **Dokumentasi** | Handover teknis, SOP, panduan deployment |

---

## 8. Refleksi

Pelajaran terpenting dari proyek ini: **kegagalan yang paling berbahaya adalah
kegagalan yang senyap.** Ketidaksesuaian QoS tidak memunculkan pesan error
apa pun — sistem tampak berjalan normal, padahal sensor sama sekali tidak
terhubung. Sejak menyadari hal tersebut, saya menjadikan *verifikasi* sebagai
bagian tak terpisahkan dari sistem, bukan sekadar langkah tambahan di akhir:
health check, pemeriksaan frekuensi, dan pengujian integrasi dijalankan sebagai
komponen yang berdiri sendiri.

Pelajaran kedua datang dari kasus *motor plugging*: **debugging yang baik
bertumpu pada bukti, bukan tebakan.** Penyebabnya ditemukan bukan dengan mencoba
perbaikan secara acak, melainkan dengan menyusun matriks pengujian terkontrol —
melepas kabel motor, mengganti sumber daya, dan mengamati pola kejadiannya.
Fakta bahwa SSH, NoMachine, dan Bluetooth terputus pada saat yang sama persis
menjadi petunjuk yang mengarahkan pada satu chip bersama, dan dari sana pada
persoalan kelistrikan.

---

*Muhammad Al Azhar Faradis — Teknologi Rekayasa Otomasi, Institut Teknologi
Sepuluh Nopember (ITS), Surabaya.*
