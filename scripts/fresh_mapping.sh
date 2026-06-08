#!/usr/bin/env bash
# =====================================================================
# fresh_mapping.sh
# =====================================================================
# Helper untuk REMAPPING — backup db lama lalu hapus, kemudian launch
# pipeline mapping. Dirancang untuk mencegah masalah:
#   - rtabmap crash karena database corrupt (sesi 7 Juni)
#   - Mapping ter-akumulasi di atas data lama yang sudah drift
#
# Yang dilakukan:
#   1. Backup db & maps lama dengan timestamp
#   2. Hapus db lama dari ~/.ros/ dan ~/maps/
#   3. Reminder verifikasi 5 param kritis hasil introspeksi 8 Juni
#   4. (User jalankan launch manual di terminal terpisah)
#
# Pakai:
#   bash scripts/fresh_mapping.sh
# =====================================================================

set -e

STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/amr_mapping_backup_$STAMP"

echo "============================================="
echo "  FRESH MAPPING — Persiapan Remap"
echo "============================================="

# ---- 1. Backup ----
mkdir -p "$BACKUP_DIR"

if [ -f "$HOME/.ros/rtabmap.db" ]; then
  mv "$HOME/.ros/rtabmap.db" "$BACKUP_DIR/rtabmap.db"
  echo "✓ ~/.ros/rtabmap.db → $BACKUP_DIR/"
fi

if [ -f "$HOME/maps/lab_vio.db" ]; then
  mv "$HOME/maps/lab_vio.db" "$BACKUP_DIR/lab_vio.db"
  echo "✓ ~/maps/lab_vio.db → $BACKUP_DIR/"
fi

# Backup PGM/YAML kalau ada
for f in "$HOME/maps/"*.pgm "$HOME/maps/"*.yaml; do
  [ -f "$f" ] && cp "$f" "$BACKUP_DIR/" && echo "✓ $(basename $f) dibackup"
done

echo ""
echo "Backup tersimpan di: $BACKUP_DIR"
echo ""

# ---- 2. Verifikasi param hasil introspeksi 8 Juni ----
WS_LAUNCH="$HOME/amr_starter/src/amr_3d_mapping/launch/rtabmap_mapping.launch.py"
[ ! -f "$WS_LAUNCH" ] && WS_LAUNCH="$HOME/autonomous-mobile-robot-ros2/src/amr_3d_mapping/launch/rtabmap_mapping.launch.py"

echo "============================================="
echo "  Verifikasi param kritis (introspeksi 8 Juni)"
echo "============================================="
echo ""

check_param() {
  local key="$1" expected="$2"
  local found=$(grep -E "'$key':" "$WS_LAUNCH" | head -1 | grep -oE "'[^']*'" | sed -n '2p')
  if [ "$found" = "'$expected'" ]; then
    echo "  ✓ $key = $expected"
  else
    echo "  ✗ $key = $found (expected: '$expected')"
  fi
}

check_param "Vis/MinInliers" "8"
check_param "Odom/MaxVariance" "0.05"
check_param "Odom/ResetCountdown" "5"
check_param "Rtabmap/DetectionRate" "2.0"
check_param "Kp/MaxFeatures" "400"
check_param "Mem/STMSize" "10"
echo "  (cek juga: cloud_max_depth=5.0, Grid/NoiseFilteringRadius=0.5)"

echo ""
echo "============================================="
echo "  Siap remapping. Langkah selanjutnya:"
echo "============================================="
echo ""
echo "Terminal 1 (sensors):"
echo "  cd ~/amr_starter && source install/setup.bash"
echo "  ros2 launch amr_bringup amr_full.launch.py \\"
echo "    use_slam:=false use_nav2:=false use_rtabmap:=false \\"
echo "    use_vr:=false use_failover:=false"
echo ""
echo "Terminal 2 (mapping):"
echo "  source ~/amr_starter/install/setup.bash"
echo "  ros2 launch amr_3d_mapping rtabmap_mapping.launch.py \\"
echo "    database_path:=\$HOME/maps/lab_remap3_$STAMP.db"
echo ""
echo "Terminal 3 (monitor loop closure):"
echo "  watch -n 1 \"ros2 topic echo /rtabmap/info --once | \\"
echo "    grep -E 'loop_closure_id|proximity_detection_id'\""
echo ""
echo "Setelah selesai mapping — simpan peta 2D:"
echo "  ros2 run nav2_map_server map_saver_cli \\"
echo "    -f \$HOME/maps/lab_remap3_$STAMP"
echo ""
