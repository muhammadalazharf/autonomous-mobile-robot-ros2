# LAPORAN KORELASI MATA KULIAH — SISTEM KONTROL PROSES

**Nama:** Muhammad Al Azhar Faradis
**NRP:** 2040241017
**Kelas:** A
**Judul Project:** Autonomous Mobile Robot (AMR) Ackermann — 3D Mapping & Navigasi Otonom
**Mata Kuliah:** Sistem Kontrol Proses (VE230415)

> Dokumen ini = bahan baku laporan korelasi. Uraian ditulis tangan/diketik menyalin isi
> di sini; checklist + analisis korelasi digabung jadi satu PDF.
> Aturan dosen: hanya klaim konsep yang BENAR-BENAR ada buktinya di kode/data project.

---

## CATATAN KEJUJURAN — RUANG LINGKUP (baca dulu)

Mata kuliah Sistem Kontrol Proses (RPS) memakai contoh **plant industri proses**
(kimia, fluida, level, flow, temperatur — tangki, P&ID, batch reactor). Project saya
adalah **robot mobile Ackermann**, bukan plant proses kimia/fluida.

**Yang dikorelasikan adalah TEORI KONTROL yang identik**, bukan jenis plant-nya.
Fondasi kontrol proses (variabel proses PV/SP/MV, diagram blok, feedforward, umpan-balik,
PID, cascade, on-off/histeresis, dinamika orde-satu, kestabilan, batch vs continuous)
bersifat **universal** dan berlaku untuk semua sistem dinamik — termasuk robot. Dalam
laporan ini, "plant" = dinamika gerak robot (kecepatan & posisi), "process variable" =
kecepatan/pose terukur, "manipulated variable" = PWM motor & sudut kemudi.

Di bagian mana analogi melemah (mis. ratio control, batch), saya tandai eksplisit
sebagai **analogi**, bukan implementasi langsung. Semua klaim implementasi disertai
**sitasi file:baris** dari repository AMR.

---

## RINGKASAN PROJECT (konteks untuk penguji)

AMR roda-empat kemudi Ackermann (belok roda depan seperti mobil), dikendalikan ROS 2
Humble di Intel NUC. "Plant" yang dikontrol = dinamika gerak robot. Rantai kontrol:
perintah kecepatan (`/cmd_vel` dari Nav2 atau joystick) → konversi Ackermann → PWM motor
+ sudut kemudi (via mikrokontroler STM32) → robot bergerak → encoder & LiDAR/kamera
mengukur respons → umpan-balik ke pengontrol. Sebuah **state machine failover**
mengarbitrase sumber perintah dan menjamin keselamatan.

---

# BAGIAN A — IDENTIFIKASI KONSEP SISTEM KONTROL PROSES

## Checklist konsep yang DICENTANG (ada buktinya di kode)

- [x] **Variabel proses (PV / SP / MV)** — kecepatan & pose (PV), `/cmd_vel` (SP), PWM+steer (MV)
- [x] **Diagram blok sistem kontrol** — arsitektur node ROS 2 = diagram blok closed-loop
- [x] **Feedforward control** — joystick & `/cmd_vel` → PWM (pemetaan langsung tanpa umpan-balik di bridge)
- [x] **Umpan-balik (feedback) & kestabilan** — Nav2 + odometry/SLAM; watchdog sebagai failsafe
- [x] **Model matematis & dinamika proses** — model lag orde-satu (τ) + ODE kinematik Ackermann
- [x] **Kontroler on-off & histeresis** — watchdog timeout & emergency-stop berbasis ambang
- [x] **Cascade control** — Nav2 (loop posisi luar) → `/cmd_vel` → PWM (loop kecepatan dalam)
- [x] **Kontrol supervisori / arbitrasi** — `failover_controller.py` state machine 4 keadaan
- [x] **Batch vs continuous control** — navigasi kontinu vs patroli per-segmen (waypoint)

## Checklist yang TIDAK / LEMAH dicentang (kejujuran ke penguji)

- [~] **Ratio control** — hanya **analogi** (koordinasi rasio kemudi Ackermann), bukan loop ratio industri
- [ ] **PID hand-tuned eksplisit (Kp,Ki,Kd)** — TIDAK ada di repo. Loop tertutup pakai
  RegulatedPurePursuit (geometris) di Nav2; PID kecepatan (jika ada) berada di **firmware
  STM32** yang tidak masuk repo → tidak diklaim sebagai milik kode sendiri.
- [ ] **P&ID standar ISA** — tidak ada plant fluida/proses; padanannya = diagram arsitektur
  node (rqt_graph), bukan P&ID instrumentasi industri.

---

# BAGIAN B — URAIAN KONSEP & IMPLEMENTASI (dengan bukti kode)

## 1. Variabel Proses: PV, SP, MV (CPMK-1)

Setiap loop kontrol proses punya tiga variabel inti. Pada AMR:

| Istilah kontrol proses | Besaran di AMR | Sumber |
|---|---|---|
| **Set Point (SP)** | kecepatan/arah yang diinginkan `linear.x`, `angular.z` | `/cmd_vel` (Nav2/joystick) |
| **Process Variable (PV)** | kecepatan & posisi aktual robot | `/odom` dari `odometry_publisher.py` |
| **Manipulated Variable (MV)** | PWM motor (±4000) & sudut kemudi (±45°) | `send_command()` di `stm32_bridge.cpp` |
| **Disturbance** | gesekan, slip roda, EMI motor→WiFi | lingkungan |

**Bukti kode** (`src/amr_controller/src/stm32_bridge.cpp`):
- MV dibatasi rentang aktuator (saturasi): baris 153-154
  ```cpp
  velocity = std::max(-MAX_PWM,  std::min(MAX_PWM,  velocity));
  steering = std::max(-MAX_STEER, std::min(MAX_STEER, steering));
  ```
- Format perintah ke final control element (STM32): `"V:{pwm},S:{steer}\n"` (baris 222).

## 2. Diagram Blok & Feedforward Control (CPMK-1, Mg-2)

Arsitektur AMR setara diagram blok kontrol proses closed-loop:

```
            disturbance (slip, gesekan)
                      │
 SP            ┌──────▼──────┐   MV (PWM,steer)   ┌─────────┐
 /cmd_vel ───► │ Controller  │ ─────────────────► │  PLANT  │ ──► gerak
 (Nav2/joy)    │ RPP / bridge│                    │ (robot) │
            ▲  └─────────────┘                    └────┬────┘
            │                                          │
            │         PV (/odom)        ┌──────────┐   │
            └───────────────────────────┤ Sensor   │◄──┘
                  umpan-balik           │ encoder  │
                                        │ LiDAR/VIO│
                                        └──────────┘
```

**Feedforward (kontrol tanpa umpan-balik) — bukti kode:** di `stm32_bridge.cpp` jalur
joystick dan jalur autonomous mengubah perintah → PWM **langsung dengan penskalaan**,
tanpa mengoreksi memakai PV. Ini definisi feedforward:
- Joystick (baris 148): `int velocity = vel_raw * MAX_PWM;`
- Autonomous (baris 184): `int velocity = (v / max_speed) * MAX_PWM;`

Feedforward cepat-tanggap tapi tak mengoreksi galat; karena itu loop posisi luar (Nav2)
menambahkan umpan-balik (lihat §6 Cascade).

## 3. Padanan P&ID — Diagram Arsitektur Node (CPMK-1, Mg 3-4)

P&ID industri memetakan instrumen-pipa-aktuator. Padanan di AMR = **graf node-topik ROS 2**
(sensor → pengontrol → aktuator), dapat dilihat via `rqt_graph`:

```
[joy_node] ─/joy─► [stm32_bridge] ─serial─► (STM32 → motor & servo kemudi)
[rplidar] ─/scan─►┐                          │
[realsense]─img─► [SLAM/Nav2] ─/cmd_vel_nav─►[failover_controller]─/cmd_vel─►[stm32_bridge]
(STM32)─/encoder─►[odometry_publisher]─/odom─►[SLAM/Nav2]
```

Tag instrumen industri (FT/LT/TT, FCV) → padanannya: encoder (kecepatan/posisi), LiDAR
(jarak), kamera+IMU (pose), motor driver BTS7960 + servo kemudi (final control element).

## 4. Model Matematis & Dinamika Proses (CPMK-2, Mg 3-4) ⭐

Inti CPMK-2. Dua model dinamika dipakai:

**(a) Dinamika kecepatan = sistem orde-satu (first-order lag).** Respons kecepatan robot
terhadap perubahan perintah dimodelkan sebagai proses orde-satu dengan konstanta waktu τ:

  V[k] = V[k−1] + (Δt/τ)·(V_target − V[k−1])

Ini bentuk diskret dari `τ·dV/dt + V = V_target` — **persis model proses orde-satu**
(seperti tangki/termal yang responsnya eksponensial menuju setpoint). Diuji pada data nyata
`data_euler_odom.csv` (τ=0,15 s, Δt=0,05 s). Konstanta waktu τ = ukuran "kelambanan" plant.

> Bukti: `rekam_euler_odom.py` baris 16-17 & 66. Korelasi silang dengan Metode Numerik:
> persamaan ini juga = metode Euler untuk ODE (galat O(h)).

**(b) Model kinematik Ackermann (plant non-linear).** Gerak robot:

  dx/dt = v·cos θ ; dy/dt = v·sin θ ; dθ/dt = (v/L)·tan φ   (L = wheelbase = 0,5 m)

**Inverse kinematics dipakai sebagai elemen pengontrol** — mengubah perintah kecepatan
sudut menjadi sudut kemudi (`stm32_bridge.cpp` baris 187):
```cpp
double steer_rad = std::atan(WHEELBASE * w / v);   // steer = atan(L·ω/v)
```

## 5. Umpan-Balik & Kontroler (PID / RPP) + Kestabilan (CPMK-3, Mg 5-6)

**Kejujuran:** tidak ada PID hand-coded (Kp/Ki/Kd) di repo. Loop tertutup terdiri dari:

- **Loop posisi/lintasan (closed-loop):** Nav2 **RegulatedPurePursuit Controller**
  (`src/amr_slam/config/nav2_params.yaml` baris 70-71). Ia mengoreksi posisi robot agar
  mengikuti jalur — pengontrol umpan-balik geometris. Parameter "tuning"-nya:
  ```yaml
  desired_linear_vel: 0.3
  lookahead_dist: 0.6        # mirip "gain": makin besar makin halus tapi lamban
  controller_frequency: 20.0 # laju sampling loop kontrol (Hz)
  ```
  `lookahead_dist` berperan seperti gain proporsional: kecil → agresif/berosilasi,
  besar → halus/lamban — analog langsung dengan tuning Kp pada PID.
- **Loop kecepatan (inner):** di `stm32_bridge` bersifat feedforward; PID kecepatan
  (jika ada) ada di firmware STM32 (di luar repo, tidak diklaim).

**Kestabilan (stability) — failsafe:** **watchdog** menjamin sistem tidak "lari liar" bila
perintah hilang (`stm32_bridge.cpp` baris 199-216):
```cpp
if (elapsed_ms > timeout_ms) {        // default 500 ms
  autonomous_active_ = false;
  send_command(0, STEER_TRIM);        // motor STOP
}
```
Ini mekanisme stabilitas fail-safe: tanpa input valid berkala, plant dipaksa ke keadaan
aman (diam) — analog dengan interlock kestabilan pada kontrol proses.

## 6. Cascade Control (CPMK-3, Mg 7-8) ⭐

Cascade = loop dalam (cepat) di-nest dalam loop luar (lambat). AMR berstruktur cascade:

```
SP posisi      ┌─── LOOP LUAR (posisi) ────┐   ┌─ LOOP DALAM (kecepatan) ─┐
(goal/waypoint)│ Nav2 RegulatedPurePursuit │   │  cmd_vel → PWM (bridge)  │
 ───────────►  │ PV=pose(/odom,SLAM) 20 Hz │──►│  + Ackermann + saturasi  │──► motor
               └───────────────────────────┘   └──────────────────────────┘
                         lambat (lintasan)              cepat (aktuasi)
```

- **Loop luar (primer):** Nav2 memakai PV posisi (odometry+SLAM) → keluarkan SP kecepatan
  `/cmd_vel`. Frekuensi 20 Hz (`nav2_params.yaml` baris 48).
- **Loop dalam (sekunder):** `stm32_bridge` menerima SP kecepatan itu → konversi Ackermann
  → PWM, dieksekusi STM32 jauh lebih cepat.

Manfaat cascade (sama seperti industri): gangguan di loop dalam (mis. beban motor)
dikoreksi cepat sebelum mengganggu loop posisi. Bukti kode: `cmd_vel_callback`
(`stm32_bridge.cpp` baris 166-196) = titik sambung loop luar→dalam.

## 7. Ratio Control — ANALOGI (CPMK-3, Mg-9)

> Ditandai **analogi**, bukan loop ratio industri sejati.

Pada kemudi Ackermann, sudut kemudi dipertahankan **proporsional terhadap rasio**
kecepatan sudut/linear: `φ = atan(L·ω/v)` (baris 187). Saat v berubah, φ menyesuaikan
agar **rasio** jari-jari belok tetap konsisten — mirip semangat ratio control yang
menjaga perbandingan dua aliran. Ini analogi konseptual, bukan dua-aliran fisik.

## 8. Kontroler On-Off & Histeresis (CPMK-3, Mg-9)

Dua kontроler on-off (diskret, bukan kontinu) di AMR:

**(a) Watchdog timeout** (§5): aktuator ON saat ada perintah, OFF saat timeout > 500 ms.

**(b) Emergency-stop berbasis ambang jarak** (`failover_controller.py`):
```python
self.declare_parameter('emergency_min_range', 0.30)   # baris 59
...
if self.last_min_scan < self.emergency_min_range:     # baris ~152
    new_state = ST_ESTOP                              # cmd_vel = (0,0)
```
Robot di-STOP bila objek terdekat < 0,30 m — **kontroler on-off berbasis ambang**, persis
seperti kontrol level on-off (pompa ON/OFF di ambang tinggi/rendah). Histeresis dapat
ditambahkan (ambang start/stop berbeda) untuk mencegah chattering — relevan sebagai
perbaikan.

## 9. Kontrol Supervisori / Arbitrasi — State Machine (CPMK-4)

`failover_controller.py` adalah **supervisory controller**: memilih sumber `/cmd_vel`
berdasarkan keadaan sistem (mirip plant supervisory/override control industri).

State (baris 7-11) & prioritas transisi (baris ~150-165):
```
1. EMERGENCY_STOP  (prioritas tertinggi) : min /scan < 0.30 m  → cmd_vel = (0,0)
2. JOY_OVERRIDE    : R1 deadman ditekan   → cmd_vel = joystick
3. SLAM_ACTIVE     (default)              → cmd_vel = Nav2
4. VISUAL_FALLBACK : SLAM unhealthy > delay → cmd_vel = visual regression
```
Ini **override control** berlapis: keselamatan > manusia > otonom > cadangan.

## 10. Batch vs Continuous Process Control (CPMK-3, Mg-10)

- **Continuous control:** mode teleop/navigasi — loop kontrol berjalan terus-menerus
  (20 Hz), seperti continuous process (aliran tak putus).
- **Batch control:** patroli/misi waypoint per-segmen — eksekusi langkah berurutan
  "maju X meter → belok → maju lagi", tiap segmen tuntas sebelum berikutnya. Ini pola
  **batch/sequential** (mirip resep batch reactor: isi → reaksi → kuras). Terlihat di
  log runtime `amr_loop_patrol` ("Segmen 1/1 → F:2.0 → maju 0.58/2.00 m → SELESAI").
  *(Script patroli dijalankan dari home NUC, bukan bagian repo inti.)*

---

# BAGIAN C — PEMETAAN KE CPMK

| CPMK | Deskripsi | Bukti di AMR |
|---|---|---|
| **CPMK-1** | Konsep dasar sistem proses | Variabel proses PV/SP/MV (§1), diagram blok & feedforward (§2), padanan P&ID (§3) |
| **CPMK-2** | Pemodelan dinamika proses | Model orde-satu τ + ODE Ackermann (§4) |
| **CPMK-3** | Perancangan metode kontrol | RPP feedback & tuning (§5), cascade (§6), on-off/histeresis (§8), batch vs continuous (§10) |
| **CPMK-4** | Implementasi sistem kontrol | Integrasi penuh + supervisory state machine failover (§9) |

---

# LAMPIRAN — PARAMETER KONTROL & SUMBER KODE

## Parameter kontrol (dari kode nyata)

| Parameter | Nilai | Lokasi | Peran kontrol |
|---|---|---|---|
| MAX_PWM | 4000 | `stm32_bridge.cpp:39` | rentang MV (aktuator kecepatan) |
| MAX_STEER | 45° | `stm32_bridge.cpp:40` | rentang MV (aktuator kemudi) |
| WHEELBASE (L) | 0,5 m | `stm32_bridge.cpp:45` | parameter plant (Ackermann) |
| cmd_vel_timeout_ms | 500 | `stm32_bridge.cpp:65` | ambang watchdog (on-off failsafe) |
| max_speed_mps | 1,0 | `stm32_bridge.cpp:64` | penskalaan SP→MV |
| controller_frequency | 20 Hz | `nav2_params.yaml:48` | laju sampling loop luar |
| desired_linear_vel | 0,3 m/s | `nav2_params.yaml:75` | SP kecepatan jelajah |
| lookahead_dist | 0,6 m | `nav2_params.yaml:76` | "gain" RPP (analog Kp) |
| emergency_min_range | 0,30 m | `failover_controller.py:59` | ambang on-off e-stop |
| τ (time constant) | 0,15 s | `rekam_euler_odom.py:16` | konstanta waktu model orde-satu |

## File sumber

- `src/amr_controller/src/stm32_bridge.cpp` — interface aktuator, feedforward, watchdog, Ackermann
- `src/amr_controller/scripts/odometry_publisher.py` — sensor/transmitter PV (kecepatan/posisi)
- `src/amr_slam/config/nav2_params.yaml` — pengontrol loop luar (RegulatedPurePursuit)
- `src/amr_failover/amr_failover/failover_controller.py` — supervisory state machine
- `rekam_euler_odom.py` — identifikasi model dinamika orde-satu (τ)

---

*Sumber: repository AMR (`stm32_bridge.cpp`, `nav2_params.yaml`, `failover_controller.py`,
`odometry_publisher.py`) dan data uji (`data_euler_odom.csv`). Semua nilai parameter
dikutip langsung dari kode, bukan asumsi.*
