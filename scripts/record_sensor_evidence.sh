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
# Jalankan di TERMINAL 4, SETELAH amr_full + rtabmap_mapping sudah
# jalan dan SEBELUM robot mulai digerakkan:
#   bash scripts/record_sensor_evidence.sh run1
#   bash scripts/record_sensor_evidence.sh run1 --with-images
#
# Stop dengan Ctrl+C SETELAH mapping selesai (setelah robot
# kembali ke titik "X" dan diam 15 detik).
#
# STRATEGI: rekam SEMUA topik (-a) lalu BUANG yang berat (regex -x).
# Dengan cara ini tidak ada satu pun sensor yang luput karena salah
# tebak nama topik — apapun yang dipublish saat record mulai, terekam.
# (-a hanya menangkap topik yang SUDAH ada saat record START, jadi
#  pastikan pipeline penuh sudah jalan dulu.)
#
# Output : ~/mapping_evidence/<nama>_<timestamp>/  (format rosbag2)
# Analisis: python3 scripts/analyze_sensor_bag.py <folder_bag>
#
# Yang DIHARAPKAN terekam (low-bandwidth, untuk laporan):
#   /scan                            LiDAR RPLIDAR C1 (~10Hz)
#   /imu/data                        IMU merge (accel+gyro, ~100-200Hz)
#   /camera/camera/accel/sample      accel mentah D455
#   /camera/camera/gyro/sample       gyro mentah D455
#   /camera/camera/color/camera_info intrinsik (bukti 848x480)
#   /rtabmap/odom                    pose VIO + kovarians
#   /odom_info (atau sejenis)        telemetri kualitas VIO (inliers/fitur/lost)
#   /rtabmap/info                    loop closure id + statistik SLAM
#   /rtabmap/grid_map                occupancy 2D (kecil)
#   /odom /encoder /joy              wheel odom + encoder mentah + joystick
#   /tf /tf_static /rosout           transformasi + log node (forensik)
#
# Estimasi ukuran:
#   tanpa images : ~5-25 MB/menit  (aman untuk sesi panjang)
#   dengan images: ~2-4 GB/menit   (RGB+depth 848x480x30,
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

# Topik BERAT yang selalu dibuang (3D cloud sudah tersimpan di .db;
# di sini kita hanya butuh telemetri & peta 2D yang ringan).
EXCLUDE_HEAVY='(.*/points.*)|(/rtabmap/(cloud_map|cloud_obstacles|cloud_ground|mapData|octomap.*|local_grid.*))|(/parameter_events)'
# Topik gambar mentah (default dibuang; disertakan dengan --with-images).
EXCLUDE_IMAGES='(/camera/camera/.*image.*)'

if $WITH_IMAGES; then
  EXCLUDE_REGEX="$EXCLUDE_HEAVY"
  echo "[WARN] Mode --with-images: ~2-4 GB/menit. Pakai untuk run pendek saja."
else
  EXCLUDE_REGEX="${EXCLUDE_HEAVY}|${EXCLUDE_IMAGES}"
fi

echo "=============================================="
echo " Rekaman bukti sensor -> ${OUT_DIR}"
echo " Mode: record -a (semua topik) minus regex berat"
echo " images: ${WITH_IMAGES}"
echo " Stop dengan Ctrl+C setelah mapping selesai."
echo "=============================================="

# -a            : rekam semua topik yang ada saat record mulai
# -x REGEX      : kecuali yang cocok regex (topik berat)
# zstd file     : kompresi per-file, hemat disk, CPU ringan
exec ros2 bag record -a \
  -x "$EXCLUDE_REGEX" \
  --compression-mode file \
  --compression-format zstd \
  -o "$OUT_DIR"
