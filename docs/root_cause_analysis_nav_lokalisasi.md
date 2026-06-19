# Root Cause Analysis — Kegagalan Navigasi & Lokalisasi AMR
**Proyek:** Autonomous Mobile Robot Ackermann — PJBL 4-24  
**Tanggal:** 19 Juni 2026  
**Penyusun:** Muhammad Al Azhar Faradis (2040241017) & Mararevi Subagyo (2040241036)

---

## Ringkasan Eksekutif

Pipeline autonomous (sensor → lokalisasi → perencanaan jalur → eksekusi gerak) melibatkan
**9 titik kegagalan tersembunyi** yang harus diselesaikan secara berurutan sebelum robot
dapat bergerak otonom. Setiap kegagalan memblokir seluruh pipeline sehingga robot tampak
"tidak merespons" meskipun sebagian sistem sudah berjalan normal.

---

## Bagian 1 — Kegagalan Stack Nav2 (8 Gerbang)

### Tabel 1. Root Cause Analysis Nav2

| # | Gejala (Log / Perilaku) | Komponen | Akar Masalah | Perbaikan | Commit |
|---|------------------------|----------|--------------|-----------|--------|
| 1 | `VoxelLayer plugin does not exist` | Nav2 Costmap | Format namespace plugin salah: `/` vs `::` campur-aduk di `nav2_params.yaml` | Ubah semua costmap/controller/smoother/waypoint → `::`, biarkan smac_planner & behaviors tetap `/` | `99373ff` |
| 2 | `ID [RemovePassedGoals] already registered` — Nav2 crash saat startup | bt_navigator | Blok `plugin_lib_names` didefinisikan eksplisit → Nav2 Humble mendaftarkan plugin dua kali (auto-load + manual) | Hapus seluruh blok `plugin_lib_names` → Nav2 auto-load via pluginlib | `99373ff` |
| 3 | `Node not recognized: RateController` | bt_navigator | Turunan dari masalah #2 (double-registration merusak registry BT) | Terselesaikan otomatis bersama fix #2 | `99373ff` |
| 4 | `Action server spin not available` — BT gagal eksekusi | behavior_server | Plugin `spin` tidak didaftarkan di `behavior_plugins`, padahal BT default memanggil node `<Spin>` | Tambahkan `spin: plugin: "nav2_behaviors/Spin"` ke `behavior_plugins` | `76b1e99` |
| 5 | `Couldn't open input XML file` — bt_navigator crash | bt_navigator | `default_nav_to_pose_bt_xml` hanya berisi nama file, bukan path absolut → file tidak ditemukan | Ganti ke path absolut: `/opt/ros/humble/share/nav2_bt_navigator/behavior_trees/...` | `76b1e99` |
| 6 | `collision ahead` / `lethal obstacle` terus-menerus — planner gagal buat jalur | Local & Global Costmap | `depth_scan` dari kamera depth (RealSense) salah mendeteksi lantai datar sebagai obstacle → costmap penuh obstacle hantu | Hapus `depth_scan` dari `observation_sources`; gunakan LiDAR (`scan`) saja untuk costmap | `76b1e99` |
| 7 | Nav2 kirim `/cmd_vel` tapi robot diam — `Failed to make progress` | nav2.launch.py & stm32_bridge | Remap aktif: Nav2 publish ke `/cmd_vel_nav`, bridge hanya mendengarkan `/cmd_vel` → perintah tidak sampai ke motor | Hapus `SetRemap` di `nav2.launch.py` → Nav2 publish langsung ke `/cmd_vel` | `76b1e99` |
| 8 | Robot tetap diam walau `/cmd_vel` menunjukkan `linear.x = 0.3` | stm32_bridge | Parameter `autonomous_enabled` default `false` (safety gate) → bridge membuang semua perintah Nav2 | `ros2 param set /stm32_bridge autonomous_enabled true` (wajib dijalankan tiap sesi) | — (runtime) |

---

## Bagian 2 — Kegagalan Lokalisasi RTAB-Map

### Tabel 2. Perbandingan Parameter Mapping vs Lokalisasi (Sebelum Fix)

| Parameter | Nilai saat Mapping | Nilai Localization (sebelum fix) | Selisih | Dampak |
|-----------|-------------------|----------------------------------|---------|--------|
| `Rtabmap/LoopThr` | 0.05 | 0.11 | **2.2× lebih ketat** | Loop closure candidate selalu di-reject walau skor tinggi |
| `Vis/MinInliers` | 8 | 10 | **+25% lebih ketat** | Verifikasi geometris gagal di area low-texture |
| `Rtabmap/DetectionRate` | 2.0 Hz | 1.0 Hz | **Setengah frekuensi** | Peluang deteksi loop closure berkurang 50% |
| `Kp/MaxFeatures` | 400 | **tidak ada** | Missing | Vocabulary BoW lemah → place recognition gagal |
| `Kp/DetectorStrategy` | 8 (GFTT/BRIEF) | **tidak ada** | Missing | Descriptor tidak cocok dengan yang tersimpan di .db |
| `RGBD/LoopClosureReextractFeatures` | true | **tidak ada** | Missing | Kandidat loop tidak di-verifikasi ulang → reject |
| `RGBD/OptimizeMaxError` | 5.0 | 3.0 (default) | Lebih ketat | Koreksi pose saat lock pertama ditolak (robot di posisi jauh) |
| `Mem/STMSize` | 10 | **tidak ada** | Missing | Working memory window tidak konsisten → scoring tidak valid |

### Tabel 3. Root Cause Analysis Lokalisasi

| Gejala | Akar Masalah | Penjelasan Teknis | Perbaikan | Commit |
|--------|--------------|-------------------|-----------|--------|
| Log RTAB-Map: `Loop closure rejected` terus-menerus | Config localization **lebih ketat** dari ambang yang baked-in di `.db` saat mapping | Map dibangun dengan `LoopThr=0.05`; relokalisasi mencoba dengan `LoopThr=0.11`. Kandidat yang sama yang diterima saat mapping selalu ditolak saat lokalisasi | Samakan semua parameter localization dengan mapping (lihat Tabel 2) | `9be5902` |
| Robot tidak bisa menemukan posisinya di peta (`Localization failed`) | 3 parameter kritis hilang dari config localization (`Kp/*`, `RGBD/LoopClosureReextractFeatures`) | Tanpa `Kp/*`: vocabulary BoW tidak diinisialisasi dengan benar → skor place recognition rendah. Tanpa re-extract: kandidat loop tidak diverifikasi ulang geometris → reject | Tambahkan semua parameter yang hilang ke `rtabmap_localization.yaml` | `9be5902` |
| Pose robot melompat / tidak stabil saat lock | `RGBD/OptimizeMaxError` terlalu ketat (3.0 default) | Saat lock pertama, initial pose estimate bisa jauh dari true pose. Koreksi besar (>3.0) ditolak oleh optimizer meski valid | Naikkan `RGBD/OptimizeMaxError` dari 3.0 → 5.0 | `9be5902` |

---

## Bagian 3 — Arsitektur Pipeline Autonomous (Setelah Fix)

```
[Hardware]                [Software Stack]                    [Output]
STM32 + Motor  ◄── UART ──── stm32_bridge ◄──────────────────── /cmd_vel
                              (autonomous_enabled=true)              ▲
                                                                     │
Encoder ────────────────────► /odom                                  │
                                                                     │
RPLidar A1 ─────────────────► /scan ──────► Nav2                ────┘
                                          Controller
RealSense D455                            (RegulatedPurePursuit)
  RGB + Depth ──► rgbd_sync ──► /rgbd_image                         ▲
                                    │                                │
                                    ├──► rgbd_odometry ──► /odom     │
                                    │    (VIO: Visual-Inertial)      │
                                    │                                │
                                    └──► RTAB-Map ──► /map ──► Nav2 ─┘
                                         (Localization)   Global Planner
                                                          (SmacHybrid)
```

**Catatan arsitektur:**
- Mode demo saat ini: **tanpa failover_controller** (dinonaktifkan). Nav2 → `/cmd_vel` langsung.
- Joystick R1 = `manual_override` di bridge → rem darurat manual wajib selalu siap.
- `depth_scan` tetap aktif untuk RTAB-Map (lokalisasi), dinonaktifkan hanya dari costmap.

---

## Bagian 4 — Metrik Peta Produksi

**File:** `lab_demo_18jun.db` (743 MB)  
**Dibangun:** 18 Juni 2026, Laboratorium E105 ITS Surabaya

| Metrik | Nilai |
|--------|-------|
| Panjang trajektori mapping | 28.9 m |
| Global loop closures | 125 |
| Proximity loop closures | 648 |
| Strategi registrasi | Vis+ICP (Strategy=2) |
| Resolusi grid | 5 cm/cell |

**Interpretasi:** Rasio proximity/global = 648/125 = **5.2** — menunjukkan robot secara konsisten mendeteksi kembali area yang sudah dikunjungi (loop closure sehat). Peta berkualitas cukup untuk lokalisasi selama layout ruangan tidak berubah signifikan.

---

## Bagian 5 — Rekomendasi Pengembangan Lanjutan

| Prioritas | Rekomendasi | Alasan |
|-----------|-------------|--------|
| Tinggi | Mapping ulang layout E105 saat ini | Layout berubah sejak 18 Juni → obstacle hantu di costmap, planner sering `no valid path` |
| Tinggi | Kalibrasi `min_obstacle_height` depth camera | Re-enable depth_scan di costmap setelah dipastikan tidak salah baca lantai |
| Sedang | Perbaiki failover_controller | Tambah `map_timeout_s` besar + filter LiDAR return < 0.15 m → auto e-stop kembali aktif |
| Sedang | Uji waypoint patrol multi-goal | Setelah single-goal stabil, uji navigasi beruntun di area lapang |
| Rendah | Dokumentasi `autonomous_enabled` di SOP | Gate ini tersembunyi di kode bridge → mudah dilupakan |

