#!/usr/bin/env bash
# setup_test_tools.sh
# ===================
# Pasang SEMUA dependensi untuk amr_test_tools dalam satu perintah.
# Jalankan SEKALI di NUC sebelum mulai pengujian.
#
#   bash ~/amr_starter/scripts/amr_test_tools/setup_test_tools.sh
#
# Aman dijalankan berulang (idempotent).

set -e

echo "============================================================"
echo " SETUP DEPENDENSI amr_test_tools"
echo "============================================================"

# ---- 1. Python deps untuk rekap Excel ----
echo
echo "[1/4] Python: openpyxl (untuk amr_test_recap.xlsx)"
if python3 -c "import openpyxl" 2>/dev/null; then
    echo "      openpyxl sudah ada — skip"
else
    pip3 install openpyxl || sudo apt install -y python3-openpyxl
fi

# ---- 2. ROS 2 message deps (biasanya sudah ada di Humble desktop) ----
echo
echo "[2/4] Cek ROS 2 message packages"
MISSING=""
for pkg in nav_msgs geometry_msgs sensor_msgs std_msgs; do
    if ! python3 -c "import ${pkg}.msg" 2>/dev/null; then
        MISSING="$MISSING ros-humble-${pkg//_/-}"
    fi
done
if [ -n "$MISSING" ]; then
    echo "      Install:$MISSING"
    sudo apt update && sudo apt install -y $MISSING
else
    echo "      Semua message package ada — skip"
fi

# ---- 3. rclpy ----
echo
echo "[3/4] Cek rclpy"
if python3 -c "import rclpy" 2>/dev/null; then
    echo "      rclpy OK"
else
    echo "      [!] rclpy tidak ditemukan. Pastikan ROS 2 sudah di-source:"
    echo "          source /opt/ros/humble/setup.bash"
fi

# ---- 4. Permission script ----
echo
echo "[4/4] chmod +x semua script"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR"/scripts/*.py 2>/dev/null || true
echo "      OK"

# ---- folder hasil ----
mkdir -p ~/amr_test_results

echo
echo "============================================================"
echo " SELESAI. Folder hasil: ~/amr_test_results"
echo " Langkah berikutnya: baca README_PENGUJIAN_AMR.md"
echo "============================================================"
