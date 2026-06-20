#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_evidence_package.py  (READ-ONLY)
=======================================================================
Generator paket data raw / bukti teknis proyek AMR.
Memindai repo (read-only) + data terverifikasi, lalu menulis:
  docs/generated/raw_amr_evidence_package/*.{md,csv,json}
dan mengemasnya menjadi .zip.

PRINSIP:
  - Tidak mengarang data.
  - status_validasi:
      "Terverifikasi dari file"  -> ada di source code repo
      "Data eksperimen (upload)" -> ada di file upload user (bukan repo)
      "Catatan/progress"         -> dari log pengerjaan; perlu validasi sumber
      "Tidak ditemukan di repo"  -> tidak ada artefaknya saat ini
  - Tidak mengubah source code utama (hanya menulis ke docs/generated/).
=======================================================================
"""
import csv
import json
import os
import zipfile
from datetime import date

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTDIR = os.path.join(REPO, "docs", "generated", "raw_amr_evidence_package")
ZIPPATH = os.path.join(REPO, "docs", "generated", "raw_amr_evidence_package.zip")

V_FILE = "Terverifikasi dari file"
V_EXP = "Data eksperimen (upload, di luar repo)"
V_NOTE = "Catatan/progress (perlu validasi sumber)"
V_NONE = "Tidak ditemukan di repo/file saat ini"


def rel(p):
    return os.path.relpath(p, REPO)


def exists(relpath):
    return os.path.isfile(os.path.join(REPO, relpath))


# =====================================================================
# WRITER HELPERS
# =====================================================================
def write_json(name, obj):
    with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_csv(name, rows, fieldnames):
    with open(os.path.join(OUTDIR, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(name, text):
    with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as f:
        f.write(text)


def md_table(rows, columns, headers=None):
    headers = headers or columns
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        cells = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, (list, tuple)):
                v = "; ".join(str(x) for x in v)
            v = str(v).replace("\n", " ").replace("|", "\\|")
            cells.append(v)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def emit(prefix, title, intro, rows, columns, headers=None, extra_md=""):
    """Tulis trio .md/.csv/.json untuk satu kategori record-based."""
    md = [f"# {title}", "", intro, ""]
    md.append(md_table(rows, columns, headers))
    if extra_md:
        md.append("\n" + extra_md)
    write_md(f"{prefix}.md", "\n".join(md) + "\n")
    write_csv(f"{prefix}.csv", rows, columns)
    write_json(f"{prefix}.json", rows)


# =====================================================================
# DATA — sumber bukti file (untuk kolom "bukti")
# =====================================================================
F = {
    "urdf": "src/amr_description/urdf/amr_description.urdf.xacro",
    "macros": "src/amr_description/urdf/amr_macros.xacro",
    "bridge": "src/amr_controller/src/stm32_bridge.cpp",
    "odom": "src/amr_controller/scripts/odometry_publisher.py",
    "imu": "src/amr_controller/scripts/imu_merger_node.py",
    "full": "src/amr_bringup/launch/amr_full.launch.py",
    "sensors": "src/amr_bringup/launch/sensors_launch.py",
    "joy": "src/amr_bringup/config/joy_params.yaml",
    "rtab_map": "src/amr_3d_mapping/config/rtabmap_mapping.yaml",
    "rtab_loc": "src/amr_3d_mapping/config/rtabmap_localization.yaml",
    "nav2": "src/amr_slam/config/nav2_params.yaml",
    "nav2_launch": "src/amr_slam/launch/nav2.launch.py",
    "slam_map": "src/amr_slam/config/slam_mapping.yaml",
    "failover": "src/amr_failover/amr_failover/failover_controller.py",
    "vr_inf": "src/amr_visual_regression/amr_visual_regression/vr_inference_node.py",
    "vr_line": "src/amr_visual_regression/amr_visual_regression/lidar_line_segments_node.py",
}

# Data eksperimen di folder upload user (bukan repo)
UPLOAD_DIR = "/root/.claude/uploads/1c5c71b5-862a-5513-8e43-27a9bf37e720"
UPLOAD_FILES = {
    "euler_csv": "data_euler_odom.csv (442 baris; t,V_target,V_smooth,V_euler,galat)",
    "lidar_1m": "data_lidar_1meter.txt (LaserScan mentah 1 m)",
    "lidar_halangan": "data_lidar_halangan.txt",
    "lidar_mentah": "data_lidar_mentah.txt",
    "jalan_maju_zip": "jalan_maju.zip (8 CSV odom uji jarak 2026-06-14)",
    "odom_docx": "Hasil_Test_ODOMETRI_VS_REALTIME.docx",
}


# =====================================================================
# A. IDENTITAS PROYEK
# =====================================================================
def build_identity():
    obj = {
        "nama_proyek": "Autonomous Mobile Robot (AMR) 4WD Ackermann Indoor",
        "deskripsi": "Robot bergerak otonom 4WD kemudi Ackermann untuk indoor, "
                     "berbasis ROS 2 Humble; mapping & localization RTAB-Map, "
                     "navigasi Navigation2, kendali via STM32 serial.",
        "jenis_robot": "Mobile robot 4WD, kemudi Ackermann (2 roda depan)",
        "lingkungan_pengujian": "Indoor / laboratorium (E105 ITS)",
        "target_utama": "Robot bergerak otonom dari goal Nav2 di atas peta indoor",
        "tim": [
            {"nama": "Mararevi Subagyo", "nrp": "2040241036",
             "peran": "Integrasi sistem, dokumentasi, analisis DB, Nav2, lokalisasi"},
            {"nama": "Muhammad Al Azhar Faradis", "nrp": "2040241017",
             "peran": "ROS2, RTAB-Map, Nav2, kalibrasi odometry, debugging"},
            {"nama": "Anwar Rifa'i", "nrp": "2040241021",
             "peran": "Hardware, wiring, STM32, aktuator, pengujian"},
        ],
        "status_capaian": {
            "platform_4wd_ackermann": "Tercapai",
            "integrasi_ros2": "Tercapai",
            "integrasi_sensor": "Tercapai (LiDAR C1 + RealSense D455)",
            "kalibrasi_odometry": "Tercapai (PPR 3858, R2=0.998)",
            "mapping_rtabmap": "Tercapai (lab_demo_18jun.db)",
            "localization": "Tercapai; bukti runtime perlu dilengkapi",
            "navigasi_nav2": "Tercapai mode demo; bukti runtime perlu dilengkapi",
            "failover": "Diimplementasi; dibypass saat demo",
        },
        "sumber": V_NOTE + " (identitas tim & status dari laporan .docx + progress; "
                  "spec hardware terverifikasi dari URDF/launch)",
    }
    write_json("00_project_identity.json", obj)
    md = [f"# 00 — Identitas Proyek AMR", ""]
    md.append(f"- **Nama:** {obj['nama_proyek']}")
    md.append(f"- **Deskripsi:** {obj['deskripsi']}")
    md.append(f"- **Jenis robot:** {obj['jenis_robot']}")
    md.append(f"- **Lingkungan:** {obj['lingkungan_pengujian']}")
    md.append(f"- **Target utama:** {obj['target_utama']}")
    md.append("\n## Tim")
    for m in obj["tim"]:
        md.append(f"- **{m['nama']}** ({m['nrp']}): {m['peran']}")
    md.append("\n## Status Capaian Umum")
    for k, v in obj["status_capaian"].items():
        md.append(f"- {k}: **{v}**")
    md.append(f"\n> Catatan sumber: {obj['sumber']}")
    write_md("00_project_identity.md", "\n".join(md) + "\n")


# =====================================================================
# B. HARDWARE INVENTORY
# =====================================================================
def build_hardware():
    cols = ["komponen", "jenis", "fungsi", "data", "topic", "package_node",
            "bukti", "status"]
    rows = [
        {"komponen": "Intel NUC 13 i7 (NUC13ANHi7)", "jenis": "Komputer onboard",
         "fungsi": "Pusat komputasi perception/mapping/navigation/ROS2",
         "data": "Menjalankan seluruh node ROS2", "topic": "-",
         "package_node": "semua", "bukti": F["full"], "status": V_NOTE},
        {"komponen": "STM32F407", "jenis": "Mikrokontroler",
         "fungsi": "Kendali motor + servo, baca encoder, jembatan serial",
         "data": "TX V:{pwm},S:{sudut}; RX E:{delta}", "topic": "/encoder, /cmd_vel, /joy",
         "package_node": "amr_controller/stm32_bridge",
         "bukti": F["bridge"], "status": V_FILE},
        {"komponen": "RPLIDAR C1", "jenis": "Sensor LiDAR 2D 360",
         "fungsi": "Scan jarak planar, obstacle, costmap, scan-matching",
         "data": "LaserScan (~720 titik, ~10 Hz)", "topic": "/scan",
         "package_node": "rplidar_ros/rplidar_node",
         "bukti": F["sensors"], "status": V_FILE},
        {"komponen": "Intel RealSense D455", "jenis": "Kamera RGB-D + IMU",
         "fungsi": "RGB+Depth untuk RTAB-Map/VIO; IMU gravity",
         "data": "RGB 848x480x30, Depth 848x480x30, accel+gyro",
         "topic": "/camera/camera/color/*, /aligned_depth_to_color/*, /accel,/gyro",
         "package_node": "realsense2_camera", "bukti": F["sensors"], "status": V_FILE},
        {"komponen": "IMU (BMI055 internal D455)", "jenis": "IMU 6-DoF",
         "fungsi": "Gravity constraint + prediksi gerak VIO",
         "data": "accel + gyro", "topic": "/camera/camera/accel/sample, /gyro/sample -> /imu/data",
         "package_node": "amr_controller/imu_merger", "bukti": F["imu"], "status": V_FILE},
        {"komponen": "Accelerometer (BMI055)", "jenis": "Bagian IMU",
         "fungsi": "Linear acceleration untuk fusi", "data": "linear_acceleration",
         "topic": "/camera/camera/accel/sample", "package_node": "amr_controller/imu_merger",
         "bukti": F["imu"], "status": V_FILE},
        {"komponen": "Gyroscope (BMI055)", "jenis": "Bagian IMU",
         "fungsi": "Angular velocity (vyaw) untuk fusi", "data": "angular_velocity",
         "topic": "/camera/camera/gyro/sample", "package_node": "amr_controller/imu_merger",
         "bukti": F["imu"], "status": V_FILE},
        {"komponen": "Encoder (pada PG45)", "jenis": "Rotary encoder",
         "fungsi": "Umpan balik gerak untuk odometry",
         "data": "delta ticks (PPR efektif 3858)", "topic": "/encoder",
         "package_node": "amr_controller/odometry_publisher", "bukti": F["odom"], "status": V_FILE},
        {"komponen": "Motor PG45", "jenis": "DC gear motor + encoder",
         "fungsi": "Penggerak 4WD (1 motor + 2 diferensial + shaft)",
         "data": "PWM dari STM32", "topic": "via /cmd_vel -> bridge",
         "package_node": "amr_controller/stm32_bridge", "bukti": F["urdf"], "status": V_FILE},
        {"komponen": "Driver motor BTS7960", "jenis": "H-bridge driver",
         "fungsi": "Antarmuka daya STM32 ke motor",
         "data": "PWM + arah", "topic": "-", "package_node": "STM32 (firmware)",
         "bukti": "-", "status": V_NOTE + " (disebut di rancangan; tak ada di repo)"},
        {"komponen": "Servo kemudi DSSERVO D25", "jenis": "Servo",
         "fungsi": "Kemudi Ackermann 2 roda depan (±45)",
         "data": "sudut S dari STM32", "topic": "via /cmd_vel -> bridge",
         "package_node": "amr_controller/stm32_bridge", "bukti": F["bridge"], "status": V_FILE},
        {"komponen": "Baterai LiPo Ovonic 5300 mAh 6S", "jenis": "Catu daya",
         "fungsi": "Suplai NUC/STM32/motor/sensor (jaga >22 V)",
         "data": "tegangan", "topic": "-", "package_node": "-",
         "bukti": "-", "status": V_NOTE + " (dari laporan/progress)"},
        {"komponen": "Buck converter", "jenis": "Konverter tegangan",
         "fungsi": "Step-down tegangan ke subsistem", "data": "-", "topic": "-",
         "package_node": "-", "bukti": "-", "status": V_NONE},
        {"komponen": "Power management module", "jenis": "Manajemen daya",
         "fungsi": "Distribusi daya", "data": "-", "topic": "-",
         "package_node": "-", "bukti": "-", "status": V_NONE},
        {"komponen": "Emergency stop", "jenis": "Keselamatan",
         "fungsi": "Hentikan robot darurat",
         "data": "-", "topic": "(software: EMERGENCY_STOP state)",
         "package_node": "amr_failover", "bukti": F["failover"],
         "status": V_NOTE + " (e-stop SOFTWARE ada; e-stop FISIK perlu validasi)"},
        {"komponen": "Push button", "jenis": "Input keselamatan",
         "fungsi": "PERLU_KONFIRMASI", "data": "-", "topic": "-",
         "package_node": "-", "bukti": "-", "status": V_NONE},
        {"komponen": "Joystick PS4/PS5", "jenis": "Kontroler manual",
         "fungsi": "Teleop manual + deadman R1",
         "data": "axes + buttons", "topic": "/joy",
         "package_node": "joy_node + stm32_bridge", "bukti": F["joy"], "status": V_FILE},
        {"komponen": "GNSS/GPS U-Blox", "jenis": "Posisi global",
         "fungsi": "DICOPOT (indoor only)", "data": "-", "topic": "-",
         "package_node": "-", "bukti": F["sensors"],
         "status": V_FILE + " (dinyatakan dicopot di sensors_launch.py)"},
    ]
    emit("01_hardware_inventory", "01 — Inventaris Hardware AMR",
         "Daftar komponen hardware. Status menandai apakah terverifikasi dari "
         "file repo atau hanya dari catatan/rancangan.", rows, cols)


# =====================================================================
# C. SENSOR RAW DATA
# =====================================================================
def build_sensors():
    cols = ["sensor", "prinsip", "output", "topic", "frame_id", "rate",
            "resolusi", "param", "node_pembaca", "dipakai_untuk", "bukti", "status"]
    rows = [
        {"sensor": "RPLIDAR C1", "prinsip": "ToF laser scan 360 planar",
         "output": "sensor_msgs/LaserScan", "topic": "/scan", "frame_id": "laser_frame",
         "rate": "~10 Hz (scan_time 0.1001 s)",
         "resolusi": "angle_increment 0.008714 rad (~720 titik)",
         "param": "baud 460800, scan_mode Standard, range 0.15-16.0 m",
         "node_pembaca": "rtabmap, nav2 costmap, slam_toolbox, failover",
         "dipakai_untuk": "mapping, costmap, scan-matching, e-stop",
         "bukti": F["sensors"] + " + " + UPLOAD_FILES["lidar_1m"], "status": V_FILE},
        {"sensor": "RealSense D455 RGB", "prinsip": "Kamera warna",
         "output": "sensor_msgs/Image", "topic": "/camera/camera/color/image_raw",
         "frame_id": "camera_color_optical_frame", "rate": "30 fps",
         "resolusi": "848x480", "param": "gain 64, exposure 156, auto_exposure",
         "node_pembaca": "rgbd_sync", "dipakai_untuk": "mapping, loop closure (BoW)",
         "bukti": F["sensors"], "status": V_FILE},
        {"sensor": "RealSense D455 Depth", "prinsip": "Stereo depth",
         "output": "sensor_msgs/Image", "topic": "/camera/camera/aligned_depth_to_color/image_raw",
         "frame_id": "camera_depth_optical_frame", "rate": "30 fps", "resolusi": "848x480",
         "param": "align_depth=true, temporal+spatial filter on, decimation off",
         "node_pembaca": "rgbd_sync, vr_inference", "dipakai_untuk": "mapping 3D, depth regression",
         "bukti": F["sensors"], "status": V_FILE},
        {"sensor": "RealSense D455 IMU", "prinsip": "MEMS IMU (BMI055)",
         "output": "sensor_msgs/Imu (accel+gyro)",
         "topic": "/camera/camera/accel/sample, /gyro/sample -> /imu/data",
         "frame_id": "camera_gyro_optical_frame", "rate": "accel ~100 Hz, gyro ~200 Hz",
         "resolusi": "-", "param": "unite_imu_method=2, sync slop 50 ms",
         "node_pembaca": "imu_merger, rgbd_odometry", "dipakai_untuk": "VIO, gravity constraint",
         "bukti": F["imu"], "status": V_FILE},
        {"sensor": "Encoder PG45", "prinsip": "Rotary increment",
         "output": "std_msgs/Int32 (delta ticks)", "topic": "/encoder",
         "frame_id": "-", "rate": "via bridge read loop",
         "resolusi": "PPR efektif 3858; dist_per_tick 0.1262 mm",
         "param": "auto-detect cumulative/delta", "node_pembaca": "odometry_publisher",
         "dipakai_untuk": "odometry", "bukti": F["odom"], "status": V_FILE},
    ]
    emit("02_sensor_raw_data", "02 — Data Raw Sensor",
         "Sensor dan keterkaitannya dengan pipeline. Parameter LiDAR (range, "
         "angle_increment) terverifikasi dari data scan eksperimen.", rows, cols)


# =====================================================================
# D. ROS2 PACKAGE INVENTORY
# =====================================================================
def build_packages():
    cols = ["package", "fungsi", "node_file", "launch", "config", "publish",
            "subscribe", "service_action", "relasi", "bukti", "status"]
    rows = [
        {"package": "amr_description", "fungsi": "Model URDF/Xacro + TF",
         "node_file": "robot_state_publisher", "launch": "view_robot.launch.py",
         "config": "urdf/*.xacro", "publish": "/robot_description, /tf_static",
         "subscribe": "-", "service_action": "-", "relasi": "dipakai amr_bringup",
         "bukti": F["urdf"], "status": V_FILE},
        {"package": "amr_controller", "fungsi": "Bridge HW + odometry + IMU merge",
         "node_file": "stm32_bridge.cpp, odometry_publisher.py, imu_merger_node.py",
         "launch": "(via amr_launch.py)", "config": "-",
         "publish": "/encoder, /odom, /imu/data, /tf", "subscribe": "/cmd_vel, /joy",
         "service_action": "-", "relasi": "input ke RTAB-Map/Nav2", "bukti": F["bridge"],
         "status": V_FILE},
        {"package": "amr_bringup", "fungsi": "Orkestrasi launch + sensor + joy",
         "node_file": "joy_node, teleop", "launch": "amr_full/sensors/amr_launch.py",
         "config": "joy_params.yaml", "publish": "/scan, /camera/*, /joy",
         "subscribe": "-", "service_action": "-", "relasi": "master launch semua",
         "bukti": F["full"], "status": V_FILE},
        {"package": "amr_3d_mapping", "fungsi": "SLAM 3D RTAB-Map + VIO",
         "node_file": "rtabmap, rgbd_odometry, rgbd_sync",
         "launch": "rtabmap_mapping/localization/vio_only.launch.py",
         "config": "rtabmap_mapping.yaml, rtabmap_localization.yaml",
         "publish": "/map, /cloud_map, /tf(map->odom)",
         "subscribe": "/rgbd_image, /scan, /imu/data",
         "service_action": "rtabmap services", "relasi": "peta untuk Nav2",
         "bukti": F["rtab_map"], "status": V_FILE},
        {"package": "amr_slam", "fungsi": "SLAM Toolbox 2D + Nav2 config",
         "node_file": "slam_toolbox, nav2 lifecycle nodes",
         "launch": "nav2.launch.py, slam_mapping/localization.launch.py",
         "config": "nav2_params.yaml, slam_mapping.yaml",
         "publish": "/cmd_vel, /plan, /global_costmap, /local_costmap",
         "subscribe": "/scan, /odom, /map", "service_action": "/navigate_to_pose (action)",
         "relasi": "konsumen peta RTAB-Map", "bukti": F["nav2"], "status": V_FILE},
        {"package": "amr_visual_regression", "fungsi": "Fallback depth-regression + line segments",
         "node_file": "vr_inference, data_collector, lidar_line_segments, feature_extractor",
         "launch": "vr_inference/line_segments/collect_dataset.launch.py",
         "config": "model .pkl (offline)", "publish": "/cmd_vel_visual, /amr/line_segments",
         "subscribe": "/camera/depth/*, /scan", "service_action": "-",
         "relasi": "sumber VISUAL_FALLBACK failover", "bukti": F["vr_inf"], "status": V_FILE},
        {"package": "amr_failover", "fungsi": "Arbiter cmd_vel (state machine)",
         "node_file": "failover_controller.py", "launch": "failover.launch.py",
         "config": "param node", "publish": "/cmd_vel, /failover_status, /failover_marker",
         "subscribe": "/cmd_vel_nav, /cmd_vel_visual, /cmd_vel_joy, /scan, /map, /joy",
         "service_action": "-", "relasi": "arbiter semua sumber gerak", "bukti": F["failover"],
         "status": V_FILE},
    ]
    emit("03_ros2_package_inventory", "03 — Inventaris Package ROS 2",
         "Tujuh package ROS 2 dan tanggung jawabnya.", rows, cols)


# =====================================================================
# E. ROS2 INTERFACE (topic/node/service/action/TF)
# =====================================================================
def build_interfaces():
    cols = ["nama", "jenis", "message_type", "publisher", "subscriber",
            "fungsi", "package", "bukti", "status"]
    rows = [
        {"nama": "/scan", "jenis": "topic", "message_type": "sensor_msgs/LaserScan",
         "publisher": "rplidar_node", "subscriber": "rtabmap, nav2, slam_toolbox, failover",
         "fungsi": "Laser scan 2D", "package": "amr_bringup", "bukti": F["sensors"], "status": V_FILE},
        {"nama": "/cmd_vel", "jenis": "topic", "message_type": "geometry_msgs/Twist",
         "publisher": "failover / nav2 (mode demo)", "subscriber": "stm32_bridge",
         "fungsi": "Perintah kecepatan ke aktuator", "package": "amr_controller",
         "bukti": F["bridge"], "status": V_FILE},
        {"nama": "/cmd_vel_nav", "jenis": "topic", "message_type": "geometry_msgs/Twist",
         "publisher": "nav2 controller", "subscriber": "failover",
         "fungsi": "cmd_vel dari Nav2 (input arbiter)", "package": "amr_failover",
         "bukti": F["failover"], "status": V_FILE},
        {"nama": "/cmd_vel_visual", "jenis": "topic", "message_type": "geometry_msgs/Twist",
         "publisher": "vr_inference", "subscriber": "failover",
         "fungsi": "cmd_vel dari visual regression", "package": "amr_failover",
         "bukti": F["failover"], "status": V_FILE},
        {"nama": "/cmd_vel_joy", "jenis": "topic", "message_type": "geometry_msgs/Twist",
         "publisher": "teleop_twist_joy", "subscriber": "failover",
         "fungsi": "cmd_vel dari joystick", "package": "amr_failover",
         "bukti": F["failover"], "status": V_FILE},
        {"nama": "/odom", "jenis": "topic", "message_type": "nav_msgs/Odometry",
         "publisher": "odometry_publisher / rgbd_odometry", "subscriber": "nav2, rtabmap",
         "fungsi": "Odometry pose+twist (50 Hz)", "package": "amr_controller",
         "bukti": F["odom"], "status": V_FILE},
        {"nama": "/encoder", "jenis": "topic", "message_type": "std_msgs/Int32",
         "publisher": "stm32_bridge", "subscriber": "odometry_publisher",
         "fungsi": "Encoder delta ticks", "package": "amr_controller", "bukti": F["bridge"],
         "status": V_FILE},
        {"nama": "/joy", "jenis": "topic", "message_type": "sensor_msgs/Joy",
         "publisher": "joy_node", "subscriber": "stm32_bridge, odometry_publisher, failover",
         "fungsi": "Input joystick (deadman R1=btn5)", "package": "amr_bringup",
         "bukti": F["joy"], "status": V_FILE},
        {"nama": "/imu/data", "jenis": "topic", "message_type": "sensor_msgs/Imu",
         "publisher": "imu_merger", "subscriber": "rgbd_odometry",
         "fungsi": "IMU gabungan accel+gyro", "package": "amr_controller", "bukti": F["imu"],
         "status": V_FILE},
        {"nama": "/rgbd_image", "jenis": "topic", "message_type": "rtabmap_msgs/RGBDImage",
         "publisher": "rgbd_sync", "subscriber": "rtabmap, rgbd_odometry",
         "fungsi": "RGB+Depth tersinkron", "package": "amr_3d_mapping", "bukti": F["rtab_map"],
         "status": V_FILE},
        {"nama": "/map", "jenis": "topic", "message_type": "nav_msgs/OccupancyGrid",
         "publisher": "rtabmap / slam_toolbox", "subscriber": "nav2 static_layer, failover",
         "fungsi": "Occupancy grid 2D", "package": "amr_3d_mapping", "bukti": F["rtab_map"],
         "status": V_FILE},
        {"nama": "/cloud_map", "jenis": "topic", "message_type": "sensor_msgs/PointCloud2",
         "publisher": "rtabmap", "subscriber": "RViz/Foxglove", "fungsi": "Point cloud 3D",
         "package": "amr_3d_mapping", "bukti": F["rtab_map"], "status": V_FILE},
        {"nama": "/depth_scan", "jenis": "topic", "message_type": "sensor_msgs/LaserScan",
         "publisher": "(depthimage_to_laserscan?)", "subscriber": "nav2 costmap (DIMATIKAN)",
         "fungsi": "Laserscan dari depth (dinonaktifkan di costmap)", "package": "amr_slam",
         "bukti": F["nav2"], "status": V_NOTE + " (node penghasil perlu validasi)"},
        {"nama": "/amr/line_segments", "jenis": "topic", "message_type": "visualization_msgs/MarkerArray",
         "publisher": "lidar_line_segments_node", "subscriber": "RViz/Foxglove",
         "fungsi": "Segmen garis dinding (RANSAC)", "package": "amr_visual_regression",
         "bukti": F["vr_line"], "status": V_FILE},
        {"nama": "/failover_status", "jenis": "topic", "message_type": "std_msgs/String",
         "publisher": "failover_controller", "subscriber": "monitor",
         "fungsi": "Status state machine (JSON)", "package": "amr_failover", "bukti": F["failover"],
         "status": V_FILE},
        {"nama": "/navigate_to_pose", "jenis": "action", "message_type": "nav2_msgs/action/NavigateToPose",
         "publisher": "bt_navigator (server)", "subscriber": "klien goal",
         "fungsi": "Aksi navigasi ke goal", "package": "amr_slam", "bukti": F["nav2_launch"],
         "status": V_FILE},
        {"nama": "/slam_toolbox/save_map", "jenis": "service", "message_type": "slam_toolbox/srv/SaveMap",
         "publisher": "slam_toolbox", "subscriber": "-", "fungsi": "Simpan peta 2D",
         "package": "amr_slam", "bukti": F["slam_map"], "status": V_FILE},
        {"nama": "/localization_pose", "jenis": "topic", "message_type": "geometry_msgs/PoseWithCovarianceStamped",
         "publisher": "(rtabmap localization)", "subscriber": "-",
         "fungsi": "Pose hasil lokalisasi", "package": "amr_3d_mapping", "bukti": "-",
         "status": V_NONE + " (tidak dikonfigurasi eksplisit; perlu validasi)"},
        # TF frames
        {"nama": "map", "jenis": "TF frame", "message_type": "tf2", "publisher": "rtabmap/slam_toolbox",
         "subscriber": "nav2", "fungsi": "Frame global peta", "package": "amr_3d_mapping",
         "bukti": F["rtab_map"], "status": V_FILE},
        {"nama": "odom", "jenis": "TF frame", "message_type": "tf2",
         "publisher": "rgbd_odometry / odometry_publisher", "subscriber": "nav2",
         "fungsi": "Frame odometry", "package": "amr_controller", "bukti": F["odom"], "status": V_FILE},
        {"nama": "base_footprint -> base_link", "jenis": "TF transform", "message_type": "tf2",
         "publisher": "robot_state_publisher", "subscriber": "semua",
         "fungsi": "Naik z=wheel_radius", "package": "amr_description", "bukti": F["urdf"],
         "status": V_FILE},
        {"nama": "base_link -> laser_frame", "jenis": "TF transform", "message_type": "tf2",
         "publisher": "robot_state_publisher", "subscriber": "rtabmap/nav2",
         "fungsi": "LiDAR z=0.25 m", "package": "amr_description", "bukti": F["urdf"], "status": V_FILE},
        {"nama": "base_link -> camera_link", "jenis": "TF transform", "message_type": "tf2",
         "publisher": "robot_state_publisher", "subscriber": "rtabmap",
         "fungsi": "Kamera x=0.35, z=0.20 m", "package": "amr_description", "bukti": F["urdf"],
         "status": V_FILE},
    ]
    extra = ("\n## Catatan TF Tree lengkap\n\n"
             "`map -> odom -> base_footprint -> base_link -> {chassis, 4 roda, "
             "2 steering_link, laser_frame, camera_link -> {color/depth_optical_frame}}`\n\n"
             "Diagram TF tersedia di repo: `frames_2026-06-09_22.08.25.pdf` dan "
             "`frames_2026-06-09_22.09.38.pdf` (output view_frames).")
    emit("04_ros2_interface_inventory", "04 — Inventaris Interface ROS 2",
         "Topic, node, service, action, dan TF frame yang teridentifikasi dari "
         "source/launch. Item tanpa bukti file ditandai status.", rows, cols, extra_md=extra)


# =====================================================================
# F. URDF / ROBOT MODEL
# =====================================================================
def build_urdf():
    cols = ["parameter", "nilai", "satuan", "bukti", "status"]
    rows = [
        {"parameter": "wheelbase", "nilai": "0.500", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "track_width", "nilai": "0.400", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "wheel_radius", "nilai": "0.0775", "satuan": "m (D=155mm)", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "wheel_width", "nilai": "0.060", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "chassis (LxWxH)", "nilai": "0.600 x 0.350 x 0.150", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "chassis_mass", "nilai": "6.0", "satuan": "kg", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "steering_range", "nilai": "±45", "satuan": "deg", "bukti": F["bridge"], "status": V_FILE},
        {"parameter": "min_turning_radius", "nilai": "0.90 (Nav2); 0.5-0.9 (rancangan)", "satuan": "m", "bukti": F["nav2"], "status": V_FILE},
        {"parameter": "lidar_height (z)", "nilai": "0.250", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "camera_x", "nilai": "0.350", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
        {"parameter": "camera_height (z)", "nilai": "0.200", "satuan": "m", "bukti": F["urdf"], "status": V_FILE},
    ]
    links = ["base_footprint", "base_link", "chassis", "rear_left_wheel", "rear_right_wheel",
             "front_left_steering_link", "front_left_wheel", "front_right_steering_link",
             "front_right_wheel", "laser_frame", "camera_link", "color_optical_frame",
             "depth_optical_frame"]
    joints = ["base_footprint_joint (fixed)", "chassis_joint (fixed)",
              "rear_*_wheel_joint (continuous Y)", "front_*_steering_joint (revolute Z)",
              "front_*_wheel_joint (continuous Y)", "laser_joint (fixed)",
              "camera_joint (fixed)", "color/depth_optical_joint (fixed, REP-103)"]
    extra = ("\n## Link\n- " + "\n- ".join(links) +
             "\n\n## Joint\n- " + "\n- ".join(joints))
    emit("05_robot_model_urdf_xacro", "05 — Model Robot (URDF/Xacro)",
         "Parameter geometri & struktur link/joint, terverifikasi dari URDF.",
         rows, cols, extra_md=extra)


# =====================================================================
# G. STM32 SERIAL
# =====================================================================
def build_stm32():
    cols = ["item", "nilai", "bukti", "status"]
    rows = [
        {"item": "Port serial", "nilai": "/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_206833894152-if00", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Baudrate", "nilai": "115200 (B115200)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Format TX (NUC->STM32)", "nilai": "V:{pwm},S:{sudut}\\n", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Format RX (STM32->NUC)", "nilai": "E:{delta}\\n", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Perintah motor (PWM)", "nilai": "MAX_PWM=4000; negatif=mundur", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Perintah servo", "nilai": "MAX_STEER=45 deg; STEER_TRIM=-5", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Data encoder", "nilai": "E:{delta} -> /encoder (Int32); auto-detect cumulative/delta", "bukti": F["bridge"], "status": V_FILE},
        {"item": "PWM ramping", "nilai": "MAX_PWM_STEP=400/call; e-stop bypass", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Safety gate", "nilai": "autonomous_enabled (default false)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Deadman", "nilai": "R1 (button index 5); manual override", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Watchdog", "nilai": "cmd_vel timeout 500 ms -> motor stop", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Konversi Ackermann", "nilai": "steer = -atan(WHEELBASE*w/v) (negasi fix 20-Jun)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Konvensi arah", "nilai": "V positif=maju (kabel motor ditukar fisik)", "bukti": F["bridge"], "status": V_FILE},
    ]
    emit("06_stm32_serial_communication", "06 — Komunikasi Serial ROS2 <-> STM32",
         "Protokol & parameter bridge, terverifikasi dari stm32_bridge.cpp.", rows, cols)


# =====================================================================
# H. ODOMETRY & KALIBRASI
# =====================================================================
def build_odometry():
    cols = ["percobaan", "jarak_aktual_cm", "jarak_odom_m", "odom_cm",
            "rasio_real_per_odom", "catatan"]
    odom_m = [0.5, 1.0, 1.5, 2.0, 2.5]
    real_cm = [22, 41, 61, 81, 96]
    rows = []
    for i, (o, r) in enumerate(zip(odom_m, real_cm), 1):
        rows.append({"percobaan": i, "jarak_aktual_cm": r, "jarak_odom_m": o,
                     "odom_cm": int(o * 100),
                     "rasio_real_per_odom": round(r / (o * 100), 4),
                     "catatan": "uji odom-vs-meteran 14-Jun"})
    extra = (
        "\n## Parameter & Hasil Kalibrasi (terverifikasi dari amr_full.launch.py)\n\n"
        "| Item | Nilai |\n|---|---|\n"
        "| Sumber odometry | Encoder PG45 (model bicycle Ackermann) |\n"
        "| Wheel radius | 0.0775 m |\n"
        "| Wheelbase | 0.500 m |\n"
        "| PPR awal (teoretis) | 1496 |\n"
        "| PPR hasil kalibrasi | 3858 |\n"
        "| dist_per_tick | 0.3255 -> 0.1262 mm |\n"
        "| Faktor over-report | 2.58x |\n"
        "| Fit regresi | real = 0.3877 x odom (proporsional) |\n"
        "| R^2 | 0.998 |\n\n"
        "## Rumus\n"
        "- dist_per_tick = 2*pi*wheel_radius / PPR\n"
        "- vx = delta_dist / dt\n"
        "- delta_theta = (vx / wheelbase) * tan(steering) * dt\n"
        "- x += delta_dist*cos(theta+dtheta/2); y += delta_dist*sin(theta+dtheta/2)\n\n"
        "## Kesimpulan\n"
        "Odometry awal over-report 2.58x; setelah koreksi PPR ke 3858, pembacaan "
        "konsisten terhadap jarak nyata (R^2=0.998). Mendukung kompetensi Metode "
        "Numerik (regresi least-squares).\n\n"
        "## Data eksperimen tambahan (upload, di luar repo)\n"
        f"- {UPLOAD_FILES['euler_csv']} -> analisis prediksi Euler vs /odom aktual\n"
        f"- {UPLOAD_FILES['jalan_maju_zip']}\n"
        f"- {UPLOAD_FILES['odom_docx']}\n"
        f"- Lokasi: `{UPLOAD_DIR}` (status: {V_EXP})\n"
    )
    emit("07_odometry_calibration", "07 — Odometry & Kalibrasi",
         "Data uji 5 jarak (odom vs meteran) + parameter & hasil regresi.",
         rows, cols, extra_md=extra)


# =====================================================================
# I. RTABMAP DATABASE
# =====================================================================
def build_rtabmap_db():
    cols = ["nama_db", "path", "status", "nodes", "keyframe", "link",
            "loop_closure", "durasi", "jarak_m", "bbox_m2", "catatan", "sumber"]
    # Database TIDAK ada di repo; data dari analisis .docx (laporan) + rtabmap-info
    rows = [
        {"nama_db": "lab_demo_18jun.db", "path": "~/maps/ (NUC, tidak di repo)",
         "status": "valid (peta acuan demo)", "nodes": 1846, "keyframe": 448,
         "link": 447 + 125 + 648, "loop_closure": "125 global + 648 proximity",
         "durasi": "1012 s (~17 min)", "jarak_m": 28.9, "bbox_m2": "-",
         "catatan": "PETA ACUAN; bersih, single session; layak bukti utama",
         "sumber": V_NOTE + " (rtabmap-info; .db di NUC)"},
        {"nama_db": "mapping_20260611_MASTER.db", "path": "~/maps/ (NUC)",
         "status": "valid (terpadat agregat)", "nodes": 1526, "keyframe": "-",
         "link": 987, "loop_closure": 754, "durasi": "-", "jarak_m": "-", "bbox_m2": "-",
         "catatan": "Peta terpadat dari analisis 24 DB; layak bukti", "sumber": V_NOTE},
        {"nama_db": "lab_vio_1620.db", "path": "~/maps/ (NUC)", "status": "valid (eksploratif)",
         "nodes": 758, "keyframe": 316, "link": 760, "loop_closure": 130,
         "durasi": "13m23s", "jarak_m": 43.511, "bbox_m2": 45.706,
         "catatan": "Lintasan terpanjang; LC relatif sedikit", "sumber": V_NOTE},
        {"nama_db": "lab_remap3_220017.db", "path": "~/maps/ (NUC)", "status": "valid",
         "nodes": "-", "keyframe": "-", "link": "tertinggi", "loop_closure": "tertinggi",
         "durasi": "-", "jarak_m": "-", "bbox_m2": 27.3,
         "catatan": "Link & LC tertinggi; eksplorasi agresif", "sumber": V_NOTE},
        {"nama_db": "test.db", "path": "~/maps/ (NUC)", "status": "valid (near-static)",
         "nodes": "-", "keyframe": "-", "link": 683, "loop_closure": 682,
         "durasi": "-", "jarak_m": 0.236, "bbox_m2": 0.0,
         "catatan": "Near-static (LC/link ~1.0); BUKAN bukti utama", "sumber": V_NOTE},
        {"nama_db": "lab_final_malam_ini.db", "path": "~/maps/ (NUC)", "status": "valid (near-static)",
         "nodes": "-", "keyframe": "-", "link": 215, "loop_closure": 215,
         "durasi": "-", "jarak_m": 0.167, "bbox_m2": "-",
         "catatan": "Near-static; bukan bukti utama", "sumber": V_NOTE},
        {"nama_db": "lab_remap3_212606.db", "path": "~/maps/ (NUC)", "status": "valid (anomali)",
         "nodes": 884, "keyframe": "-", "link": "-", "loop_closure": "-",
         "durasi": "-", "jarak_m": 1.941, "bbox_m2": 0.005,
         "catatan": "Anomali: banyak node gerak minim", "sumber": V_NOTE},
    ]
    emit("08_rtabmap_database_inventory", "08 — Inventaris Database RTAB-Map",
         "PENTING: file .db berada di `~/maps/` pada NUC, TIDAK ada di repo. "
         "Angka di bawah dari analisis laporan (.docx) + rtabmap-info. Untuk "
         "verifikasi ulang, jalankan `rtabmap-info <db>` di NUC.", rows, cols)

    # Summary
    summary_cols = ["metrik", "nilai", "sumber"]
    srows = [
        {"metrik": "Total file .db ditemukan", "nilai": 24, "sumber": V_NOTE},
        {"metrik": "Total terbaca", "nilai": 22, "sumber": V_NOTE},
        {"metrik": "Total rusak/malformed", "nilai": 2, "sumber": V_NOTE},
        {"metrik": "Total kosong", "nilai": 3, "sumber": V_NOTE},
        {"metrik": "Total valid", "nilai": 19, "sumber": V_NOTE},
        {"metrik": "Total mentah node", "nilai": 16317, "sumber": V_NOTE},
        {"metrik": "Total mentah keyframe", "nilai": 2500, "sumber": V_NOTE},
        {"metrik": "Total mentah link", "nilai": 11500, "sumber": V_NOTE},
        {"metrik": "Total mentah loop closure", "nilai": 7675, "sumber": V_NOTE},
        {"metrik": "Total dedup node", "nilai": 11739, "sumber": V_NOTE},
        {"metrik": "Total dedup keyframe", "nilai": 1798, "sumber": V_NOTE},
        {"metrik": "Total dedup link", "nilai": 8539, "sumber": V_NOTE},
        {"metrik": "Total dedup loop closure", "nilai": 5413, "sumber": V_NOTE},
        {"metrik": "Database terbaik (agregat)", "nilai": "mapping_20260611_MASTER.db", "sumber": V_NOTE},
        {"metrik": "Database peta acuan (demo)", "nilai": "lab_demo_18jun.db", "sumber": V_NOTE},
        {"metrik": "DB tidak layak bukti utama", "nilai": "test.db, lab_final_malam_ini.db, lab_remap3_223920.db (near-static)", "sumber": V_NOTE},
    ]
    write_csv("08_rtabmap_database_summary.csv", srows, summary_cols)
    write_json("08_rtabmap_database_summary.json", srows)
    write_md("08_rtabmap_database_summary.md",
             "# 08 — Ringkasan Database RTAB-Map\n\n"
             "Sumber: analisis agregat pada laporan .docx (BAB IV). File .db di NUC.\n\n"
             + md_table(srows, summary_cols) + "\n")


# =====================================================================
# J. LOCALIZATION
# =====================================================================
def build_localization():
    cols = ["aspek", "nilai", "kategori", "bukti", "status"]
    rows = [
        {"aspek": "Launch localization", "nilai": "rtabmap_localization.launch.py",
         "kategori": "terverifikasi", "bukti": "src/amr_3d_mapping/launch/rtabmap_localization.launch.py", "status": V_FILE},
        {"aspek": "Config localization", "nilai": "rtabmap_localization.yaml",
         "kategori": "terverifikasi", "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "Database dipakai", "nilai": "lab_demo_18jun.db", "kategori": "progress",
         "bukti": "SOP/handover", "status": V_NOTE},
        {"aspek": "Mode", "nilai": "Mem/IncrementalMemory=false; InitWMWithAllNodes=true",
         "kategori": "terverifikasi", "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "LoopThr", "nilai": "0.05 (disamakan dgn mapping)", "kategori": "terverifikasi",
         "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "Vis/MinInliers", "nilai": "8", "kategori": "terverifikasi", "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "DetectionRate", "nilai": "2.0 Hz", "kategori": "terverifikasi", "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "Masalah: loop rejection", "nilai": "config localization lebih ketat dari mapping",
         "kategori": "progress", "bukti": "docs/root_cause_analysis_nav_lokalisasi.md", "status": V_FILE},
        {"aspek": "Solusi", "nilai": "samakan ambang localization = mapping", "kategori": "terverifikasi",
         "bukti": F["rtab_loc"], "status": V_FILE},
        {"aspek": "Topic /localization_pose", "nilai": "tidak dikonfigurasi eksplisit",
         "kategori": "kurang", "bukti": "-", "status": V_NONE},
        {"aspek": "Bukti keberhasilan", "nilai": "loop closure hijau (handover 18-Jun)",
         "kategori": "progress", "bukti": "handover", "status": V_NOTE},
        {"aspek": "Bukti yang kurang", "nilai": "screenshot/log /localization_pose, RMSE vs ground truth",
         "kategori": "kurang", "bukti": "-", "status": V_NONE},
    ]
    emit("09_localization_evidence", "09 — Bukti Localization",
         "Dipisah: terverifikasi (config) vs progress (handover) vs kurang "
         "(bukti runtime). Tabel ambang mapping vs localization ada di file 11/08.",
         rows, cols)


# =====================================================================
# K. NAVIGATION2
# =====================================================================
def build_nav2():
    cols = ["aspek", "nilai", "bukti", "status"]
    rows = [
        {"aspek": "Config", "nilai": "nav2_params.yaml", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Launch", "nilai": "nav2.launch.py (remap dihapus, mode demo)", "bukti": F["nav2_launch"], "status": V_FILE},
        {"aspek": "Planner", "nilai": "nav2_smac_planner/SmacPlannerHybrid (DUBIN)", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "min_turning_radius", "nilai": "0.90 m; reverse_penalty 2.0", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Controller", "nilai": "RegulatedPurePursuitController (desired_linear_vel 0.3)", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Global costmap", "nilai": "static + obstacle + inflation; obs scan saja", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Local costmap", "nilai": "4x4 rolling; voxel + inflation", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Inflation layer", "nilai": "inflation_radius 0.25; cost_scaling 3.0", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Voxel/Obstacle layer", "nilai": "nav2_costmap_2d::{Voxel,Obstacle}Layer", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "robot_radius", "nilai": "0.28 (dari 0.35)", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "depth_scan di costmap", "nilai": "DIMATIKAN (obstacle hantu lantai)", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Behavior tree XML", "nilai": "path absolut navigate_to_pose_w_replanning_and_recovery.xml", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Recovery behaviors", "nilai": "spin, backup, drive_on_heading, wait", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Smoother", "nilai": "nav2_smoother::SimpleSmoother", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Format plugin", "nilai": ":: (costmap/controller/smoother/waypoint), / (smac/behaviors)", "bukti": F["nav2"], "status": V_FILE},
        {"aspek": "Topic cmd_vel", "nilai": "/cmd_vel (remap dihapus, mode demo)", "bukti": F["nav2_launch"], "status": V_FILE},
        {"aspek": "Action", "nilai": "/navigate_to_pose (nav2_msgs/NavigateToPose)", "bukti": F["nav2_launch"], "status": V_FILE},
        {"aspek": "Status pengujian", "nilai": "Robot bergerak otonom (mode demo, 19-Jun)", "bukti": "handover", "status": V_NOTE},
        {"aspek": "Bukti runtime tersedia", "nilai": "log error 8 gerbang (progress)", "bukti": "docs/root_cause_analysis_nav_lokalisasi.md", "status": V_FILE},
        {"aspek": "Bukti runtime kurang", "nilai": "video navigasi, log /cmd_vel saat goal, screenshot RViz path", "bukti": "-", "status": V_NONE},
    ]
    emit("10_nav2_configuration_and_evidence", "10 — Konfigurasi & Bukti Navigation2",
         "Konfigurasi terverifikasi dari nav2_params.yaml. Rantai 8 gerbang ada "
         "di file 14. Bukti runtime navigasi masih perlu dilengkapi.", rows, cols)


# =====================================================================
# L. ACKERMANN
# =====================================================================
def build_ackermann():
    cols = ["item", "nilai", "bukti", "status"]
    rows = [
        {"item": "Wheelbase", "nilai": "0.500 m", "bukti": F["urdf"], "status": V_FILE},
        {"item": "Track width", "nilai": "0.400 m", "bukti": F["urdf"], "status": V_FILE},
        {"item": "Wheel radius", "nilai": "0.0775 m", "bukti": F["urdf"], "status": V_FILE},
        {"item": "Steering limit", "nilai": "±45 deg (STEER_TRIM -5)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Min turning radius", "nilai": "0.90 m (Nav2)", "bukti": F["nav2"], "status": V_FILE},
        {"item": "Konversi Twist->steer", "nilai": "steer = -atan(wheelbase*angular.z/linear.x)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Hubungan v & w", "nilai": "delta = atan(L*w/v); v dari linear.x, w dari angular.z", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Masalah arah kemudi", "nilai": "angular.z kiri -> roda belok kanan (kebalik)", "bukti": "bench test 20-Jun", "status": V_NOTE},
        {"item": "Solusi negasi", "nilai": "steer_rad = -atan(...) (commit fec1ee5)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Keterbatasan Nav2", "nilai": "tak bisa rotate-in-place (use_rotate_to_heading=false); butuh ruang manuver", "bukti": F["nav2"], "status": V_FILE},
    ]
    emit("11_ackermann_steering_data", "11 — Data Ackermann Steering",
         "Parameter & rumus kemudi Ackermann, terverifikasi dari URDF & bridge.",
         rows, cols)


# =====================================================================
# M. SAFETY / FAILOVER
# =====================================================================
def build_safety():
    cols = ["item", "nilai", "bukti", "status"]
    rows = [
        {"item": "Joystick", "nilai": "PS4/PS5; axis_linear=1, axis_angular=3", "bukti": F["joy"], "status": V_FILE},
        {"item": "Deadman button", "nilai": "R1 (index 5); wajib untuk gerak manual", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Emergency stop (software)", "nilai": "min /scan < 0.30 m -> cmd_vel (0,0)", "bukti": F["failover"], "status": V_FILE},
        {"item": "Emergency stop (fisik)", "nilai": "PERLU_KONFIRMASI", "bukti": "-", "status": V_NONE},
        {"item": "autonomous_enabled", "nilai": "default false; set true runtime (gerbang ke-8)", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Failover states", "nilai": "SLAM_ACTIVE / VISUAL_FALLBACK / JOY_OVERRIDE / EMERGENCY_STOP", "bukti": F["failover"], "status": V_FILE},
        {"item": "Trigger fallback", "nilai": "SLAM unhealthy >=2s -> VISUAL; recovery 5s histeresis", "bukti": F["failover"], "status": V_FILE},
        {"item": "Sumber gerak", "nilai": "Nav2(/cmd_vel_nav), VR(/cmd_vel_visual), joy(/cmd_vel_joy), e-stop(0)", "bukti": F["failover"], "status": V_FILE},
        {"item": "PWM ramping", "nilai": "MAX_PWM_STEP=400/call; e-stop bypass", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Brownout issue", "nilai": "inrush PG45 -> NUC voltage sag (SSH freeze, RealSense timeout)", "bukti": "progress 15-Jun", "status": V_NOTE},
        {"item": "Watchdog", "nilai": "cmd_vel timeout 500 ms -> stop", "bukti": F["bridge"], "status": V_FILE},
        {"item": "Status failover saat demo", "nilai": "DIBYPASS (Nav2 -> /cmd_vel langsung); R1 rem manual", "bukti": F["nav2_launch"], "status": V_FILE},
    ]
    emit("12_safety_failover_manual_control", "12 — Safety, Failover & Manual Control",
         "Mekanisme keselamatan & arbitrasi, terverifikasi dari failover & bridge.",
         rows, cols)


# =====================================================================
# N. VISUAL REGRESSION
# =====================================================================
def build_vr():
    cols = ["item", "nilai", "bukti", "status"]
    rows = [
        {"item": "Pendekatan", "nilai": "RandomForestRegressor (scikit-learn), tanpa CNN", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "Pipeline", "nilai": "data_collector -> train.py (offline) -> vr_inference", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "Input", "nilai": "depth image ROI (top 200, bottom 360), num_regions=9", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "Statistik depth", "nilai": "fitur per region (modul feature_extractor)", "bukti": "src/amr_visual_regression/amr_visual_regression/feature_extractor.py", "status": V_FILE},
        {"item": "Output", "nilai": "/cmd_vel_visual (linear.x + angular.z)", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "Safety", "nilai": "min_depth < 0.4 m -> velocity=0", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "Param gerak", "nilai": "vx_max 0.4; steer_max 0.785 rad", "bukti": F["vr_inf"], "status": V_FILE},
        {"item": "LiDAR line segments", "nilai": "Split-and-Merge + RANSAC; /amr/line_segments", "bukti": F["vr_line"], "status": V_FILE},
        {"item": "Alasan line segments", "nilai": "kritik dosen: dinding = entitas utuh, bukan titik diskrit", "bukti": F["vr_line"], "status": V_FILE},
        {"item": "Hubungan failover", "nilai": "sumber state VISUAL_FALLBACK", "bukti": F["failover"], "status": V_FILE},
        {"item": "Status implementasi", "nilai": "Node ada; model .pkl perlu training; runtime perlu validasi", "bukti": F["vr_inf"], "status": V_NOTE},
    ]
    emit("13_visual_regression_fallback", "13 — Visual Regression / Fallback",
         "Path B fallback berbasis regresi depth + line segments LiDAR.", rows, cols)


# =====================================================================
# O. ISSUES & SOLUTIONS
# =====================================================================
def build_issues():
    cols = ["kategori", "kendala", "gejala", "penyebab", "dampak", "solusi",
            "status_akhir", "bukti", "tindak_lanjut"]
    rows = [
        {"kategori": "Power", "kendala": "Brownout saat motor start",
         "gejala": "SSH freeze, RealSense timeout", "penyebab": "inrush PG45 -> voltage sag NUC",
         "dampak": "sistem freeze saat akselerasi", "solusi": "PWM ramping (400/call), e-stop bypass",
         "status_akhir": "Selesai", "bukti": F["bridge"], "tindak_lanjut": "tidak"},
        {"kategori": "Odometry", "kendala": "Over-report 2.58x",
         "gejala": "jarak odom > nyata", "penyebab": "PPR teoretis salah",
         "dampak": "estimasi posisi meleset", "solusi": "kalibrasi PPR -> 3858 (R2=0.998)",
         "status_akhir": "Selesai", "bukti": F["full"], "tindak_lanjut": "tidak"},
        {"kategori": "Sensor/VIO", "kendala": "VIO drift area minim tekstur",
         "gejala": "3D cloud ghosting", "penyebab": "pencahayaan & low-texture",
         "dampak": "peta menjalar", "solusi": "tuning exposure, re-mapping bersih, gravity constraint",
         "status_akhir": "Mitigasi", "bukti": F["sensors"], "tindak_lanjut": "ya (lighting)"},
        {"kategori": "Mapping", "kendala": "Database kacau (duplikat/korup/near-static)",
         "gejala": "24 DB, 2 rusak, 3 kosong, banyak duplikat", "penyebab": "sesi terputus + backup manual",
         "dampak": "agregat membengkak", "solusi": "re-mapping bersih lab_demo_18jun.db; SOP penamaan",
         "status_akhir": "Selesai", "bukti": "docs/SOP_MAPPING_DAN_AUTONOMOUS.md", "tindak_lanjut": "tidak"},
        {"kategori": "Localization", "kendala": "Loop rejection",
         "gejala": "robot tak lock ke peta", "penyebab": "ambang localization > mapping",
         "dampak": "lokalisasi gagal", "solusi": "samakan ambang (LoopThr 0.05, MinInliers 8, dst)",
         "status_akhir": "Selesai", "bukti": F["rtab_loc"], "tindak_lanjut": "ya (bukti runtime)"},
        {"kategori": "Nav2/plugin", "kendala": "VoxelLayer does not exist",
         "gejala": "plugin gagal load", "penyebab": "format :: vs / campur",
         "dampak": "bringup gagal", "solusi": "seragamkan format per package",
         "status_akhir": "Selesai", "bukti": F["nav2"], "tindak_lanjut": "tidak"},
        {"kategori": "Nav2/BT", "kendala": "RemovePassedGoals already registered",
         "gejala": "crash startup", "penyebab": "plugin_lib_names eksplisit -> registrasi ganda",
         "dampak": "Nav2 crash", "solusi": "hapus blok plugin_lib_names (auto-load)",
         "status_akhir": "Selesai", "bukti": F["nav2"], "tindak_lanjut": "tidak"},
        {"kategori": "Nav2/BT", "kendala": "Action server spin not available",
         "gejala": "BT gagal", "penyebab": "spin tak terdaftar", "dampak": "navigasi gagal",
         "solusi": "daftarkan nav2_behaviors/Spin", "status_akhir": "Selesai", "bukti": F["nav2"], "tindak_lanjut": "tidak"},
        {"kategori": "Nav2/BT", "kendala": "Couldn't open input XML file",
         "gejala": "bt_navigator crash", "penyebab": "path BT XML bukan absolut",
         "dampak": "navigasi gagal", "solusi": "path absolut BT XML", "status_akhir": "Selesai",
         "bukti": F["nav2"], "tindak_lanjut": "tidak"},
        {"kategori": "Nav2/costmap", "kendala": "collision ahead / lethal",
         "gejala": "planner no path", "penyebab": "depth_scan baca lantai = obstacle hantu",
         "dampak": "robot tak bisa jalan", "solusi": "matikan depth_scan; radius 0.28; inflation 0.25",
         "status_akhir": "Selesai", "bukti": F["nav2"], "tindak_lanjut": "ya (kalibrasi depth)"},
        {"kategori": "Nav2/topic", "kendala": "Nav2 kirim cmd_vel tapi diam",
         "gejala": "Failed to make progress", "penyebab": "remap /cmd_vel->/cmd_vel_nav",
         "dampak": "robot diam", "solusi": "hapus remap (mode demo)", "status_akhir": "Selesai",
         "bukti": F["nav2_launch"], "tindak_lanjut": "ya (failover)"},
        {"kategori": "Safety gate", "kendala": "Robot diam walau cmd_vel!=0",
         "gejala": "tak gerak", "penyebab": "autonomous_enabled default false",
         "dampak": "demo terblok", "solusi": "set true runtime", "status_akhir": "Selesai (runtime)",
         "bukti": F["bridge"], "tindak_lanjut": "tidak"},
        {"kategori": "Steering", "kendala": "Arah kemudi otonom terbalik",
         "gejala": "kiri -> kanan", "penyebab": "tanda kemudi terbalik (bench test)",
         "dampak": "navigasi salah arah", "solusi": "negasi steer_rad", "status_akhir": "Diterapkan; verifikasi HW",
         "bukti": F["bridge"], "tindak_lanjut": "ya (tes di robot)"},
        {"kategori": "Dokumentasi", "kendala": "Progress tak tercatat di laporan",
         "gejala": "laporan ketinggalan", "penyebab": "iterasi cepat",
         "dampak": "klaim kurang bukti", "solusi": "suplemen + bank data + evidence package",
         "status_akhir": "Selesai", "bukti": "docs/", "tindak_lanjut": "ya (bukti runtime)"},
    ]
    emit("14_issues_and_solutions", "14 — Kendala & Solusi",
         "Daftar kendala lintas subsistem (hardware s/d dokumentasi), termasuk "
         "rantai 8 gerbang Nav2.", rows, cols)


# =====================================================================
# P. REPORT EVIDENCE MATRIX
# =====================================================================
def build_matrix():
    cols = ["subbab", "data_pendukung", "bentuk_bukti", "file_sumber",
            "status_bukti", "tabel_disarankan", "gambar_disarankan", "catatan"]
    rows = [
        {"subbab": "2.1 Konsep AMR", "data_pendukung": "identitas proyek, target",
         "bentuk_bukti": "narasi + spec", "file_sumber": "00_project_identity",
         "status_bukti": "Kuat", "tabel_disarankan": "perbandingan AMR vs AGV",
         "gambar_disarankan": "konsep robot", "catatan": "definisi & cakupan"},
        {"subbab": "2.2 Perancangan Hardware", "data_pendukung": "inventaris hardware",
         "bentuk_bukti": "tabel komponen", "file_sumber": "01_hardware_inventory",
         "status_bukti": "Kuat (sebagian perlu konfirmasi)", "tabel_disarankan": "spec komponen",
         "gambar_disarankan": "foto komponen, wiring", "catatan": "BTS7960/buck perlu validasi"},
        {"subbab": "2.3 Perakitan Platform", "data_pendukung": "geometri, penempatan sensor",
         "bentuk_bukti": "foto + dimensi", "file_sumber": "05_robot_model_urdf_xacro",
         "status_bukti": "Sedang", "tabel_disarankan": "posisi sensor",
         "gambar_disarankan": "foto robot terakit", "catatan": "FOTO perlu ditambah"},
        {"subbab": "2.4 Setup ROS2", "data_pendukung": "env, workspace, deps",
         "bentuk_bukti": "daftar + screenshot", "file_sumber": "03_ros2_package_inventory",
         "status_bukti": "Kuat", "tabel_disarankan": "daftar package",
         "gambar_disarankan": "ros2 node list", "catatan": "screenshot terminal"},
        {"subbab": "2.5 Pembagian Package", "data_pendukung": "7 package",
         "bentuk_bukti": "tabel package", "file_sumber": "03_ros2_package_inventory",
         "status_bukti": "Kuat", "tabel_disarankan": "fungsi package",
         "gambar_disarankan": "diagram dependency", "catatan": "-"},
        {"subbab": "2.6 STM32/Joystick/Motor/Servo/Encoder", "data_pendukung": "protokol serial",
         "bentuk_bukti": "tabel protokol", "file_sumber": "06_stm32_serial_communication",
         "status_bukti": "Kuat", "tabel_disarankan": "format pesan TX/RX",
         "gambar_disarankan": "foto wiring STM32", "catatan": "video uji manual"},
        {"subbab": "2.7 RPLIDAR & RealSense", "data_pendukung": "data sensor",
         "bentuk_bukti": "tabel sensor + scan params", "file_sumber": "02_sensor_raw_data",
         "status_bukti": "Kuat", "tabel_disarankan": "spec sensor",
         "gambar_disarankan": "RViz scan + pointcloud", "catatan": "scan params dari data nyata"},
        {"subbab": "2.8 URDF/TF", "data_pendukung": "link/joint/frame",
         "bentuk_bukti": "tabel + diagram TF", "file_sumber": "05_robot_model_urdf_xacro",
         "status_bukti": "Kuat", "tabel_disarankan": "parameter geometri",
         "gambar_disarankan": "frames_*.pdf (ADA), RViz RobotModel", "catatan": "TF diagram tersedia"},
        {"subbab": "2.9 Kalibrasi Odometry", "data_pendukung": "uji 5 jarak, regresi",
         "bentuk_bukti": "tabel + plot", "file_sumber": "07_odometry_calibration",
         "status_bukti": "Kuat", "tabel_disarankan": "jarak nyata vs odom",
         "gambar_disarankan": "plot regresi R2", "catatan": "data CSV upload tersedia"},
        {"subbab": "2.10 Mapping RTAB-Map", "data_pendukung": "pipeline, params",
         "bentuk_bukti": "tabel param + screenshot", "file_sumber": "08_rtabmap_database_inventory",
         "status_bukti": "Sedang", "tabel_disarankan": "param mapping",
         "gambar_disarankan": "rtabmap_viz, graph view", "catatan": "screenshot perlu"},
        {"subbab": "2.11 Analisis Database", "data_pendukung": "inventaris 24 DB",
         "bentuk_bukti": "tabel + ringkasan", "file_sumber": "08_rtabmap_database_summary",
         "status_bukti": "Kuat (di laporan)", "tabel_disarankan": "metrik per DB",
         "gambar_disarankan": "bar chart node/LC", "catatan": "verifikasi ulang via rtabmap-info"},
        {"subbab": "2.12 Remapping & Peta Acuan", "data_pendukung": "lab_demo_18jun.db",
         "bentuk_bukti": "tabel metrik", "file_sumber": "08_rtabmap_database_inventory",
         "status_bukti": "Sedang", "tabel_disarankan": "peta lama vs bersih",
         "gambar_disarankan": "loop closure hijau, cloud", "catatan": "screenshot perlu"},
        {"subbab": "2.13 Localization", "data_pendukung": "params, root cause",
         "bentuk_bukti": "tabel ambang", "file_sumber": "09_localization_evidence",
         "status_bukti": "Sedang (bukti runtime kurang)", "tabel_disarankan": "mapping vs localization",
         "gambar_disarankan": "screenshot localization, log pose", "catatan": "BUKTI RUNTIME perlu"},
        {"subbab": "2.14 Navigation2", "data_pendukung": "config, 8 gerbang",
         "bentuk_bukti": "tabel config + kronologi", "file_sumber": "10_nav2_configuration_and_evidence",
         "status_bukti": "Sedang (bukti runtime kurang)", "tabel_disarankan": "plugin & param",
         "gambar_disarankan": "RViz path, video navigasi", "catatan": "VIDEO/LOG runtime perlu"},
        {"subbab": "2.15 Safety/Failover/Kendala", "data_pendukung": "failover, kendala",
         "bentuk_bukti": "tabel state + kendala", "file_sumber": "12_safety_failover_manual_control",
         "status_bukti": "Kuat", "tabel_disarankan": "state machine, kendala-solusi",
         "gambar_disarankan": "marker RViz failover", "catatan": "-"},
        {"subbab": "2.16 Project Terselesaikan", "data_pendukung": "status capaian",
         "bentuk_bukti": "tabel ketercapaian", "file_sumber": "00_project_identity",
         "status_bukti": "Kuat", "tabel_disarankan": "target vs realisasi",
         "gambar_disarankan": "-", "catatan": "jaga kejujuran teknis"},
    ]
    emit("15_report_evidence_matrix", "15 — Matriks Bukti per Subbab Laporan",
         "Menghubungkan data raw ke subbab 2.1-2.16. Kolom status_bukti menandai "
         "kekuatan bukti; gambar yang perlu ditambah manual disebut eksplisit.",
         rows, cols)


# =====================================================================
# Q. VISUAL DOCUMENTATION
# =====================================================================
def build_visual():
    cols = ["nama_file", "path", "jenis", "isi", "subbab_cocok", "caption",
            "status"]
    rows = []
    # File visual yang ADA di repo
    for f in ["frames_2026-06-09_22.08.25.pdf", "frames_2026-06-09_22.09.38.pdf",
              "frames_2026-06-09_22.08.25.gv", "frames_2026-06-09_22.09.38.gv"]:
        if exists(f):
            rows.append({"nama_file": f, "path": f, "jenis": "Diagram TF (view_frames)",
                         "isi": "TF tree robot (frames)", "subbab_cocok": "2.8 URDF/TF",
                         "caption": "TF tree hasil view_frames", "status": V_FILE + " (ADA di repo)"})
    # PCD prototype / docs mermaid
    rows.append({"nama_file": "diagram Mermaid frame-to-map", "path": "docs/LAPORAN_KORELASI_PENGOLAHAN_CITRA_DIGITAL.md",
                 "jenis": "Diagram alir", "isi": "alur frame-to-map", "subbab_cocok": "2.10 Mapping",
                 "caption": "Alur pipeline frame-to-map", "status": V_FILE})
    # Yang BELUM ada (checklist)
    missing = [
        ("Foto robot terakit", "2.3 Perakitan", "Foto AMR 4WD Ackermann"),
        ("Wiring diagram", "2.2/2.6 Hardware", "Skema kelistrikan"),
        ("Arsitektur sistem", "2.1/3.1", "Diagram blok berlapis"),
        ("Screenshot RViz /scan + pointcloud", "2.7 Sensor", "Validasi sensor"),
        ("Screenshot rtabmap_viz / graph view", "2.10/2.11 Mapping", "Pose graph"),
        ("Screenshot loop closure hijau", "2.12/2.13", "Bukti lokalisasi"),
        ("Screenshot RViz global/local plan", "2.14 Nav2", "Bukti navigasi"),
        ("Video robot bergerak otonom", "2.14 Nav2", "Bukti runtime navigasi"),
        ("Plot trajektori (x-y)", "2.11 Analisis DB", "Lintasan mapping"),
        ("Plot regresi odometry R2", "2.9 Kalibrasi", "Real vs odom"),
    ]
    for nama, sub, cap in missing:
        rows.append({"nama_file": nama, "path": "-", "jenis": "(belum ada)",
                     "isi": cap, "subbab_cocok": sub, "caption": cap,
                     "status": V_NONE + " (perlu dibuat/screenshot manual)"})
    emit("16_visual_documentation_inventory", "16 — Inventaris Dokumentasi Visual",
         "Visual yang ADA di repo (diagram TF) + checklist visual yang masih "
         "perlu dibuat/diambil manual.", rows, cols)


# =====================================================================
# R. SUMMARY DOCS
# =====================================================================
def build_summaries(file_list):
    today = date.today().isoformat()
    # README
    readme = [
        "# Raw AMR Evidence Package",
        f"\n_Generated: {today} (read-only scan repo)_\n",
        "Paket data raw & bukti teknis proyek AMR untuk penyusunan laporan final PjBL.",
        "\n## Struktur\n",
        "- `00`–`16`: kategori data (`.md` baca-manusia, `.csv` tabel, `.json` terstruktur).",
        "- `RAW_DATA_SUMMARY.md`: ringkasan data terkumpul.",
        "- `MISSING_EVIDENCE_CHECKLIST.md`: bukti yang masih harus ditambah manual.",
        "- `REPORT_TABLE_RECOMMENDATIONS.md`: rekomendasi tabel per subbab.",
        "\n## Legenda status validasi\n",
        f"- **{V_FILE}**: ada di source code repo.",
        f"- **{V_EXP}**: ada di file upload user (di luar repo).",
        f"- **{V_NOTE}**: dari catatan/progress; perlu validasi sumber.",
        f"- **{V_NONE}**: tidak ada artefaknya saat ini.",
        "\n## Daftar file\n",
    ]
    for fn in sorted(file_list):
        readme.append(f"- `{fn}`")
    write_md("README.md", "\n".join(readme) + "\n")

    # RAW_DATA_SUMMARY
    summ = [
        "# RAW DATA SUMMARY",
        "\n## Data yang BERHASIL dikumpulkan (terverifikasi dari file)\n",
        "- Spesifikasi hardware terkonfigurasi (URDF, sensors_launch, bridge).",
        "- Parameter sensor LiDAR & RealSense (termasuk scan params dari data nyata).",
        "- 7 package ROS2 + topic/node/service/action/TF.",
        "- Model robot URDF (geometri, link, joint, TF tree) + diagram frames_*.pdf.",
        "- Protokol serial STM32 lengkap (TX/RX, PWM, servo, gate, ramping).",
        "- Kalibrasi odometry: 5 titik uji, regresi R2=0.998, PPR 3858.",
        "- Konfigurasi RTAB-Map mapping & localization (+ tabel ambang).",
        "- Konfigurasi Nav2 lengkap + rantai 8 gerbang debugging.",
        "- Ackermann steering (parameter, rumus, fix arah).",
        "- Failover state machine + safety + PWM ramping.",
        "- Visual regression + line segments.",
        "- 14 kendala lintas subsistem dengan solusi.",
        "\n## Data KUAT sebagai bukti\n",
        "1. Kalibrasi odometry (data numerik + R2=0.998) — paling kuat & auditable.",
        "2. Konfigurasi sistem (semua YAML/launch/source) — 100% file-verified.",
        "3. Rantai 8 gerbang Nav2 (kronologi debugging dengan akar masalah).",
        "4. Parameter sensor LiDAR dari scan nyata (data_lidar_*.txt).",
        "\n## Data yang MASIH KURANG\n",
        "- File `.db` TIDAK ada di repo (di `~/maps/` NUC) — metrik dari laporan .docx; "
        "verifikasi ulang `rtabmap-info` di NUC.",
        "- Bukti RUNTIME lokalisasi (screenshot loop closure hijau, log /localization_pose).",
        "- Bukti RUNTIME navigasi (video, log /cmd_vel saat goal, RViz path).",
        "- Foto fisik robot, wiring diagram, screenshot RViz/rtabmap_viz.",
        "- Konfirmasi hardware: BTS7960, buck converter, push button/e-stop fisik.",
        "\n## Bagian laporan dengan bukti KUAT\n",
        "2.2, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.15 — sudah didukung data file.",
        "\n## Bagian laporan yang MASIH butuh bukti tambahan\n",
        "2.3 (foto), 2.10/2.11/2.12 (screenshot mapping/DB), 2.13 (bukti lokalisasi "
        "runtime), 2.14 (video/log navigasi runtime).",
        "\n## Rekomendasi urutan penggunaan data\n",
        "1. Mulai dari yang file-verified (2.4-2.9) untuk fondasi kuat.",
        "2. Lengkapi 2.10-2.14 dengan screenshot/log saat sesi lab berikutnya.",
        "3. Tambah foto hardware (2.2-2.3) dari dokumentasi tim.",
        "4. Jaga kejujuran: tandai klaim yang belum ada bukti runtime.",
    ]
    write_md("RAW_DATA_SUMMARY.md", "\n".join(summ) + "\n")

    # MISSING_EVIDENCE_CHECKLIST
    chk = [
        "# MISSING EVIDENCE CHECKLIST",
        "\nBukti yang HARUS ditambahkan manual (di luar kemampuan ekstraksi repo).\n",
        "## Foto / Hardware",
        "- [ ] Foto keseluruhan robot terakit",
        "- [ ] Foto kerangka & penggerak 4WD + kemudi Ackermann",
        "- [ ] Foto penempatan NUC/STM32/driver/baterai",
        "- [ ] Wiring diagram / skema kelistrikan",
        "- [ ] Konfirmasi spec: driver BTS7960, buck converter, push button/e-stop fisik",
        "\n## Sensor (RViz)",
        "- [ ] Screenshot RViz /scan (LaserScan)",
        "- [ ] Screenshot RViz point cloud RGB-D",
        "- [ ] Output `ros2 topic hz` tiap sensor",
        "\n## Mapping / Database",
        "- [ ] Screenshot rtabmap_viz saat mapping",
        "- [ ] Screenshot DatabaseViewer graph view",
        "- [ ] Output `rtabmap-info lab_demo_18jun.db` (verifikasi metrik)",
        "- [ ] Plot trajektori (x-y)",
        "\n## Localization",
        "- [ ] Screenshot loop closure hijau (mode localization)",
        "- [ ] Log /localization_pose atau /rtabmap pose",
        "- [ ] (Opsional) RMSE pose vs ground truth",
        "\n## Navigation2",
        "- [ ] Video robot bergerak otonom dari goal",
        "- [ ] Log `/cmd_vel` saat goal aktif (linear.x != 0)",
        "- [ ] Screenshot RViz global plan + local plan + costmap",
        "- [ ] Log 'Managed nodes are active'",
        "\n## Kalibrasi (perkuat)",
        "- [ ] Plot regresi real vs odom (dari data_euler_odom.csv / jalan_maju)",
        "- [ ] Foto pengukuran meteran saat uji jarak",
    ]
    write_md("MISSING_EVIDENCE_CHECKLIST.md", "\n".join(chk) + "\n")

    # REPORT_TABLE_RECOMMENDATIONS
    rec = [
        "# REPORT TABLE RECOMMENDATIONS",
        "\nTabel siap-pakai per subbab (sumber CSV ada di paket ini).\n",
        "| Subbab | Tabel disarankan | Sumber CSV |",
        "|---|---|---|",
        "| 2.2 Hardware | Spesifikasi komponen | 01_hardware_inventory.csv |",
        "| 2.5 Package | Fungsi 7 package | 03_ros2_package_inventory.csv |",
        "| 2.6 STM32 | Format pesan TX/RX & parameter | 06_stm32_serial_communication.csv |",
        "| 2.7 Sensor | Spec & parameter sensor | 02_sensor_raw_data.csv |",
        "| 2.8 URDF/TF | Parameter geometri | 05_robot_model_urdf_xacro.csv |",
        "| 2.9 Odometry | Jarak nyata vs odom + regresi | 07_odometry_calibration.csv |",
        "| 2.10 Mapping | Parameter RTAB-Map | (lihat 08 + bank data) |",
        "| 2.11 Database | Metrik per DB + ringkasan | 08_rtabmap_database_*.csv |",
        "| 2.13 Localization | Ambang mapping vs localization | 09_localization_evidence.csv |",
        "| 2.14 Nav2 | Plugin & parameter + 8 gerbang | 10_nav2_*.csv, 14_issues_*.csv |",
        "| 2.15 Safety | State machine + kendala-solusi | 12_*.csv, 14_*.csv |",
        "| 2.16 Capaian | Target vs realisasi | 00_project_identity.json |",
        "\n## Catatan",
        "- CSV dapat langsung di-import ke Word/Excel/Sheets lalu diformat.",
        "- JSON untuk pemrosesan lanjut / generate ulang.",
        "- Selalu cantumkan sumber & jaga kejujuran teknis (tandai bukti runtime "
        "yang belum ada).",
    ]
    write_md("REPORT_TABLE_RECOMMENDATIONS.md", "\n".join(rec) + "\n")


# =====================================================================
# MAIN
# =====================================================================
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    build_identity()
    build_hardware()
    build_sensors()
    build_packages()
    build_interfaces()
    build_urdf()
    build_stm32()
    build_odometry()
    build_rtabmap_db()
    build_localization()
    build_nav2()
    build_ackermann()
    build_safety()
    build_vr()
    build_issues()
    build_matrix()
    build_visual()

    file_list = sorted(os.listdir(OUTDIR))
    build_summaries(file_list)
    file_list = sorted(os.listdir(OUTDIR))

    # ZIP
    with zipfile.ZipFile(ZIPPATH, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in file_list:
            z.write(os.path.join(OUTDIR, fn), arcname=os.path.join(
                "raw_amr_evidence_package", fn))

    # Ringkasan terminal
    n_md = sum(1 for f in file_list if f.endswith(".md"))
    n_csv = sum(1 for f in file_list if f.endswith(".csv"))
    n_json = sum(1 for f in file_list if f.endswith(".json"))
    print("=" * 60)
    print("PAKET DATA RAW AMR — SELESAI DIBUAT")
    print("=" * 60)
    print(f"Folder : {rel(OUTDIR)}")
    print(f"ZIP    : {rel(ZIPPATH)}")
    print(f"Total file: {len(file_list)}  (MD={n_md}, CSV={n_csv}, JSON={n_json})")
    print("-" * 60)
    for fn in file_list:
        print(f"  {fn}")
    print("=" * 60)


if __name__ == "__main__":
    main()
