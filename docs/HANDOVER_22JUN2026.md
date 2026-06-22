# Handover AMR — Minggu 16–22 Juni 2026

**Penyusun:** Muhammad Al Azhar Faradis (NRP 2040241017)
**Branch:** `claude/zealous-darwin-6l4bs5`
**Status:** Audit 48h diterapkan & dibuild di NUC. Siap uji lapangan.
**Basis:** Handover Mervi 19 Jun 2026 + Audit Arsitektur 48 Jam.

---

## 0. TL;DR (baca ini saja kalau buru-buru)

1. **Adopsi runtime Mervi BERHASIL.** 4 fix Nav2 + ambang RTAB-Map → autonomous navigation berfungsi (commit `76b1e99`, `9be5902`).
2. **Steering autonomous DIPERBAIKI** (commit `fec1ee5`): `steer_rad = -atan(L·ω/v)`. Velocity tidak dinegasi — kabel motor sudah ditukar fisik.
3. **Audit 48h diterapkan** (commit `19cebb7`): pivot frame `map → odom`, self-scan filter, runtime cap 10s, odom yaw dari `/cmd_vel`.
4. **Build amr_controller sukses di NUC** (6.40s). Skrip Mervi (`run_amr_demo.sh`, `demo_drive_forward.sh`, `log_localization.py`, `reset_odom.sh`, `behavior_trees/`) **sudah ada lokal** — tidak perlu sinkron dari repo Mervi.
5. **Mode demo:** navigasi otonom di frame **odom** (VIO mulus), goal jarak pendek (≤2 m relatif `base_link`). Map-frame = future work.

---

## 1. Yang Sudah Beres (Commit History Minggu Ini)

| Hari | Commit | Ringkasan |
|------|--------|-----------|
| Sen 16 | `19b3660` | Laporan korelasi Sistem Kontrol Proses |
| Sen 16 | `15a213b` | Laporan korelasi Pengolahan Citra Digital |
| Sel 17 | `fab3ef4` | Kalibrasi empiris PPR 1496→3858 (over-report 2.58×, R²=0.998) + `publish_tf` kondisional |
| Sel 17 | `6d48dde` | Software PWM ramping (`MAX_PWM_STEP=400`) — anti-brownout NUC |
| Rab 18 | `99373ff` `e047af2` | Fix Nav2 plugin namespace (`nav2_smoother::SimpleSmoother`) + hapus `plugin_lib_names` |
| Rab 18 | `444917f` | Diagram alir frame-to-map (Mermaid) |
| Kam 19 | `9be5902` | Samakan ambang RTAB-Map localization dengan mapping (fix loop rejection) |
| Kam 19 | `76b1e99` | **Apply 4 fix Mervi handover** → autonomous navigation berfungsi |
| Kam 19 | `052e5d7` | Root cause analysis Nav2 + RTAB-Map (9 gerbang) |
| Kam 19 | `fec1ee5` | **Fix steering autonomous** (negasi `steer_rad`) |
| Jum 20 | `5fc2fd2` `3fa2e0a` `1a0614a` | Laporan teknis final + suplemen + briefing |
| Jum 20 | `252dbfe` | Bank data terkonsolidasi + generator kerangka laporan |
| Sab 21 | `9df05c7` | **Evidence package** (57 file MD/CSV/JSON + ZIP, 17 kategori) |
| Sab 21 | `0c5296f` | **Fishbone analysis** autonomous navigation → kerangka BAB II |
| Sab 21 | `2425223` | Ringkasan sesi + perbandingan repo (kamu vs Mervi) |
| Min 22 | `f0fc6ee` | **Defense brief sidang** — jawaban 7 pertanyaan kritis + data |
| Min 22 | `19cebb7` | **Audit 48h fixes** — pivot odom-frame + 4 fix lain |

---

## 2. Perubahan Arsitektural (Audit 48h, Commit `19cebb7`)

### A. Diterapkan (5 fix)

| # | Fix | File | Detail |
|---|-----|------|--------|
| 1 🔴 | Frame `map → odom` | `nav2_params.yaml` | `bt_navigator.global_frame: odom`; global_costmap rolling_window + `track_unknown_space: false`; **static_layer dihapus** |
| 2 🔴 | Yaw odom saat autonomous | `odometry_publisher.py` | Tambah `cmd_vel_cb` (Ackermann inverse `steer=atan(L·ω/v)`) + deadzone guard `joy_cb` |
| 4 🔴 | Filter self-scan | `nav2_params.yaml` | `raytrace/obstacle_min_range` `0.0 → 0.3` (kedua costmap) |
| 5 🟡 | Longgarkan costmap | `nav2_params.yaml` | `robot_radius 0.28→0.22`, `inflation_radius 0.25→0.10` |
| 6 🟠 | Runtime cap anti-runaway | `stm32_bridge.cpp` | Param `autonomous_max_runtime_s` (default 10s) → auto-stop |

### B. Dipertahankan (keunggulan branch-mu)

- **PWM ramping** (`MAX_PWM_STEP=400`) — anti-brownout NUC. Mervi tak punya.
- **`publish_tf` kondisional** — desain TF lebih bersih dari hardcoded `False`.
- **Param BoW RTAB-Map** (`Kp/MaxFeatures`, `OptimizeMaxError`) — untuk map-frame future work.

### C. Ditahan (sengaja TIDAK diubah)

- **BT minimal `navigate_to_pose_simple.xml`** — tetap pakai BT default `/opt/ros/humble/...` yang dijamin ada (mitigasi via runtime cap #6).
- **`Vis/MinInliers 8 → 6`** — biarkan 8, ubah hanya bila lock kurang nempel.
- **Skrip runtime** — **sudah ada lokal di NUC** (`src/amr_slam/scripts/`), tidak perlu duplikasi.

---

## 3. Status File di NUC

### File Audit (sudah aktif setelah pull + build)

```
✓ src/amr_slam/config/nav2_params.yaml           [YAML, no rebuild]
✓ src/amr_controller/scripts/odometry_publisher.py [Python, symlink]
✓ src/amr_controller/src/stm32_bridge.cpp        [C++, rebuilt 6.40s]
✓ docs/IMPLEMENTASI_AUDIT_48JAM.md               [dokumentasi]
```

### Skrip Mervi sudah ada lokal (audit item #8 resolved)

```
src/amr_slam/scripts/run_amr_demo.sh        ← launcher tmux 4-pane
src/amr_slam/scripts/demo_drive_forward.sh  ← Plan B (cmd_vel direct)
src/amr_slam/scripts/log_localization.py    ← bukti lokalisasi real-time
src/amr_slam/scripts/reset_odom.sh          ← reset odom sebelum goal
src/amr_slam/scripts/amr_loop_patrol.py     ← patrol mode
src/amr_slam/behavior_trees/                ← BT custom (kalau ada)
```

### Build status

```
$ colcon build --packages-select amr_controller
Starting >>> amr_controller
Finished <<< amr_controller [6.40s]
Summary: 1 package finished [6.58s]
```

---

## 4. Rencana Uji Lapangan (Sesuai Audit Section D)

### Verifikasi berurutan (jangan lompat)

1. **TF chain**
   ```bash
   ros2 run tf2_tools view_frames
   # Expect: odom→base_link→{laser,camera}, no conflict
   ```

2. **Tanda kemudi kiri=kiri** (fix `fec1ee5` butuh verifikasi)
   ```bash
   # Joystick: dorong analog kanan ke KIRI → roda depan harus belok KIRI
   ros2 topic echo /joy
   ```

3. **Single `/odom` publisher** (tak ada bentrok wheel vs VIO)
   ```bash
   ros2 topic info /odom -v
   # Expect: hanya 1 publisher
   ```

4. **Nav2 lifecycle active**
   ```bash
   ros2 lifecycle get /bt_navigator
   # Expect: active [3]
   ```

5. **Goal relatif `base_link x=0.5`**
   ```bash
   bash src/amr_slam/scripts/reset_odom.sh
   ros2 param set /stm32_bridge autonomous_enabled true
   ros2 topic pub --once /goal_pose geometry_msgs/PoseStamped \
     "{header: {frame_id: 'base_link'}, pose: {position: {x: 0.5}}}"
   # Expect: maju 0.5 m → berhenti (runtime cap 10s sbg jaring pengaman)
   ```

### Plan B (jaring pengaman demo)

Bila Nav2 BT nakal:
```bash
bash src/amr_slam/scripts/demo_drive_forward.sh 0.5 0.2
# Bypass Nav2, cmd_vel direct, jarak 0.5 m kec 0.2 m/s, auto-stop
```

---

## 5. Bukti yang Wajib Direkam (untuk Laporan)

| Bukti | Cara Capture | File output |
|-------|--------------|-------------|
| Video robot terima goal & bergerak | HP/kamera | `evidence/demo_goal_xx.mp4` |
| `/cmd_vel` selama autonomous | `ros2 bag record /cmd_vel /odom` | `bags/demo_run.db3` |
| Log lokalisasi real-time | `python3 src/amr_slam/scripts/log_localization.py` | `logs/localization_22jun.csv` |
| `rqt_graph` | screenshot | `evidence/rqt_graph.png` |
| RViz path + costmap | screenshot | `evidence/rviz_nav_goal.png` |
| Database RTAB-Map | sudah ada | `~/maps/lab_demo_xxxxx.db` |

---

## 6. Klaim Laporan (Jujur & Tahan Sidang)

> *"Sistem mendemonstrasikan navigasi otonom berbasis goal pada **frame odometry**: robot menerima goal Nav2 (SmacPlannerHybrid + RegulatedPurePursuit) → bergerak ke titik tujuan jarak pendek → berhenti, dengan odometri visual-inersia (RTAB-Map `rgbd_odometry`) sebagai sumber transform yang mulus. Lokalisasi global pada frame map masih mengalami ketidakstabilan lock pada layout pengujian; navigasi map-frame yang andal menjadi **pekerjaan lanjutan**. Pengaman runtime cap (10 s auto-stop) + PWM ramping (anti-brownout) aktif; failover controller diimplementasikan namun dinonaktifkan saat demo."*

---

## 7. Yang TIDAK Bisa Dipastikan dari Kode (Wajib Cek Runtime)

1. **Tanda kemudi kiri=kiri** di hardware (fix `fec1ee5` belum diverifikasi NUC).
2. **Drift VIO** sepanjang jarak demo — kalau goal > 2 m, drift bisa signifikan.
3. **Brownout NUC** saat motor start — PWM ramping seharusnya jaring, tapi cek live.
4. **Encoder format auto-detect** di `odometry_publisher.py` — pastikan log `[AUTO-DETECT]` muncul dengan format yang benar.

---

## 8. Future Work (Setelah Demo & Sidang)

- **Map-frame navigation**: investigasi root cause kedip RTAB-Map lock (kemungkinan: pencahayaan, fitur visual kurang, BoW vocab terlalu kecil).
- **IMU integration**: tanpa IMU, yaw drift odometry signifikan (covariance 0.10 rad). Tambah IMU → fuse via `robot_localization` EKF.
- **Failover controller**: aktifkan kembali untuk robustness produksi (saat ini dinonaktifkan demi simplifikasi demo).
- **`depth_scan` re-enable**: kalibrasi proper untuk 3D obstacle avoidance.
- **`Vis/MinInliers` tuning**: uji 6 vs 8 di layout produksi.

---

## 9. Referensi Dokumen Penting

| Topik | File |
|-------|------|
| Audit arsitektur lengkap | `AUDIT_ARSITEKTUR_DAN_RENCANA_48JAM.md` (uploaded, tidak di-commit) |
| Catatan eksekusi audit | `docs/IMPLEMENTASI_AUDIT_48JAM.md` |
| Defense brief 7 pertanyaan | `docs/DEFENSE_BRIEF_SIDANG_AMR.md` |
| Perbandingan repo kamu vs Mervi | `docs/RINGKASAN_SESI_DAN_PERBANDINGAN_REPO.md` |
| Evidence package | `docs/generated/raw_amr_evidence_package/` |
| Fishbone analysis | `docs/generated/fishbone_autonomous_navigation_analysis/` |
| Root cause Nav2 9 gerbang | (commit `052e5d7`) |

---

**Status akhir minggu:** Sistem siap demo di mode **odom-frame, goal jarak pendek**. Semua jaring pengaman aktif (runtime cap + PWM ramping + watchdog cmd_vel). Tinggal verifikasi lapangan & rekam bukti.
