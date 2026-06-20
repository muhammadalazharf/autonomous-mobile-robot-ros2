# BRIEFING UNTUK CLAUDE CHAT — Revisi Laporan Final AMR

> **Cara pakai:** salin SELURUH isi dokumen ini ke Claude chat (claude.ai), lampirkan
> file `Laporan_AMR.docx`. Dokumen ini sudah self-contained — Claude chat tidak butuh
> akses repository; semua data mentah tertanam di bawah.

---

## 0. PERAN & TUGAS KAMU (Claude chat)

Kamu adalah asisten penulisan teknis akademik. Tugasmu: **merevisi dan melengkapi**
`Laporan_AMR.docx` (Laporan PjBL Autonomous Mobile Robot) agar mencatat seluruh
progress aktual proyek dari awal hingga akhir, yang saat ini BELUM terdokumentasi.

Output yang diharapkan: **teks revisi siap-tempel per subbab** (atau dokumen Word
final bila diminta), dalam Bahasa Indonesia akademik formal.

**Prinsip wajib (jangan dilanggar):**
1. **Kejujuran teknis.** Hanya klaim yang ada buktinya. Klaim "berhasil/otonom" harus
   diberi catatan "lampirkan bukti runtime (video/log/screenshot)" bila bukti formal
   belum tersedia. JANGAN mengarang data, angka, atau hasil.
2. **Pertahankan gaya laporan asli** (formal, naratif-akademik, hati-hati).
3. **Jangan hapus** analisis lama yang sahih; tambahkan babak berikutnya sebagai
   kelanjutan, bukan kontradiksi.
4. **Konsisten angka.** Pakai data mentah di Bagian 5 dokumen ini; jangan ubah nilai.

---

## 1. KONTEKS PROYEK (ringkas)

- **Judul:** Autonomous Mobile Robot (AMR) 4WD Ackermann, indoor, ROS2 Humble.
- **Tim:** Mararevi Subagyo (2040241036), Muhammad Al Azhar Faradis (2040241017),
  Anwar Rifa'i (2040241021). Institusi: Teknik Elektro Otomasi, ITS Surabaya.
- **Hardware:** Intel NUC 13 i7; STM32F407; Motor PG45 (4WD via 1 motor + diferensial);
  servo kemudi DSSERVO D25; LiDAR RPLIDAR C1 (2D); kamera Intel RealSense D455
  (RGB-D + IMU internal); catu daya Ovonic 5300 mAh 6S. Wheelbase 0,5 m; track width
  0,4 m; wheel radius 0,0775 m; steering ±45°; radius putar minimum ±0,5–0,9 m.
- **Software:** RTAB-Map (SLAM 3D RGB-D + LiDAR), Nav2 (navigasi), 7 package ROS2
  (amr_bringup, amr_controller, amr_description, amr_slam, amr_3d_mapping,
  amr_failover, amr_visual_regression).

---

## 2. MASALAH LAPORAN SAAT INI (mengapa direvisi)

Laporan versi sekarang berhenti di kondisi LAMA dan TIDAK mencatat progress besar.
Yang usang/hilang:

| Aspek | Laporan sekarang (usang) | Realita progress (harus dimasukkan) |
|-------|--------------------------|--------------------------------------|
| Nav2 | "Belum optimal, bringup debugging, navigasi penuh belum terbukti" | Bringup SUKSES; robot bergerak otonom dari goal (mode demo) |
| Kendala Nav2 | Hanya 1 masalah (format plugin :: vs /) | Sebenarnya RANTAI 8 GERBANG berurutan |
| Peta acuan | `mapping_20260611_MASTER.db` (analisis agregat) | + babak baru: `lab_demo_18jun.db` (re-mapping bersih tervalidasi) |
| Localization | "Runtime belum lengkap" | Lock tervalidasi; root cause loop rejection ditemukan & diperbaiki |
| Odometry | Tidak dibahas detail | Kalibrasi empiris PPR 1496→3858, R²=0,998 |
| Hardware fix | Tidak ada | Fix brownout (PWM ramping) & fix arah kemudi (bench test) |
| Proses | Hanya hasil akhir | Belum ada TIMELINE kronologis awal→akhir |

---

## 3. RENCANA EKSEKUSI REVISI (RUNTUT — kerjakan berurutan)

Kerjakan langkah demi langkah. Setelah tiap langkah, tunjukkan teks hasil revisi.

**LANGKAH 1 — Tambah Timeline Kronologis.**
Sisipkan di awal BAB IV (atau Lampiran) tabel timeline 11 fase (lihat Bagian 4.A).
Tujuan: laporan menunjukkan proses iteratif, bukan hanya hasil.

**LANGKAH 2 — Perbarui Tabel Ketercapaian Target (subbab 4.1).**
Ganti tabel status lama dengan versi diperbarui (Bagian 4.B). Nav2 & lokalisasi naik
status menjadi tercapai, dengan catatan bukti runtime.

**LANGKAH 3 — Sisipkan subbab baru 4.5b "Re-Mapping Bersih".**
Jelaskan transisi dari banyak peta kacau → satu peta bersih `lab_demo_18jun.db`
sebagai SOLUSI atas masalah duplikat/korup yang sudah dilaporkan (Bagian 4.C).

**LANGKAH 4 — Revisi subbab 4.8 "Localization".**
Tulis ulang dengan narasi root cause loop rejection + tabel ambang mapping vs
localization (Bagian 4.D). Tetap beri catatan kejujuran (bukti runtime).

**LANGKAH 5 — Revisi subbab 4.9 "Navigation2".**
Ganti narasi "hanya 1 kendala" menjadi RANTAI 8 GERBANG lengkap (Bagian 4.E).
Tambahkan ringkasan konfigurasi Ackermann-aware.

**LANGKAH 6 — Sisipkan subbab 4.3b "Kalibrasi Odometry".**
Jelaskan metode uji 5 jarak + regresi R²=0,998 → PPR 3858 (Bagian 4.F). Kaitkan
dengan kompetensi metode numerik.

**LANGKAH 7 — Lengkapi Tabel Kendala & Solusi (subbab 4.10).**
Tambah baris hardware: brownout, arah kemudi, drift VIO (Bagian 4.G).

**LANGKAH 8 — Revisi Kesimpulan (5.1) & Rekomendasi (5.2).**
Perbarui poin Nav2 & lokalisasi; tambah rekomendasi lanjutan (Bagian 4.H & 4.I).

**LANGKAH 9 — Daftar lampiran bukti yang masih perlu disiapkan.**
Ingatkan penulis melampirkan: video navigasi, log /cmd_vel & /localization_pose,
screenshot RViz path, screenshot RTAB-Map loop closure hijau (Bagian 4.J).

**LANGKAH 10 — (Opsional) Rakit dokumen Word final** bila diminta penulis.

---

## 4. KONTEN SIAP-TEMPEL PER SUBBAB

### 4.A — Timeline Kronologis (LANGKAH 1)

| Fase | Periode | Kegiatan & capaian |
|------|---------|--------------------|
| 1. Platform & integrasi | Awal | Rakit 4WD Ackermann, ROS2 Humble di NUC, STM32 bridge, joystick manual |
| 2. Integrasi sensor | — | RPLIDAR C1 → /scan, RealSense D455 (RGB-D+IMU); static TF bridge |
| 3. Kalibrasi odometry | 14 Jun | Uji odom-vs-meteran 5 jarak → PPR 1496→3858 (R²=0,998) |
| 4. Mapping iteratif | s/d 17 Jun | Banyak sesi (24 berkas .db); temukan masalah duplikat/korup/near-static |
| 5. Stabilisasi VIO | 8-9 Jun | Tuning anti-drift (Odom/MaxVariance, ResetCountdown, STMSize 30→10) |
| 6. Fix brownout | 15 Jun | PWM software ramping (anti voltage-sag NUC saat motor inrush) |
| 7. Re-mapping bersih | 18 Jun | 1 loop pendek → lab_demo_18jun.db (peta demo tervalidasi) |
| 8. Lokalisasi lock | 17-19 Jun | Root cause loop rejection diperbaiki (ambang localization = mapping) |
| 9. Nav2 bringup | 18-19 Jun | Rantai 8 gerbang Nav2 selesai → bringup sukses |
| 10. Autonomous navigation | 19 Jun | Robot bergerak otonom dari goal Nav2 (mode demo tanpa failover) |
| 11. Fix arah kemudi | 20 Jun | Bench test: negasi tanda kemudi pada formula Ackermann |

### 4.B — Tabel Ketercapaian Target (LANGKAH 2)

| No. | Target | Realisasi | Status |
|-----|--------|-----------|--------|
| 1 | Platform robot AMR | 4WD Ackermann terbangun & bergerak (manual+otonom) | Tercapai |
| 2 | Integrasi ROS2 Humble | ROS2 + node utama aktif di NUC | Tercapai |
| 3 | Integrasi sensor | LiDAR C1 + RealSense D455 (RGB-D+IMU) terbaca | Tercapai |
| 4 | Manual control | Teleop joystick PS4/PS5 (deadman R1) | Tercapai |
| 5 | SLAM/Mapping | Peta .db valid; peta demo bersih lab_demo_18jun.db | Tercapai |
| 6 | Kalibrasi odometry | PPR empiris 3858, R²=0,998 | Tercapai |
| 7 | Localization | Lock tervalidasi pada peta bersih; loop closure diterima | Tercapai |
| 8 | Navigasi Nav2 | Bringup sukses; robot bergerak otonom dari goal | Tercapai (mode demo) |
| 9 | Failover/safety | PWM ramping; deadman; autonomous_enabled gate | Tercapai sebagian |
| 10 | Dokumentasi | Laporan + analisis akar masalah + SOP | Tercapai |

### 4.C — Subbab 4.5b Re-Mapping Bersih (LANGKAH 3)

Narasi: analisis agregat 24 .db menyingkap masalah (duplikat, near-static, korup).
Tindak lanjut: pemetaan ulang bersih satu sesi (kualitas > kuantitas) → peta demo
`lab_demo_18jun.db`. Metrik (rtabmap-info):

| Metrik | Nilai |
|--------|-------|
| Sessions | 1 |
| Durasi mapping | ~17 menit (1012 s) |
| Panjang trajektori | 28,9 m |
| Pose (optimized graph) | 448 |
| Nodes (LTM) | 1846 (126.506 words) |
| Global loop closure | 125 |
| Proximity loop closure | 648 |
| Jarak antar-keyframe | 0,06 m |
| Ukuran database | 743 MB (Depth 56% · RGB 25% · Features 10% · Grid 5%) |

Bandingkan dgn peta lama "menjalar" (~1224 pose, ~175 m, 1,2 GB) → drift VIO akumulatif.
Pelajaran: 1 loop bersih > banyak lap panjang.

### 4.D — Subbab 4.8 Localization (LANGKAH 4)

Root cause loop rejection: config localization lebih KETAT dari ambang baked-in di .db.

| Parameter | Mapping (.db) | Localization (sblm fix) | Stlh fix |
|-----------|---------------|--------------------------|----------|
| Rtabmap/LoopThr | 0,05 | 0,11 | 0,05 |
| Vis/MinInliers | 8 | 10 | 8 |
| Rtabmap/DetectionRate | 2,0 Hz | 1,0 Hz | 2,0 Hz |
| Kp/MaxFeatures | 400 | (hilang) | 400 |
| RGBD/LoopClosureReextractFeatures | true | (hilang) | true |
| RGBD/OptimizeMaxError | 5,0 | 3,0 | 5,0 |
| Mem/STMSize | 10 | (hilang) | 10 |

Catatan kejujuran: lampirkan screenshot loop closure hijau / log /localization_pose.

### 4.E — Subbab 4.9 Navigation2: RANTAI 8 GERBANG (LANGKAH 5)

| # | Gejala | Akar masalah | Perbaikan |
|---|--------|--------------|-----------|
| 1 | VoxelLayer does not exist | Format plugin / vs :: campur | Seragamkan per package |
| 2 | ID [RemovePassedGoals] already registered (crash) | plugin_lib_names eksplisit → registrasi ganda | Hapus blok → auto-load |
| 3 | Node not recognized: RateController | Turunan #2 | Selesai bersama #2 |
| 4 | Action server spin not available | spin tak terdaftar, BT default memanggilnya | Daftarkan nav2_behaviors/Spin |
| 5 | Couldn't open input XML file | BT XML bukan path absolut | Pakai path absolut |
| 6 | collision ahead / lethal terus | depth_scan salah baca lantai = obstacle hantu | Matikan depth_scan di costmap; radius 0,35→0,28; inflation 0,45→0,25 |
| 7 | Nav2 kirim cmd_vel, robot diam | Remap /cmd_vel→/cmd_vel_nav, bridge dengar /cmd_vel | Hapus remap (mode demo) |
| 8 | Robot tetap diam walau cmd_vel≠0 | autonomous_enabled default false (safety) | Set true saat runtime |

Konfigurasi Ackermann-aware: planner SmacPlannerHybrid (DUBIN, min turning radius
0,90 m, reverse_penalty 2,0); controller RegulatedPurePursuit (desired_linear_vel
0,3 m/s, use_rotate_to_heading=false); costmap resolusi 0,05 m, obstacle dari /scan.

### 4.F — Subbab 4.3b Kalibrasi Odometry (LANGKAH 6)

Metode: 5 jarak acuan (0,5/1,0/1,5/2,0/2,5 m) vs meteran (22/41/61/81/96 cm).
Hasil: regresi proporsional real = 0,3877×odom, R²=0,998; over-report 2,58×.
Koreksi: PPR efektif = 1496/0,3877 = 3858 (dist_per_tick 0,3255 → 0,1262 mm).
Kaitkan dengan metode numerik (regresi kuadrat terkecil).

### 4.G — Tambahan baris Tabel Kendala & Solusi (LANGKAH 7)

| Kendala | Penyebab | Dampak | Solusi |
|---------|----------|--------|--------|
| Brownout saat motor start | Inrush motor PG45 → tegangan NUC sag (SSH freeze, RealSense timeout) | Sistem freeze saat akselerasi | PWM ramping (Δ400/call); e-stop bypass ramp |
| Odometry over-report 2,58× | PPR teoretis ≠ realita | Posisi meleset | Kalibrasi → PPR 3858 (R²=0,998) |
| Arah kemudi otonom terbalik | Tanda kemudi formula Ackermann terbalik | angular.z kiri → roda kanan | Negasi steer_rad = -atan(L·ω/v) (bench test) |
| VIO drift area minim tekstur | Pencahayaan & low-texture | 3D cloud ghosting | Re-mapping bersih; tuning exposure; gravity constraint IMU |

### 4.H — Revisi Kesimpulan 5.1 (LANGKAH 8)

1. Platform AMR 4WD Ackermann ROS2 Humble fungsional (manual+otonom).
2. Sensor LiDAR C1 + RealSense D455 (RGB-D+IMU) terintegrasi penuh.
3. Odometry dikalibrasi empiris (PPR 3858, R²=0,998).
4. RTAB-Map menghasilkan peta demo bersih lab_demo_18jun.db (448 pose; 125+648 LC).
5. Lokalisasi berhasil setelah root cause loop rejection diperbaiki.
6. Nav2 mencapai lifecycle active (8 gerbang selesai); robot bergerak otonom (mode demo).
7. Penyempurnaan keandalan (failover, depth_scan terkalibrasi, patrol multi-goal) = lanjutan.

### 4.I — Tambahan Rekomendasi 5.2 (LANGKAH 8)

8. Aktifkan kembali failover_controller (map_timeout_s besar, filter LiDAR <0,15 m).
9. Re-mapping setiap layout berubah signifikan.
10. Sinkronkan sudut kemudi odometry dari /cmd_vel (bukan hanya /joy).
11. Lampirkan bukti runtime navigasi & lokalisasi.

### 4.J — Lampiran bukti yang perlu disiapkan (LANGKAH 9)

- Video robot bergerak otonom + log /cmd_vel saat goal aktif.
- Screenshot RViz: global plan, local plan, costmap.
- Screenshot RTAB-Map mode localization (loop closure hijau) / log /localization_pose.
- Foto hardware & wiring; screenshot RViz /scan + point cloud.

---

## 5. DATA MENTAH ACUAN (jangan diubah nilainya)

**Peta demo `lab_demo_18jun.db`:** Sessions 1; durasi 1012 s; trajektori 28,9 m;
pose 448; LTM 1846 nodes / 126.506 words; global LC 125; proximity LC 648; jarak
antar-keyframe 0,06 m; DB 743 MB (Depth 56/RGB 25/Features 10/Grid 5 %).

**Kalibrasi odometry:** jarak uji 0,5/1,0/1,5/2,0/2,5 m → odom 22/41/61/81/96 cm;
real = 0,3877×odom; R²=0,998; over-report 2,58×; PPR 1496→3858;
dist_per_tick 0,3255→0,1262 mm.

**Geometri robot:** wheelbase 0,5 m; track width 0,4 m; wheel radius 0,0775 m;
steering ±45°; min turning radius 0,5–0,9 m (Nav2 pakai 0,90 m).

**Parameter Nav2 kunci:** desired_linear_vel 0,3 m/s; minimum_turning_radius 0,90 m;
robot_radius 0,28 m; inflation_radius 0,25 m; resolusi costmap 0,05 m;
motion model DUBIN; reverse_penalty 2,0.

**Parameter RTAB-Map (mapping, baked di .db):** Reg/Strategy 2 (Vis+ICP);
Reg/Force3DoF true; Rtabmap/LoopThr 0,05; Rtabmap/DetectionRate 2,0;
Vis/FeatureType 8 (GFTT/BRIEF); Vis/MaxFeatures 1000; Vis/MinInliers 8;
Kp/MaxFeatures 400; GFTT/QualityLevel 0,001; RGBD/LocalRadius 5,0;
RGBD/LoopClosureReextractFeatures true; Optimizer/GravitySigma 0,3;
Grid/CellSize 0,05.

**Sensor:** RealSense D455 RGB & Depth 848×480×30; IMU gyro+accel aktif; align_depth
true. RPLIDAR C1 baudrate 460800. STM32 serial 115200 baud (V:{pwm},S:{sudut} /
E:{delta}).

---

## 6. CATATAN PENTING UNTUK CLAUDE CHAT

- Bila penulis (pengguna) menyebut "navigasi otonom berhasil", itu merujuk pengujian
  tim 19 Juni; bila diminta klaim formal, SELALU minta/menandai bukti runtime.
- Mode demo = TANPA failover (Nav2 → /cmd_vel langsung), rem darurat manual (R1) wajib.
- Fix arah kemudi (negasi steer_rad) statusnya: diterapkan + diverifikasi bench test;
  bila penulis belum re-test di robotnya, tandai "menunggu verifikasi hardware".
- Jangan menambah referensi/sitasi palsu. Daftar Pustaka lama sudah memadai; tambah
  sitasi hanya bila benar-benar relevan dan valid.
