# 03 — Panduan Perangkat Keras

Spesifikasi komponen, protokol komunikasi, konfigurasi perangkat, dan catatan
persoalan kelistrikan yang telah teridentifikasi.

---

## 1. Daftar Komponen

### 1.1 Komputasi

| Komponen | Spesifikasi |
|---|---|
| Komputer utama | Intel NUC13 (NUC13ANHi7) |
| Sistem operasi | Ubuntu 22.04 LTS |
| Middleware | ROS 2 Humble |
| Mikrokontroler | STM32F407 |
| Wi-Fi / Bluetooth | Intel AX211 (**satu chip untuk keduanya**) |

> Catatan penting: Wi-Fi dan Bluetooth berada pada **satu chip yang sama**.
> Bila keduanya terputus bersamaan, penyebabnya hampir pasti gangguan
> kelistrikan pada chip tersebut — bukan persoalan jaringan. Lihat Bagian 6.

### 1.2 Sensor

| Sensor | Model | Keluaran | Frekuensi |
|---|---|---|---|
| LiDAR | RPLIDAR C1 | `/scan` (2D, 360°) | 10 Hz |
| Kamera | Intel RealSense D455 | RGB 848×480, Depth 848×480 | ~30 fps |
| IMU | Bosch BMI055 (di dalam D455) | accel 100 Hz, gyro 200 Hz | — |
| Encoder | Terpasang pada motor | Delta pulsa | 20 Hz |

**Spesifikasi RPLIDAR C1:**

| Parameter | Nilai |
|---|---|
| Jangkauan (objek putih) | 0,05 – 12 m |
| Jangkauan (objek hitam) | 0,05 – 6 m |
| Akurasi jarak | ± 30 mm |
| Resolusi sudut | 0,72° |
| Sample rate | 5 kHz |

### 1.3 Aktuator

| Komponen | Model | Fungsi |
|---|---|---|
| Motor penggerak | PG45 (DC) | Gerak maju / mundur |
| Driver motor | BTS7960 | Pengendali daya motor |
| Servo kemudi | DS3225 | Sudut belok roda depan |

### 1.4 Mekanik

| Parameter | Nilai | Status |
|---|---|---|
| Konfigurasi kemudi | Ackermann 2WS (roda depan) | Terverifikasi |
| Wheelbase | 0,5 m | Terverifikasi |
| Sudut kemudi maksimum | 45° | Dari kode terverifikasi |
| Steering trim | −5° | Dari kode terverifikasi |
| Radius putar minimum | **belum diukur** | ⚠️ Perlu pengukuran |
| Dimensi footprint | **belum diukur** | ⚠️ Perlu pengukuran |

---

## 2. Protokol Komunikasi NUC ↔ STM32

Komunikasi menggunakan **USB CDC (serial virtual)** dengan format teks ASCII.

### 2.1 Format pesan

```
NUC → STM32 :  "V:{pwm},S:{sudut}\n"
STM32 → NUC :  "E:{delta}\n"
```

| Medan | Rentang | Keterangan |
|---|---|---|
| `V` (PWM) | −4000 … +4000 | Nilai positif = maju, negatif = mundur |
| `S` (sudut) | −45 … +45 | Sudut kemudi dalam derajat |
| `E` (delta) | bilangan bulat | Selisih pulsa encoder sejak pesan sebelumnya |

### 2.2 Parameter komunikasi

| Parameter | Nilai |
|---|---|
| Baud rate | 115200 |
| Port | `/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_*` |
| `MAX_PWM` | 4000 |
| `MAX_STEER` | 45 |
| `STEER_TRIM` | −5 |
| `MAX_PWM_STEP` | 250 (pembatas laju perubahan) |

> **Penting:** nilai `MAX_PWM = 4000`, **bukan 255**. Berkas `motor.yaml` yang
> pernah mencantumkan 255 sudah tidak sesuai dengan kode aktual.

### 2.3 Menguji komunikasi secara manual

```bash
# Memantau keluaran encoder
ros2 topic echo /encoder

# Mengirim perintah gerak (hati-hati — robot akan bergerak)
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"
```

---

## 3. Konfigurasi udev — Nama Perangkat Tetap

**Masalah:** penamaan `/dev/ttyUSB0` dan `/dev/ttyUSB1` berubah-ubah mengikuti
urutan pemasangan kabel, sehingga konfigurasi sering gagal.

**Solusi:** membuat aturan berbasis Vendor/Product ID.

```bash
sudo nano /etc/udev/rules.d/99-amr-sensors.rules
```

```
# RPLIDAR C1
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"

# STM32F407
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="stm32", MODE="0666"
```

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/rplidar /dev/stm32      # verifikasi
```

**Mencari Vendor/Product ID perangkat lain:**
```bash
lsusb
udevadm info -a -n /dev/ttyUSB0 | grep -E "idVendor|idProduct"
```

---

## 4. Sistem Catu Daya

| Komponen | Sumber |
|---|---|
| NUC | Baterai LiPo (melalui modul manajemen daya) atau PSU 25 V |
| Motor + servo | Jalur daya yang sama (**inilah sumber persoalan** — lihat Bagian 6) |
| Sensor | Daya USB dari NUC |

⚠️ **Peringatan:** NUC dan motor saat ini berbagi satu jalur daya. Lonjakan arus
dari motor dapat mengganggu kestabilan NUC.

---

## 5. Konfigurasi Kamera RealSense

Resolusi yang digunakan: **848×480 @ 30 fps** untuk RGB maupun depth.

**Alasan pemilihan resolusi ini:**
- Beban komputasi lebih ringan dibandingkan 1280×720 — penting karena RTAB-Map
  dijalankan secara *real-time*.
- Bandwidth USB lebih rendah, mengurangi risiko frame terbuang.

**Memverifikasi resolusi aktif:**
```bash
ros2 param get /camera/camera rgb_camera.color_profile
ros2 topic echo /camera/camera/color/image_raw --once | grep -E "height|width"
```

> Parameter dari berkas YAML pernah **tidak terbaca** oleh driver RealSense.
> Selalu verifikasi dengan perintah di atas, jangan berasumsi.

---

## 6. Persoalan Kelistrikan yang Teridentifikasi: *Motor Plugging*

### 6.1 Gejala

NUC mati total (saat memakai baterai), atau seluruh koneksi Wi-Fi dan Bluetooth
terputus bersamaan (saat memakai PSU) — **hanya ketika motor diperintahkan
mundur.**

### 6.2 Matriks pengujian

| Kondisi | Hasil |
|---|---|
| PWM negatif, kabel motor **dilepas** | NUC aman |
| PWM negatif, kabel motor **tersambung**, baterai | NUC **mati total** |
| PWM negatif, kabel motor **tersambung**, PSU 25 V | NUC hidup, Wi-Fi + BT **putus** |
| Transisi maju → mundur mendadak | Putus tepat saat perubahan arah |

### 6.3 Akar masalah

Ketika PWM berubah mendadak dari maju ke mundur, motor yang **masih berputar**
menghasilkan *back-EMF* yang berlawanan arah dengan tegangan baru. Keduanya
bertumpuk sehingga arus melonjak sekitar dua kali lipat. Lonjakan ini
menimbulkan **transien EMI** pada jalur daya bersama, yang kemudian me-*reset*
chip Intel AX211 (Wi-Fi + Bluetooth).

**Petunjuk kunci:** SSH, NoMachine, dan Bluetooth terputus **pada saat yang sama
persis**. Ketiganya bergantung pada satu chip — ini menunjukkan persoalan berada
pada ranah kelistrikan, bukan perangkat lunak.

### 6.4 Mitigasi perangkat lunak yang telah diterapkan

1. **Slew-rate limiter** — membatasi perubahan PWM maksimum 250 per pesan,
   sehingga transisi maju → mundur melewati nol secara bertahap.
2. **Watchdog `/joy`** — menghentikan motor bila data joystick hilang.
3. **`autorepeat_rate: 0.0`** — mencegah `joy_node` mengulang perintah terakhir
   saat koneksi terputus (tanpa ini, watchdog tidak pernah aktif).

**Hasil:** frekuensi kejadian berkurang, tetapi **belum hilang sepenuhnya**.

### 6.5 Perbaikan perangkat keras yang disarankan

| Solusi | Cara kerja |
|---|---|
| **Pisahkan jalur daya** | Baterai terpisah untuk NUC dan motor — solusi paling efektif |
| **Ferrite bead** | Meredam gangguan frekuensi tinggi pada kabel motor |
| **Kapasitor decoupling** | Menstabilkan tegangan saat terjadi lonjakan arus |
| **Turunkan `MAX_PWM`** | Membatasi arus puncak (mis. 2000, setengah kecepatan) |

### 6.6 Cara aman mengoperasikan sementara

- Gunakan **joystick melalui kabel USB** (tidak bergantung Bluetooth).
- Gunakan **SSH melalui kabel Ethernet** (tidak bergantung Wi-Fi).
- Jalankan robot dengan kecepatan rendah, hindari perubahan arah mendadak.

---

## 7. Parameter yang Masih Perlu Diukur

| Parameter | Cara pengukuran |
|---|---|
| Radius putar minimum | Belokkan penuh, jalankan hingga membentuk satu lingkaran, ukur diameter ÷ 2 |
| Dimensi footprint | Ukur panjang × lebar robot dari ujung terluar (termasuk sensor yang menonjol) |
| Pulsa per putaran (PPR) | Putar roda tepat satu putaran, catat selisih nilai `/encoder` |
| Arah tanda encoder | Dorong robot maju, pastikan nilai `/encoder` bertambah |
| Posisi sensor | Ukur jarak x, y, z dari `base_footprint` ke `camera_link` dan `laser_frame` |

**Prinsip:** jangan menebak. Parameter yang salah menghasilkan perilaku navigasi
yang salah, dan penyebabnya sangat sulit ditelusuri belakangan.

---

**Lanjut:** [05_SLAM_NAV2_GUIDE.md](05_SLAM_NAV2_GUIDE.md) untuk konfigurasi
pemetaan dan navigasi.
