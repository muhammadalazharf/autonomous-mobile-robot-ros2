# 07 — Pemecahan Masalah

Kumpulan masalah yang **benar-benar terjadi** pada proyek ini, lengkap dengan
gejala, cara penelusuran, akar masalah, dan perbaikannya.

---

## 0. Metode Penelusuran

Sebelum mengubah apa pun, kumpulkan bukti terlebih dahulu:

```bash
ros2 node list                    # node mana yang berjalan?
ros2 topic list                   # topic mana yang tersedia?
ros2 topic hz <topic>             # apakah data mengalir? berapa cepat?
ros2 topic info <topic> --verbose # bagaimana profil QoS-nya?
ros2 param get <node> <param>     # nilai parameter apa yang benar-benar aktif?
ros2 run tf2_tools view_frames    # apakah rantai TF lengkap?
```

**Prinsip:** periksa **dari lapisan terbawah**. Kegagalan sensor selalu merambat
ke atas — memperbaiki navigasi sementara sensor bermasalah hanya membuang waktu.

---

## 1. Sensor Tidak Terhubung, Tanpa Pesan Error

### Gejala
Node berjalan normal, tidak ada pesan error, tetapi data tidak pernah sampai ke
node tujuan.

### Penyebab
**QoS mismatch** — publisher menggunakan `BestEffort`, subscriber meminta
`Reliable`. Dalam ROS 2, ketidakcocokan ini **tidak menimbulkan error**; koneksi
hanya diam-diam tidak terbentuk.

### Penelusuran
```bash
ros2 topic info /scan --verbose
```
Bandingkan bagian *Reliability* antara publisher dan subscriber.

### Perbaikan
Samakan profil QoS. Untuk seluruh sensor gunakan `BEST_EFFORT`:

```python
SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)
```

> Ini adalah jenis kegagalan paling berbahaya pada proyek ini — tidak terlihat
> sampai seseorang secara khusus memeriksanya.

---

## 2. Encoder Tidak Terbaca (0 Hz)

### Gejala
Health check menunjukkan 4/5 sensor PASS; encoder FAIL.

### Penelusuran
```bash
ros2 topic info /encoder     # hasil: "Unknown topic"
ls -l /dev/stm32             # hasil: perangkat fisik TERDETEKSI
```
Perangkat keras terpasang, tetapi tidak ada node yang menerbitkan data.

### Akar masalah
Package `amr_motor` masih berupa kerangka kosong — hanya berisi `CMakeLists.txt`
dan `package.xml`, tanpa node.

### Perbaikan
Mengintegrasikan `stm32_bridge.cpp` yang **sudah terbukti berjalan** di
perangkat keras.

**Pelajaran:** kode yang sudah terverifikasi pada perangkat keras jauh lebih
berharga daripada kode baru berdasarkan asumsi. Parameter seperti
`MAX_PWM = 4000` mustahil ditebak dengan benar.

---

## 3. Resolusi Kamera Tidak Sesuai

### Gejala
```bash
ros2 topic echo /camera/camera/color/image_raw --once | grep -E "height|width"
# height: 720, width: 1280   ← seharusnya 848×480
```

### Penelusuran
```bash
ros2 param get /camera/camera rgb_camera.color_profile
# hasil: 1280x720x30   ← nilai bawaan driver, bukan dari berkas YAML
```

### Akar masalah
Parameter pada `sensors.yaml` **tidak terbaca** oleh node RealSense karena
persoalan pencocokan namespace.

### Perbaikan
Menambahkan override parameter langsung pada launch file:

```python
parameters=[config, {
    'rgb_camera.color_profile': '848x480x30',
    'depth_module.depth_profile': '848x480x30',
}]
```

**Pelajaran:** parameter yang tertulis di berkas YAML belum tentu benar-benar
diterapkan. **Selalu verifikasi dengan `ros2 param get`.**

---

## 4. `PermissionError` Saat Merekam Data

### Gejala
```
PermissionError: [Errno 13] Permission denied: '/home/azhar'
```

### Akar masalah
Path direktori di-*hardcode* mengikuti nama pengguna di **laptop**, sedangkan
nama pengguna di NUC berbeda.

### Perbaikan
```python
import os
record_dir = os.path.expanduser('~/lidar_data')   # portabel di semua komputer
```

**Pelajaran:** jangan pernah menuliskan path absolut berisi nama pengguna.
Gunakan `~` disertai `os.path.expanduser()`.

---

## 5. Berkas CSV Terbentuk Tetapi Kosong

### Gejala
Berkas CSV ada, ukurannya 0 byte atau hanya berisi baris header.

### Akar masalah
Dua persoalan sekaligus:
1. Filter `scan_count % 10` membuang hampir seluruh data.
2. Buffer tidak pernah di-*flush* ke disk, sehingga data hilang saat program
   dihentikan.

### Perbaikan
```python
writer.writerow(row)
file.flush()          # tulis ke disk segera

try:
    # ... proses perekaman ...
finally:
    file.close()      # pastikan berkas tertutup rapi
```

**Hasil:** terekam 92.743 baris data valid.

---

## 6. Joystick Tidak Berfungsi

### Gejala
```bash
ros2 topic echo /joy     # tidak ada keluaran sama sekali
```

### Penelusuran
```bash
ls /dev/input/js*        # perangkat terdeteksi
ros2 node list | grep joy # joy_node TIDAK ADA dalam daftar
```

### Akar masalah
`joy_node` tidak pernah disertakan pada launch file mana pun.

### Perbaikan
Menambahkan `joy_node` ke launch file:

```python
Node(
    package='joy',
    executable='joy_node',
    parameters=[{'dev': '/dev/input/js0', 'autorepeat_rate': 0.0}],
)
```

**Pelajaran:** perangkat keras terdeteksi ≠ node berjalan. Periksa keduanya.

---

## 7. NUC Mati Saat Motor Mundur ⭐

Masalah tersulit pada proyek ini.

### Gejala
NUC mati total (saat memakai baterai) atau seluruh koneksi Wi-Fi dan Bluetooth
terputus bersamaan (saat memakai PSU) — **hanya ketika motor mundur.**

### Matriks pengujian
| Kondisi | Hasil |
|---|---|
| PWM negatif, kabel motor **dilepas** | NUC aman |
| PWM negatif, kabel motor **tersambung**, baterai | NUC **mati total** |
| PWM negatif, kabel motor **tersambung**, PSU 25 V | NUC hidup, Wi-Fi + BT **putus** |
| Transisi maju → mundur mendadak | Putus tepat saat perubahan arah |

### Akar masalah — *motor plugging*
Ketika PWM berubah mendadak dari maju ke mundur, motor yang masih berputar
menghasilkan *back-EMF* berlawanan arah dengan tegangan baru. Keduanya
bertumpuk sehingga arus melonjak sekitar dua kali lipat, menimbulkan **transien
EMI** yang me-*reset* chip Intel AX211 (Wi-Fi + Bluetooth dalam satu paket).

**Petunjuk kunci:** SSH, NoMachine, dan Bluetooth terputus **pada saat yang sama
persis** → ketiganya bergantung pada satu chip → persoalan kelistrikan, bukan
perangkat lunak.

### Mitigasi perangkat lunak
1. Slew-rate limiter (`MAX_PWM_STEP = 250`)
2. Watchdog `/joy`
3. `autorepeat_rate: 0.0`

**Hasil:** frekuensi kejadian berkurang, **belum hilang sepenuhnya**.

### Solusi tuntas (perangkat keras)
Pisahkan jalur daya NUC dan motor · pasang ferrite bead · tambahkan kapasitor
decoupling · turunkan `MAX_PWM`.

### Cara aman mengoperasikan sementara
Gunakan joystick melalui kabel USB · SSH melalui Ethernet · jalankan pelan.

---

## 8. RTAB-Map Tidak Menghasilkan Peta

### Gejala
Node berjalan, tetapi peta tidak terbentuk dan loop closure tidak pernah terpicu.

### Penelusuran
```bash
ros2 topic hz /rgbd_image      # bila 0 Hz → citra tidak sampai
ros2 run tf2_tools view_frames # apakah rantai TF lengkap?
```

### Kemungkinan penyebab

| Penyebab | Perbaikan |
|---|---|
| QoS `rgbd_sync` salah | Setel `qos: 1` dan `qos_image: 1` (BestEffort) |
| TF tree tidak lengkap | Pastikan `base_footprint → camera_link` dan `→ laser_frame` tersedia |
| RealSense `publish_tf: false` | Ubah menjadi `true` |
| Dinding polos tanpa tekstur | Tempelkan poster atau objek bercorak |

---

## 9. Loop Closure Tidak Pernah Terpicu

### Gejala
```bash
ros2 topic echo /rtabmap/info --field loop_closure_id
# selalu bernilai 0
```

### Penyebab & perbaikan

| Penyebab | Perbaikan |
|---|---|
| Citra tidak sampai (QoS) | Verifikasi `/rgbd_image` > 0 Hz |
| Robot tidak kembali ke titik awal | Rencanakan lintasan yang membentuk lingkaran tertutup |
| Ruangan terlalu monoton | Tambahkan objek visual yang khas |
| Berjalan terlalu cepat | Perlambat gerakan, hindari citra kabur |

---

## 10. Lintasan Navigasi Berbelit

### Gejala
Robot mencapai tujuan, tetapi melalui lintasan berkelok yang tidak masuk akal.

### Penyebab & perbaikan

| Penyebab | Perbaikan |
|---|---|
| `minimum_turning_radius` terlalu besar | Ukur radius putar sebenarnya |
| `inflation_radius` terlalu besar | Kurangi bantalan |
| `use_rotate_to_heading: true` | Ubah menjadi `false` |
| Recovery `spin` masih aktif | Hapus dari `behavior_plugins` |

---

## 11. RViz2 Gagal Berjalan melalui Remote

### Gejala
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

### Penyebab
NoMachine tidak meneruskan tampilan X11 dengan benar.

### Solusi
Jalankan RViz2 langsung dari layar yang terhubung ke NUC, atau jalankan node
tanpa visualisasi:

```bash
ros2 run amr_sensors lidar_xy --ros-args -p record:=true
```

---

## 12. Node Tidak Ditemukan Setelah Build

### Gejala
```
Package 'nama_package' not found
```

### Solusi
```bash
source ~/amr_ws/install/setup.bash     # sering terlupakan

# Bila masih gagal, lakukan build bersih:
rm -rf build/ install/ log/
colcon build --symlink-install
```

---

## Ringkasan Diagnosis Cepat

| Gejala | Periksa pertama |
|---|---|
| Data tidak sampai, tanpa error | QoS (`ros2 topic info --verbose`) |
| Topic tidak ada | Apakah node berjalan? (`ros2 node list`) |
| Parameter tidak berlaku | `ros2 param get` — verifikasi nilai aktif |
| TF error | `ros2 run tf2_tools view_frames` |
| Perilaku tidak sesuai | Apakah parameter sudah diukur, atau masih tebakan? |
| Gangguan kelistrikan | Apakah terjadi bersamaan dengan gerakan motor? |

---

## Prinsip Debugging

1. **Kumpulkan bukti sebelum mengubah apa pun.** Menebak menghabiskan waktu
   lebih banyak daripada memeriksa.
2. **Ubah satu hal dalam satu waktu.** Bila mengubah tiga hal sekaligus,
   penyebab perubahan perilaku tidak dapat diketahui.
3. **Periksa dari lapisan terbawah.** Kegagalan sensor merambat ke atas.
4. **Verifikasi, jangan berasumsi.** Berkas YAML boleh berisi apa saja —
   `ros2 param get` menunjukkan kenyataannya.
5. **Kegagalan senyap adalah yang paling berbahaya.** Tidak adanya pesan error
   bukan berarti sistem berjalan benar.
