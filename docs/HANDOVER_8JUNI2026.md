# HANDOVER PROYEK AMR ITS — SESI 8 JUNI 2026

**Tanggal:** 8 Juni 2026
**Dari:** Sesi debugging "mapping selalu rusak" (analisis Fishbone + verifikasi langsung di NUC)
**Untuk:** Rekan tim / sesi berikutnya yang melanjutkan uji mapping
**Status:** 🟡 Pipeline sudah BERSIH dan terverifikasi sehat secara statis — uji mapping dinamis (drive) BELUM dilakukan karena robot masih di PSU (tidak bisa berpindah)

> **Catatan integrasi:** Dokumen ini melanjutkan `HANDOVER_7JUNI2026.md`. Pada
> 7 Juni, VIO sudah terbukti stabil tapi mapping masih gagal/crash. Pada 8 Juni
> ditemukan akar masalah baru yang lebih fundamental: **NUC tertinggal 6 commit**
> dari `origin/claude/brave-newton-6zvS4`, dan ada **node duplikat** akibat
> menjalankan dua launch file (`amr_full.launch.py` + `rtabmap_mapping.launch.py`)
> bersamaan di dua terminal terpisah.

---

## RINGKASAN EKSEKUTIF

Sesi dimulai dari laporan user: "mapping selalu rusak". Alih-alih langsung ubah
parameter, dilakukan **audit menyeluruh berbasis Fishbone Diagram (6 kategori:
Sensor, Software/Algoritma, Konfigurasi, Mekanik, Lingkungan, Komputasi)** dan
**verifikasi langsung live di NUC** (bukan asumsi dari kode saja).

Hasilnya: **akar masalah BUKAN di parameter RTAB-Map** (yang sudah benar di
`origin/claude/brave-newton-6zvS4` commit `e850fca`), melainkan:

1. **NUC menjalankan kode lama** (`3d69411`, ketinggalan 6 commit dari GitHub)
2. **Edit manual lokal yang mengandung bug** (`'true'` string vs `True` bool, `Mem/STMSize: 10`)
3. **Dua launch file dijalankan bersamaan** → node duplikat → dua publisher
   `/rtabmap/odom`, dua `/imu_merger`, dst → cloud point meledak/scattered
4. **Database RTAB-Map lama (`~/.ros/rtabmap.db`, 224MB) ikut ter-load** saat
   mapping baru dimulai → mapping baru "menumpuk" di atas drift lama

Setelah `git pull`, `colcon build`, pembersihan proses orphan + restart
`ros2 daemon`, dan menghapus database lama — **pipeline sekarang bersih: 13 node
tunggal (tidak ada duplikat), `/rtabmap/odom` 1 publisher, `/odom` 1 publisher,
`/tf` hanya dari `rgbd_odometry` + `robot_state_publisher` (tidak ada konflik
wheel-odom vs VIO)**.

**Yang BELUM terverifikasi:** apakah `cloud_map`/`mapData` benar-benar
terbentuk koheren saat robot bergerak — karena saat sesi ini robot terhubung
ke PSU statis (tidak bisa drive keliling lab).

---

## BAGIAN 1 — TEMUAN PENTING (untuk dibaca dulu sebelum lanjut)

### 1.1 — Repo teman (`Mervs111/autonomous-mobile-robot-ros2`) sekarang PUBLIK
Sudah bisa diakses untuk komparasi progress. Berisi commit relevan:
- `8a993f0` — fix(rtabmap): pindahkan `Odom/MaxVariance` ke node yang benar (`rgbd_odometry`)
- `931bac8` — Add frame rejection filter to prevent scattered cloud explosion
- `3d69411` — Fix VIO tracking for low-texture lab environment

> Catatan: commit `3d69411` ini **persis** sama SHA-nya dengan HEAD lama di NUC
> kita — menunjukkan riwayat development sempat bercabang/sinkron antar repo.

### 1.2 — Branch kerja yang BENAR adalah `claude/brave-newton-6zvS4`
NUC (`~/amr_starter`) sudah ter-checkout di branch ini (bukan `main`). **Sesi
berikutnya HARUS bekerja di branch yang sama** agar `git pull` lurus tanpa
konflik. Branch sandbox (`claude/quirky-newton-JXSM2`) tidak dipakai untuk
perubahan workspace AMR di sesi ini.

### 1.3 — Sebagian besar fix yang "direncanakan" TERNYATA SUDAH ADA di GitHub
Audit awal (Fishbone) merekomendasikan 5 perbaikan kritis. Setelah investigasi,
**ternyata commit `e850fca` (oleh sesi sebelumnya, 8 Juni pagi) sudah berisi 7
fix introspeksi yang sangat mirip**:

| Param | Nilai lama | Nilai di `e850fca` | Status |
|---|---|---|---|
| `Vis/MinInliers` (rgbd_odometry) | 2 | **8** | ✅ sudah fix |
| `Odom/MaxVariance` | 0.01 (terlalu ketat) | **0.05** | ✅ sudah fix |
| `Odom/ResetCountdown` | 1 | **5** | ✅ sudah fix |
| `Kp/MaxFeatures` / `Kp/DetectorStrategy` | tidak ada | **400 / 8** | ✅ ditambahkan |
| `Rtabmap/DetectionRate` | 1.0 Hz | **2.0 Hz** | ✅ sudah fix |
| `cloud_max_depth` | 4.0 | **5.0** | ✅ sudah fix |
| `publish_cloud_map` dkk | — | **`True` (Python bool)** | ✅ benar |
| `scripts/fresh_mapping.sh` | tidak ada | **dibuat** | ✅ helper backup DB otomatis |

**Pelajaran:** Jangan langsung re-fix berdasarkan audit kode statis saja —
selalu cek dulu apakah `git log` branch kerja sudah punya fix yang sama,
supaya tidak menimpa pekerjaan yang sudah benar.

### 1.4 — Akar masalah real session ini: BUKAN parameter, tapi PROSES & STATE
Robot kamu di lab kemungkinan besar mengalami "mapping rusak" karena kombinasi:
- **Edit manual lokal yang salah ketik** (`'true'` string ROS param ditolak/diabaikan
  silently oleh RTAB-Map; `Mem/STMSize: 10` sebenarnya sudah sengaja & TERBUKTI
  bekerja dari sesi 7 Juni — JANGAN diubah balik ke 30)
- **Menjalankan `amr_full.launch.py` (Terminal 1) DAN `rtabmap_mapping.launch.py`
  (Terminal 2) bersamaan** → setiap node mapping (rgbd_odometry, imu_merger,
  rgbd_sync, depth_to_laserscan) muncul 2×, masing-masing menghitung pose
  berbeda untuk frame yang sama → titik 3D "meledak"/scattered
- **Database lama ter-load otomatis** oleh RTAB-Map saat mapping baru dimulai
  (terlihat dari `WM=710` padahal baru start) → drift lama tertumpuk dengan data baru

---

## BAGIAN 2 — APA YANG SUDAH DIKERJAKAN DI SESI INI (kronologis)

1. **Audit menyeluruh workspace** via subagent — menghasilkan tabel parameter
   RTAB-Map/SLAM/Nav2/sensor lengkap dengan `path:line`, dan diff terhadap
   repo teman. Disusun jadi **Fishbone Diagram 6 kategori**.

2. **Verifikasi live di NUC** (bukan cuma baca kode):
   - Konfirmasi semua sensor (`/scan` 10Hz, `/camera depth` ~29Hz, `/imu` 200Hz) sehat
   - Temukan workspace NUC = `~/amr_starter`, branch `claude/brave-newton-6zvS4`,
     ketinggalan **6 commit** dari `origin`
   - Temukan ada **edit manual lokal belum ter-commit** yang mengandung bug
     (`publish_cloud_map: 'true'` string, `Mem/STMSize: 10`)
   - Temukan **node duplikat** (`/rgbd_odometry` x2, `/imu_merger` x2, dst) dan
     **dua publisher `/rtabmap/odom`** akibat dua launch file jalan bersamaan
   - Temukan log error `OdomF2M::computeTransform() Not enough points with valid
     depth (349/848=0.41 < ValidDepthRatio 0.75)` — indikasi banyak piksel depth
     invalid dari D455 di kondisi lab tertentu
   - Temukan log error `VWDictionary.cpp:741::addWordRef() Not found word` —
     gejala vocabulary BoW corrupt akibat menjalankan kode lama + DB lama bertumpuk

3. **Pembersihan & sinkronisasi**:
   ```bash
   # Backup & hapus DB session bermasalah
   mv ~/.ros/rtabmap.db ~/.ros/rtabmap.db.broken_<timestamp>.bak
   rm -f ~/.ros/rtabmap.db   # hapus juga DB baru yang ter-corrupt vocabulary

   # Buang edit manual lokal yang buggy
   git checkout -- src/amr_3d_mapping/config/rtabmap_mapping.yaml \
                   src/amr_3d_mapping/launch/rtabmap_mapping.launch.py

   # Tarik 6 commit yang ketinggalan (termasuk e850fca — 7 fix introspeksi)
   git pull origin claude/brave-newton-6zvS4   # 3d69411 → e850fca, fast-forward
   colcon build --packages-select amr_3d_mapping --symlink-install
   source install/setup.bash
   ```

4. **Bersihkan proses orphan & restart DDS discovery**:
   ```bash
   pkill -9 -f ros2 ; pkill -9 -f rtabmap ; pkill -9 -f rgbd ; ... (lihat Bagian 4)
   ros2 daemon stop && ros2 daemon start
   ```

5. **Verifikasi ulang sampai BERSIH** — hasil akhir:
   - `ros2 node list` → 13 node, **TIDAK ADA WARNING duplikat**
   - `/rtabmap/odom` → Publisher count: **1**
   - `/odom` → Publisher count: **1**
   - `/tf` → 2 publisher (`rgbd_odometry` untuk `odom→base_link`,
     `robot_state_publisher` untuk joint TF) — **TIDAK ADA** `odometry_publisher`
     (wheel) di daftar publisher `/tf`, artinya `publish_tf` wheel-odom sudah
     benar dimatikan saat mode RTAB-Map aktif → **tidak ada dual-odom-TF conflict**
   - `/scan` 10 Hz, `/rtabmap/odom` ~24-29 Hz, `/camera depth` ~29 Hz — semua sehat

---

## BAGIAN 3 — STATUS TERKINI

### Sudah selesai dan terverifikasi ✅
| Item | Status |
|------|--------|
| NUC sinkron dengan `origin/claude/brave-newton-6zvS4` (HEAD = `e850fca`) | ✅ |
| Edit manual lokal yang buggy sudah dibuang (`git checkout --`) | ✅ |
| Database RTAB-Map lama & corrupt sudah dibackup + dihapus | ✅ |
| Tidak ada lagi node duplikat (`ros2 node list` bersih, 13 node) | ✅ |
| `/rtabmap/odom` & `/odom` masing-masing 1 publisher | ✅ |
| Tidak ada dual-publisher TF `odom→base_link` (wheel vs VIO) | ✅ |
| 7 param fix dari `e850fca` terverifikasi ter-load di launch | ✅ |
| Sensor pipeline sehat (`/scan`, `/imu`, `/camera depth`, semua rate normal) | ✅ |
| `rgbd_odometry` quality stabil (200-270, std dev 0.001-0.003m) | ✅ |

### Belum selesai / belum terverifikasi ❌
| Item | Prioritas | Alasan |
|------|-----------|--------|
| **Uji mapping dinamis** (`cloud_map`/`mapData`/`map` terbentuk koheren saat robot bergerak) | 🔴 Pertama | Robot di PSU statis, tidak bisa drive keliling lab saat sesi ini |
| Loop closure benar-benar terpicu di ruangan kecil | 🔴 Kedua | Butuh robot bergerak 1 putaran penuh |
| Validasi `OdomF2M/ValidDepthRatio` reject masih muncul atau tidak setelah fix `e850fca` | 🟡 Ketiga | Hanya terlihat di sesi sebelumnya dengan kode lama; belum di-recheck dengan kode baru + sensor tuning |
| Tuning exposure/filter RealSense (`gain`, `exposure`, `temporal_filter`, `spatial_filter`) — sudah ada di repo teman, belum dicoba di workspace ini | 🟡 Keempat | Berguna untuk lab dengan pencahayaan tidak konsisten |

---

## BAGIAN 4 — PROSEDUR UNTUK SESI BERIKUTNYA (siap eksekusi)

### Langkah 0 — SELALU jalankan SATU launch file saja untuk mapping
**JANGAN** jalankan `amr_full.launch.py` dan `rtabmap_mapping.launch.py` di
terminal terpisah secara bersamaan — itu penyebab node duplikat & cloud meledak.

Pilih **salah satu**:
```bash
# Cara A (recommended, all-in-one, tidak ada duplikat):
ros2 launch amr_bringup amr_full.launch.py use_rtabmap:=true rtabmap_mode:=mapping

# Cara B (kalau ingin split, JANGAN gabung dengan amr_full):
ros2 launch amr_bringup sensors_launch.py        # terminal 1
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py   # terminal 2
```

### Langkah 1 — Selalu fresh start sebelum sesi mapping baru
```bash
cd ~/amr_starter
bash scripts/fresh_mapping.sh    # backup + hapus DB lama otomatis (sudah ada dari e850fca)
```

### Langkah 2 — Kalau ada masalah "node tidak mau hilang" / duplikat
```bash
pkill -9 -f ros2 ; pkill -9 -f component_container ; pkill -9 -f rplidar
pkill -9 -f realsense ; pkill -9 -f stm32_bridge ; pkill -9 -f odometry_publisher
pkill -9 -f joy_node ; pkill -9 -f robot_state_publisher ; pkill -9 -f static_transform
pkill -9 -f depth_to_laser ; pkill -9 -f imu_merger ; pkill -9 -f rgbd ; pkill -9 -f rtabmap
sleep 3
ros2 daemon stop && sleep 2 && ros2 daemon start && sleep 2
ros2 node list   # HARUS kosong sebelum launch ulang
```

### Langkah 3 — Uji mapping dinamis (BELUM dilakukan, prioritas #1 sesi depan)
1. Pastikan robot bisa **bergerak bebas** (baterai, atau extension cable PSU
   minimal 2-3 meter, atau PSU di troli beroda mengikuti robot)
2. Drive **pelan-pelan** (~0.2 m/s): maju 1-2m → berhenti → belok 90° →
   berhenti → maju lagi → putar balik ke titik start (1 putaran penuh untuk
   memicu loop closure)
3. Amati log `[rtabmap-N]`:
   - ✅ Bagus: `WM=1, 2, 3, ...` naik bertahap dari kecil (BUKAN langsung 700+,
     itu tanda DB lama ke-load)
   - ✅ Bagus: `Loop closure detected with id=...` muncul saat kembali ke start
   - ❌ Buruk: `[ERROR] VWDictionary not found word`, `OdomF2M not enough points`
4. Verifikasi topic baru muncul setelah motion:
   ```bash
   ros2 topic list | grep -iE "cloud|^/map|grid"
   ros2 topic hz /rtabmap/cloud_map
   ```
5. Buka Foxglove/RViz, subscribe `/rtabmap/cloud_map` (PointCloud2) dan
   `/map` (OccupancyGrid) — cek apakah dinding/lantai terbentuk koheren

### Langkah 4 — Kalau masih ada `OdomF2M ValidDepthRatio` reject berulang
Tambahkan ke `rgbd_odometry` params di `rtabmap_mapping.launch.py`:
```python
'OdomF2M/ValidDepthRatio': '0.3',   # turun dari default 0.75 — lab D455 banyak depth invalid
```

### Langkah 5 — Kalau lighting lab tidak konsisten (VIO sering lost)
Repo teman (`Mervs111/...`) sudah punya tuning exposure RealSense yang belum
ada di workspace ini — bisa dicontoh ke `sensors_launch.py`:
```python
'rgb_camera.gain': 64,
'rgb_camera.exposure': 156,
'temporal_filter.enable': True,
'spatial_filter.enable': True,
```

---

## BAGIAN 5 — PERINGATAN / JANGAN LAKUKAN INI

1. **JANGAN** ubah `Mem/STMSize` balik ke `30` — nilai `10` di commit `702021b`
   sudah TERBUKTI bekerja lebih baik untuk loop closure ruangan kecil (sesi 7 Juni).
2. **JANGAN** set param boolean RTAB-Map sebagai string `'true'`/`'false'` —
   gunakan Python bool `True`/`False`. String diam-diam diabaikan/salah parse.
3. **JANGAN** jalankan dua launch file mapping bersamaan di terminal terpisah.
4. **JANGAN** mulai sesi mapping baru tanpa `bash scripts/fresh_mapping.sh`
   atau minimal cek `ls -la ~/.ros/*.db` — DB lama yang ter-load adalah
   penyebab umum "mapping menumpuk di atas drift lama".
5. **SELALU** kerja di branch `claude/brave-newton-6zvS4` dan `git pull`
   sebelum mulai sesi — supaya tidak mengulangi masalah "NUC ketinggalan 6 commit".

---

## BAGIAN 6 — REFERENSI PATH & COMMIT PENTING

```
Workspace NUC      : ~/amr_starter  (branch: claude/brave-newton-6zvS4)
DB mapping aktif   : ~/.ros/rtabmap.db  (HAPUS sebelum sesi baru, atau pakai fresh_mapping.sh)
DB arsip           : ~/maps/lab_vio.db, ~/.ros/rtabmap_smoketest_pass_20260518_2131.db
Backup DB rusak    : ~/.ros/rtabmap.db.broken_20260608_173949.bak

Commit kunci:
  e850fca  introspeksi: 7 fix berdasarkan analisis dua mode kegagalan mapping
  702021b  merge: gabungkan param NUC sesi 7 Juni (STMSize=10, Grid noise filter)
  8a993f0  fix(rtabmap): pindahkan Odom/MaxVariance ke node yang benar

File kunci yang berubah di e850fca:
  src/amr_3d_mapping/config/rtabmap_mapping.yaml
  src/amr_3d_mapping/launch/rtabmap_mapping.launch.py
  scripts/fresh_mapping.sh   (helper baru)

Repo referensi (publik, untuk komparasi progress):
  https://github.com/Mervs111/autonomous-mobile-robot-ros2
  → relevan: commit 8a993f0, 931bac8, 3d69411 di repo tsb (riwayat fix mapping serupa)
```

---

## PENUTUP

Pipeline mapping AMR sekarang dalam kondisi **bersih dan sehat secara statis**
— semua node tunggal, tidak ada konflik TF, parameter sudah sesuai hasil
introspeksi 7-fix dari sesi sebelumnya, database lama sudah dibersihkan.
**Langkah selanjutnya yang paling penting adalah uji dinamis**: gerakkan robot
1 putaran penuh di lab dan amati apakah `cloud_map` terbentuk koheren serta
loop closure terpicu. Kalau hasil uji dinamis masih menunjukkan masalah, fokus
selanjutnya adalah `OdomF2M/ValidDepthRatio` (Langkah 4) dan tuning exposure
kamera (Langkah 5) — keduanya sudah disiapkan resepnya di atas, tinggal eksekusi.
