# LAPORAN KORELASI MATA KULIAH — METODE NUMERIK

**Nama:** Muhammad Al Azhar Faradis  
**NRP:** 2040241017  
**Kelas:** A  
**Judul Project:** Autonomous Mobile Robot (AMR) Ackermann — 3D Mapping & Navigasi Otonom  
**Mata Kuliah:** Metode Numerik (VE230413)

> Dokumen ini = bahan baku laporan korelasi. Soal 1 & 2 (uraian) **ditulis tangan**
> menyalin isi di sini; checklist + analisis korelasi **diketik/di-scan jadi satu PDF**.
> Aturan dosen: hanya centang topik yang BENAR-BENAR ada buktinya di sini.

---

## RINGKASAN PROJECT (konteks untuk penguji)

AMR roda-empat dengan kemudi Ackermann (belok roda depan seperti mobil), dikendalikan
ROS 2 Humble di Intel NUC. Sensor: RPLIDAR C1 (LiDAR 2D, 720 berkas, 10 Hz),
Intel RealSense D455 (RGB-D + IMU), dan encoder roda via STM32. Tujuan: membangun
peta 3D ruangan (SLAM) lalu navigasi otonom. Pose robot diperkirakan dari Visual-
Inertial Odometry dan odometry roda (model kinematik Ackermann).

Seluruh metode numerik di bawah ini **muncul alami** dari pemrosesan data sensor diskret
menjadi besaran fisik (jarak, kecepatan, posisi, peta).

---

# BAGIAN A — IDENTIFIKASI TOPIK METODE NUMERIK

## Checklist yang DICENTANG (ada buktinya)

- [x] **Galat & angka signifikan**
- [x] **Interpolasi**
- [x] **Diferensiasi numerik**
- [x] **Integrasi numerik**
- [x] **Persamaan diferensial (ODE)**

## Checklist yang TIDAK dicentang (alasan kejujuran ke penguji)

- [ ] Akar persamaan (root finding) — tidak ada implementasi eksplisit di kode sendiri
- [ ] Sistem persamaan linear — ada, tapi di dalam library RTAB-Map (ICP/pose-graph), bukan kode sendiri
- [x] **Regresi / curve fitting** — kuat, didukung data empiris odom-vs-real (R² = 0,998,
  lihat Bagian B Fase 5)
- [ ] Optimasi numerik — ada, tapi tersembunyi di RTAB-Map (pose-graph optimization)

> Catatan: Regresi awalnya hanya didukung fit dinding LiDAR (RMSE 2,9 mm). Sekarang
> ada bukti lebih kuat: regresi linear odom-vs-real (5 titik pengukuran meteran),
> R² = 0,998 — sekaligus mengungkap galat kalibrasi `dist_per_tick` (lihat Fase 5).

---

## SOAL 1 (URAIAN, 40) — 2 topik terpilih

Topik dipilih: **(1) Integrasi Numerik** dan **(2) Diferensiasi Numerik**.
Keduanya ada di materi RPS (minggu 4–7) dan punya bukti angka konkret dari data project.

### TOPIK 1 — INTEGRASI NUMERIK

**(a) Metode spesifik yang dipakai**

Dua tempat integrasi numerik bekerja:

1. **Aturan Trapesium & Simpson 1/3** — menghitung luas sektor ruangan yang dipindai
   LiDAR memakai rumus luas polar:

   A = ½ ∫(θmin→θmax) r(θ)² dθ

   Integral tidak punya bentuk analitik (r(θ) hanya tersedia sebagai 720 titik diskret),
   sehingga didekati numerik:
   - Trapesium: A ≈ ½ · Δθ/2 · [f₀ + fₙ + 2Σfᵢ],  fᵢ = rᵢ²
   - Simpson 1/3: A ≈ ½ · Δθ/3 · [f₀ + fₘ + 4Σ(ganjil) + 2Σ(genap)]

   > **Catatan kejujuran:** Trapesium/Simpson di atas **bukan node ROS 2 yang berjalan
   > di robot** — tidak ada file produksi yang menghitung luas sektor ini. Ini adalah
   > **analisis numerik yang dijalankan terhadap data `/scan` nyata** (rekaman
   > `sensor_msgs/LaserScan` dari RPLIDAR C1, 128 berkas pertama) sebagai jawaban
   > soal UAS: menerapkan metode integrasi numerik pada data project sendiri.
   > Jika ditanya "kodenya di file mana?", jawabannya: perhitungan manual/skrip
   > analisis dari data scan, bukan node produksi.

2. **Metode Midpoint (RK2)** — integrasi kecepatan menjadi posisi (dead-reckoning) pada
   `odometry_publisher.py`, baris 205-208:

   ```python
   self.x += delta_dist * math.cos(self.theta + delta_theta / 2.0)
   self.y += delta_dist * math.sin(self.theta + delta_theta / 2.0)
   self.theta += delta_theta
   ```

   Posisi (x, y) diintegrasi dengan **metode titik-tengah (midpoint)**: arah gerak
   dievaluasi pada sudut rata-rata `θ + Δθ/2` (bukan `θ` di awal interval seperti
   Euler murni), sehingga galat per langkah O(h²) — lebih akurat dari Euler O(h)
   tanpa perlu kompleksitas RK4. Sudut `θ` sendiri tetap diakumulasi dengan Euler
   (`θ += Δθ`).

   > Catatan kecil: komentar pada baris kode tersebut menulis "Euler forward" —
   > tapi rumusnya secara matematis adalah midpoint. Ini contoh nyata bahwa
   > komentar kode bisa menyesatkan; identifikasi metode harus dari **rumus**,
   > bukan dari nama yang disebut programmer.

**(b) Bagian project tempat metode bekerja**

- Trapesium/Simpson: analisis numerik terhadap data scan LiDAR nyata (`/scan`) →
  estimasi luas sektor ruangan, sebagai jawaban soal UAS (lihat catatan kejujuran
  di atas).
- Midpoint: node `odometry_publisher.py`, tiap pesan encoder masuk → akumulasi posisi.

**(c) Pemicunya**

Data sensor bersifat **diskret** (720 berkas LiDAR per scan; satu tick encoder per
interval waktu). Besaran yang dicari (luas ruangan, posisi robot) adalah **integral
kontinu** yang tidak punya solusi analitik dari data diskret → wajib didekati numerik.

**Bukti angka (dari data scan nyata, 128 titik pertama):**

| Metode | Luas sektor A |
|---|---|
| Trapesium | 0.80599 m² |
| Simpson 1/3 | 0.80347 m² |
| **Selisih (galat antar-metode)** | **2.52 × 10⁻³ m²** |

Selisih kecil ini = ilustrasi langsung galat pemotongan (truncation error):
Simpson (orde h⁴) lebih akurat dari Trapesium (orde h²).

---

### TOPIK 2 — DIFERENSIASI NUMERIK

**(a) Metode spesifik yang dipakai**

1. **Beda Pusat (central difference)** — turunan jarak terhadap sudut `dr/dθ` pada
   array ranges LiDAR, untuk mendeteksi tepi/sudut objek:

   (dr/dθ)ᵢ ≈ (rᵢ₊₁ − rᵢ₋₁) / (2·Δθ)

   Nilai |dr/dθ| besar = lonjakan jarak mendadak = tepi dinding/objek.

2. **Beda Maju (forward difference)** — estimasi kecepatan dari perubahan posisi
   encoder pada `odometry_publisher.py`:

   vₖ ≈ Δs/Δt = (Δtick · dist_per_tick) / Δt

**(b) Bagian project tempat metode bekerja**

- Beda pusat: pra-pemrosesan scan LiDAR untuk segmentasi dinding (mendukung pembuatan
  peta & deteksi sudut ruangan).
- Beda maju: `odometry_publisher.py`, mengubah pembacaan encoder menjadi kecepatan
  linear yang lalu diintegrasi (Topik 1) menjadi posisi.

**(c) Pemicunya**

Sensor hanya memberi besaran "posisi" (jarak r, jumlah tick), bukan "laju". Untuk
mendapatkan laju perubahan (tepi = perubahan jarak; kecepatan = perubahan posisi)
dari data diskret, turunan didekati dengan beda-hingga.

**Bukti angka (dari data scan nyata):**

| Besaran | Nilai |
|---|---|
| \|dr/dθ\| maksimum | 3.801 m/rad pada berkas ke-57 |
| Transisi jarak di titik itu | 1.469 m → 1.403 m |
| Interpretasi | tepi objek / sudut dinding terdeteksi |

---

# BAGIAN B — PEMETAAN METODE NUMERIK PER FASE PROJECT

## Checklist fase yang DICENTANG

- [x] **Akuisisi data** — kalibrasi/konversi sensor (regresi), estimasi galat alat
- [x] **Preprocessing** — smoothing / resampling / isi data hilang (interpolasi)
- [x] **Pemodelan / komputasi inti** — solusi ODE (Euler/midpoint), identifikasi sistem
- [x] **Analisis turunan & akumulasi** — rate (diferensiasi) / total (integrasi)
- [x] **Validasi & evaluasi** — RMSE, bandingkan vs solusi eksak / antar-metode

## SOAL 2 (URAIAN, 40) — Alur data masuk → hasil

### Fase 1 — AKUISISI DATA
Sensor mentah masuk: LiDAR (`/scan`, 720 berkas @ 10 Hz), encoder (tick), IMU.
- **Kalibrasi/konversi (regresi linear):** tick encoder → jarak tempuh.
  Faktor skala `dist_per_tick = keliling roda / PPR = (2π·0,0775)/1496 = 0,3255 mm/tick`.
  Ini hubungan linear (regresi proporsional) jarak terhadap jumlah tick.
- **Estimasi galat alat:** array `intensities` LiDAR memuat nilai 0.0 = berkas tanpa
  pantulan valid (data hilang/dropout). Kovarians pose IMU/odometry mencatat
  ketidakpastian → masuk ke analisis galat.

### Fase 2 — PREPROCESSING
- **Interpolasi timestamp:** sensor punya laju beda (LiDAR 10 Hz, IMU accel 100 Hz,
  gyro 200 Hz). `ApproximateTimeSynchronizer` dan node `imu_merger` menyamakan waktu
  antar-sensor dengan mencocokkan/menyisipkan sampel pada timestamp bersama —
  prinsipnya interpolasi data terhadap waktu.
- **Isi data hilang (interpolasi):** berkas LiDAR yang dropout (range/intensity = 0)
  *secara prinsip* dapat diisi dengan interpolasi linear/spline dari berkas
  tetangga yang valid — metode yang relevan untuk gap ini. (Belum ada node
  produksi yang menjalankan interpolasi ini; framing-nya adalah "metode yang
  cocok diterapkan", bukan "sudah diimplementasikan".)

### Fase 3 — PEMODELAN / KOMPUTASI INTI
- **Solusi ODE (Euler + Midpoint):** gerak robot dimodelkan persamaan diferensial
  kinematik Ackermann:

  dx/dt = v·cos θ ; dy/dt = v·sin θ ; dθ/dt = (v/L)·tan φ   (L = wheelbase = 0,5 m)

  Diselesaikan numerik tiap langkah waktu: `θ` dengan Euler (`θ += Δθ`), `x,y`
  dengan midpoint (`θ + Δθ/2`) → lintasan robot. Lihat Soal 1 Topik 1.
- **Identifikasi sistem / SLAM:** RTAB-Map menggabung VIO + LiDAR membangun peta
  (di balik layar: sistem persamaan linear & optimasi pose-graph).

### Fase 4 — ANALISIS TURUNAN & AKUMULASI
- **Diferensiasi (rate):** kecepatan v = Δs/Δt (beda maju); deteksi tepi dr/dθ (beda
  pusat). Lihat Soal 1 Topik 2.
- **Integrasi (total):** posisi = ∫v dt (midpoint, di `odometry_publisher.py`);
  luas ruangan = ½∫r²dθ (Trapesium/Simpson, analisis data nyata). Lihat Soal 1 Topik 1.

### Fase 5 — VALIDASI & EVALUASI
- **Bandingkan antar-metode:** luas sektor Trapesium (0,80599 m²) vs Simpson
  (0,80347 m²), selisih 2,5×10⁻³ m² → mengukur galat pemotongan.
- **RMSE fit dinding:** regresi garis kuadrat-terkecil pada segmen dinding LiDAR
  memberi RMSE residual **2,9 mm** → membuktikan titik membentuk garis lurus (dinding
  rata) dan sensor akurat.
- **Bandingkan vs referensi (odom vs meteran):** robot diperintah menempuh jarak
  target 0,5/1,0/1,5/2,0/2,5 m, posisi `/odom` dicatat dan jarak fisik diukur dengan
  meteran. Hasil:

  | Target (m) | Odom (m) | Real/meteran (m) | Galat absolut (m) | Galat relatif |
  |---|---|---|---|---|
  | 0,5 | 0,551 | 0,22 | 0,331 | 150,5% |
  | 1,0 | 1,046 | 0,41 | 0,636 | 155,1% |
  | 1,5 | 1,553 | 0,61 | 0,943 | 154,6% |
  | 2,0 | 2,043 | 0,81 | 1,233 | 152,2% |
  | 2,5 | 2,534 | 0,96 | 1,574 | 164,0% |

  **Regresi linear** (real = a·odom + b), metode kuadrat-terkecil (normal equations):

  ```
  [ Σodom²  Σodom ] [a]   [Σ(odom·real)]
  [ Σodom    n    ] [b] = [   Σreal     ]

  [ 14,4045  7,7270 ] [a]   [5,5849]
  [  7,7270  5      ] [b] = [3,0100]
  ```

  Hasil: **a = 0,3789**, **b = 0,0165**, **R² = 0,998**, RMSE = 0,012 m.

  Linearitas R² = 0,998 menunjukkan hubungan odom-vs-real **konsisten** (bukan noise
  acak) → ini galat **sistematik kalibrasi**, bukan galat alat random. Rasio rata-rata
  odom/real ≈ **2,55×**, konstan di semua jarak → mengindikasikan parameter
  `dist_per_tick` (Lampiran, 0,3255 mm/tick) terlalu besar dengan faktor ~2,55, sehingga
  odometry melaporkan jarak ~2,55× lebih jauh dari gerak fisik aktual robot.
  *(Perbaikan parameter ini didiskusikan terpisah di luar laporan — di sini cukup
  sebagai bukti penerapan regresi linear pada data project.)*

---

# LAMPIRAN — RUMUS & ANGKA KUNCI

## Rumus

**Aturan Trapesium (komposit):**
∫ₐᵇ f(x)dx ≈ (h/2)[f₀ + 2f₁ + 2f₂ + … + 2fₙ₋₁ + fₙ],  h = (b−a)/n

**Aturan Simpson 1/3 (komposit):**
∫ₐᵇ f(x)dx ≈ (h/3)[f₀ + 4f₁ + 2f₂ + 4f₃ + … + 4fₙ₋₁ + fₙ]

**Beda Pusat (turunan pertama):**
f′(xᵢ) ≈ [f(xᵢ₊₁) − f(xᵢ₋₁)] / (2h),  galat O(h²)

**Beda Maju:**
f′(xᵢ) ≈ [f(xᵢ₊₁) − f(xᵢ)] / h,  galat O(h)

**Metode Euler (solusi ODE y′ = f(t,y)):**
yₖ₊₁ = yₖ + h·f(tₖ, yₖ),  galat O(h)

**Metode Midpoint / RK2 (dipakai di `odometry_publisher.py` untuk x,y):**
yₖ₊₁ = yₖ + h·f(tₖ + h/2, yₖ),  galat O(h²)

**Luas polar (basis integrasi LiDAR):**
A = ½ ∫(θmin→θmax) r(θ)² dθ

## Spesifikasi sensor (dihitung dari header scan)

| Besaran | Nilai |
|---|---|
| Jumlah berkas | 720 |
| FOV | 359,0° |
| Resolusi sudut (Δθ) | 0,4993°/berkas = 0,008714 rad |
| Frekuensi scan | 9,985 Hz |
| range_min / range_max | 0,15 m / 16,0 m |

## Parameter model Ackermann (dari `odometry_publisher.py`)

| Parameter | Nilai |
|---|---|
| wheel_radius | 0,0775 m |
| wheelbase (L) | 0,5 m |
| PPR encoder | 1496 |
| dist_per_tick | 0,3255 mm |

## Hasil hitung (data scan nyata, 128 titik pertama)

| Analisis | Hasil |
|---|---|
| Luas sektor — Trapesium | 0,80599 m² |
| Luas sektor — Simpson 1/3 | 0,80347 m² |
| Galat antar-metode | 2,52 × 10⁻³ m² |
| \|dr/dθ\| maksimum (tepi) | 3,801 m/rad @ berkas 57 |
| RMSE fit dinding (regresi) | 2,9 mm |

---

*Sumber data: pesan `sensor_msgs/LaserScan` dari RPLIDAR C1 (data_lidar_mentah.txt)
dan parameter node `odometry_publisher.py` repository AMR.*
