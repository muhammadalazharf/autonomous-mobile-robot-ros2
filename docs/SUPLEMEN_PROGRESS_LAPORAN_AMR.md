# Suplemen Progress untuk Laporan Final AMR

> **Tujuan dokumen:** melengkapi `Laporan_AMR.docx` dengan progress aktual yang belum
> tercatat (terutama setelah snapshot analisis database awal). Setiap blok di bawah
> ditujukan untuk **menggantikan atau menambah** subbab tertentu pada laporan.
> Gaya penulisan dijaga formal-akademik dan **jujur secara teknis** (hanya klaim yang
> didukung bukti; bukti runtime yang belum tersedia ditandai eksplisit).
>
> Catatan rekonsiliasi: laporan versi .docx memakai `mapping_20260611_MASTER.db`
> sebagai peta acuan dari analisis 24 berkas. Dokumen ini menambahkan babak
> berikutnya: **re-mapping bersih 18 Juni** yang justru merupakan *solusi* atas masalah
> database kacau yang dilaporkan, dan menghasilkan peta demo `lab_demo_18jun.db`.

---

## A. Timeline Kronologis Pengembangan (untuk BAB IV pembuka / Lampiran)

Tabel berikut merangkum perjalanan proyek dari awal hingga kondisi terakhir, agar
laporan mencerminkan proses iteratif (bukan hanya hasil akhir).

| Fase | Periode | Kegiatan & capaian |
|------|---------|--------------------|
| 1. Platform & integrasi | Awal | Rakit 4WD Ackermann, integrasi ROS2 Humble di NUC, STM32 bridge, joystick manual |
| 2. Integrasi sensor | — | RPLIDAR C1 → `/scan`, RealSense D455 (RGB-D + IMU) terbaca; static TF bridge |
| 3. Kalibrasi odometry | 14 Jun | Uji odom-vs-meteran 5 jarak → koreksi PPR 1496→3858 (R²=0.998) |
| 4. Mapping iteratif | s/d 17 Jun | Banyak sesi mapping (24 berkas .db); identifikasi masalah duplikat/korup/near-static |
| 5. Stabilisasi VIO | 8-9 Jun | Tuning anti-drift (`Odom/MaxVariance`, `ResetCountdown`, STMSize 30→10) |
| 6. Fix brownout | 15 Jun | PWM software ramping (anti voltage-sag NUC saat motor inrush) |
| 7. Re-mapping bersih | 18 Jun | Mapping ulang 1 loop pendek → `lab_demo_18jun.db` (peta demo tervalidasi) |
| 8. Lokalisasi lock | 17-19 Jun | Root cause loop rejection ditemukan & diperbaiki (ambang localization = mapping) |
| 9. Nav2 bringup | 18-19 Jun | Penyelesaian rantai 8 gerbang Nav2 → bringup sukses |
| 10. Autonomous navigation | 19 Jun | Robot bergerak otonom dari goal Nav2 (mode demo tanpa failover) |
| 11. Fix arah kemudi | 20 Jun | Bench test: negasi tanda kemudi pada formula Ackermann |

---

## B. REVISI Tabel Ketercapaian Target (ganti tabel di subbab 4.1)

Status diperbarui sesuai kondisi terakhir (tetap jujur; runtime yang perlu bukti
tambahan ditandai).

| No. | Target | Realisasi | Status |
|-----|--------|-----------|--------|
| 1 | Platform robot AMR | Robot 4WD Ackermann terbangun & bergerak (manual + otonom) | Tercapai |
| 2 | Integrasi ROS2 Humble | ROS2 + node utama aktif di NUC | Tercapai |
| 3 | Integrasi sensor | LiDAR C1 + RealSense D455 (RGB-D+IMU) terbaca | Tercapai |
| 4 | Manual control | Teleop joystick PS4/PS5 (deadman R1) | Tercapai |
| 5 | SLAM/Mapping | Peta `.db` valid; peta demo bersih `lab_demo_18jun.db` | Tercapai |
| 6 | Kalibrasi odometry | PPR empiris 3858, R²=0.998 | Tercapai |
| 7 | Localization | Lock tervalidasi pada peta bersih; loop closure diterima | Tercapai |
| 8 | Navigasi Nav2 | Bringup sukses; **robot bergerak otonom dari goal** | Tercapai (mode demo) |
| 9 | Failover/safety | PWM ramping anti-brownout; deadman; `autonomous_enabled` gate | Tercapai sebagian |
| 10 | Dokumentasi | Laporan + analisis akar masalah + SOP | Tercapai |

> **Kejujuran teknis:** klaim "bergerak otonom" merujuk pengujian tim (19 Juni) dengan
> goal `navigate_to_pose`; untuk laporan final disarankan melampirkan **bukti runtime**
> (video/log `/cmd_vel`, screenshot RViz path) sebagai penguat. Mode demo berjalan
> **tanpa failover** (Nav2 → `/cmd_vel` langsung), sehingga rem darurat manual (R1) wajib.

---

## C. TAMBAHAN Subbab — Re-Mapping Bersih & Peta Kanonik (sisipkan setelah 4.5)

### 4.5b Re-Mapping Bersih sebagai Solusi Masalah Kualitas Peta

Analisis agregat 24 basis data (subbab 4.4-4.5) menyingkap masalah nyata: banyak sesi
duplikat, near-static, atau korup, sehingga agregat membengkak namun tidak semuanya
sahih sebagai bukti SLAM bergerak. Sebagai tindak lanjut, dilakukan **pemetaan ulang
bersih satu sesi** dengan prinsip *kualitas mengungguli kuantitas*: satu loop pendek,
gerak pelan, kamera selalu menghadap area bertekstur.

Hasilnya adalah peta acuan demo **`lab_demo_18jun.db`** dengan metrik berikut
(ekstraksi `rtabmap-info`):

| Metrik | Nilai | Interpretasi |
|--------|-------|--------------|
| Sessions | 1 | Single coherent run (bukan gabungan lap) |
| Durasi mapping | ~17 menit (1012 s) | Sesi tunggal terkendali |
| Panjang trajektori | 28,9 m | Loop pendek, tidak berlebih |
| Pose (optimized graph) | 448 | Padat tapi efisien |
| Nodes (LTM) | 1846 (126.506 words) | Vocabulary BoW kaya |
| Global loop closure | 125 | Sangat sehat (lab kecil cukup 10-20) |
| Proximity loop closure | 648 | Revisit kuat → drift mendekati nol |
| Jarak antar-keyframe | 0,06 m | Trajektori mulus |
| Ukuran database | 743 MB (Depth 56% · RGB 25% · Features 10% · Grid 5%) | Komposisi sehat |

**Perbandingan dengan peta lama yang "menjalar"** (mis. sesi 17 Juni ~1224 pose, ~175 m,
1,2 GB): peta panjang berulang mengakumulasi drift VIO sehingga 3D cloud ghosting.
Re-mapping bersih menurunkan pose 63% dan jarak 83% namun justru menghasilkan loop
closure yang lebih sahih. **Pelajaran:** untuk lokalisasi andal, satu loop bersih lebih
baik daripada banyak lap panjang.

---

## D. REVISI Subbab 4.8 — Hasil Implementasi Localization

Lokalisasi berhasil dilakukan terhadap peta bersih `lab_demo_18jun.db` pada mode
localization RTAB-Map (`Mem/IncrementalMemory:false`, `Mem/InitWMWithAllNodes:true`),
dengan loop closure diterima saat robot bergerak.

**Root cause yang sempat menggagalkan lokalisasi (loop rejection):** konfigurasi mode
localization awalnya **lebih ketat** daripada ambang yang ter-*baked* di dalam `.db`
saat mapping. Karena peta dibangun dengan ambang longgar tertentu, relokalisasi yang
memakai ambang lebih ketat akan **selalu menolak** kandidat loop closure yang sebenarnya
valid. Tabel berikut merangkum ketidakcocokan dan perbaikannya:

| Parameter | Saat Mapping (`.db`) | Localization (sebelum fix) | Setelah fix |
|-----------|----------------------|----------------------------|-------------|
| `Rtabmap/LoopThr` | 0,05 | 0,11 (2× lebih ketat) | 0,05 |
| `Vis/MinInliers` | 8 | 10 | 8 |
| `Rtabmap/DetectionRate` | 2,0 Hz | 1,0 Hz | 2,0 Hz |
| `Kp/MaxFeatures` | 400 | (hilang) | 400 |
| `RGBD/LoopClosureReextractFeatures` | true | (hilang) | true |
| `RGBD/OptimizeMaxError` | 5,0 | 3,0 (default) | 5,0 |
| `Mem/STMSize` | 10 | (hilang) | 10 |

Setelah ambang localization disamakan 1:1 dengan ambang mapping, loop closure yang valid
diterima dan robot dapat melokalisasi diri terhadap peta.

> **Kejujuran teknis:** untuk laporan final disarankan melampirkan bukti runtime
> (screenshot RTAB-Map mode localization dengan loop closure hijau, atau log
> `/localization_pose`) guna menguatkan klaim ini secara objektif.

---

## E. REVISI Subbab 4.9 — Hasil Implementasi Navigation2 (rantai 8 gerbang)

Laporan versi awal hanya mencatat satu kendala Nav2 (format plugin). Faktanya, bringup
Nav2 pada ROS2 Humble harus melewati **rangkaian delapan "gerbang" berurutan** yang
masing-masing memblokir aktivasi. Seluruhnya berhasil diselesaikan sehingga Nav2
mencapai *lifecycle active* dan robot dapat bergerak otonom dari goal.

| # | Gejala (log/perilaku) | Akar masalah | Perbaikan |
|---|------------------------|--------------|-----------|
| 1 | `VoxelLayer does not exist` | Format plugin `/` vs `::` campur | Seragamkan format per package |
| 2 | `ID [RemovePassedGoals] already registered` (crash) | Blok `plugin_lib_names` eksplisit → registrasi ganda | Hapus blok → Nav2 auto-load via pluginlib |
| 3 | `Node not recognized: RateController` | Turunan #2 | Terselesaikan bersama #2 |
| 4 | `Action server spin not available` | Behavior `spin` tak terdaftar, padahal BT default memanggilnya | Daftarkan `nav2_behaviors/Spin` |
| 5 | `Couldn't open input XML file` | `default_nav_to_pose_bt_xml` bukan path absolut | Pakai path absolut Behavior Tree |
| 6 | `collision ahead` / lethal terus | `depth_scan` salah baca lantai = obstacle hantu | Matikan depth_scan di costmap (LiDAR saja); `robot_radius` 0,35→0,28; `inflation_radius` 0,45→0,25 |
| 7 | Nav2 kirim cmd_vel tapi robot diam | Remap `/cmd_vel`→`/cmd_vel_nav`, bridge dengar `/cmd_vel` | Hapus remap (mode demo tanpa failover) |
| 8 | Robot tetap diam walau cmd_vel≠0 | `autonomous_enabled` default `false` (safety gate) | Set `true` saat runtime (gerbang terakhir) |

**Konfigurasi Nav2 yang Ackermann-aware** (relevan untuk laporan):
- Planner `nav2_smac_planner/SmacPlannerHybrid`, model gerak **DUBIN**,
  `minimum_turning_radius: 0,90 m`, `reverse_penalty: 2,0`.
- Controller `RegulatedPurePursuitController`, `desired_linear_vel: 0,3 m/s`,
  `use_rotate_to_heading: false` (Ackermann tak bisa berputar di tempat).
- Costmap resolusi 0,05 m; obstacle dari LiDAR `/scan`.

> **Kejujuran teknis:** disarankan melampirkan bukti runtime navigasi (video robot
> bergerak, log `/cmd_vel` saat goal aktif, screenshot RViz global/local plan).

---

## F. TAMBAHAN Subbab — Kalibrasi Odometry Empiris (sisipkan di 4.3 atau baru)

### 4.3b Kalibrasi Encoder Odometry

Odometry roda menggunakan model kinematika sepeda (Ackermann). Nilai *pulses per
revolution* (PPR) teoretis tidak sesuai realita, sehingga dilakukan kalibrasi empiris:

- **Metode:** robot dijalankan pada 5 jarak acuan (0,5 / 1,0 / 1,5 / 2,0 / 2,5 m) dan
  dibandingkan jarak terbaca odometry vs pengukuran meteran (22 / 41 / 61 / 81 / 96 cm).
- **Analisis:** regresi proporsional menghasilkan `real = 0,3877 × odom` dengan
  **R² = 0,998** — odometry awal over-report **2,58×**.
- **Koreksi:** PPR efektif = 1496 / 0,3877 = **3858** (`dist_per_tick` 0,3255 → 0,1262 mm).

Kalibrasi ini menautkan proyek dengan kompetensi metode numerik (regresi kuadrat
terkecil) dan menjadi bukti kuantitatif yang dapat diaudit.

---

## G. TAMBAHAN — Kendala & Solusi Hardware (lengkapi tabel 4.10)

Tambahkan baris berikut ke tabel Kendala dan Solusi:

| Kendala | Penyebab | Dampak | Solusi |
|---------|----------|--------|--------|
| Brownout power-rail saat motor start | Lonjakan arus inrush motor PG45 → tegangan NUC sag (SSH freeze, RealSense timeout) | Sistem freeze saat akselerasi mendadak | Software PWM ramping (batas Δ400/call); e-stop bypass ramp demi safety |
| Odometry over-report 2,58× | PPR teoretis tidak sesuai realita gear/quadrature | Estimasi posisi meleset | Kalibrasi empiris → PPR 3858 (R²=0,998) |
| Arah kemudi otonom terbalik | Tanda kemudi pada formula Ackermann terbalik | `angular.z` kiri → roda belok kanan | Negasi `steer_rad = -atan(L·ω/v)` (terverifikasi bench test) |
| VIO drift area minim tekstur | Pencahayaan tidak konsisten + low-texture | 3D cloud ghosting pada sesi panjang | Re-mapping 1 loop bersih; tuning exposure/gain; gravity constraint IMU |

---

## H. REVISI Kesimpulan (subbab 5.1)

Ganti poin Nav2 & localization yang lama dengan rumusan diperbarui:

1. Platform AMR 4WD Ackermann berbasis ROS2 Humble berhasil dirancang & direalisasikan
   sebagai platform fungsional indoor (manual + otonom).
2. Sensor LiDAR C1 dan RealSense D455 (RGB-D + IMU) terintegrasi penuh; data laser,
   RGB, depth tersimpan bersamaan per node.
3. Odometry dikalibrasi empiris (PPR 3858, R²=0,998), menautkan praktik dengan metode
   numerik (regresi).
4. RTAB-Map menghasilkan peta demo bersih `lab_demo_18jun.db` (448 pose; 125 global +
   648 proximity loop closure) sebagai peta acuan tervalidasi.
5. Lokalisasi berhasil setelah akar masalah *loop rejection* (ketidakcocokan ambang
   mapping↔localization) diidentifikasi dan diperbaiki.
6. Navigation2 mencapai *lifecycle active* setelah rangkaian **8 gerbang** bringup
   diselesaikan; robot **bergerak otonom dari goal** pada mode demo (tanpa failover).
7. Penyempurnaan keandalan (failover otomatis, re-enable depth_scan terkalibrasi,
   pengujian patrol multi-goal) menjadi pekerjaan lanjutan.

---

## I. REVISI Rekomendasi (subbab 5.2) — tambahkan

8. Mengaktifkan kembali `failover_controller` (perbesar `map_timeout_s`, filter LiDAR
   return < 0,15 m) agar auto emergency-stop dapat dipakai saat demo.
9. Melakukan re-mapping setiap kali layout ruangan berubah signifikan (lokalisasi
   sensitif terhadap perubahan tata ruang).
10. Menyinkronkan pembacaan sudut kemudi odometry dari `/cmd_vel` (bukan hanya `/joy`)
    agar yaw odometry akurat saat navigasi otonom murni.
11. Melampirkan bukti runtime (video/log) navigasi & lokalisasi untuk memperkuat klaim.

---

## J. Catatan Konsistensi Data (untuk editor laporan)

- **Spesifikasi hardware** sesuai laporan: STM32F407, Motor PG45, servo DSSERVO D25,
  catu daya Ovonic 5300 mAh 6S, wheelbase 0,5 m, track width 0,4 m, wheel radius
  0,0775 m, steering ±45°.
- **Peta acuan**: laporan boleh menyebut dua artefak dengan konteks berbeda —
  `mapping_20260611_MASTER.db` (peta terpadat dari analisis agregat) dan
  `lab_demo_18jun.db` (peta bersih untuk demo navigasi). Keduanya bagian sah dari
  perjalanan; yang dipakai untuk uji Nav2/lokalisasi terakhir adalah yang 18 Juni.
- **Prinsip kejujuran**: semua klaim "berhasil/otonom" sebaiknya disertai bukti runtime
  di Lampiran; bagian yang belum ada buktinya ditandai "perlu bukti tambahan".
