# Development Guide — AMR ROS2 Ackermann 2WS

## Quick Reference

### Start the Robot
```bash
# Terminal 1 — permissions
sudo chmod 666 /dev/ttyACM1 /dev/ttyACM0 /dev/ttyUSB0

# Terminal 2 — teleop
cd ~/amr_ws && source install/setup.bash
ros2 launch amr_bringup amr_launch.py

# Terminal 3 — sensors
cd ~/amr_ws && source install/setup.bash
ros2 launch amr_bringup sensors_launch.py
```

## Port Mapping
| Port | Device |
|---|---|
| `/dev/ttyACM0` | GPS U-Blox |
| `/dev/ttyACM1` | STM32F407 |
| `/dev/ttyUSB0` | RPLIDAR C1 |
| `/dev/input/js0` | Joystick Rexus GX300 |

## Joystick Control
- Hold **R1** = deadman switch (required)
- Left analog up/down = forward / backward
- Right analog left/right = steer left / right

## Communication Protocol

NUC -> STM32 : V:{-4000~4000},S:{-45~45}\n
STM32 -> NUC : E:{delta_encoder}\n

## Build Workspace
```bash
cd ~/amr_ws
colcon build
source install/setup.bash
```

## First-Time Setup
```bash
sudo usermod -aG dialout $USER
sudo apt install ros-humble-joy ros-humble-teleop-twist-joy -y
sudo apt install ros-humble-nmea-msgs ros-humble-gps-tools -y
sudo apt install ros-humble-nmea-navsat-driver -y
sudo apt install ros-humble-realsense2-camera -y

cd ~/amr_ws/src
git clone https://github.com/Slamtec/rplidar_ros.git
cd rplidar_ros && git checkout ros2

cd ~/amr_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## Manual STM32 Test (tanpa ROS2)
```bash
echo -n "V:500,S:0"   > /dev/ttyACM1   # forward slow
echo -n "V:-500,S:0"  > /dev/ttyACM1   # backward slow
echo -n "V:0,S:20"    > /dev/ttyACM1   # turn right
echo -n "V:0,S:0"     > /dev/ttyACM1   # stop
```

## Troubleshooting
| Problem | Solution |
|---|---|
| Serial belum terbuka | `sudo chmod 666 /dev/ttyACM1` |
| STM32 tidak terdeteksi | Cek kabel USB, pastikan port Micro-B USER |
| Motor mundur saat maju | Velocity polarity: sudah fix dengan `-MAX_PWM` |
| RealSense tidak terdeteksi | Pindah ke port USB3 (port biru) |
| Port ACM bertukar | Pasang udev rules `/etc/udev/rules.d/99-amr.rules` |

## udev Rules (next agenda)
```bash
udevadm info -a -n /dev/ttyACM1 | grep idVendor
udevadm info -a -n /dev/ttyACM1 | grep idProduct

sudo nano /etc/udev/rules.d/99-amr.rules
# Isi:
# SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="ttyAMR"

sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Next Agenda
1. udev rules untuk port stabil `/dev/ttyAMR`
2. Kalibrasi steering fisik
3. Full end-to-end integration test
4. Nav2 autonomous navigation
