# HANDOVER PENGAMBILAN BUKTI — 5 Kategori
**Sensor · Mapping · Lokalisasi · Autonomous · Data Terolah `.db`**

**Untuk:** Tim PjBL AMR | **Waktu eksekusi:** ~125 menit total
**Lokasi:** NUC `itssurabaya@10.17.36.151`, workspace `~/amr_starter`
**Branch:** `claude/zealous-darwin-6l4bs5`

> Revisi dari `HANDOVER_BUKTI_3_KATEGORI.md`: **ditambahkan Kategori 1 (Bukti tiap sensor saat mapping & lokalisasi)** memakai skrip yang sudah ada di repo (`scripts/record_sensor_evidence.sh` + `scripts/analyze_sensor_bag.py`). Tiga kategori lain (Map, Lokalisasi, Autonomous) dipertahankan & dinomori ulang.

---

## STATUS SEKARANG (jangan diulang yang sudah ada)

### Yang SUDAH lengkap di repo/NUC:
- ✅ **24 database RTAB-Map** (`~/maps/*.db`) — peta acuan: `lab_demo_18jun.db` (1846 node, 28.9m)
- ✅ **Config lokalisasi terverifikasi** (`rtabmap_localization.yaml`)
- ✅ **Config Nav2 terverifikasi** (`nav2_params.yaml`)
- ✅ **Bag recording autonomous** (`bags/demo_run2_23jun/`, status SUCCEEDED)
- ✅ **TF tree PDF** (`frames_2026-06-09_*.pdf`)
- ✅ **Paket evidence CSV** (`docs/generated/raw_amr_evidence_package/`)
- ✅ **Skrip bukti sensor** (`scripts/record_sensor_evidence.sh`, `scripts/analyze_sensor_bag.py`)

### Yang HARUS diambil (fokus handover ini):
- ❌ **[K1]** Health check + bag + CSV tiap sensor saat **mapping** & saat **lokalisasi**
- ❌ **[K1]** Snapshot gambar RGB/Depth (bukti kamera hidup)
- ❌ **[K2]** Screenshot map visual (databaseViewer), plot lintasan x-y
- ❌ **[K3]** Screenshot loop closure hijau, log `/localization_pose`
- ❌ **[K4]** Video robot otonom, log `/cmd_vel`, screenshot RViz path+costmap
- ❌ **[K5]** Data terolah dari semua database `.db` (Excel + chart) untuk laporan Bab 2.10–2.12

---

## ENVIRONMENT — Wajib tiap terminal baru

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash
mkdir -p ~/amr_starter/docs/evidence/{sensor,map,lokalisasi,autonomous}
```
*Apa:* set domain ROS, RMW, source workspace, siapkan folder bukti. *Kenapa:* tim memakai `ROS_DOMAIN_ID=42` + CycloneDDS; tanpa source workspace `ros2 launch amr_*` gagal.

---

## BUKTI 1 — SENSOR saat MAPPING & LOKALISASI (~25 menit)

**Tujuan:** buktikan **setiap sensor sehat** (publish dengan rate benar) selama sesi mapping DAN sesi lokalisasi. Ini bukti forensik: kalau mapping/lokalisasi gagal, data ini menunjukkan kegagalan dari lingkungan (lab textureless), **bukan hardware**.

### Daftar sensor yang dibuktikan

| Topik | Sensor | Rate harapan |
|-------|--------|-------------|
| `/scan` | RPLIDAR C1 | ~10 Hz |
| `/camera/camera/color/image_raw` | D455 RGB | ~30 Hz |
| `/camera/camera/depth/image_rect_raw` | D455 Depth | ~30 Hz |
| `/camera/camera/color/camera_info` | Intrinsik (bukti 848×480) | ~30 Hz |
| `/camera/camera/accel/sample` | IMU accel D455 | ~100 Hz |
| `/camera/camera/gyro/sample` | IMU gyro D455 | ~200 Hz |
| `/imu/data` | IMU merge | ~100–200 Hz |
| `/odom` | Wheel odometry (encoder) | ~50 Hz |
| `/rtabmap/odom` | VIO pose | ~15–30 Hz |

### 1.A — Sensor saat MAPPING

```bash
# T1: sensor + driver (base)
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false \
  use_vr:=false use_failover:=false

# T2: RTAB-Map MAPPING (fresh atau lanjut DB)
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py \
  database_path:=$HOME/maps/sensor_check_mapping.db
```
*Apa:* jalankan pipeline mapping penuh. *Kenapa:* sensor harus dibuktikan **dalam konteks mapping** (semua node konsumen aktif).

```bash
# T3: HEALTH CHECK rate tiap sensor (jalankan satu per satu, ~5 detik tiap topik)
for t in /scan /camera/camera/color/image_raw /camera/camera/depth/image_rect_raw \
         /camera/camera/color/camera_info /camera/camera/accel/sample \
         /camera/camera/gyro/sample /imu/data /odom /rtabmap/odom; do
  echo "===== $t ====="
  timeout 5 ros2 topic hz "$t"
done | tee ~/amr_starter/docs/evidence/sensor/hz_mapping_24jun.txt
```
*Apa:* ukur rate publikasi tiap topik 5 detik & simpan. *Kenapa:* `average rate` membuktikan sensor hidup; rate 0/timeout = sensor mati → harus diperbaiki sebelum lanjut.

```bash
# T3: bukti intrinsik kamera 848x480 (bukti resolusi tidak diubah)
ros2 topic echo /camera/camera/color/camera_info --once \
  > ~/amr_starter/docs/evidence/sensor/camera_info_mapping.txt
```
*Apa:* simpan camera_info. *Kenapa:* field `width: 848, height: 480` = bukti profil sesuai spesifikasi.

```bash
# T4: REKAM bag semua sensor (skrip repo) — SEBELUM gerakkan robot
bash ~/amr_starter/scripts/record_sensor_evidence.sh mapping_sensor
# Gerakkan robot manual (joystick) ~60 detik untuk mapping pendek
# Ctrl+C setelah selesai
```
*Apa:* rekam semua topik (minus yang berat) ke `~/mapping_evidence/`. *Kenapa:* satu bag = historian lengkap semua "field device"; tidak ada sensor luput karena salah tebak nama topik.

```bash
# (opsional) Satu run pendek DENGAN gambar mentah (sampel visual RGB+depth)
bash ~/amr_starter/scripts/record_sensor_evidence.sh mapping_sensor_img --with-images
# CATATAN: ~2-4 GB/menit, pakai 10-15 detik saja
```

### 1.B — Sensor saat LOKALISASI

```bash
# T2 (ganti mode): RTAB-Map LOCALIZATION di peta acuan
#   (matikan dulu T2 mapping, jangan dua RTAB-Map sekaligus)
ros2 launch amr_3d_mapping rtabmap_localization.launch.py \
  database_path:=$HOME/maps/lab_demo_18jun.db
```
*Apa:* jalankan lokalisasi di peta tersimpan. *Kenapa:* sensor harus dibuktikan juga **dalam konteks lokalisasi**.

```bash
# T3: HEALTH CHECK rate sensor saat lokalisasi (+ topik lokalisasi)
for t in /scan /camera/camera/color/image_raw /imu/data /rtabmap/odom \
         /rtabmap/localization_pose /rtabmap/info; do
  echo "===== $t ====="
  timeout 5 ros2 topic hz "$t"
done | tee ~/amr_starter/docs/evidence/sensor/hz_lokalisasi_24jun.txt
```
*Apa:* ukur rate sensor + topik lokalisasi. *Kenapa:* bukti sensor tetap sehat saat sistem lokalisasi.

```bash
# T4: bag sensor saat lokalisasi
bash ~/amr_starter/scripts/record_sensor_evidence.sh lokalisasi_sensor
# Gerakkan robot manual ~60 detik di area yang sudah dipetakan
# Ctrl+C setelah selesai
```

### 1.C — Analisis bag → CSV + ringkasan kesehatan

```bash
# Untuk SETIAP folder bag hasil di atas (cek nama dengan: ls ~/mapping_evidence/)
python3 ~/amr_starter/scripts/analyze_sensor_bag.py \
  ~/mapping_evidence/mapping_sensor_<TIMESTAMP>

python3 ~/amr_starter/scripts/analyze_sensor_bag.py \
  ~/mapping_evidence/lokalisasi_sensor_<TIMESTAMP>
```
*Apa:* ekstrak bag → `summary.txt` (kesehatan tiap topik: jumlah pesan, rate, gap maks) + CSV per sensor (imu, accel_raw, gyro_raw, vio_odom, vio_quality, loop_closure, encoder, scan_stats). *Kenapa:* `summary.txt` = laporan kesehatan telemetri siap lampir; CSV = data mentah untuk plot laporan.

```bash
# Salin hasil analisis ke folder evidence
cp ~/mapping_evidence/mapping_sensor_*/analysis/summary.txt \
   ~/amr_starter/docs/evidence/sensor/summary_mapping.txt
cp ~/mapping_evidence/lokalisasi_sensor_*/analysis/summary.txt \
   ~/amr_starter/docs/evidence/sensor/summary_lokalisasi.txt
```

**Output Bukti 1 (yang harus ada):**
```
docs/evidence/sensor/
├── hz_mapping_24jun.txt          (rate tiap sensor saat mapping)
├── hz_lokalisasi_24jun.txt       (rate tiap sensor saat lokalisasi)
├── camera_info_mapping.txt       (bukti 848x480)
├── summary_mapping.txt           (kesehatan telemetri — analisis bag)
├── summary_lokalisasi.txt
└── (bag sumber di ~/mapping_evidence/, CSV di subfolder analysis/)
```

---

## BUKTI 2 — MAP (~20 menit, robot TIDAK perlu nyala)

Database `.db` sudah ada — yang kurang adalah **visualisasi**-nya. Bisa offline tanpa robot.

### 2.1 Screenshot map dari rtabmap-databaseViewer
```bash
# Butuh GUI — jalankan dari NoMachine
export DISPLAY=:0
rtabmap-databaseViewer ~/maps/lab_demo_18jun.db
```
Ambil 4 screenshot → `~/amr_starter/docs/evidence/map/`:
1. **`map_01_overview.png`** — pose graph + lintasan (View → Show all)
2. **`map_02_2d_grid.png`** — peta 2D grid (View → 2D Map)
3. **`map_03_loop_closures.png`** — pose graph + loop closure hijau (View → Constraints View)
4. **`map_04_3d_cloud.png`** — point cloud 3D (View → 3D Map) — opsional

### 2.2 Plot lintasan x-y
```bash
rtabmap-report --poses-only ~/maps/lab_demo_18jun.db \
  > ~/amr_starter/docs/evidence/map/trajectory_lab_demo_18jun.txt 2>&1 || \
echo "rtabmap-report tidak ada → databaseViewer File→Export poses"
```
Plot dengan Python:
```bash
cd ~/amr_starter
python3 << 'EOF'
import matplotlib.pyplot as plt
poses = []
with open('docs/evidence/map/trajectory_lab_demo_18jun.txt') as f:
    for line in f:
        p = line.strip().split()
        if len(p) >= 4:
            try: poses.append((float(p[1]), float(p[2])))
            except: pass
xs, ys = zip(*poses)
plt.figure(figsize=(10, 8))
plt.plot(xs, ys, '-', linewidth=1.5)
plt.plot(xs[0], ys[0], 'go', markersize=10, label='Start')
plt.plot(xs[-1], ys[-1], 'r^', markersize=10, label='End')
plt.axis('equal'); plt.grid(True); plt.legend()
plt.xlabel('x (m)'); plt.ylabel('y (m)')
plt.title('Lintasan Mapping — lab_demo_18jun.db')
plt.savefig('docs/evidence/map/trajectory_plot.png', dpi=150, bbox_inches='tight')
print("Saved: docs/evidence/map/trajectory_plot.png")
EOF
```

### 2.3 Ringkasan database
```bash
rtabmap-info ~/maps/lab_demo_18jun.db \
  > ~/amr_starter/docs/evidence/map/lab_demo_18jun_info.txt 2>&1
```

**Output Bukti 2:**
```
docs/evidence/map/
├── map_01_overview.png
├── map_02_2d_grid.png
├── map_03_loop_closures.png
├── map_04_3d_cloud.png            (opsional)
├── trajectory_plot.png
├── trajectory_lab_demo_18jun.txt
└── lab_demo_18jun_info.txt
```

---

## BUKTI 3 — LOKALISASI (~30 menit, robot HARUS nyala)

Tujuan: robot **menemukan posisinya** di peta `lab_demo_18jun.db` (bukan mapping ulang).

### 3.1 Bringup mode lokalisasi
```bash
# T1: sensor
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false \
  use_vr:=false use_failover:=false

# T2: RTAB-Map LOCALIZATION (bukan mapping, bukan vio_only)
ros2 launch amr_3d_mapping rtabmap_localization.launch.py \
  database_path:=$HOME/maps/lab_demo_18jun.db
# Tunggu log: "Loaded ... nodes" + "Localization mode"
```

### 3.2 Verifikasi topic lokalisasi
```bash
ros2 topic list | grep -E "localization|rtabmap"   # cek /rtabmap/localization_pose
ros2 topic echo /rtabmap/localization_pose --once   # tampil pose
```

### 3.3 Rekam log lokalisasi 60 detik
```bash
ros2 topic echo /rtabmap/localization_pose --no-arr \
  > ~/amr_starter/docs/evidence/lokalisasi/localization_log_24jun.txt &
LOCPID=$!
# Gerakkan robot manual (joystick) 0.5–1m di area yang sudah dipetakan
sleep 60
kill $LOCPID
```

### 3.4 Bag recording lokalisasi
```bash
ros2 bag record -o ~/amr_starter/docs/evidence/lokalisasi/loc_demo_24jun \
  /rtabmap/localization_pose /rtabmap/info /tf /tf_static /scan /odom &
BAGPID=$!
sleep 30   # gerakkan robot rute melingkar
kill $BAGPID
```

### 3.5 Screenshot loop closure di rtabmap_viz
```bash
export DISPLAY=:0
rtabmap_viz
```
Screenshot → `~/amr_starter/docs/evidence/lokalisasi/`:
- `loc_01_constraint_view.png` (link hijau = loop closure)
- `loc_02_graph_view.png` (pose graph ter-update)
- `loc_03_robot_in_map.png`

### 3.6 Screenshot RViz dengan pose
```bash
export DISPLAY=:0
export LIBGL_ALWAYS_SOFTWARE=1
rviz2
```
Fixed Frame=`map`; display: TF, Map (`/rtabmap/map`), RobotModel, Pose (`/rtabmap/localization_pose`). Screenshot → `loc_04_rviz_pose_tracking.png`.

**Output Bukti 3:**
```
docs/evidence/lokalisasi/
├── localization_log_24jun.txt
├── loc_demo_24jun/                 (bag)
├── loc_01_constraint_view.png
├── loc_02_graph_view.png
├── loc_03_robot_in_map.png
└── loc_04_rviz_pose_tracking.png
```

---

## BUKTI 4 — AUTONOMOUS (~40 menit, robot HARUS nyala, area kosong)

Tujuan: robot terima goal Nav2 → bergerak otonom → berhenti otomatis (SUCCEEDED).

### 4.1 Bringup (4 terminal)
```bash
# T1: sensor
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false \
  use_vr:=false use_failover:=false

# T2: VIO (sumber pose)
ros2 launch amr_3d_mapping vio_only.launch.py

# T3: Nav2
ros2 launch amr_slam nav2.launch.py

# T4: static TF map→odom (supaya RViz goal click bisa, Fixed Frame=map)
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
```

### 4.2 Set parameter aman
```bash
ros2 param set /stm32_bridge autonomous_max_runtime_s 60.0
ros2 param set /stm32_bridge autonomous_enabled true
```
*Kenapa:* default cap 10s bisa hentikan motor sebelum SUCCEEDED; gate default `false`.

### 4.3 Rekam SEMUA log paralel SEBELUM kirim goal
```bash
ros2 topic echo /cmd_vel \
  > ~/amr_starter/docs/evidence/autonomous/cmdvel_24jun.txt & CMDPID=$!
ros2 topic echo /odom --no-arr \
  > ~/amr_starter/docs/evidence/autonomous/odom_24jun.txt & ODOMPID=$!
ros2 topic echo /rtabmap/odom --no-arr \
  > ~/amr_starter/docs/evidence/autonomous/vio_odom_24jun.txt & VIOPID=$!
ros2 bag record -o ~/amr_starter/docs/evidence/autonomous/auto_demo_24jun \
  /cmd_vel /odom /rtabmap/odom /scan /goal_pose /tf /tf_static \
  /plan /local_plan & BAGPID=$!
```

### 4.4 REKAM VIDEO HP sambil kirim goal (3 RUN)
Buka RViz (Fixed Frame=`map`; display: Map, GlobalCostmap, LocalCostmap, Path, RobotModel, TF).
```bash
# Run 1: goal 1m lurus depan (frame odom, jarak >= 1m WAJIB)
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'odom'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}" --feedback
# Tunggu SUCCEEDED, JANGAN abort

# Run 2: goal serong kiri
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'odom'}, pose: {position: {x: 1.0, y: 0.5, z: 0.0}, orientation: {w: 1.0}}}}" --feedback

# Run 3: KLIK GOAL di RViz (toolbar "Nav2 Goal", klik ~1.5m) — bukti interaktif
```

### 4.5 Stop recording
```bash
kill $CMDPID $ODOMPID $VIOPID $BAGPID
ros2 param set /stm32_bridge autonomous_enabled false
```

### 4.6 Screenshot pendukung
```bash
export DISPLAY=:0
ros2 run rqt_graph rqt_graph     # → auto_rqt_graph.png
# RViz path + costmap saat goal aktif → auto_rviz_path.png, auto_rviz_costmap.png
ros2 run tf2_tools view_frames
mv frames_*.pdf ~/amr_starter/docs/evidence/autonomous/auto_tf_tree.pdf
```

**Output Bukti 4:**
```
docs/evidence/autonomous/
├── cmdvel_24jun.txt
├── odom_24jun.txt
├── vio_odom_24jun.txt
├── auto_demo_24jun/                (bag)
├── auto_rqt_graph.png
├── auto_rviz_path.png
├── auto_rviz_costmap.png
├── auto_tf_tree.pdf
├── video_run1_lurus.mp4            (HP, transfer manual)
├── video_run2_serong.mp4
└── video_run3_rviz_click.mp4
```

---

## BUKTI 5 — DATA TEROLAH dari DATABASE `.db` (~15 menit, OFFLINE, tanpa robot)

**Tujuan:** ubah 26 database `.db` di `~/maps/` menjadi data numerik + grafik siap-pakai untuk Bab 2.10–2.12 laporan. Bisa dikerjakan kapan saja, tanpa robot/sensor menyala.

### 5.1 Install dependency (sekali saja)
```bash
pip3 install openpyxl
```
*Apa:* library untuk menulis Excel `.xlsx` multi-sheet + chart. *Kenapa:* output utama bab analisis database adalah file Excel; tanpa openpyxl hanya CSV yang ditulis.

### 5.2 Ekstrak struktur database → Excel multi-sheet
```bash
cd ~/amr_starter
python3 scripts/export_rtabmap_db.py ~/maps --out ~/hasil_ekstrak
```
*Apa:* setiap `.db` jadi `<db>.xlsx` (4 sheet: RINGKASAN, TRAJECTORY, LOOP_CLOSURE, NODE_DETAIL) + `RINGKASAN_SEMUA.xlsx` (perbandingan semua database). *Kenapa:* TRAJECTORY (ratusan baris x, y, z, yaw) adalah data mentah untuk Bab 2.10.2; RINGKASAN_SEMUA jadi tabel di Bab 2.11.1.

> Database yang rusak/kosong otomatis di-SKIP — pesan `[SKIP] file rusak: ...` muncul, proses lanjut ke berikutnya.

### 5.3 Analisis turunan + chart embedded
```bash
python3 scripts/analyze_rtabmap_excel.py --input ~/hasil_ekstrak --output ~/hasil_olahan
```
*Apa:* baca semua `<db>.xlsx`, hitung **kecepatan rata-rata mapping (m/s), density keyframe (node/m), loop closure rate (%), drift Z (m)**. Output `<db>_ANALISIS.xlsx` (5 chart embedded) + `PERBANDINGAN_SEMUA_ANALISIS.xlsx` (4 bar chart ranking). *Kenapa:* sheet GRAFIK siap di-screenshot/embed ke Word untuk Gambar Bab 2.10–2.12; tidak perlu re-plot manual.

### 5.4 (Opsional) Ekstrak gambar RGB + depth per-frame
```bash
# Preview 10 frame dulu:
python3 scripts/extract_rtabmap_images.py --single ~/maps/lab_demo_18jun.db --limit 10

# Kalau OK, jalankan untuk peta acuan (hemat: stride 5):
python3 scripts/extract_rtabmap_images.py --single ~/maps/lab_demo_18jun.db --stride 5
```
*Apa:* simpan RGB JPEG + Depth PNG per keyframe ke `~/hasil_ekstrak/images/<db>/{rgb,depth}/` + `poses.csv`. *Kenapa:* bukti visual akuisisi data Bab 2.10.1 (lampirkan 3-5 frame sample); `poses.csv` sinkron dengan TRAJECTORY untuk korelasi pose ↔ gambar.

### 5.5 (Opsional) Ekstrak scan LiDAR mentah per-frame
```bash
python3 scripts/extract_rtabmap_scan.py --single ~/maps/lab_demo_18jun.db --stride 5
```
*Apa:* setiap keyframe jadi CSV ratusan baris (`x, y, z, intensity, range, angle`) + `scan_summary.csv` (1 baris/frame: jumlah point, range min/max/mean). *Kenapa:* data mentah untuk analisis kualitas mapping di Bab 2.11.2 (sebaran range valid menunjukkan apakah ruangan dipindai dengan baik).

### 5.6 Pemetaan ke sub-bab laporan

| Sub-bab Laporan | File yang dipakai dari `~/hasil_olahan/` |
|---|---|
| **2.10.1** Akuisisi data mapping | `lab_demo_18jun_ANALISIS.xlsx` → RINGKASAN_ANALISIS (durasi, panjang) + sample gambar dari 5.4 |
| **2.10.2** Pembentukan pose graph | `lab_demo_18jun_ANALISIS.xlsx` → sheet GRAFIK chart **#1 Lintasan 2D** (screenshot) |
| **2.10.3** Penyimpanan `.db` | `RINGKASAN_SEMUA.xlsx` (daftar 26 db + ukuran MB) |
| **2.11.1** Status database | `PERBANDINGAN_SEMUA_ANALISIS.xlsx` (valid vs kosong/rusak — catat manual: 4 corrupt, 2 kosong) |
| **2.11.2** Node/keyframe/LC | `lab_demo_18jun_ANALISIS.xlsx` → RINGKASAN_ANALISIS (LC rate 70.21% → "SANGAT BAIK") |
| **2.11.3** Deduplikasi + utama | `PERBANDINGAN_SEMUA_ANALISIS.xlsx` → GRAFIK bar chart LC rate (justifikasi `lab_demo_18jun` jadi peta acuan) |
| **2.12.1** Evaluasi peta awal | `lab_acuan_ANALISIS.xlsx` (LC=0) vs `lab_demo_18jun_ANALISIS.xlsx` (LC=70%) |
| **2.12.2** Pelaksanaan remapping | Chart Lintasan 2D `lab_acuan` vs `lab_demo_18jun` (sebelum-sesudah) |
| **2.12.3** Penentuan peta acuan | `PERBANDINGAN_SEMUA_ANALISIS.xlsx` ranking — `lab_demo_18jun` top-2 dari 20 |

### 5.7 Output Bukti 5 (yang harus ada)
```
~/hasil_ekstrak/                           ← struktur dasar (per-db Excel + CSV)
├── RINGKASAN_SEMUA.xlsx
├── <26 file>.xlsx
└── csv/<db>/{RINGKASAN,TRAJECTORY,LOOP_CLOSURE,NODE_DETAIL}.csv

~/hasil_olahan/                            ← UTAMA untuk laporan
├── PERBANDINGAN_SEMUA_ANALISIS.xlsx       ← Bab 2.11.3 + 2.12.3
├── lab_demo_18jun_ANALISIS.xlsx           ← peta acuan, Bab 2.10–2.11
├── lab_acuan_ANALISIS.xlsx                ← kontras peta awal, Bab 2.12.1
└── <18 file _ANALISIS>.xlsx               ← arsip
```

### 5.8 Top-5 database — referensi cepat (hasil sample upload)

| Database | Node | LC Rate | Kualitas | Catatan |
|---|---|---|---|---|
| `lab_final_20260609_212523` | 463 | 77.75% | SANGAT BAIK | sesi pendek, sangat banyak loop |
| **`lab_demo_18jun`** ⭐ | **1846** | **70.21%** | **SANGAT BAIK** | **peta acuan, paling lengkap** |
| `lab_demo_17jun` | 2244 | 50.36% | SANGAT BAIK | sesi terpanjang (1276s, 176m) |
| `lab_demo_20jun` | 927 | 48.98% | SANGAT BAIK | |
| `lab_final_20260609_210604` | 494 | 43.72% | SANGAT BAIK | |

---

## COMMIT KE REPO (setelah bukti terkumpul)

```bash
cd ~/amr_starter
git add docs/evidence/
git commit -m "feat: bukti runtime 4 kategori — sensor, map, lokalisasi, autonomous"
git push origin claude/zealous-darwin-6l4bs5
```
> Bag besar (`auto_demo_*`, `loc_demo_*`) cek `.gitignore` dulu — kalau >100MB, simpan di drive terpisah, commit hanya summary/CSV/screenshot.

---

## TROUBLESHOOTING CEPAT

| Masalah | Solusi |
|---------|--------|
| `ros2 topic hz` rate 0 / timeout | Sensor mati — cek `ls /dev/serial/by-id/`, restart T1 |
| `rtabmap-databaseViewer` tidak buka | Butuh GUI NoMachine + `export DISPLAY=:0`. CLI: `rtabmap-info` |
| `/rtabmap/localization_pose` tidak muncul | Cek `database_path` — file `.db` ada? |
| Loop closure tidak hijau | Gerakkan robot ke area yang pernah dipetakan |
| RViz goal click ditolak | Pastikan `static_transform_publisher map→odom` jalan & Fixed Frame=map |
| Robot bergerak liar | R1 joystick + `autonomous_enabled false` |
| `analyze_sensor_bag.py` error | Pastikan source ROS 2 + workspace dulu; folder bag valid |
| Display error (RViz/rqt) | Jalankan dari NoMachine, `export DISPLAY=:0` (+`LIBGL_ALWAYS_SOFTWARE=1`) |

---

## EMERGENCY STOP (hafalkan)

```bash
# 1. Pegang R1 joystick → manual override
# 2. ros2 param set /stm32_bridge autonomous_enabled false
# 3. ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

---

## URUTAN PRIORITAS (kalau waktu mepet)

1. **Bukti 5 (Data terolah `.db` → Excel)** — paling cepat (~15 mnt), offline, langsung pakai untuk Bab 2.10–2.12 laporan
2. **Bukti 4 (Autonomous)** — paling penting sidang; 1 video + 1 bag cukup
3. **Bukti 1 (Sensor)** — cepat (~25 mnt), bukti forensik kuat, sekalian saat mapping/lokalisasi
4. **Bukti 2 (Map)** — offline, kapan saja, tanpa robot
5. **Bukti 3 (Lokalisasi)** — paling lama; kalau loop closure susah, fokus log+bag, screenshot bonus

**Estimasi: 125 menit (semua) | 80 menit (prioritas 1+2+3+4)**
