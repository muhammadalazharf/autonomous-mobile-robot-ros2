# SOP LENGKAP — Mapping "Semua Hijau" & Robot Jalan Sendiri (Tanpa Joystick)

**Proyek:** AMR Ackermann ITS · **Disusun:** 11 Juni 2026
**Prasyarat kode:** repo Mervs111 commit `6c37fd9` atau lebih baru
(stm32_bridge + cmd_vel, amr_auto_patrol.py)

> Aturan emas: SATU langkah, SATU verifikasi. Jangan lompat langkah.
> Setiap terminal baru WAJIB: `export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`

---

# BAGIAN A — MAPPING SAMPAI SEMUA HIJAU → DB ACUAN

## A0. Persiapan fisik & lingkungan (PALING MENENTUKAN)
- [ ] Tempel tekstur (poster/koran/kertas motif) di dinding polos, tinggi 0.3–0.8 m,
      terutama rute yang akan dilewati & dihadapi robot.
- [ ] Ruangan terang merata (hindari backlight/jendela silau, area gelap).
- [ ] Baterai > 21 V (6S; jangan ulangi insiden 16 V). Joystick menyala (R1 = deadman).
- [ ] Titik START ditandai lakban di lantai — harus kembali PERSIS ke sini.

## A1. Power & akses
```bash
ssh itssurabaya@10.17.36.151        # atau NoMachine ke IP yang sama
```

## A2. Terminal 1 — Sensor (jangan ditutup)
```bash
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false use_vr:=false use_failover:=false
```
**Verifikasi (tunggu ±30 dtk):** `RPLidar health: OK` · `RealSense Node Is Up!` · `[TX] V:0,S:0` berulang.

Terminal verifikasi cepat:
```bash
timeout 5 ros2 topic hz /scan     # ~10 Hz
timeout 8 ros2 topic hz /camera/camera/color/image_raw   # ~30 Hz
```

## A3. Terminal 2 — RTAB-Map mapping, DB BARU khusus acuan
```bash
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py \
  database_path:=$HOME/maps/lab_acuan.db
```
**Verifikasi:**
```bash
ros2 topic list | grep rtabmap          # harus ada /rtabmap/grid_map, /rtabmap/odom, /rtabmap/info
timeout 5 ros2 topic hz /rtabmap/odom   # 27-30 Hz
timeout 5 ros2 topic hz /imu/data       # ~100 Hz (baru muncul setelah launch ini)
```

## A4. Terminal 3 — Monitor visual + Terminal 4 — monitor loop closure
```bash
# T3 (NoMachine):
ros2 run rtabmap_viz rtabmap_viz
# T4:
watch -n 1 "ros2 topic echo /rtabmap/info --once | grep -E 'loop_closure_id|proximity'"
```

## A5. Teknik mengemudi (kunci "semua hijau")
| Aturan | Detail |
|---|---|
| Kecepatan | Stik **10%** maksimal. Pelan = hijau. |
| Belok | **Berhenti 3 detik** dulu, belok pelan, jangan putar di tempat |
| Rute | Susuri dinding, **keliling penuh**, kembali PERSIS ke titik START |
| Arah kamera | Selalu menghadap area bertekstur — hindari menghadap dinding kosong/kaca |

**Aturan warna rtabmap_viz (WAJIB dipatuhi):**
- 🟢 **HIJAU** → lanjut normal.
- 🟡 **KUNING** → pelankan ke 5%, arahkan kamera ke area bertekstur.
- 🔴 **MERAH (lost)** → **BERHENTI TOTAL**. Mundur pelan sedikit ke area yang tadi
  hijau, diam sampai hijau lagi, ULANGI segmen itu lebih pelan. Jangan lanjut
  selama merah — semua frame merah = racun bagi peta.

**Smoke test 30 detik:** sebelum keliling penuh, maju 1 m di area bertekstur →
pastikan cloud koheren & hijau. Kalau langsung kacau, perbaiki tekstur dulu.

## A6. Kriteria SELESAI (semua harus ✓)
- [ ] Satu putaran penuh tanpa segmen merah yang tidak diulang
- [ ] `loop_closure_id > 0` di Terminal 4 (saat kembali ke START)
- [ ] Peta 2D di viz: dinding tunggal & lurus, tidak double, tidak radial
- [ ] Cloud 3D koheren (bukan starburst)

## A7. Simpan & jadikan ACUAN (library)
```bash
# 1. Simpan peta 2D untuk Nav2:
ros2 run nav2_map_server map_saver_cli -f ~/maps/lab_acuan_map

# 2. Stop mapping dengan benar — Ctrl+C Terminal 2, TUNGGU:
#    "Saving database... done!"  ← jangan paksa tutup sebelum ini

# 3. Kunci sebagai MASTER (acuan localization selamanya):
cp ~/maps/lab_acuan.db ~/maps/backups/lab_acuan_MASTER.db
ls -lh ~/maps/lab_acuan* ~/maps/backups/
```
Hasil akhir Bagian A: `lab_acuan.db` (3D, untuk localization) + `lab_acuan_map.pgm/.yaml` (2D, untuk Nav2).

---

# BAGIAN B — ROBOT JALAN SENDIRI (TANPA JOYSTICK)

## B0. Deploy kode di NUC (SEKALI saja)
```bash
cd ~/amr_starter
git remote add mervs https://github.com/Mervs111/autonomous-mobile-robot-ros2.git 2>/dev/null
git fetch mervs
git checkout mervs/main -- \
  src/amr_controller/src/stm32_bridge.cpp \
  src/amr_slam/scripts/amr_auto_patrol.py \
  src/amr_slam/CMakeLists.txt
chmod +x src/amr_slam/scripts/amr_auto_patrol.py
colcon build --packages-select amr_controller amr_slam --symlink-install
source install/setup.bash
```
**Verifikasi build:** tidak ada error; `ros2 pkg executables amr_controller` menampilkan stm32_bridge.

## B1. BENCH TEST — RODA DIANGKAT DARI LANTAI! (wajib, 5 menit)
Robot di atas dudukan/balok, roda bebas berputar. Terminal 1 (sensor) jalan.

```bash
# 1. Aktifkan mode autonomous:
ros2 param set /stm32_bridge autonomous_enabled true

# 2. Tes maju + belok kiri:
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.2}, angular: {z: 0.3}}' -r 10
```
**Checklist verifikasi:**
- [ ] Roda berputar MAJU pelan
- [ ] Roda depan belok **KIRI** (angular.z positif = kiri, standar ROS).
      ❗ Kalau beloknya KANAN → STOP, lapor (tanda steering perlu dibalik di kode)
- [ ] **Tes watchdog:** Ctrl+C perintah di atas → roda HARUS berhenti ≤ 0.5 detik
- [ ] **Tes override R1:** ulangi publish, lalu pegang R1 + stik → joystick yang menang
- [ ] Matikan lagi: `ros2 param set /stm32_bridge autonomous_enabled false`

## B2. Kalibrasi kecepatan (max_speed_mps)
Default `max_speed_mps = 1.0` (artinya cmd 0.3 m/s → PWM 1200 / 30%).
Tes di lantai, area lapang:
```bash
ros2 param set /stm32_bridge autonomous_enabled true
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}}' -r 10
# Ukur: robot harus menempuh ±3 m dalam 10 detik (0.3 m/s).
# Terlalu cepat? naikkan: ros2 param set /stm32_bridge max_speed_mps 1.5
# Terlalu lambat? turunkan: ros2 param set /stm32_bridge max_speed_mps 0.7
```
Catat nilai final → nanti dipermanenkan di launch file.

## B3. RUN PENUH — Localization + Nav2 + Patroli

**Terminal 1 — Sensor** (seperti A2).

**Terminal 2 — RTAB-Map LOCALIZATION (pakai DB acuan):**
```bash
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping rtabmap_localization.launch.py \
  database_path:=$HOME/maps/lab_acuan.db
```
**Verifikasi KRITIS (jangan lanjut sebelum semua ✓):**
- [ ] Log awal **MEMUAT database** (menyebut jumlah node/words). Kalau
      "creating new database" → **Ctrl+C SEGERA**, jangan lanjut.
- [ ] `ros2 param get /rtabmap Mem/IncrementalMemory` → **false**
- [ ] `timeout 5 ros2 topic hz /rtabmap/odom` → 27-30 Hz (VIO hidup)
- [ ] `ros2 run tf2_ros tf2_echo map odom` → transform mengalir
- [ ] Dorong/joystick-kan robot pelan di area terpetakan → tunggu
      relokalisasi "snap" (cek `/rtabmap/localization_pose` terbit)

**Terminal 3 — Cek topic peta untuk Nav2:**
```bash
ros2 topic list | grep -E "grid_map|^/map$"
```
- Ada `/map` → langsung lanjut.
- Hanya ada `/rtabmap/grid_map` → jembatani (biarkan terminal ini jalan):
```bash
sudo apt install -y ros-humble-topic-tools   # sekali saja
ros2 run topic_tools relay /rtabmap/grid_map /map
```

**Terminal 4 — Nav2:**
```bash
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 launch amr_slam nav2.launch.py
```
**Verifikasi:** `ros2 action list | grep navigate_to_pose` → harus muncul.

**Terminal 5 — AKTIFKAN & JALAN SENDIRI:**
```bash
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 param set /stm32_bridge autonomous_enabled true

# Tes SATU goal dulu (RViz: Publish Point utk ambil koordinat, atau goal_sender):
ros2 run amr_slam goal_sender.py        # ketik: x y yaw, contoh: 1.5 0.5 0

# Kalau satu goal sukses → patroli multi-waypoint:
ros2 run amr_slam amr_auto_patrol.py --ros-args \
  -p waypoints:="1.0,0.0,0; 2.0,1.0,90; 0.5,1.5,180" -p loop:=true
```

**Cara ambil koordinat waypoint:** RViz (peta tampil) → toolbar **Publish Point**
→ klik titik di peta → `ros2 topic echo /clicked_point --once` → catat x,y.

## B4. CARA BERHENTI DARURAT (hafalkan 3-tingkat)
1. **Pegang R1 + stik netral** → manual override instan (joystick selalu menang)
2. `ros2 param set /stm32_bridge autonomous_enabled false` → blok semua cmd_vel
3. Ctrl+C node patrol/Nav2 → watchdog stop motor ≤ 0.5 detik

## Troubleshooting cepat
| Gejala | Penyebab / solusi |
|---|---|
| Robot diam saat goal dikirim | `autonomous_enabled` masih false; atau R1 tertekan; cek `ros2 param get /stm32_bridge autonomous_enabled` |
| Robot stop sendiri tiap ±0.5 dtk | Watchdog — Nav2 tidak publish cmd_vel kontinu; cek `ros2 topic hz /cmd_vel` |
| Nav2 tolak goal | Localization belum lock (cek TF map→odom); atau goal di luar peta |
| Path aneh / muter jauh | Wajar utk Ackermann (radius belok 0.9 m); taruh goal di area lapang |
| Belok terbalik | Lapor — tanda steering di stm32_bridge perlu dibalik |
| `/map` kosong di costmap | Jalankan relay topic (Terminal 3) |
