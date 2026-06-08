# HANDOVER UNTUK ANWAR — TRIAL REMAPPING KE-3

**Dari:** Al Azhar (sesi remote, 8 Juni 2026)
**Untuk:** Anwar (di lab, eksekutor lapangan)
**Tujuan:** Persiapan trial remapping ke-3 di lab — apa yang harus dilakukan, indikasi hasil baik/jelek, dan kapan harus stop

> Anwar, ini briefing lengkap untuk remapping besok. Baca sekali full
> sebelum mulai. Kalau ragu di tengah jalan, lebih baik berhenti dan
> WA aku dulu daripada lanjut dan rusak mapping lagi.

---

## BAGIAN 1 — APA YANG SUDAH BERUBAH SEJAK MAPPING TERAKHIR

### 1.1 Update parameter VIO & Loop Closure (commit `e850fca`)
7 parameter dibetulkan berdasarkan analisis 2 mode kegagalan (scattered cloud + ghosting):

| Parameter | Sebelumnya | Sekarang | Kenapa diubah |
|---|---|---|---|
| `Vis/MinInliers` (di rgbd_odometry) | 2 | **8** | 2 = pose PnP nyaris random saat textureless → cloud meledak jadi bola fraktal |
| `Odom/MaxVariance` | 0.01 | **0.05** | 0.01 terlalu ketat → hampir semua frame ditolak → reset terus |
| `Odom/ResetCountdown` | 1 | **5** | Reset 1 frame = setiap motion blur sesaat trajectory pecah |
| `Kp/MaxFeatures` + `Kp/DetectorStrategy` | tidak ada | **400 + 8** | Aktifkan BoW vocabulary untuk place recognition (loop closure) |
| `Rtabmap/DetectionRate` | 1.0 Hz | **2.0 Hz** | Window deteksi loop closure 2x lebih lebar |
| `cloud_max_depth` | 4.0 m | **5.0 m** | Bisa "lihat" dinding seberang untuk landmark |
| `Mem/STMSize` | 30 | **10** | Loop closure lebih cepat terpicu di ruangan kecil |

### 1.2 Workspace NUC sudah dibersihkan (sesi 8 Juni siang)
- Database lama corrupt dihapus (backup di `~/.ros/rtabmap.db.broken_*.bak`)
- Edit manual lokal yang buggy (string `'true'` vs bool `True`) dibuang
- 6 commit yang ketinggalan di NUC sudah di-pull
- Node duplikat dari double-launch sudah hilang

### 1.3 Helper script baru: `scripts/fresh_mapping.sh`
Otomatis backup DB lama + verifikasi 6 param kritis sebelum mapping. Wajib dijalankan setiap kali mau mapping baru.

### 1.4 Protokol kolaborasi dengan Mervi (commit `b43fca4`)
Aturan baru: cek repo Mervi sebelum eksekusi, jangan overwrite konfig dia, repo dia hanya untuk monitoring. Detail di `docs/PROTOKOL_KOLABORASI_MERVI.md` — Anwar tidak perlu eksekusi, hanya tahu aturannya.

---

## BAGIAN 2 — PROSEDUR REMAPPING (URUTAN WAJIB, JANGAN DILEWATI)

### Langkah 1 — Update workspace NUC ke versi terbaru

```bash
ssh itssurabaya@10.17.36.151

cd ~/amr_starter
git status                                          # harus clean, kalau ada uncommitted → stash dulu
git pull origin claude/brave-newton-6zvS4           # tarik 4 commit terbaru
git log --oneline -3                                # HEAD HARUS = b43fca4
```

Build ulang **hanya kalau** ada perubahan di `src/` (4 commit terakhir sebenarnya cuma docs, jadi build biasanya tidak perlu):

```bash
colcon build --packages-select amr_3d_mapping --symlink-install
source install/setup.bash
```

### Langkah 2 — Fresh start (WAJIB sebelum mapping baru)

```bash
cd ~/amr_starter
bash scripts/fresh_mapping.sh
```

Script ini akan:
- Backup DB lama otomatis dengan timestamp
- Hapus DB aktif (supaya tidak menumpuk drift lama)
- Verifikasi 6 param kritis sudah benar (kalau ada yang merah ✗, STOP, WA aku)
- Print perintah launch yang benar

### Langkah 3 — Pastikan tidak ada proses ROS yang nyangkut

```bash
ros2 node list                # harus kosong / cuma /_ros2cli_daemon
# Kalau masih ada node dari sesi lama:
pkill -9 -f ros2 ; pkill -9 -f rtabmap ; pkill -9 -f rgbd
pkill -9 -f realsense ; pkill -9 -f rplidar ; pkill -9 -f stm32
pkill -9 -f imu_merger ; pkill -9 -f depth_to_laser
sleep 3
ros2 daemon stop && sleep 2 && ros2 daemon start && sleep 2
ros2 node list                # WAJIB kosong sekarang
```

### Langkah 4 — Launch (JANGAN double launch!)

⚠️ **JANGAN** jalankan `amr_full.launch.py` + `rtabmap_mapping.launch.py` bersamaan — itu penyebab cloud meledak di trial sebelumnya.

Pakai satu dari dua cara di bawah:

**Cara A (recommended — satu launch, tidak ada duplikat):**
```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash
ros2 launch amr_bringup amr_full.launch.py \
  use_rtabmap:=true rtabmap_mode:=mapping \
  use_slam:=false use_nav2:=false use_vr:=false use_failover:=false
```

**Cara B (split, tapi WAJIB pakai `sensors_launch.py`, BUKAN `amr_full.launch.py`):**
```bash
# Terminal 1:
ros2 launch amr_bringup sensors_launch.py

# Terminal 2 (setelah Terminal 1 siap):
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py \
  database_path:=$HOME/maps/lab_remap3_$(date +%Y%m%d).db
```

### Langkah 5 — Verifikasi sebelum drive

Buka terminal terpisah, jalankan satu per satu:

```bash
ros2 node list                                    # 13 node, tidak ada yg duplikat (no -2 suffix)
ros2 topic hz /scan                               # ~10 Hz
ros2 topic hz /imu/data                           # ~100-200 Hz
ros2 topic hz /rtabmap/odom                       # ~20-30 Hz (KUNCI: ini VIO)
ros2 topic info /rtabmap/odom | grep "Publisher"  # HARUS: count 1 (bukan 2)
ros2 topic info /odom | grep "Publisher"          # HARUS: count 1
```

**Kalau ada yang tidak sesuai → STOP, WA aku dulu sebelum drive.**

### Langkah 6 — Buka monitor loop closure (terminal terpisah)

```bash
watch -n 1 "ros2 topic echo /rtabmap/info --once | grep -E 'loop_closure_id|proximity_detection_id|memory'"
```

Pantau terus selama mapping. Yang dicari:
- `loop_closure_id` masih `0` di awal → wajar
- Setelah robot kembali ke titik start: `loop_closure_id` berubah ke angka positif (1, 2, dst)
- Kalau sampai akhir tetap `0` → loop closure gagal terpicu (lihat Bagian 4)

### Langkah 7 — Drive pelan & terencana

**Aturan drive:**
- Tahan **R1 terus** (deadman switch)
- Stik analog **10-15% saja** (~0.2 m/s) — sangat pelan
- **Berhenti 3 detik** sebelum tiap belok (kasih VIO waktu konvergen)
- **JANGAN** putar di tempat (Ackermann, bukan diff drive)
- **JANGAN** mundur tajam (VIO Frame-to-Map lemah saat reverse)

**Pola jalur (PENTING — wajib 1 loop tertutup):**
```
START (pojok bawah kiri lab)
  ↓ 1. Susuri dinding kiri → naik
  ↓ 2. Susuri dinding atas → ke kanan
  ↓ 3. Susuri dinding kanan → turun
  ↓ 4. Susuri dinding bawah → KEMBALI KE START
        ↑ Di sini loop closure HARUS terpicu
```

Total durasi target: 5-10 menit. Jangan kelamaan — drift terakumulasi.

### Langkah 8 — Simpan peta

```bash
# Di terminal terpisah, setelah selesai keliling:
source ~/amr_starter/install/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/lab_remap3_$(date +%Y%m%d)
ls -lh ~/maps/lab_remap3_*
```

Jangan tutup terminal launch sampai save selesai. Setelah save berhasil, baru CTRL+C launch.

---

## BAGIAN 3 — INDIKASI HASIL BAIK vs JELEK

### ✅ Indikasi BAIK (lanjutkan, sudah benar)

| Sinyal | Dimana lihat | Nilai bagus |
|---|---|---|
| VIO rate stabil | Terminal `ros2 topic hz /rtabmap/odom` | 25-30 Hz konsisten |
| Background rtabmap_viz | NoMachine, buka `rtabmap_viz` | **Hijau** terus |
| Loop closure terpicu | Terminal monitor (Langkah 6) | `loop_closure_id` jadi >0 saat balik ke START |
| Memori graph naik bertahap | Log rtabmap | `WM=1, 2, 3, ... 50, 100` naik linier |
| Visualisasi point cloud RViz | RViz topic `/rtabmap/cloud_map` | Dinding, lantai, plafon koheren terlihat |
| Peta .pgm setelah save | Buka di file manager | Garis dinding jelas, area putih ruang kosong |

### 🟡 Indikasi WARNING (lanjut hati-hati, awas)

| Sinyal | Arti | Tindakan |
|---|---|---|
| Background rtabmap_viz **kuning** | VIO mulai kesulitan fitur | Pelankan ke 5%, jangan belok |
| VIO rate fluktuatif (15-30 Hz) | Ada area textureless atau drop frame | Lewati area itu pelan, jangan stop di sana |
| Log `Rejected loop closure hypothesis` berulang | Threshold loop closure ketat | Wajar muncul beberapa kali, **TIDAK** wajar muncul 20+ kali |
| `OdomF2M Not enough points (X/Y < 0.75)` | Banyak depth invalid | Catat di mana terjadi, lanjut jangan stop di area itu |

### 🔴 Indikasi JELEK — STOP REMAPPING SEKARANG

| Sinyal | Arti | Yang harus dilakukan |
|---|---|---|
| Background rtabmap_viz **merah** terus 10+ detik | VIO lost tracking | STOP joystick, tunggu hijau lagi. Kalau tidak balik hijau dalam 1 menit → CTRL+C, mulai dari Langkah 2 (`fresh_mapping.sh`) |
| Log `VWDictionary not found word` | BoW vocabulary corrupt | STOP. Pasti DB lama masih ke-load. CTRL+C, `rm ~/.ros/rtabmap.db`, mulai ulang |
| Cloud di RViz "meledak" / scatter ke segala arah | Pose estimation divergen total | STOP. Cek `ros2 topic info /rtabmap/odom` — kalau Publisher count = 2, ada double launch. Bunuh proses, mulai dari Langkah 3 |
| VIO rate drop ke <10 Hz konsisten | CPU overload atau drop frame parah | STOP. Cek `htop` — kalau CPU >95% sustained, kemungkinan ada proses zombie. Kill semua + restart |
| Setelah loop tertutup, `loop_closure_id` tetap `0` | Loop closure tidak pernah terpicu | Lanjut keliling sekali lagi. Kalau masih `0` setelah loop kedua → save peta apa adanya, screenshot, kirim ke aku |
| Peta .pgm hasil save kosong (file <10KB) atau hitam semua | `/map` topic tidak publish | STOP. Cek `ros2 topic echo /map --once` — kalau timeout, rtabmap node crash. Cek log error. |

---

## BAGIAN 4 — KALAU REMAPPING JELEK, INI YANG DIINFOKAN KE AKU

Supaya aku bisa debug cepat tanpa nanya berulang, kirim info ini via WA/chat:

1. **Screenshot rtabmap_viz** saat warna berubah (hijau→kuning→merah)
2. **Output `ros2 node list`** sebelum drive (untuk cek duplikat)
3. **Output `ros2 topic hz /rtabmap/odom`** durasi 30 detik (cek rate stabilitas)
4. **Last 50 line log rtabmap**:
   ```bash
   ls -lt ~/.ros/log/ | head -3      # cari folder log terbaru
   tail -50 ~/.ros/log/latest_*/rtabmap*/stdout.log
   ```
5. **File .pgm + .yaml hasil save** (kalau berhasil sampai save) — copy ke laptop via NoMachine atau scp
6. **Pola jalur drive** yang dilakukan (foto sketsa atau text "saya keliling ABCD lalu balik via lorong tengah")

Dengan 6 info itu, aku biasanya bisa diagnosa root cause dalam 1 sesi remote.

---

## BAGIAN 5 — CHECKLIST AKHIR SEBELUM MULAI

Centang satu per satu di kertas/notes:

- [ ] SSH ke NUC sukses (`ssh itssurabaya@10.17.36.151`)
- [ ] `git pull` sukses, HEAD = `b43fca4`
- [ ] `bash scripts/fresh_mapping.sh` jalan tanpa error merah
- [ ] `ros2 node list` kosong setelah pkill (kalau perlu pkill)
- [ ] Sensor cek: scan 10Hz, imu 100+Hz, VIO 25+Hz (Langkah 5)
- [ ] Monitor loop closure terbuka di terminal terpisah (Langkah 6)
- [ ] rtabmap_viz terbuka di NoMachine (untuk pantau warna)
- [ ] Joystick connected, R1 responsive
- [ ] Baterai/PSU cukup untuk 15 menit drive minimal
- [ ] Sudah baca ulang Bagian 3 (tahu kapan harus STOP)

---

## REFERENSI CEPAT

```
Branch     : claude/brave-newton-6zvS4
HEAD target: b43fca4
NUC IP     : 10.17.36.151
Workspace  : ~/amr_starter
DB lokasi  : ~/.ros/rtabmap.db (akan auto-backup oleh fresh_mapping.sh)
Maps dir   : ~/maps/
Doc utama  : docs/HANDOVER_8JUNI2026.md (background lengkap)
Doc PCD    : docs/HANDOVER_KORELASI_PCD.md (referensi teori, kalau perlu)
```

Semangat Anwar. Kalau ada apa-apa langsung WA, jangan dipaksa terus. Lebih baik stop di tengah trial daripada rusak dan harus debug 2 jam.

— Al Azhar
