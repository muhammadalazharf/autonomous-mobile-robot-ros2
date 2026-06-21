# Defense Brief Sidang — Autonomous Mobile Robot (AMR)

**Untuk:** Muhammad Al Azhar Faradis (2040241017) & Tim PjBL 4-24
**Repo:** `muhammadalazharf/autonomous-mobile-robot-ros2` — branch `claude/zealous-darwin-6l4bs5`
**Tujuan:** jawaban defensible untuk 7 pertanyaan kritis penguji, dengan sitasi
`file:baris` dan penanda jujur status bukti.

**Legenda status:**
[VF] Terverifikasi dari file repo · [VL] Terverifikasi dari data/log ·
[PG] Catatan progress · [BT] Belum terbukti (perlu bukti runtime)

---

## Q1 — Drivetrain: 4WD vs RWD, geometri Ackermann

### Jawaban
Robot **dirancang 4WD** dengan kemudi **Ackermann pada 2 roda depan**.

**Bukti file** (`src/amr_description/urdf/amr_description.urdf.xacro`):
- Baris 7: `Drive : 4WD via 1 motor PG45 + 2 differentials + shaft`
- Baris 9: `Steering: Servo Ackermann pada 2 roda depan`
- 4 roda dimodelkan (`xacro:wheel`): `rear_left` (baris 109), `rear_right` (116),
  `front_left` (138), `front_right` (145) — semua joint roda `continuous Y`.
- 2 roda depan di atas `steering_link` dengan `steering_joint = revolute Z` (baris 126).

### Data geometri (URDF baris 36–50) [VF]
| Parameter | Nilai |
|-----------|-------|
| Wheelbase | 0,500 m |
| Track width | 0,400 m |
| Wheel radius | 0,0775 m (D = 155 mm) |
| Wheel width | 0,060 m |
| Chassis (P×L×T) | 0,600 × 0,350 × 0,150 m |
| Steering range | ±45° |
| Min turning radius | 0,90 m (dipakai Nav2) |
| LiDAR height (z) | 0,250 m |
| Camera (x, z) | 0,350 m, 0,200 m |

### ⚠️ Titik rawan & cara menjawab
URDF hanya **memodelkan 4 roda berputar**; "4WD" (keempat roda **digerakkan** dari
1 motor lewat shaft + 2 diferensial) adalah **pernyataan desain mekanik**, tidak bisa
dibuktikan dari URDF. **Konfirmasi fisik dulu**: apakah shaft benar menyalurkan tenaga
ke poros depan DAN belakang. Jika di robot hanya poros belakang yang terhubung, jawab
jujur **RWD dengan kemudi Ackermann depan** — jangan klaim 4WD bila mekanik tidak
mendukung. Status: [VF] untuk model & geometri; [PG/perlu konfirmasi fisik] untuk
klaim "4 roda digerakkan".

---

## Q2 — Siapa publish `map→odom`? (AMCL vs RTAB-Map)

### Jawaban
**RTAB-Map** yang menerbitkan `map→odom`. **AMCL TIDAK aktif (OFF).**

**Bukti file:**
- `src/amr_3d_mapping/config/rtabmap_localization.yaml`:
  - baris 14: `map_frame_id: map`
  - baris 15: `odom_frame_id: odom`
  - baris 29: `publish_tf: true` → node `rtabmap` menerbitkan **map→odom**.
- **AMCL OFF — terbukti dari launch:** `src/amr_slam/launch/nav2.launch.py:26` hanya
  meng-include `nav2_bringup/navigation_launch.py`. Launch ini **tidak men-spawn**
  `amcl` maupun `map_server` (hanya controller, planner, behavior, bt_navigator,
  smoother, velocity_smoother, waypoint). Section `amcl:` di `nav2_params.yaml:13`
  adalah **sisa konfigurasi (vestigial)** yang **tidak pernah dijalankan**.

### TF tree lengkap (mode RTAB-Map localization) [VF]
```
map → odom        : node rtabmap            (rtabmap_localization.yaml:29, publish_tf true)
odom → base_link  : node rgbd_odometry (VIO) (rtabmap_localization.launch.py:107, publish_tf True)
base_link → {laser_frame, camera_link, roda, steering} : robot_state_publisher (static, URDF)
base_footprint → base_link : static (URDF, z = wheel_radius)
```

**Kunci:** wheel `odometry_publisher` `publish_tf` bersifat **kondisional** — hanya
aktif saat `use_rtabmap=false` (`amr_full.launch.py`). Jadi di mode RTAB-Map,
**VIO (rgbd_odometry)** yang menerbitkan `odom→base_link`, **tanpa konflik TF**.

### ⚠️ Catatan untuk dicek di runtime
Topik `/odom` bisa diterbitkan dua node (wheel + VIO) bila keduanya jalan. Pastikan
saat demo hanya satu sumber `/odom` yang dikonsumsi Nav2 (`bt_navigator odom_topic:
/odom`, `nav2_params.yaml:22`). Status: [VF] untuk TF; [BT] untuk konfirmasi runtime
single-publisher `/odom`.

---

## Q3 — Konversi `cmd_vel → Ackermann`: di mana?

### Jawaban
Di **`src/amr_controller/src/stm32_bridge.cpp`**, node **`stm32_bridge`**, fungsi
**`cmd_vel_callback`**. Ini jantung navigasi Ackermann. [VF]

### Logika konversi (stm32_bridge.cpp)
```cpp
void cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg) {
  // gate: hanya jika autonomous_enabled=true DAN R1 tidak ditekan
  double v = msg->linear.x;                       // kecepatan linear (m/s)
  double w = msg->angular.z;                       // yaw rate (rad/s)
  int velocity = (v / max_speed) * MAX_PWM;        // -> PWM motor (MAX_PWM=4000)
  int steering = STEER_TRIM;
  if (fabs(v) > 0.05) {
    double steer_rad = -atan(WHEELBASE * w / v);   // <- Ackermann steering angle
    steering = steer_rad * 180/M_PI + STEER_TRIM;  // -> derajat servo
  }
  // clamp lalu kirim serial: "V:{pwm},S:{sudut}\n"  (115200 baud)
}
```

### Data protokol [VF]
| Item | Nilai |
|------|-------|
| Topik input | `/cmd_vel` (geometry_msgs/Twist) |
| Rumus kemudi | `steer = −atan(wheelbase · ω / v)` |
| Wheelbase | 0,5 m (`#define WHEELBASE 0.5f`) |
| MAX_PWM / MAX_STEER / STEER_TRIM | 4000 / 45° / −5° |
| Format TX | `V:{pwm},S:{sudut}\n` |
| Format RX | `E:{delta}\n` (encoder) |
| Baudrate | 115200 |
| Gate | `autonomous_enabled` (default false) |

---

## Q4 — Tanda kemudi (kiri = kiri)

### Jawaban — STATUS: [BT] PERLU BUKTI RUNTIME
Fix tanda kemudi **sudah diterapkan di kode** tapi **belum diverifikasi di NUC-mu**.

**Bukti file:** `stm32_bridge.cpp`, `cmd_vel_callback`:
`double steer_rad = -std::atan(WHEELBASE * w / v);` (tanda **negatif**).
- Asal: bench test Mervi (commit `3d16e7d`, 20 Jun) — `angular.z` positif (perintah
  kiri) sebelumnya membuat roda belok kanan; negasi membalik agar kiri = kiri.
- Diadopsi ke repo kamu: commit `fec1ee5`.
- **Velocity TIDAK dinegasi** (maju/mundur sudah benar; kabel motor ditukar fisik).

### Cara verifikasi (wajib sebelum klaim final)
```bash
cd ~/amr_starter && colcon build --packages-select amr_controller && source install/setup.bash
# kirim goal/twist belok kiri -> roda depan HARUS belok kiri
```
Sampai langkah ini lulus, label kemudi otonom **"perlu bukti runtime"**. Jangan
klaim final di sidang sebelum diverifikasi di robot.

---

## Q5 — R²=0,998 / PPR 3858 (angka kuantitatif utama)

### Jawaban
Kalibrasi empiris encoder via uji jarak. **Sumber:** `amr_full.launch.py:143-148`
(komentar kalibrasi) + data uji `data_euler_odom.csv` & `jalan_maju.zip` (14 Jun). [VL]

### Data lengkap
| Percobaan | Jarak terbaca odometry (m) | Jarak nyata meteran (m) | Rasio nyata/odom |
|-----------|----------------------------|--------------------------|------------------|
| 1 | 0,5 | 0,22 | 0,440 |
| 2 | 1,0 | 0,41 | 0,410 |
| 3 | 1,5 | 0,61 | 0,407 |
| 4 | 2,0 | 0,81 | 0,405 |
| 5 | 2,5 | 0,96 | 0,384 |

**Definisi regresi (harus kamu kuasai persis):**
- **Jumlah titik:** 5
- **Sumbu:** X = jarak **terbaca odometry**; Y = jarak **nyata (meteran)**
- **Model:** linear **proporsional lewat origin** → `real = 0,3877 × odom`
- **R² = 0,998** (goodness-of-fit garis real-vs-odom)
- **Over-report:** 1 / 0,3877 = **2,58×** (odometry melebih-lebihkan jarak)

**Koreksi PPR:**
- PPR efektif = PPR_lama / slope = 1496 / 0,3877 = **3858**
- dist_per_tick = 2π·r / PPR = 2π·0,0775 / 3858 = **0,1262 mm** (dari 0,3255 mm)
- Korelasi mata kuliah: **Metode Numerik — regresi kuadrat terkecil**

### ⚠️ Antisipasi serangan penguji + jawaban
| Pertanyaan penguji | Jawaban defensible |
|--------------------|--------------------|
| "5 titik + fit lewat origin → R² tinggi itu mudah." | Akui: ini kalibrasi kasar 1-sumbu (gerak lurus). Cukup untuk skala jarak translasi; **belum** mencakup kalibrasi rotasi/yaw. Rekomendasi: tambah titik, uji bolak-balik, uji belok. |
| "Over-report 2,58× itu besar, kenapa?" | Asumsi PPR teoretis salah (rantai 11 PPR × 4 quad × 1:34). Setelah dikoreksi ke 3858, residual fit R²=0,998 → kalibrasi empiris berhasil mengoreksi. |
| "Bukti datanya mana?" | `data_euler_odom.csv` (442 baris), `jalan_maju.zip` (8 run odom 14 Jun) — siapkan plot real-vs-odom + garis regresi. |
| "Kenapa bukan tick vs jarak langsung?" | Diturunkan: slope real-vs-odom dipakai mengoreksi PPR; ekuivalen, lebih mudah diukur lapangan (meteran). |

---

## Q6 — Branch mana yang didemokan?

### Jawaban (keputusan + pernyataan eksplisit)
Dua repo punya karakter berbeda:
- **Branch kamu** (`claude/zealous-darwin-6l4bs5`): kuat **dokumentasi/analisis**;
  fix inti selaras Mervi; **BELUM** ada fix runtime Mervi 20-21 Jun.
- **Repo Mervi `main`**: kuat **runtime**, teruji lapangan lebih lanjut.

**Fix runtime Mervi yang BELUM ada di branch kamu:**
| Commit Mervi | Isi |
|--------------|-----|
| `75c86f3` (21 Jun) | Filter LiDAR self-scan + inflation lebih kecil |
| `bfba43d` (20 Jun) | All-odom navigation, radius lebih kecil |
| `a91d937` (20 Jun) | Safety cap + minimal BT (perbaikan overshoot) |
| `a9b5fcf` (20 Jun) | `log_localization.py` (bukti runtime lokalisasi) |
| `e134319` (20 Jun) | LoopThr 0.11→0.05, MinInliers 10→**6** (kamu pakai 8) |

**Rekomendasi:** demo di **branch terintegrasi tim (Mervi `main`)** karena runtime
divalidasi di sana. Jika wajib pakai branch-mu → **sinkron dulu** fix runtime di atas.
Saat sidang **nyatakan eksplisit**: *"Runtime divalidasi di branch terintegrasi tim;
branch saya berkontribusi fix inti (plugin Nav2, ambang lokalisasi, kalibrasi
odometry, steering) + dokumentasi & analisis."* Jangan klaim runtime pada branch yang
belum memuat fix runtime-nya.

---

## Q7 — Plugin controller Nav2 (DWB atau bukan?)

### Jawaban
**BUKAN DWB.** Dikonfigurasi khusus untuk kendala Ackermann. [VF]
**Bukti file:** `src/amr_slam/config/nav2_params.yaml`.

**Controller (local planner):**
- `FollowPath` plugin = **`nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`**
- `desired_linear_vel: 0.3`
- `use_rotate_to_heading: false` ← Ackermann tak bisa putar di tempat
- `allow_reversing: true`

**Planner (global planner):**
- `GridBased` plugin = **`nav2_smac_planner/SmacPlannerHybrid`**
- `motion_model_for_search: "DUBIN"` ← Ackermann maju
- **`minimum_turning_radius: 0.90`** ← kendala Ackermann eksplisit
- `reverse_penalty: 2.0`, `angle_quantization_bins: 72`

### Cara menjawab serangan "DWB diff-drive di Ackermann?"
Tegaskan: **tidak menggunakan DWB.** Sistem memakai **Regulated Pure Pursuit**
(controller, ramah Ackermann) + **Smac Hybrid model DUBIN** (planner) yang
**menghormati radius putar minimum 0,90 m**. Justru ini pilihan yang benar untuk
platform Ackermann — DWB (diff-drive) sengaja dihindari.

---

## Ringkasan Status Pertahanan

| # | Pertanyaan | Status | Catatan |
|---|------------|--------|---------|
| 1 | Drivetrain 4WD/RWD | [VF] model + [perlu konfirmasi fisik] | Cek shaft depan |
| 2 | map→odom = RTAB-Map, AMCL off | [VF] aman | TF tree solid |
| 3 | cmd_vel→Ackermann di stm32_bridge | [VF] aman | jantung navigasi |
| 4 | Tanda kemudi kiri=kiri | [BT] perlu runtime | rebuild + tes di NUC |
| 5 | R²/PPR | [VL] kuat | kuasai "5 titik, real-vs-odom, lewat origin" |
| 6 | Branch demo | keputusan | nyatakan eksplisit |
| 7 | Controller RPP + Smac (bukan DWB) | [VF] aman | Ackermann-aware |

**Aman penuh (file-verified):** Q2, Q3, Q7.
**Kuat tapi kuasai detail:** Q5.
**Perlu tindakan sebelum sidang:** Q1 (konfirmasi mekanik), Q4 (verifikasi runtime
kemudi), Q6 (putuskan branch + sinkron bila perlu).

---

## Lampiran — Daftar file sumber (untuk membuka saat ditanya)
- `src/amr_description/urdf/amr_description.urdf.xacro` — drivetrain, geometri, TF
- `src/amr_controller/src/stm32_bridge.cpp` — cmd_vel→Ackermann, steering, serial
- `src/amr_controller/scripts/odometry_publisher.py` — odometry, PPR
- `src/amr_bringup/launch/amr_full.launch.py` — kalibrasi PPR (komentar)
- `src/amr_3d_mapping/config/rtabmap_localization.yaml` — map→odom (publish_tf)
- `src/amr_3d_mapping/launch/rtabmap_localization.launch.py` — VIO odom→base_link
- `src/amr_slam/config/nav2_params.yaml` — planner & controller (RPP + Smac)
- `src/amr_slam/launch/nav2.launch.py` — Nav2 bringup (tanpa AMCL)
