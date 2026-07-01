#!/bin/bash
# ============================================================
# Deploy AMR Workspace ke NUC
#
# Cara pakai:
#   1. Copy seluruh folder amr_ws/src/ ke NUC (USB/scp)
#   2. Taruh script ini di ~/amr_ws/deploy.bash
#   3. chmod +x ~/amr_ws/deploy.bash
#   4. ./deploy.bash
#
# Script ini IDEMPOTENT — aman dijalankan berkali-kali.
# ============================================================

set -e  # Berhenti kalau ada error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WS_DIR="$HOME/amr_ws"
SRC_DIR="$WS_DIR/src"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Deploy AMR Workspace — NUC Ubuntu 22.04  ${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ---- STEP 0: Cek prasyarat ----
echo -e "${YELLOW}[0/7] Cek prasyarat...${NC}"

if [ ! -f /opt/ros/humble/setup.bash ]; then
    echo -e "${RED}GAGAL: ROS 2 Humble tidak ditemukan di /opt/ros/humble/${NC}"
    echo "Install dulu: https://docs.ros.org/en/humble/Installation.html"
    exit 1
fi

source /opt/ros/humble/setup.bash
echo -e "${GREEN}  ✓ ROS 2 Humble ditemukan${NC}"

if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}GAGAL: Folder $SRC_DIR tidak ditemukan${NC}"
    echo "Copy folder src/ dari Windows ke $SRC_DIR dulu."
    exit 1
fi

PACKAGES=(amr_sensors amr_pose amr_mapping amr_navigation amr_brain amr_startup)
for pkg in "${PACKAGES[@]}"; do
    if [ ! -d "$SRC_DIR/$pkg" ]; then
        echo -e "${RED}GAGAL: Package $SRC_DIR/$pkg tidak ditemukan${NC}"
        exit 1
    fi
done
echo -e "${GREEN}  ✓ Semua 6 package ditemukan di src/${NC}"

# ---- STEP 1: Install system dependencies ----
echo ""
echo -e "${YELLOW}[1/7] Install system dependencies...${NC}"

sudo apt-get update -qq

sudo apt-get install -y -qq \
    ros-humble-rtabmap-ros \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-robot-localization \
    ros-humble-rplidar-ros \
    ros-humble-realsense2-camera \
    ros-humble-realsense2-description \
    ros-humble-depthimage-to-laserscan \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-xacro \
    ros-humble-diagnostic-msgs \
    ros-humble-tf2-tools \
    python3-colcon-common-extensions \
    python3-rosdep

echo -e "${GREEN}  ✓ System dependencies installed${NC}"

# ---- STEP 2: rosdep ----
echo ""
echo -e "${YELLOW}[2/7] Resolve rosdep dependencies...${NC}"

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init 2>/dev/null || true
fi
rosdep update --rosdistro=humble 2>/dev/null || true
rosdep install --from-paths "$SRC_DIR" --ignore-src -y -r 2>/dev/null || true

echo -e "${GREEN}  ✓ rosdep selesai${NC}"

# ---- STEP 3: Bersihkan build lama ----
echo ""
echo -e "${YELLOW}[3/7] Bersihkan build lama (kalau ada)...${NC}"

cd "$WS_DIR"
rm -rf build/ install/ log/
echo -e "${GREEN}  ✓ Folder build/install/log dihapus${NC}"

# ---- STEP 4: Build satu per satu (ATURAN: tidak boleh colcon build penuh) ----
echo ""
echo -e "${YELLOW}[4/7] Build packages satu per satu...${NC}"

source /opt/ros/humble/setup.bash

BUILD_ORDER=(
    amr_body
    amr_motor
    amr_sensors
    amr_pose
    amr_mapping
    amr_navigation
    amr_brain
    amr_startup
)

for pkg in "${BUILD_ORDER[@]}"; do
    if [ -d "$SRC_DIR/$pkg" ]; then
        echo -e "  Building ${CYAN}$pkg${NC}..."
        colcon build --symlink-install --packages-select "$pkg" 2>&1 | tail -1
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo -e "${RED}  ✗ GAGAL build $pkg${NC}"
            exit 1
        fi
        echo -e "${GREEN}  ✓ $pkg${NC}"
    fi
done

source "$WS_DIR/install/setup.bash"
echo -e "${GREEN}  ✓ Semua package berhasil di-build${NC}"

# ---- STEP 5: Setup udev rules untuk sensor ----
echo ""
echo -e "${YELLOW}[5/7] Setup udev rules...${NC}"

UDEV_FILE="/etc/udev/rules.d/99-amr-sensors.rules"

sudo tee "$UDEV_FILE" > /dev/null << 'UDEV_EOF'
# RPLIDAR C1 — selalu muncul sebagai /dev/rplidar
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"

# STM32 (encoder/motor) — selalu muncul sebagai /dev/stm32
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="stm32", MODE="0666"
UDEV_EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

echo -e "${GREEN}  ✓ udev rules: /dev/rplidar dan /dev/stm32${NC}"

# ---- STEP 6: Setup auto-source di bashrc ----
echo ""
echo -e "${YELLOW}[6/7] Setup bashrc...${NC}"

BASHRC="$HOME/.bashrc"
SOURCE_LINE="source $WS_DIR/install/setup.bash"

if ! grep -qF "$SOURCE_LINE" "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# AMR Workspace" >> "$BASHRC"
    echo "source /opt/ros/humble/setup.bash" >> "$BASHRC"
    echo "$SOURCE_LINE" >> "$BASHRC"
    echo -e "${GREEN}  ✓ Ditambahkan ke .bashrc${NC}"
else
    echo -e "${GREEN}  ✓ Sudah ada di .bashrc${NC}"
fi

# Buat folder untuk data
mkdir -p "$HOME/amr_bags"
mkdir -p "$HOME/maps"

echo -e "${GREEN}  ✓ Folder ~/amr_bags/ dan ~/maps/ siap${NC}"

# ---- STEP 7: Verifikasi ----
echo ""
echo -e "${YELLOW}[7/7] Verifikasi...${NC}"

source "$WS_DIR/install/setup.bash"

VERIFY_OK=true

for pkg in "${PACKAGES[@]}"; do
    if ros2 pkg prefix "$pkg" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ $pkg terdeteksi ROS 2${NC}"
    else
        echo -e "${RED}  ✗ $pkg TIDAK terdeteksi${NC}"
        VERIFY_OK=false
    fi
done

# Cek launch files bisa ditemukan
echo ""
echo -e "  Cek launch files..."
LAUNCHES=(
    "amr_startup amr_sensors_only.launch.py"
    "amr_startup layer2_pose.launch.py"
    "amr_startup layer3_mapping.launch.py"
    "amr_startup layer4_navigation.launch.py"
    "amr_startup full_system.launch.py"
    "amr_startup record_sensors.launch.py"
)

for entry in "${LAUNCHES[@]}"; do
    pkg=$(echo "$entry" | cut -d' ' -f1)
    launch=$(echo "$entry" | cut -d' ' -f2)
    launch_dir=$(ros2 pkg prefix "$pkg" 2>/dev/null)/share/$pkg/launch
    if [ -f "$launch_dir/$launch" ]; then
        echo -e "${GREEN}  ✓ $launch${NC}"
    else
        echo -e "${RED}  ✗ $launch TIDAK ditemukan${NC}"
        VERIFY_OK=false
    fi
done

# ---- SELESAI ----
echo ""
echo -e "${CYAN}============================================${NC}"
if [ "$VERIFY_OK" = true ]; then
    echo -e "${GREEN}  DEPLOY BERHASIL!${NC}"
else
    echo -e "${RED}  DEPLOY SELESAI DENGAN WARNING — cek error di atas${NC}"
fi
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "Langkah selanjutnya:"
echo -e "  1. Colok semua sensor (LiDAR, RealSense, STM32)"
echo -e "  2. Buka terminal BARU (supaya bashrc ter-source)"
echo -e "  3. Jalankan:"
echo -e "     ${CYAN}ros2 launch amr_startup amr_sensors_only.launch.py${NC}"
echo -e "  4. Ikuti checklist: ${CYAN}cat ~/amr_ws/DEPLOY_NUC.md${NC}"
echo ""
