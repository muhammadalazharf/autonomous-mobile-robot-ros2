# Implementasi Audit Arsitektur 48 Jam — Catatan Eksekusi

**Tanggal:** 21 Juni 2026 · **Branch:** `claude/zealous-darwin-6l4bs5`
**Basis:** `AUDIT_ARSITEKTUR_DAN_RENCANA_48JAM.md` (audit kode branch kamu vs Mervi)
**Prinsip eksekusi (arahan kamu):** terapkan yang memajukan progress, jangan bikin
stuck/mundur; skrip & BT dicek dulu di NUC (kalau Mervi sudah punya, pakai itu).

---

## A. DITERAPKAN (sudah diedit di repo, perlu rebuild di NUC)

| # | Fix | File | Detail |
|---|-----|------|--------|
| 1 🔴 | Frame nav `map → odom` | `nav2_params.yaml` | `bt_navigator.global_frame: odom`; `global_costmap`: `odom` + `rolling_window: true` + `width/height 10` + `track_unknown_space: false`; **static_layer dimatikan** |
| 4 🔴 | Filter self-scan | `nav2_params.yaml` | `raytrace_min_range`/`obstacle_min_range` `0.0 → 0.3` (kedua costmap) — chassis/roda tak lagi jadi obstacle hantu |
| 5 🟡 | Longgarkan costmap | `nav2_params.yaml` | `robot_radius 0.28→0.22`, `inflation_radius 0.25→0.10` (kedua costmap) |
| 2 🔴 | Yaw odom saat autonomous | `odometry_publisher.py` | Tambah `cmd_vel_cb` (Ackermann inverse `steer=atan(L·ω/v)`) + guard `joy_cb` deadzone agar joystick netral tak menimpa steering jadi 0 |
| 6 🟠 | Runtime cap anti-runaway | `stm32_bridge.cpp` | Param `autonomous_max_runtime_s` (default 10s) → auto-stop; **PWM ramping dipertahankan** (komplementer) |

## B. DIPERTAHANKAN (keunggulan branch-mu — tidak dibuang, sesuai Bagian 3 audit)

- **PWM ramping** (`stm32_bridge.cpp`, `MAX_PWM_STEP=400`) — anti-brownout NUC. Mervi tak punya.
- **`publish_tf` kondisional** (`amr_full.launch.py`, `use_rtabmap != true`) — desain TF lebih bersih.
- **Param BoW RTAB-Map** (`Kp/MaxFeatures`, `RGBD/LoopClosureReextractFeatures`, `OptimizeMaxError`) — untuk map-frame future work.

## C. DITAHAN (sengaja TIDAK diubah — alasan jelas)

| # | Item | Alasan |
|---|------|--------|
| 3 🟠 | BT minimal `navigate_to_pose_simple.xml` | **Tetap pakai BT default** (`/opt/ros/humble/.../navigate_to_pose_w_replanning_and_recovery.xml`) yang **dijamin ada**. Mengganti ke path custom berisiko mengulang bug "Couldn't open input XML file" (stuck). Overshoot recovery dimitigasi **runtime cap #6 (10s auto-stop)**. Switch ke BT minimal hanya setelah file-nya dipastikan ada di NUC. |
| 7 🟡 | `Vis/MinInliers 8 → 6` | Audit sendiri: "uji dulu, bisa naikkan false positive". Dibiarkan **8**. Ubah hanya bila uji NUC menunjukkan lock kurang nempel. |
| 8 | Skrip runtime (`run_amr_demo.sh`, `demo_drive_forward.sh`, `log_localization.py`, `reset_odom.sh`) + BT xml | **Tidak diduplikasi** — cek dulu di NUC. Kalau sudah ada (punya Mervi), pakai itu. Hindari konflik/duplikat. |

---

## D. WAJIB diverifikasi di NUC (tidak bisa dari kode)

1. **Rebuild:** `cd ~/amr_starter && colcon build --packages-select amr_slam amr_controller && source install/setup.bash`
2. **Tanda kemudi kiri=kiri** (fix `fec1ee5` belum diverifikasi) — uji joystick belok kiri → roda kiri.
3. **Satu sumber `/odom`** — pastikan tidak ada dua publisher (wheel + VIO) bentrok saat Nav2 jalan.
4. **Cek skrip Mervi di NUC** — `ls ~/amr_starter/src/amr_slam/scripts/ ~/amr_starter/.../behavior_trees/`. Kalau ada `log_localization.py` / `demo_drive_forward.sh`, pakai.
5. **TF chain** `ros2 run tf2_tools view_frames` → `odom→base_link→{laser,camera}` tanpa konflik.
6. **Goal relatif** frame `base_link x=0.5` → robot maju 0,5 m & berhenti (runtime cap jaring pengaman).

## E. Plan B (jaring pengaman demo)
Bila Nav2 BT masih nakal: pakai skrip cmd_vel-direct Mervi (`demo_drive_forward.sh`) bila
ada di NUC — bypass Nav2, publish `/cmd_vel` jarak tetap + auto-stop.

## F. Klaim laporan (jujur, sesuai Bagian 5 audit)
Navigasi otonom berbasis goal pada **frame odom** (robot terima goal Nav2 → bergerak ke
titik jarak pendek → berhenti, VIO sebagai transform mulus). Navigasi global **map-frame**
diimplementasi namun lock RTAB-Map masih kedip = **future work**. Pengaman: runtime cap +
PWM ramping aktif; failover diimplementasi namun dinonaktifkan saat demo.

---

## Reversibilitas
Semua nilai map-frame lama didokumentasikan via komentar `AUDIT 48h` di `nav2_params.yaml`,
sehingga bisa dikembalikan untuk pengembangan map-frame nanti tanpa kehilangan konteks.
