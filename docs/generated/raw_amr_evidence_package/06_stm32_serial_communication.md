# 06 — Komunikasi Serial ROS2 <-> STM32

Protokol & parameter bridge, terverifikasi dari stm32_bridge.cpp.

| item | nilai | bukti | status |
|---|---|---|---|
| Port serial | /dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_206833894152-if00 | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Baudrate | 115200 (B115200) | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Format TX (NUC->STM32) | V:{pwm},S:{sudut}\n | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Format RX (STM32->NUC) | E:{delta}\n | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Perintah motor (PWM) | MAX_PWM=4000; negatif=mundur | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Perintah servo | MAX_STEER=45 deg; STEER_TRIM=-5 | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Data encoder | E:{delta} -> /encoder (Int32); auto-detect cumulative/delta | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| PWM ramping | MAX_PWM_STEP=400/call; e-stop bypass | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Safety gate | autonomous_enabled (default false) | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Deadman | R1 (button index 5); manual override | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Watchdog | cmd_vel timeout 500 ms -> motor stop | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Konversi Ackermann | steer = -atan(WHEELBASE*w/v) (negasi fix 20-Jun) | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
| Konvensi arah | V positif=maju (kabel motor ditukar fisik) | src/amr_controller/src/stm32_bridge.cpp | Terverifikasi dari file |
