#!/usr/bin/env bash
# ============================================================
# record_sensor_evidence.sh
# Rekam data SEMUA sensor selama sesi mapping/remapping.
#
# Tujuan (rule owner, 11 Juni 2026):
#   1. Dataset korelasi mata kuliah Metode Numerik & DCS SCADA
#   2. Bukti forensik: kalau mapping gagal, data ini membuktikan
#      semua sensor sehat dan kegagalan berasal dari lingkungan
#      (lab putih polos / textureless), bukan dari hardware.
#
# Jalankan di TERMINAL 4, SEBELUM robot mulai digerakkan,
# setelah amr_full + rtabmap_mapping sudah jalan:
#   bash scripts/record_sensor_evidence.sh run1
#   bash scripts/record_sensor_evidence.sh run1 --with-images
#
# Stop dengan Ctrl+C SETELAH mapping selesai (setelah robot
# kembali ke titik "X" dan diam 15 detik).
#
# Output : ~/mapping_evidence/<nama>_<timestamp>/  (format rosbag2)
# Analisis: python3 scripts/analyze_sensor_bag.py <folder_bag>
#
# Estimasi ukuran:
#   tanpa images : ~5-20 MB/menit  (aman untuk sesi panjang)
#   dengan images: ~2-4 GB/menit   (RGB+depth raw 848x480x30,
#                  pakai hanya untuk 1 run pendek sebagai sampel visual)
# ============================================================
set -u

NAME="${1:-run}"
WITH_IMAGES=false
for arg in "$@"; do
  [ "$arg" = "--with-images" ] && WITH_IMAGES=true
done

TS=$(date +%Y%m%d_%H%M%S)
OUT_DIR="$HOME/mapping_evidence/${NAME}_${TS}"
mkdir -p "$HOME/mapping_evidence"

# ---- Topik yang direkam (semua low-bandwidth, full rate) ----
TOPICS=(
  # LiDAR RPLIDAR C1
  /scan
  # IMU RealSense D455: hasil merge + stream mentah accel & gyro
  /imu/data
  /camera/camera/accel/sample
  /camera/camera/gyro/sample
  # Intrinsik kamera (bukti konfigurasi 848x480)
  /camera/camera/color/camera_info
  # VIO output + telemetri kualitas tracking (inliers, fitur, variance)
  /rtabmap/odom
  /odom_info
  /odom_last_frame
  # Telemetri SLAM: loop closure id, hypothesis value, statistik
  /rtabmap/info
  # Hasil peta 2D (kecil) sebagai bukti progres
  /rtabmap/grid_map
  # Wheel odometry + encoder mentah STM32 + perintah joystick
  /odom
  /encoder
  /joy
  # Pohon transformasi (untuk rekonstruksi trajektori)
  /tf
  /tf_static
)

if $WITH_IMAGES; then
  TOPICS+=(
    /camera/camera/color/image_raw
    /camera/camera/aligned_depth_to_color/image_raw
  )
  echo "[WARN] Mode --with-images: ~2-4 GB/menit. Pakai untuk run pendek saja."
fi

echo "=============================================="
echo " Rekaman bukti sensor -> ${OUT_DIR}"
echo " Topik: ${#TOPICS[@]} | images: ${WITH_IMAGES}"
echo " Stop dengan Ctrl+C setelah mapping selesai."
echo "=============================================="

# zstd: kompresi per-file, hemat disk tanpa beban CPU berarti
exec ros2 bag record \
  --compression-mode file \
  --compression-format zstd \
  -o "$OUT_DIR" \
  "${TOPICS[@]}"
