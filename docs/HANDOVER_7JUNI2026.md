# HANDOVER PROYEK AMR ITS — SESI 7 JUNI 2026

**Tanggal:** 7 Juni 2026
**Dari:** Sesi 7 Juni 2026
**Untuk:** Rekan tim yang melanjutkan
**Status:** ⚠️ Mapping belum berhasil — ada masalah rtabmap crash yang perlu diselesaikan

> **Catatan arsip (8 Juni):** Param hasil sesi ini (`Mem/STMSize: 10`,
> `Grid/NoiseFilteringRadius: 0.5`, `Grid/NoiseFilteringMinNeighbors: 5`)
> sudah digabung (merge) ke `rtabmap_mapping.launch.py` di branch
> `claude/brave-newton-6zvS4`, bersama fix hasil audit param VIO
> (`Odom/MaxVariance` dipindah ke node `rgbd_odometry`, dst). Jangan
> overwrite param ini saat sync berikutnya tanpa cross-check dulu.

---

## RINGKASAN EKSEKUTIF

Sistem VIO sudah terbukti bekerja dengan baik (27-30 Hz stabil, TF tracking smooth). Namun mapping belum berhasil diselesaikan karena serangkaian masalah teknis yang sudah diidentifikasi. Dokumen ini mencatat semua masalah dan solusinya agar sesi berikutnya bisa langsung eksekusi tanpa debugging ulang dari awal.

---

## BAGIAN 1 — INFORMASI AKSES

**IP NUC:**

```
10.17.36.151
```

**SSH dari laptop:**

```bash
ssh itssurabaya@10.17.36.151
```

**Akses visual langsung:**
Pakai NoMachine — buka aplikasi NoMachine di laptop, connect ke IP NUC di atas.

**Environment variables wajib di setiap terminal:**

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

---

## BAGIAN 2 — STATUS TERKINI

### Sudah selesai dan terbukti bekerja ✅
| Item | Status |
|------|--------|
| Hardware terdeteksi (LiDAR, RealSense, STM32) | ✅ |
| `/scan` 10 Hz stabil | ✅ |
| `/imu/data` 100 Hz stabil | ✅ |
| VIO `/rtabmap/odom` 27-30 Hz stabil | ✅ |
| TF tracking diverifikasi — Translation X naik smooth saat robot maju | ✅ |
| `publish_tf: false` di odometry_publisher (tidak ada TF conflict) | ✅ |
| Nav2 params Ackermann-aware di-deploy (10 fixes) | ✅ |
| Peta lama tersimpan di `~/maps/lab_vio_map.pgm` (bisa dipakai darurat) | ✅ |

### Belum selesai ❌
| Item | Prioritas |
|------|-----------|
| Mapping lab yang bersih dengan loop closure | 🔴 Pertama |
| Localization (RTAB-Map mode localization) | 🔴 Kedua |
| Nav2 navigasi otonom A→B | 🔴 Ketiga |
| Obstacle avoidance | 🟡 Keempat |
| Visual Regression (RANSAC) | 🟡 Kelima |
| Video demonstrasi + slide | 🟡 Keenam |

---

## BAGIAN 3 — MASALAH YANG DITEMUKAN DAN SOLUSINYA

### Masalah 1 — rtabmap crash saat launch (MASALAH TERAKHIR, BELUM SELESAI)

**Gejala:** Dialog Ubuntu muncul "Sorry, the application rtabmap has stopped unexpectedly" saat menjalankan `rtabmap_mapping.launch.py`. Topic `/rtabmap/grid_map` tidak pernah muncul.

**Kemungkinan penyebab:**
- Database lama yang corrupt masih tersisa
- Memory NUC tidak cukup saat semua sensor + rtabmap jalan bersamaan
- Dependency missing atau versi tidak kompatibel

**Yang harus dilakukan pertama kali:**

```bash
# Hapus semua database lama
rm -f ~/maps/lab_vio.db
rm -f ~/.ros/rtabmap.db

# Verifikasi sudah bersih
ls ~/maps/
ls ~/.ros/*.db 2>/dev/null && echo "masih ada db" || echo "sudah bersih"
```

Lalu cek log crash untuk tahu penyebab pasti:

```bash
ls -lt ~/.ros/log/ | head -5
cat ~/.ros/log/latest_*/rtabmap*/stdout.log 2>/dev/null | tail -50
```

---

### Masalah 2 — `/rtabmap/grid_map` tidak muncul

**Gejala:** `ros2 topic list | grep rtabmap` hanya muncul `/rtabmap/odom` dan `/rtabmap/republish_node_data`.

**Penyebab:** `amr_full.launch.py` dengan `use_rtabmap:=true` tidak meneruskan parameter `publish_grid_map: true` ke node rtabmap dengan benar.

**Solusi:** Jangan pakai `amr_full.launch.py use_rtabmap:=true`. Selalu pakai **dua terminal terpisah** seperti di Bagian 4.

---

### Masalah 3 — Loop closure tidak pernah terpicu

**Gejala:** `loop_closure_id: 0` dan `proximity_detection_id: 0` terus menerus.

**Penyebab:** Robot tidak pernah keliling penuh dan kembali ke titik start. Maju mundur 2 meter tidak cukup karena `Mem/STMSize: 10` artinya 10 node terakhir dikecualikan dari pencarian loop closure.

**Solusi:** Keliling penuh satu putaran menyusuri semua dinding, kembali ke titik start persis.

---

### Masalah 4 — VIO lost tracking di ruangan kecil

**Gejala:** Point cloud 3D hancur seperti "meledak", warna merah di rtabmap_viz.

**Penyebab:** Dinding polos tanpa tekstur — kamera tidak bisa track fitur visual. Ruangan kecil memperparah karena robot terlalu dekat ke dinding.

**Solusi:** Mapping di ruangan yang lebih besar dengan furniture (meja, kursi, dll) dan tempel kertas bermotif di dinding kalau perlu.

---

### Masalah 5 — Peta 2D bergaris double

**Gejala:** Dinding di peta .pgm terlihat dua garis paralel.

**Penyebab:** Robot melewati area yang sama dari dua estimasi posisi berbeda akibat odometri drift sebelum loop closure terpicu.

**Solusi:** Pastikan loop closure terpicu sebelum mapping area yang sama dua kali.

---

## BAGIAN 4 — PROSEDUR MAPPING YANG BENAR

> ⚠️ WAJIB pakai cara dua terminal terpisah ini. Jangan pakai `amr_full.launch.py use_rtabmap:=true` karena bermasalah.

### Persiapan sebelum mapping

```bash
# Hapus database lama
rm -f ~/maps/lab_vio.db
rm -f ~/.ros/rtabmap.db
```

### Terminal 1 — Sensor utama (jangan pernah ditutup)

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash && ros2 launch amr_bringup amr_full.launch.py use_slam:=false use_nav2:=false use_rtabmap:=false use_vr:=false use_failover:=false
```

Tunggu sampai muncul:
- `RPLidar health status: OK`
- `RealSense Node Is Up!`
- `[stm32_bridge] [TX] V:0,S:0` berulang

### Terminal 2 — RTAB-Map mapping (jangan pernah ditutup)

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py database_path:=$HOME/maps/lab_vio.db
```

Tunggu 15 detik. Warning `DepthAsMask` dan `Rejected loop closure` → normal, abaikan.

### Terminal 3 — Verifikasi topic muncul

```bash
source ~/amr_starter/install/setup.bash
ros2 topic list | grep rtabmap
```

Harus muncul minimal:

```
/rtabmap/grid_map
/rtabmap/odom
/rtabmap/info
```

Kalau `/rtabmap/grid_map` tidak muncul → Terminal 2 bermasalah, cek log error.

### Terminal 4 — Pantau loop closure selama mapping

```bash
source ~/amr_starter/install/setup.bash
watch -n 1 "ros2 topic echo /rtabmap/info --once | grep -E 'loop_closure_id|proximity'"
```

### Terminal 5 (opsional) — Buka rtabmap_viz di NoMachine

```bash
source ~/amr_starter/install/setup.bash
ros2 run rtabmap_viz rtabmap_viz
```

---

## BAGIAN 5 — TEKNIK MENGEMUDI UNTUK MAPPING

### Aturan wajib
- Tahan **R1 terus** (deadman switch)
- Stik **10-15% saja** — sangat pelan
- **Berhenti 3 detik** sebelum setiap belok
- **Jangan keluar ruangan**
- **Jangan berputar di tempat**

### Pola jalur untuk ruangan dengan 6 meja (2 kolom)

```
START (pojok bawah kiri)
  │
  ▼ 1. Susuri dinding kiri → naik ke atas
  ▼ 2. Susuri dinding atas → ke kanan
  ▼ 3. Susuri dinding kanan → turun ke bawah
  ▼ 4. Susuri dinding bawah → kembali ke START
         ← LOOP CLOSURE PERTAMA terpicu di sini
  ▼ 5. Masuk lorong tengah (antara 2 kolom meja) → naik ke atas
  ▼ 6. Balik → lorong tengah turun ke bawah
  ▼ 7. Lorong kiri (antara dinding kiri dan kolom kiri meja)
  ▼ 8. Lorong kanan (antara kolom kanan meja dan dinding kanan)
  ▼ 9. Kembali ke START → LOOP CLOSURE KEDUA
```

### Pantau warna di rtabmap_viz
| Warna | Arti | Tindakan |
|-------|------|----------|
| Hijau | VIO tracking bagus | Lanjut normal |
| Kuning | VIO mulai kesulitan | Pelankan stik jadi 5% |
| Merah | VIO lost tracking | Berhenti total, tunggu hijau lagi |

### Tanda loop closure berhasil
Di Terminal 4, `loop_closure_id` berubah dari `0` ke angka positif (misal `1`, `2`, dst).

---

## BAGIAN 6 — SIMPAN PETA SETELAH MAPPING

```bash
source ~/amr_starter/install/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/lab_vio_map
```

Tunggu `Map saved successfully`. Verifikasi:

```bash
ls -lh ~/maps/
```

Harus ada `lab_vio_map.pgm` (minimal 50K) dan `lab_vio_map.yaml`.

Lihat hasil di NoMachine — buka file manager → navigasi ke `~/maps/` → buka `lab_vio_map.pgm`.

**Peta yang bagus:** garis dinding jelas, area putih ruang kosong, tidak ada garis double, tidak ada garis radial berlebihan.

---

## BAGIAN 7 — LANGKAH SETELAH MAPPING BERHASIL

### Localization

```bash
# Terminal 1 tetap sama (sensor)

# Terminal 2 — ganti ke mode localization
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping rtabmap_localization.launch.py database_path:=$HOME/maps/lab_vio.db
```

Verifikasi:

```bash
ros2 param get /rtabmap Mem/IncrementalMemory
# Harus: false (localization mode)
```

### Nav2 navigasi otonom

```bash
# Terminal 1
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash && ros2 launch amr_bringup amr_full.launch.py use_slam:=false use_nav2:=true use_rtabmap:=false use_vr:=false use_failover:=false map:=$HOME/maps/lab_vio_map.yaml
```

Buka RViz2 di laptop:

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run rviz2 rviz2
```

Gunakan **2D Pose Estimate** untuk set posisi awal robot, lalu **2D Goal Pose** untuk set tujuan.

---

## BAGIAN 8 — PARAMETER TEKNIS PENTING

### Config yang sudah diubah
| File | Parameter | Nilai | Alasan |
|------|-----------|-------|--------|
| `rtabmap_mapping.yaml` | `Mem/STMSize` | `10` | Loop closure lebih cepat di ruangan kecil |
| `rtabmap_mapping.yaml` | `Grid/NoiseFilteringRadius` | `0.5` | Buang titik noise yang sendirian |
| `rtabmap_mapping.yaml` | `Grid/NoiseFilteringMinNeighbors` | `5` | Minimum tetangga untuk titik valid |
| `odometry_publisher.py` | `publish_tf` | `False` | Cegah TF conflict dengan VIO |

### Lokasi file penting

```
~/amr_starter/src/amr_3d_mapping/config/rtabmap_mapping.yaml   ← config utama RTAB-Map
~/amr_starter/src/amr_3d_mapping/launch/rtabmap_mapping.launch.py
~/amr_starter/src/amr_3d_mapping/launch/rtabmap_localization.launch.py
~/amr_starter/src/amr_slam/config/nav2_params.yaml              ← Nav2 Ackermann config
~/amr_starter/src/amr_controller/scripts/odometry_publisher.py  ← publish_tf=False
~/maps/                                                          ← semua peta tersimpan
```

---

## BAGIAN 9 — TROUBLESHOOTING CEPAT

| Masalah | Solusi |
|---------|--------|
| rtabmap crash saat launch | Hapus db lama, cek log `~/.ros/log/latest_*/rtabmap*/stdout.log` |
| `/rtabmap/grid_map` tidak muncul | Jangan pakai `amr_full use_rtabmap:=true`, pakai dua terminal terpisah |
| Loop closure tidak terpicu | Keliling penuh satu putaran, kembali ke titik start persis |
| Point cloud 3D hancur (merah semua) | Ruangan terlalu kecil/polos, pindah ruangan lebih besar |
| Peta 2D bergaris double | Loop closure belum terpicu sebelum area dilewati dua kali |
| Joystick tidak merespons | Pastikan tahan R1, tekan tombol PS untuk reconnect |
| SSH tidak konek | IP NUC: `10.17.36.151`, cek jaringan |

---

## BAGIAN 10 — RINGKASAN PERINTAH LENGKAP

```bash
# === PERSIAPAN ===
rm -f ~/maps/lab_vio.db
rm -f ~/.ros/rtabmap.db

# === TERMINAL 1 (jangan tutup) ===
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/amr_starter && source install/setup.bash && \
ros2 launch amr_bringup amr_full.launch.py \
  use_slam:=false use_nav2:=false use_rtabmap:=false \
  use_vr:=false use_failover:=false

# === TERMINAL 2 (jangan tutup) ===
export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/amr_starter/install/setup.bash
ros2 launch amr_3d_mapping rtabmap_mapping.launch.py \
  database_path:=$HOME/maps/lab_vio.db

# === TERMINAL 3 (verifikasi) ===
source ~/amr_starter/install/setup.bash
ros2 topic list | grep rtabmap              # cek topic muncul
ros2 topic hz /rtabmap/odom                 # cek VIO rate (harus 27-30 Hz)

# === TERMINAL 4 (pantau loop closure) ===
source ~/amr_starter/install/setup.bash
watch -n 1 "ros2 topic echo /rtabmap/info --once | grep -E 'loop_closure_id|proximity'"

# === SIMPAN PETA ===
ros2 run nav2_map_server map_saver_cli -f ~/maps/lab_vio_map
ls -lh ~/maps/
```

---

## PESAN PENUTUP

Fondasi sistem sudah sangat kuat — VIO bekerja dengan baik, TF bersih, semua sensor stabil. Yang tersisa hanya menyelesaikan mapping dengan benar.

**Satu hal terpenting yang harus dilakukan pertama kali:** cek log crash rtabmap dan pastikan database lama sudah terhapus sebelum launch ulang.

Urutan prioritas yang tersisa:
1. 🔴 Selesaikan masalah rtabmap crash
2. 🔴 Mapping lab baru yang bersih dengan loop closure
3. 🔴 Localization + Nav2 navigasi otonom
4. 🟡 Obstacle avoidance
5. 🟡 Visual Regression (RANSAC)
6. 🟡 Video demonstrasi + slide

Semangat! 🤖
