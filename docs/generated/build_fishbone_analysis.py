#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_fishbone_analysis.py  (READ-ONLY)
=======================================================================
Fishbone (Ishikawa) System Analysis untuk target:
  "AMR berjalan otonom: global planner point-to-point + local planner
   obstacle-avoidant."

Menulis ke: docs/generated/fishbone_autonomous_navigation_analysis/
+ ZIP: docs/generated/fishbone_autonomous_navigation_analysis.zip

Gaya systems-engineering per bone:
  Requirement -> Implementation evidence -> Dependency -> Risk/Gap -> Report placement
Status validasi:
  [VF] Terverifikasi dari file repo
  [VL] Terverifikasi dari database/log
  [PG] Berdasarkan catatan progress
  [BT] Belum terbukti (perlu bukti runtime)
Tidak mengubah source utama. Tidak mengarang data.
=======================================================================
"""
import csv, json, os, zipfile
from datetime import date

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "generated", "fishbone_autonomous_navigation_analysis")
ZIP = os.path.join(REPO, "docs", "generated", "fishbone_autonomous_navigation_analysis.zip")

VF = "Terverifikasi dari file repo"
VL = "Terverifikasi dari database/log"
PG = "Berdasarkan catatan progress"
BT = "Belum terbukti (perlu bukti runtime)"

EFFECT = ("AMR berjalan otonom: global planner point-to-point dari pose robot "
          "menuju goal, dan local planner obstacle-avoidant menghindari rintangan.")

# Sumber file (path repo)
F = {
    "urdf": "src/amr_description/urdf/amr_description.urdf.xacro",
    "bridge": "src/amr_controller/src/stm32_bridge.cpp",
    "odom": "src/amr_controller/scripts/odometry_publisher.py",
    "imu": "src/amr_controller/scripts/imu_merger_node.py",
    "full": "src/amr_bringup/launch/amr_full.launch.py",
    "sensors": "src/amr_bringup/launch/sensors_launch.py",
    "joy": "src/amr_bringup/config/joy_params.yaml",
    "rmap": "src/amr_3d_mapping/config/rtabmap_mapping.yaml",
    "rloc": "src/amr_3d_mapping/config/rtabmap_localization.yaml",
    "rloc_launch": "src/amr_3d_mapping/launch/rtabmap_localization.launch.py",
    "rmap_launch": "src/amr_3d_mapping/launch/rtabmap_mapping.launch.py",
    "nav2": "src/amr_slam/config/nav2_params.yaml",
    "nav2_launch": "src/amr_slam/launch/nav2.launch.py",
    "goal": "src/amr_slam/scripts/goal_sender.py",
    "failover": "src/amr_failover/amr_failover/failover_controller.py",
    "rca": "docs/root_cause_analysis_nav_lokalisasi.md",
    "frames": "frames_2026-06-09_22.09.38.pdf",
}

# =====================================================================
# DEFINISI 12 BONE
# =====================================================================
BONES = [
 {"id": "A", "title": "Platform Hardware dan Aktuator", "subbab": "2.2",
  "requirement": "Robot memiliki platform fisik 4WD Ackermann yang mampu "
                 "mengeksekusi gerak translasi & kemudi sesuai perintah navigasi.",
  "evidence": [
     ("Sasis 4WD + 4 roda + 2 steering link", f"{F['urdf']}", VF),
     ("Motor PG45 (4WD: 1 motor + 2 diferensial + shaft)", f"{F['urdf']} (komentar)", VF),
     ("Servo kemudi DSSERVO D25, MAX_STEER 45, STEER_TRIM -5", f"{F['bridge']}", VF),
     ("STM32F407 (USB Virtual COM 115200)", f"{F['bridge']}", VF),
     ("Encoder pada PG45 -> /encoder", f"{F['bridge']}, {F['odom']}", VF),
     ("Geometri: wheelbase 0.5 m, track 0.4 m, wheel_radius 0.0775 m", f"{F['urdf']}", VF),
     ("Baterai LiPo Ovonic 5300 mAh 6S (>22 V)", "laporan/progress", PG),
     ("Driver motor BTS7960", "Tidak ditemukan di repo saat ini (rancangan)", PG),
     ("Buck converter / power management", "Tidak ditemukan di repo saat ini", BT),
     ("Emergency stop FISIK / push button", "Tidak ditemukan di repo (e-stop SOFTWARE ada)", BT),
  ],
  "dependency": "Catu daya stabil; firmware STM32; PWM ramping anti-brownout.",
  "risk": "BTS7960/buck/push button tak terbukti di repo; foto fisik belum ada; "
          "Ackermann tak bisa rotate-in-place (min turning radius 0.90 m) -> goal "
          "sempit gagal; brownout inrush PG45 (dimitigasi PWM ramping).",
  "status": PG},

 {"id": "B", "title": "Sensor dan Persepsi Lingkungan", "subbab": "2.3",
  "requirement": "Robot membaca lingkungan (jarak, citra, gerak) sebagai masukan "
                 "mapping, costmap, odometry, dan localization.",
  "evidence": [
     ("RPLIDAR C1 -> /scan, frame laser_frame, baud 460800, ~10 Hz", f"{F['sensors']}", VF),
     ("Parameter scan nyata: range 0.15-16 m, ~720 titik", "data_lidar_*.txt (upload)", VL),
     ("RealSense D455 RGB+Depth 848x480x30, align_depth", f"{F['sensors']}", VF),
     ("IMU D455 accel+gyro -> /imu/data (imu_merger, slop 50 ms)", f"{F['imu']}", VF),
     ("LiDAR /scan = sumber utama costmap (depth_scan dimatikan di costmap)", f"{F['nav2']}", VF),
     ("RGB+Depth+Scan+IMU = input mapping/VIO RTAB-Map", f"{F['rmap_launch']}", VF),
     ("Encoder = sumber odometry", f"{F['odom']}", VF),
     ("depth_scan diproduksi depthimage_to_laserscan_node -> /depth_scan", f"{F['rloc_launch']}", VF),
  ],
  "dependency": "TF sensor benar (URDF); sinkronisasi RGB-D-Scan-IMU (approx 0.05 s).",
  "risk": "VIO drift pada area minim tekstur/cahaya tidak konsisten; depth_scan "
          "salah baca lantai (obstacle hantu) -> dimatikan di costmap; LiDAR 1 "
          "bidang horizontal -> obstacle sangat rendah/tinggi bisa terlewat.",
  "status": VF},

 {"id": "C", "title": "ROS 2 Middleware dan Arsitektur Software", "subbab": "2.4",
  "requirement": "ROS 2 menghubungkan seluruh subsistem secara modular (7 package) "
                 "via topic/service/action/TF.",
  "evidence": [
     ("amr_description (URDF/TF)", f"{F['urdf']}", VF),
     ("amr_controller (stm32_bridge, odometry, imu_merger)", f"{F['bridge']}", VF),
     ("amr_bringup (master launch + sensor + joy)", f"{F['full']}", VF),
     ("amr_3d_mapping (RTAB-Map mapping/localization, VIO)", f"{F['rmap']}", VF),
     ("amr_slam (Nav2 + SLAM Toolbox)", f"{F['nav2']}", VF),
     ("amr_visual_regression (fallback depth-regression + line segments)",
      "src/amr_visual_regression/", VF),
     ("amr_failover (arbiter cmd_vel)", f"{F['failover']}", VF),
     ("Env: ROS2 Humble, CycloneDDS, DOMAIN_ID 42", "SOP/launch", PG),
  ],
  "dependency": "colcon --symlink-install; urutan launch sensor->localization->Nav2.",
  "risk": "Konflik TF map->odom bila SLAM Toolbox & RTAB-Map jalan bersamaan "
          "(dicegah: gunakan salah satu).",
  "status": VF},

 {"id": "D", "title": "Model Robot, URDF/Xacro, dan TF Tree", "subbab": "2.5",
  "requirement": "Representasi geometris benar agar transform map->odom->base_link "
                 "->sensor konsisten untuk mapping, localization, navigation.",
  "evidence": [
     ("TF tree: base_footprint->base_link->{chassis,roda,steering,laser,camera}", f"{F['urdf']}", VF),
     ("laser_frame z=0.25; camera x=0.35 z=0.20; optical frame REP-103", f"{F['urdf']}", VF),
     ("Geometri wheelbase 0.5 / track 0.4 / wheel_radius 0.0775 / steer ±45", f"{F['urdf']}", VF),
     ("Diagram TF runtime (view_frames)", f"{F['frames']}", VL),
     ("robot_state_publisher load xacro", f"{F['full']}", VF),
  ],
  "dependency": "xacro ter-parse; static TF bridge ke frame RealSense.",
  "risk": "Diagram frames_*.pdf bertanggal 9 Jun (mungkin belum mencerminkan "
          "TF terbaru); TF salah -> mapping/localization/costmap meleset.",
  "status": VF},

 {"id": "E", "title": "Odometry dan Estimasi Gerak", "subbab": "2.6",
  "requirement": "Robot mengestimasi perubahan posisi (odometry) sebagai motion "
                 "prior untuk SLAM & Nav2.",
  "evidence": [
     ("odometry_publisher (bicycle model Ackermann), 50 Hz", f"{F['odom']}", VF),
     ("Rumus dist_per_tick=2*pi*r/PPR; theta+=(vx/L)tan(delta)dt", f"{F['odom']}", VF),
     ("PPR awal 1496 -> kalibrasi 3858; dist_per_tick 0.3255->0.1262 mm", f"{F['full']}", VF),
     ("Uji 5 jarak: real=0.3877*odom; R2=0.998; over-report 2.58x", f"{F['full']} (komentar) + data upload", VL),
     ("Data eksperimen odom CSV (442 baris + 8 run jalan_maju)", "upload (di luar repo)", VL),
     ("publish_tf kondisional (True hanya saat VIO mati)", f"{F['full']}", VF),
  ],
  "dependency": "Encoder /encoder valid; wheel_radius & PPR akurat.",
  "risk": "Sudut setir odometry dibaca dari /joy, bukan /cmd_vel -> saat autonomous "
          "murni yaw odom tak update (dikoreksi RTAB-Map); tanpa IMU eksternal "
          "yaw drift (dikoreksi scan-matching/loop closure).",
  "status": VF},

 {"id": "F", "title": "Mapping Lingkungan (RTAB-Map)", "subbab": "2.7",
  "requirement": "Robot membangun peta lingkungan (pose graph + occupancy grid) "
                 "yang valid sebagai basis localization & global costmap.",
  "evidence": [
     ("Config mapping: Reg/Strategy 2, LoopThr 0.05, MinInliers 8", f"{F['rmap']}", VF),
     ("Launch mapping (RGB-D+Scan+IMU sync, VIO)", f"{F['rmap_launch']}", VF),
     ("Peta acuan lab_demo_18jun.db: 448 pose, 125 global + 648 proximity LC, 28.9 m",
      "rtabmap-info (.db di ~/maps/ NUC, tidak di repo)", PG),
     ("Analisis agregat 24 DB (19 valid, 2 rusak, 3 kosong)", "laporan .docx BAB IV", PG),
     ("DB terpadat: mapping_20260611_MASTER.db (1526 node, 754 LC)", "laporan .docx", PG),
  ],
  "dependency": "Odometry/VIO stabil; sensor sinkron; loop closure cukup.",
  "risk": "File .db TIDAK ada di repo (di NUC) -> metrik perlu verifikasi ulang "
          "rtabmap-info; peta lama ghosting/near-static (sebagian tak layak bukti); "
          "screenshot rtabmap_viz/graph belum ada.",
  "status": PG},

 {"id": "G", "title": "Localization terhadap Peta", "subbab": "2.8",
  "requirement": "Robot menentukan posisinya terhadap peta acuan (lock) sebelum "
                 "menerima goal navigasi.",
  "evidence": [
     ("Config localization: Mem/IncrementalMemory=false, InitWMWithAllNodes=true", f"{F['rloc']}", VF),
     ("Launch localization (rtabmap mode localization + depth_to_scan)", f"{F['rloc_launch']}", VF),
     ("Ambang disamakan dgn mapping (LoopThr 0.05, MinInliers 8, DetectionRate 2.0)", f"{F['rloc']}", VF),
     ("Root cause loop rejection (ambang localization > mapping) + fix", f"{F['rca']}", VF),
     ("Bukti lock (loop closure hijau) 18 Jun", "handover/progress", PG),
     ("Topic /localization_pose", "tidak di-remap eksplisit (rtabmap default mode loc)", BT),
  ],
  "dependency": "Peta .db valid; TF benar; ambang localization = mapping.",
  "risk": "Bukti runtime lock belum lengkap (screenshot/log /localization_pose, "
          "RMSE vs ground truth belum ada); lock tipis bila layout berubah.",
  "status": PG},

 {"id": "H", "title": "Navigation2 Global Planner — Point-to-Point", "subbab": "2.9",
  "requirement": "Robot menerima goal dan menghitung lintasan global dari pose "
                 "saat ini menuju target (point-to-point), Ackermann-aware.",
  "evidence": [
     ("Planner SmacPlannerHybrid (DUBIN, min turning radius 0.90, reverse_penalty 2.0)", f"{F['nav2']}", VF),
     ("Global costmap (static+obstacle+inflation, res 0.05)", f"{F['nav2']}", VF),
     ("Action navigate_to_pose (server bt_navigator)", f"{F['nav2_launch']}", VF),
     ("goal_sender.py (klien NavigateToPose dari terminal)", f"{F['goal']}", VF),
     ("BT XML path absolut; lifecycle autostart", f"{F['nav2']}, {F['nav2_launch']}", VF),
     ("Bringup sukses (8 gerbang) -> lifecycle active", f"{F['rca']} + handover", PG),
     ("Bukti path runtime (screenshot global plan / log)", "belum ada", BT),
  ],
  "dependency": "Peta valid + localization lock + TF map->odom->base_link + lifecycle active.",
  "risk": "Bukti runtime path belum ada (screenshot RViz plan/log action); area "
          "sempit -> no valid path (radius putar 0.90 m).",
  "status": PG},

 {"id": "I", "title": "Navigation2 Local Planner — Obstacle Avoidant", "subbab": "2.10",
  "requirement": "Robot mengikuti lintasan global sambil menghasilkan /cmd_vel yang "
                 "menghindari rintangan dari costmap lokal.",
  "evidence": [
     ("Controller RegulatedPurePursuit (desired_linear_vel 0.3, use_rotate_to_heading false)", f"{F['nav2']}", VF),
     ("Local costmap 4x4 rolling: voxel_layer + inflation_layer", f"{F['nav2']}", VF),
     ("Obstacle source = LiDAR /scan; depth_scan DIMATIKAN di costmap", f"{F['nav2']}", VF),
     ("robot_radius 0.28; inflation_radius 0.25; cost_scaling 3.0", f"{F['nav2']}", VF),
     ("Output /cmd_vel (velocity_smoother max 0.3)", f"{F['nav2']}", VF),
     ("Fix obstacle hantu (matikan depth_scan, kecilkan radius)", f"{F['rca']}", VF),
     ("Bukti avoidance runtime (robot belok hindar obstacle)", "belum ada", BT),
  ],
  "dependency": "LiDAR /scan masuk costmap; controller server lifecycle active.",
  "risk": "Bukti runtime obstacle avoidance belum ada (video/log); depth_scan off "
          "-> obstacle sangat rendah/tinggi bisa terlewat (single-plane LiDAR).",
  "status": PG},

 {"id": "J", "title": "Eksekusi Perintah ke STM32 dan Aktuator", "subbab": "2.11",
  "requirement": "Hasil planner (/cmd_vel) diteruskan ke STM32 dan menjadi gerak "
                 "motor + servo kemudi.",
  "evidence": [
     ("stm32_bridge subscribe /cmd_vel -> serial V:{pwm},S:{sudut}", f"{F['bridge']}", VF),
     ("Baudrate 115200; konversi steer=-atan(L*w/v)", f"{F['bridge']}", VF),
     ("Gate autonomous_enabled (default false -> set true runtime)", f"{F['bridge']}", VF),
     ("Remap /cmd_vel->/cmd_vel_nav DIHAPUS (mode demo)", f"{F['nav2_launch']}", VF),
     ("Feedback encoder E:{delta} -> /encoder", f"{F['bridge']}", VF),
     ("PWM ramping (400/call) + watchdog 500 ms", f"{F['bridge']}", VF),
     ("Bukti aktuator bergerak saat goal (log /cmd_vel != 0)", "progress (19 Jun) / belum ada log", PG),
  ],
  "dependency": "Port serial terbuka; autonomous_enabled true; R1 tak ditekan.",
  "risk": "Masalah historis: remap salah & autonomous_enabled false -> robot diam "
          "(sudah diperbaiki); bukti log /cmd_vel saat goal belum dilampirkan.",
  "status": VF},

 {"id": "K", "title": "Safety, Failover, dan Manual Override", "subbab": "2.12",
  "requirement": "Sistem aman saat autonomous: e-stop, deadman, arbitrasi sumber gerak.",
  "evidence": [
     ("Failover state machine (SLAM/VISUAL/JOY/E-STOP)", f"{F['failover']}", VF),
     ("E-stop software: min /scan < 0.30 m -> cmd_vel (0,0)", f"{F['failover']}", VF),
     ("Deadman R1 (button 5); watchdog cmd_vel 500 ms", f"{F['bridge']}", VF),
     ("autonomous_enabled gate", f"{F['bridge']}", VF),
     ("PWM ramping anti-brownout", f"{F['bridge']}", VF),
     ("Mode demo: failover DIBYPASS (Nav2->/cmd_vel langsung)", f"{F['nav2_launch']}", VF),
     ("E-stop FISIK", "Tidak ditemukan di repo (perlu validasi)", BT),
  ],
  "dependency": "failover node aktif (mode lengkap); joystick terhubung.",
  "risk": "Mode demo tanpa failover = tanpa auto e-stop (R1 rem manual wajib); "
          "uji failover runtime belum terdokumentasi; e-stop fisik perlu validasi.",
  "status": VF},

 {"id": "L", "title": "Evidence, Testing, dan Gap Validasi", "subbab": "2.13",
  "requirement": "Klaim autonomous didukung bukti yang dapat diaudit; gap "
                 "dinyatakan jujur.",
  "evidence": [
     ("Konfigurasi sistem (semua YAML/launch/source)", "src/ (file-verified)", VF),
     ("Kalibrasi odometry numerik + R2=0.998", f"{F['full']} + data upload", VL),
     ("Diagram TF (frames_*.pdf)", f"{F['frames']}", VL),
     ("Rantai 8 gerbang Nav2 (kronologi debugging)", f"{F['rca']}", VF),
     ("Analisis 24 DB mapping", "laporan .docx + evidence package", PG),
     ("Screenshot RViz/rtabmap/Nav2, video navigasi, log runtime", "belum ada", BT),
  ],
  "dependency": "Sesi lab untuk merekam bukti runtime.",
  "risk": "Bukti runtime (lokalisasi, global path, obstacle avoidance, /cmd_vel "
          "saat goal, encoder feedback) belum dilampirkan -> gap utama laporan.",
  "status": PG},
]

# Subbab khusus (bukan bone): 2.1 target, 2.14 ringkasan
SUBBAB_EXTRA = {
    "2.1": "Penentuan Target Autonomous Navigation AMR",
    "2.14": "Project yang Terselesaikan",
}
SUBBAB_TITLE = {b["subbab"]: b["title"] for b in BONES}
SUBBAB_TITLE.update(SUBBAB_EXTRA)

# Kriteria keberhasilan
SUCCESS = [
    ("Mapping tersedia & valid", PG, "lab_demo_18jun.db (448 pose, 125+648 LC)",
     f"{F['rmap']}; .db di NUC", "Verifikasi ulang rtabmap-info + screenshot graph"),
    ("Localization lock terhadap peta", PG, "ambang disamakan; lock 18 Jun",
     f"{F['rloc']}; {F['rca']}", "Log /localization_pose / screenshot loop hijau"),
    ("Global planner menghasilkan path point-to-point", PG,
     "SmacPlannerHybrid + navigate_to_pose + goal_sender", f"{F['nav2']}; {F['goal']}",
     "Screenshot global plan / log action result"),
    ("Local planner command obstacle-avoidant", PG,
     "RegulatedPurePursuit + local costmap (scan)", f"{F['nav2']}",
     "Video/log robot menghindar obstacle"),
    ("Costmap menerima data obstacle", VF, "obstacle_layer/voxel_layer sumber /scan",
     f"{F['nav2']}", "Screenshot costmap dgn obstacle"),
    ("/cmd_vel muncul", PG, "controller -> /cmd_vel (remap dihapus)",
     f"{F['nav2_launch']}", "Log ros2 topic echo /cmd_vel saat goal"),
    ("STM32 menerima command", PG, "stm32_bridge subscribe /cmd_vel, gate enabled",
     f"{F['bridge']}", "Log serial / indikator motor"),
    ("Motor & servo bergerak sesuai perintah", PG, "robot bergerak otonom 19 Jun",
     f"{F['bridge']}", "Video robot bergerak ke goal"),
    ("Encoder feedback", VF, "E:{delta} -> /encoder -> /odom", f"{F['bridge']}; {F['odom']}",
     "Plot /encoder atau /odom saat gerak"),
    ("Safety siap", VF, "failover + deadman + e-stop software + ramping", f"{F['failover']}",
     "Uji runtime failover; konfirmasi e-stop fisik"),
]

GAP_CHECKLIST = [
    "Screenshot RViz /scan (LaserScan)",
    "Screenshot RealSense RGB-D (image + pointcloud)",
    "Screenshot RTAB-Map database (DatabaseViewer graph view)",
    "Output rtabmap-info lab_demo_18jun.db (verifikasi metrik)",
    "Screenshot/log localization pose (/localization_pose atau loop closure hijau)",
    "Screenshot Nav2 lifecycle active ('Managed nodes are active')",
    "Screenshot global path (RViz Path dari planner)",
    "Screenshot local costmap (dengan obstacle)",
    "Log /cmd_vel saat goal aktif (linear.x != 0)",
    "Video robot bergerak menuju goal (point-to-point)",
    "Bukti obstacle avoidance (robot belok menghindar)",
    "Bukti STM32 menerima command (log serial / motor bergerak)",
    "Bukti encoder feedback (plot /encoder atau /odom)",
    "Foto fisik robot + wiring + penempatan komponen",
    "Konfirmasi hardware: BTS7960, buck converter, push button/e-stop fisik",
]


def w(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)


def main():
    os.makedirs(OUT, exist_ok=True)
    today = date.today().isoformat()

    # ---- 1. README ----
    w("README.md",
      f"# Fishbone Analysis — Autonomous Navigation AMR\n\n_Generated: {today} "
      f"(read-only)_\n\n## Tujuan\nAnalisis sebab-akibat (Ishikawa/Fishbone) faktor "
      f"teknis yang mendukung **effect** utama:\n\n> {EFFECT}\n\n"
      "## Cara membaca\n"
      "- `fishbone_autonomous_navigation.md` — 12 bone (A-L) gaya systems-engineering "
      "(Requirement/Evidence/Dependency/Risk/Placement).\n"
      "- `fishbone_autonomous_navigation.mmd` — diagram Mermaid (flowchart LR).\n"
      "- `fishbone_bone_to_bab2_mapping.md` — peta bone -> subbab BAB II.\n"
      "- `bab2_restructured_outline_from_fishbone.md` — kerangka BAB II.\n"
      "- `bab2_subchapter_prompts.md` — prompt nulis tiap subbab.\n"
      "- `bab2_evidence_matrix.{md,csv}` — matriks bukti.\n"
      "- `autonomous_navigation_success_criteria.md` — kriteria sukses + status.\n"
      "- `gap_and_missing_evidence_checklist.md` — bukti yang masih kurang.\n"
      "- `fishbone_summary_for_report.md` — ringkasan siap tempel.\n\n"
      "## Legenda status\n"
      f"- **[VF]** {VF}\n- **[VL]** {VL}\n- **[PG]** {PG}\n- **[BT]** {BT}\n\n"
      "> Prinsip: tidak ada klaim 'autonomous penuh' tanpa bukti runtime. "
      "Gap ditandai eksplisit.\n")

    # ---- 2. Fishbone detail ----
    code = {VF: "[VF]", VL: "[VL]", PG: "[PG]", BT: "[BT]"}
    md = [f"# Fishbone Analysis — {EFFECT}", "",
          "Effect (kepala ikan): **" + EFFECT + "**", "",
          "Dianalisis melalui 12 tulang (bone). Tiap bone: Requirement -> "
          "Implementation evidence -> Dependency -> Risk/Gap -> Report placement.", ""]
    for b in BONES:
        md.append(f"\n## Bone {b['id']}. {b['title']}  ->  BAB II {b['subbab']}")
        md.append(f"\n**Requirement:** {b['requirement']}")
        md.append(f"\n**Status bone:** {code[b['status']]} {b['status']}")
        md.append("\n**Implementation evidence:**\n")
        md.append("| Faktor teknis | Sumber | Status |")
        md.append("|---|---|---|")
        for fac, src, st in b["evidence"]:
            md.append(f"| {fac} | `{src}` | {code[st]} |")
        md.append(f"\n**Dependency:** {b['dependency']}")
        md.append(f"\n**Risk/Gap:** {b['risk']}")
        md.append(f"\n**Report placement:** BAB II {b['subbab']} "
                  f"{SUBBAB_TITLE[b['subbab']]}")
    w("fishbone_autonomous_navigation.md", "\n".join(md) + "\n")

    # ---- 3. Mermaid ----
    mm = ["flowchart LR",
          f'    EFFECT["EFFECT: AMR otonom<br/>global planner point-to-point +<br/>'
          f'local planner obstacle-avoidant"]']
    for b in BONES:
        bid = b["id"]
        mm.append(f'    {bid}["Bone {bid}<br/>{b["title"]}"] --> EFFECT')
        # 2 faktor kunci + status
        for i, (fac, src, st) in enumerate(b["evidence"][:3]):
            fac_short = fac[:42].replace('"', "'")
            mm.append(f'    {bid}_{i}["{code[st]} {fac_short}"] --> {bid}')
    mm_text = "\n".join(mm)
    w("fishbone_autonomous_navigation.mmd", mm_text + "\n")
    # juga sertakan versi mindmap sebagai alternatif di file md kecil
    mind = ["mindmap", "  root((AMR Autonomous))"]
    for b in BONES:
        mind.append(f"    {b['id']}. {b['title']}")
        for fac, src, st in b["evidence"][:3]:
            mind.append(f"      {code[st]} {fac[:40]}")
    w("fishbone_mindmap_alt.mmd", "\n".join(mind) + "\n")

    # ---- 4. Bone -> BAB II mapping ----
    cols = ["bone", "subbab_bab2", "fokus_pembahasan", "data_bukti",
            "gambar_tabel_disarankan", "status_bukti"]
    rows = []
    gambar = {
        "A": "Foto robot, wiring; tabel spec hardware",
        "B": "Screenshot RViz /scan + pointcloud; tabel sensor",
        "C": "Diagram arsitektur package; tabel package",
        "D": "frames_*.pdf, RViz RobotModel; tabel geometri",
        "E": "Plot regresi R2; tabel jarak nyata vs odom",
        "F": "rtabmap_viz/graph view; tabel metrik DB",
        "G": "Screenshot loop closure hijau; tabel ambang map vs loc",
        "H": "Screenshot global plan; tabel param planner",
        "I": "Screenshot local costmap + path; tabel param controller",
        "J": "Log /cmd_vel; tabel protokol serial",
        "K": "Marker failover RViz; tabel state machine",
        "L": "Galeri bukti; checklist gap",
    }
    for b in BONES:
        rows.append({"bone": f"{b['id']}. {b['title']}", "subbab_bab2":
                     f"{b['subbab']} {SUBBAB_TITLE[b['subbab']]}",
                     "fokus_pembahasan": b["requirement"],
                     "data_bukti": "; ".join(f"{f}" for f, _, _ in b["evidence"][:4]),
                     "gambar_tabel_disarankan": gambar[b["id"]],
                     "status_bukti": b["status"]})
    w("fishbone_bone_to_bab2_mapping.md",
      "# Pemetaan Bone Fishbone -> Subbab BAB II\n\n" +
      _table(rows, cols) + "\n")

    # ---- 5. BAB II outline ----
    ol = ["# BAB II REALISASI PROJECT — Kerangka dari Fishbone", "",
          "Disusun mengikuti rantai sebab-akibat fishbone menuju autonomous "
          "navigation point-to-point + obstacle avoidance.", "",
          "## 2.1 Penentuan Target Autonomous Navigation AMR",
          f"Target akhir: {EFFECT}", ""]
    for b in BONES:
        ol.append(f"## 2.{b['subbab'].split('.')[1]} {b['title']}")
        ol.append(f"- Dari Bone {b['id']}. {b['requirement']}")
        ol.append(f"- Status bukti: {b['status']}")
        ol.append("")
    ol.append("## 2.14 Project yang Terselesaikan")
    ol.append("- Ringkasan capaian per bone + status kejujuran teknis (mana yang "
              "terbukti file, mana yang masih perlu bukti runtime).")
    w("bab2_restructured_outline_from_fishbone.md", "\n".join(ol) + "\n")

    # ---- 6. Subchapter prompts ----
    pr = ["# Prompt Penulisan per Subbab BAB II", "",
          "Salin prompt ke AI untuk menulis narasi tiap subbab. Lampirkan data dari "
          "evidence package & file sumber terkait.", "",
          "## 2.1 Penentuan Target Autonomous Navigation AMR",
          f"> Tulis subbab yang menetapkan target sistem: '{EFFECT}'. Jelaskan "
          "definisi global planner point-to-point & local planner obstacle-avoidant. "
          "Data: konsep AMR vs AGV. Hindari klaim hasil; ini penetapan target.", ""]
    for b in BONES:
        ev = "; ".join(f for f, _, _ in b["evidence"][:5])
        bukti_kuat = "; ".join(f for f, _, st in b["evidence"] if st in (VF, VL))[:300]
        pr.append(f"## 2.{b['subbab'].split('.')[1]} {b['title']}")
        pr.append(f"> **Tujuan:** jelaskan {b['requirement']}\n>\n"
                  f"> **Data yang dimasukkan:** {ev}\n>\n"
                  f"> **Bukti yang disebut (kuat):** {bukti_kuat}\n>\n"
                  f"> **Gambar/tabel:** {gambar[b['id']]}\n>\n"
                  f"> **Hindari klaim:** {b['risk'][:200]}\n>\n"
                  f"> **Catatan:** tandai bukti runtime yang belum ada sebagai gap.")
        pr.append("")
    pr.append("## 2.14 Project yang Terselesaikan")
    pr.append("> Ringkas capaian per bone dengan status jujur (terbukti file vs "
              "perlu bukti runtime). Hindari klaim 'autonomous penuh' tanpa video/log.")
    w("bab2_subchapter_prompts.md", "\n".join(pr) + "\n")

    # ---- 7. Evidence matrix ----
    mcols = ["subbab_bab2", "bone", "data_teknis", "file_sumber",
             "bukti_tersedia", "bukti_belum_tersedia", "status_validasi", "catatan"]
    mrows = []
    for b in BONES:
        tersedia = "; ".join(f for f, _, st in b["evidence"] if st in (VF, VL))
        belum = "; ".join(f for f, _, st in b["evidence"] if st == BT)
        src = "; ".join(sorted(set(s for _, s, _ in b["evidence"]
                                   if s.startswith("src") or s.endswith(".md")
                                   or s.endswith(".pdf")))[:4])
        mrows.append({"subbab_bab2": f"2.{b['subbab'].split('.')[1]} {b['title']}",
                      "bone": b["id"], "data_teknis": b["requirement"],
                      "file_sumber": src or "(lihat detail bone)",
                      "bukti_tersedia": tersedia[:400] or "-",
                      "bukti_belum_tersedia": belum[:300] or "-",
                      "status_validasi": b["status"],
                      "catatan": b["risk"][:160]})
    with open(os.path.join(OUT, "bab2_evidence_matrix.csv"), "w", encoding="utf-8",
              newline="") as f:
        wr = csv.DictWriter(f, fieldnames=mcols)
        wr.writeheader()
        wr.writerows(mrows)
    w("bab2_evidence_matrix.md", "# Matriks Bukti BAB II (dari Fishbone)\n\n" +
      _table(mrows, mcols) + "\n")

    # ---- 8. Success criteria ----
    sc = ["# Kriteria Keberhasilan Autonomous Navigation", "",
          f"Effect: {EFFECT}", "",
          "| Kriteria | Status | Bukti | Sumber file | Gap |",
          "|---|---|---|---|---|"]
    for crit, st, bukti, src, gap in SUCCESS:
        sc.append(f"| {crit} | {st} | {bukti} | `{src}` | {gap} |")
    sc.append("\n> Kesimpulan: fondasi (config, hardware, kalibrasi, sensor) "
              "**terverifikasi dari file**. Rantai autonomous end-to-end "
              "(localization lock -> global path -> obstacle avoidance -> /cmd_vel "
              "-> aktuator) berstatus **catatan progress**; perlu bukti runtime "
              "untuk klaim final.")
    w("autonomous_navigation_success_criteria.md", "\n".join(sc) + "\n")

    # ---- 9. Gap checklist ----
    gc = ["# Gap & Missing Evidence Checklist", "",
          "Bukti yang HARUS ditambahkan manual (di luar ekstraksi repo):", ""]
    for item in GAP_CHECKLIST:
        gc.append(f"- [ ] {item}")
    gc.append("\n## Prioritas untuk klaim autonomous\n"
              "1. Log /cmd_vel saat goal + video robot bergerak (Bone H,I,J).\n"
              "2. Screenshot loop closure hijau / log localization (Bone G).\n"
              "3. Screenshot global plan + local costmap (Bone H,I).\n"
              "4. rtabmap-info DB acuan (Bone F).")
    w("gap_and_missing_evidence_checklist.md", "\n".join(gc) + "\n")

    # ---- 10. Summary for report ----
    n_vf = sum(1 for b in BONES if b["status"] == VF)
    n_pg = sum(1 for b in BONES if b["status"] == PG)
    w("fishbone_summary_for_report.md",
      "# Ringkasan Fishbone untuk Laporan\n\n"
      "BAB II Realisasi Project disusun menggunakan **Fishbone (Ishikawa) Analysis** "
      f"terhadap effect utama: _{EFFECT}_\n\n"
      "Analisis memecah sistem menjadi **12 tulang (bone)** yang saling bergantung: "
      "(A) platform hardware & aktuator, (B) sensor & persepsi, (C) arsitektur ROS 2, "
      "(D) model robot & TF, (E) odometry, (F) mapping RTAB-Map, (G) localization, "
      "(H) global planner point-to-point, (I) local planner obstacle-avoidant, "
      "(J) eksekusi STM32, (K) safety/failover, (L) bukti & gap.\n\n"
      "Setiap bone menjadi satu subbab BAB II (2.2-2.13), diapit penetapan target "
      "(2.1) dan ringkasan capaian (2.14). Pendekatan ini menampilkan hubungan "
      "**sebab-akibat**: hardware->sensor->ROS2->TF->odometry->mapping->localization "
      "menjadi prasyarat global & local planner, yang keluarannya (/cmd_vel) "
      "dieksekusi STM32 di bawah pengawasan safety.\n\n"
      f"Dari 12 bone, **{n_vf} bone terverifikasi dari file** (config/hardware/sensor/"
      f"odometry/eksekusi/safety) dan **{n_pg} bone berstatus catatan progress** "
      "(mapping, localization, global/local planner, bukti) yang **masih memerlukan "
      "bukti runtime** (screenshot/log/video). Penyajian ini menjaga kejujuran "
      "teknis: capaian yang terbukti dinyatakan tegas, sedangkan rantai autonomous "
      "end-to-end ditandai sebagai gap yang harus dilengkapi.\n")

    # ---- ZIP ----
    files = sorted(os.listdir(OUT))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in files:
            z.write(os.path.join(OUT, fn),
                    arcname=os.path.join("fishbone_autonomous_navigation_analysis", fn))

    print("=" * 60)
    print("FISHBONE ANALYSIS — SELESAI")
    print("=" * 60)
    print(f"Folder: docs/generated/fishbone_autonomous_navigation_analysis")
    print(f"ZIP   : docs/generated/fishbone_autonomous_navigation_analysis.zip")
    print(f"Bone  : {len(BONES)} | Subbab BAB II: 2.1-2.14")
    print(f"Status bone: {n_vf} [VF], {n_pg} [PG]")
    print("-" * 60)
    for fn in files:
        print(f"  {fn}")
    print("=" * 60)


def _table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        cells = []
        for c in cols:
            v = str(r.get(c, "")).replace("\n", " ").replace("|", "\\|")
            cells.append(v)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    main()
