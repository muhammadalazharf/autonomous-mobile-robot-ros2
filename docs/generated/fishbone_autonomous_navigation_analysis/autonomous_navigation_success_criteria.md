# Kriteria Keberhasilan Autonomous Navigation

Effect: AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.

| Kriteria | Status | Bukti | Sumber file | Gap |
|---|---|---|---|---|
| Mapping tersedia & valid | Berdasarkan catatan progress | lab_demo_18jun.db (448 pose, 125+648 LC) | `src/amr_3d_mapping/config/rtabmap_mapping.yaml; .db di NUC` | Verifikasi ulang rtabmap-info + screenshot graph |
| Localization lock terhadap peta | Berdasarkan catatan progress | ambang disamakan; lock 18 Jun | `src/amr_3d_mapping/config/rtabmap_localization.yaml; docs/root_cause_analysis_nav_lokalisasi.md` | Log /localization_pose / screenshot loop hijau |
| Global planner menghasilkan path point-to-point | Berdasarkan catatan progress | SmacPlannerHybrid + navigate_to_pose + goal_sender | `src/amr_slam/config/nav2_params.yaml; src/amr_slam/scripts/goal_sender.py` | Screenshot global plan / log action result |
| Local planner command obstacle-avoidant | Berdasarkan catatan progress | RegulatedPurePursuit + local costmap (scan) | `src/amr_slam/config/nav2_params.yaml` | Video/log robot menghindar obstacle |
| Costmap menerima data obstacle | Terverifikasi dari file repo | obstacle_layer/voxel_layer sumber /scan | `src/amr_slam/config/nav2_params.yaml` | Screenshot costmap dgn obstacle |
| /cmd_vel muncul | Berdasarkan catatan progress | controller -> /cmd_vel (remap dihapus) | `src/amr_slam/launch/nav2.launch.py` | Log ros2 topic echo /cmd_vel saat goal |
| STM32 menerima command | Berdasarkan catatan progress | stm32_bridge subscribe /cmd_vel, gate enabled | `src/amr_controller/src/stm32_bridge.cpp` | Log serial / indikator motor |
| Motor & servo bergerak sesuai perintah | Berdasarkan catatan progress | robot bergerak otonom 19 Jun | `src/amr_controller/src/stm32_bridge.cpp` | Video robot bergerak ke goal |
| Encoder feedback | Terverifikasi dari file repo | E:{delta} -> /encoder -> /odom | `src/amr_controller/src/stm32_bridge.cpp; src/amr_controller/scripts/odometry_publisher.py` | Plot /encoder atau /odom saat gerak |
| Safety siap | Terverifikasi dari file repo | failover + deadman + e-stop software + ramping | `src/amr_failover/amr_failover/failover_controller.py` | Uji runtime failover; konfirmasi e-stop fisik |

> Kesimpulan: fondasi (config, hardware, kalibrasi, sensor) **terverifikasi dari file**. Rantai autonomous end-to-end (localization lock -> global path -> obstacle avoidance -> /cmd_vel -> aktuator) berstatus **catatan progress**; perlu bukti runtime untuk klaim final.
