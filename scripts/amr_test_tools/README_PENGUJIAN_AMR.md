# AMR Test Tools — Odometry · Localization · Mode Demo Navigation2

Paket logging untuk mengambil **data pengujian final** AMR dan merekapnya jadi
**satu file Excel** siap-laporan (`amr_test_recap.xlsx`).

> Disesuaikan untuk proyek ini: workspace `~/amr_starter`, `ROS_DOMAIN_ID=42`,
> CycloneDDS, topik & launch file sudah diverifikasi dari source repo.

---

## ⚠️ Yang perlu dipahami dulu

Script ini **TIDAK menjalankan robot**. Script hanya **merekam data** saat sistem
AMR (sensor, odometry, RTAB-Map, Nav2) **sudah berjalan**. Alurnya:

```
Nyalakan AMR  →  cek topik hidup  →  jalankan logger  →  rekap jadi Excel
```

---

## 0. SETUP (sekali saja)

```bash
# Pindahkan folder amr_test_tools sudah ada di repo: ~/amr_starter/scripts/amr_test_tools
bash ~/amr_starter/scripts/amr_test_tools/setup_test_tools.sh
```
Script ini pasang `openpyxl`, cek message ROS 2, chmod, dan buat `~/amr_test_results`.

---

## 1. ENVIRONMENT — wajib di SETIAP terminal baru

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/humble/setup.bash
source ~/amr_starter/install/setup.bash
```
> Tanpa ini: `ModuleNotFoundError: No module named 'rclpy'` atau topik tidak terbaca.

Singkatan path logger (dipakai di bawah):
```bash
TOOLS=~/amr_starter/scripts/amr_test_tools/scripts
```

---

## 2. CEK TOPIK DULU (sebelum logging apa pun)

Setelah AMR menyala, di terminal baru (sudah di-source):
```bash
ros2 topic list | grep -E "odom|scan|cmd_vel|localization|plan|tf"
```
Topik yang DIHARAPKAN di proyek ini (sudah diverifikasi dari source):

| Topik | Sumber | Dipakai untuk |
|---|---|---|
| `/odom` | `odometry_publisher.py` (wheel) | Odometry & Navigation |
| `/scan` | RPLIDAR C1 | snapshot sensor |
| `/cmd_vel` | Nav2 demo mode (langsung) | Navigation |
| `/rtabmap/localization_pose` | RTAB-Map localization | Localization |
| `/plan` | Nav2 global planner | Navigation |

Snapshot kesehatan topik (opsional, bukti Bab 2.7):
```bash
python3 $TOOLS/topic_snapshot.py --output ~/amr_test_results
```

---

## 3. UJI 1 — VALIDASI ODOMETRY  (Bab 2.9)

**Prasyarat:** robot menyala, joystick aktif, `/odom` publish.
Mode manual (bukan autonomous). Ukur jarak aktual pakai **meteran**.

```bash
python3 $TOOLS/odom_trial_logger.py \
  --trial O01 --actual-distance 1.0 \
  --odom-topic /odom --output ~/amr_test_results
```
Alur interaktif:
1. Taruh robot di titik awal → tekan **ENTER**
2. Jalankan robot lurus pakai joystick sampai jarak terukur
3. Tekan **ENTER** → script hitung jarak odom, selisih, % error

Ulangi minimal 5 trial dengan jarak berbeda:
```bash
python3 $TOOLS/odom_trial_logger.py --trial O02 --actual-distance 1.5 --odom-topic /odom --output ~/amr_test_results
python3 $TOOLS/odom_trial_logger.py --trial O03 --actual-distance 2.0 --odom-topic /odom --output ~/amr_test_results
python3 $TOOLS/odom_trial_logger.py --trial O04 --actual-distance 2.5 --odom-topic /odom --output ~/amr_test_results
python3 $TOOLS/odom_trial_logger.py --trial O05 --actual-distance 3.0 --odom-topic /odom --output ~/amr_test_results
```
→ `~/amr_test_results/odometry_trials.csv`

---

## 4. UJI 2 — LOCALIZATION TERHADAP PETA  (Bab 2.13)

**Prasyarat:** RTAB-Map mode localization jalan dengan peta acuan.
```bash
# Terminal A — sensor
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false use_vr:=false use_failover:=false
# Terminal B — RTAB-Map LOCALIZATION
ros2 launch amr_3d_mapping rtabmap_localization.launch.py \
  database_path:=$HOME/maps/lab_demo_18jun.db
```
Cek topik pose muncul:
```bash
ros2 topic list | grep localization
# harus: /rtabmap/localization_pose
```
Jalankan logger (sambil gerakkan robot pelan pakai joystick agar pose berubah):
```bash
python3 $TOOLS/localization_pose_logger.py \
  --trial L01 --map-file lab_demo_18jun.db \
  --pose-topic /rtabmap/localization_pose \
  --duration 30 --output ~/amr_test_results
```
> Kalau pose ternyata `PoseStamped` (bukan covariance), tambah `--msg-type pose_stamped`.

→ `~/amr_test_results/localization_trials.csv`

---

## 5. UJI 3 — MODE DEMO NAVIGATION2  (Bab 2.14)

**Prasyarat (4 terminal):**
```bash
# T1 sensor
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false use_vr:=false use_failover:=false
# T2 VIO (sumber pose Nav2)
ros2 launch amr_3d_mapping vio_only.launch.py
# T3 Nav2
ros2 launch amr_slam nav2.launch.py
# T4 static TF map→odom (agar goal click RViz bisa)
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
```
Parameter aman runtime:
```bash
ros2 param set /stm32_bridge autonomous_max_runtime_s 60.0
ros2 param set /stm32_bridge autonomous_enabled true
```
Jalankan logger LALU kirim Nav2 Goal dari RViz (atau action) dalam durasi:
```bash
python3 $TOOLS/navigation_demo_logger.py \
  --trial N01 --start-label A --goal-label B --duration 60 \
  --cmd-topic /cmd_vel --odom-topic /odom --plan-topic /plan \
  --output ~/amr_test_results
```
Contoh goal via action (frame **odom**, jarak ≥1 m — lihat temuan handover):
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'odom'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}" --feedback
```
Setelah selesai: `ros2 param set /stm32_bridge autonomous_enabled false`

→ `~/amr_test_results/navigation_trials.csv`

---

## 6. REKAP JADI SATU FILE EXCEL

Setelah semua uji selesai:
```bash
python3 $TOOLS/make_master_recap.py --input ~/amr_test_results
```
Output:
```
~/amr_test_results/
├── odometry_trials.csv          (summary 1 baris/trial)
├── localization_trials.csv
├── navigation_trials.csv
├── raw/                         ← DATA MENTAH time-series (ratusan baris/trial)
│   ├── odom_O01.csv             (t, x, y, yaw, jarak_kumulatif, v_instan)
│   ├── loc_L01.csv              (t, x, y, z, yaw, cov_x, cov_y, cov_yaw)
│   ├── nav_cmd_N01.csv          (t, linear_x, angular_z)
│   └── nav_odom_N01.csv         (t, x, y, yaw, jarak_kumulatif)
├── amr_test_recap.csv           (mentah gabungan, universal)
└── amr_test_recap.xlsx          ← UTAMA, multi-sheet siap laporan
```
Isi `.xlsx`:
| Sheet | Isi |
|---|---|
| `INFO` | ringkasan jumlah trial |
| `Odometry_Raw` / `Odometry_Summary` | tabel + rata-rata % error (warna) **+ chart bar aktual-vs-odom & line error%** |
| `Localization_Raw` / `Localization_Summary` | status lock, rate, pose terakhir |
| `Navigation_Raw` / `Navigation_Summary` | path, cmd_vel aktif, robot bergerak, displacement |
| `RAW_odom_*`, `RAW_loc_*`, `RAW_nav_*` | **time-series mentah (ratusan baris) + chart lintasan x-y** |
| `Topic_Snapshot` | type + rate tiap topik |
| `Evidence_Index` | checklist bukti (otomatis + manual) |

**3 lapis data dari satu pengujian:**
1. **Raw** (`raw/*.csv` + sheet `RAW_*`) → kamu proses sendiri sesuka hati
2. **Summary** (sheet `*_Summary`) → tabel siap salin ke laporan
3. **Perbandingan** (chart di `Odometry_Summary` + `RAW_*`) → grafik siap screenshot

**Ambil `amr_test_recap.xlsx` → semua sudah ada di dalamnya.**

---

## 7. TROUBLESHOOTING

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: rclpy` | Source ROS 2 dulu (lihat §1) |
| Topik pose tidak muncul | Cek `database_path` di launch localization; pastikan file `.db` ada |
| `odom` rate 0 | odometry_publisher belum jalan / serial STM32 mati |
| `/plan` kosong saat Nav2 | Cek `ros2 topic list \| grep plan`; ganti `--plan-topic` bila beda |
| `.xlsx` tidak terbuat | `pip3 install openpyxl` lalu jalankan ulang recap |
| Robot tidak berhenti di goal | Goal frame **odom** (bukan base_link), jarak ≥1 m — lihat HANDOVER_BUKTI |

---

## 8. RINGKASAN SATU LAYAR

```bash
# (1) setup sekali
bash ~/amr_starter/scripts/amr_test_tools/setup_test_tools.sh

# (2) tiap terminal
export ROS_DOMAIN_ID=42; export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/humble/setup.bash; source ~/amr_starter/install/setup.bash
TOOLS=~/amr_starter/scripts/amr_test_tools/scripts

# (3) uji (robot harus menyala dulu)
python3 $TOOLS/odom_trial_logger.py --trial O01 --actual-distance 1.0 --output ~/amr_test_results
python3 $TOOLS/localization_pose_logger.py --trial L01 --map-file lab_demo_18jun.db --duration 30 --output ~/amr_test_results
python3 $TOOLS/navigation_demo_logger.py --trial N01 --duration 60 --output ~/amr_test_results

# (4) rekap → Excel
python3 $TOOLS/make_master_recap.py --input ~/amr_test_results
```
