# 10 — Konfigurasi & Bukti Navigation2

Konfigurasi terverifikasi dari nav2_params.yaml. Rantai 8 gerbang ada di file 14. Bukti runtime navigasi masih perlu dilengkapi.

| aspek | nilai | bukti | status |
|---|---|---|---|
| Config | nav2_params.yaml | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Launch | nav2.launch.py (remap dihapus, mode demo) | src/amr_slam/launch/nav2.launch.py | Terverifikasi dari file |
| Planner | nav2_smac_planner/SmacPlannerHybrid (DUBIN) | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| min_turning_radius | 0.90 m; reverse_penalty 2.0 | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Controller | RegulatedPurePursuitController (desired_linear_vel 0.3) | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Global costmap | static + obstacle + inflation; obs scan saja | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Local costmap | 4x4 rolling; voxel + inflation | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Inflation layer | inflation_radius 0.25; cost_scaling 3.0 | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Voxel/Obstacle layer | nav2_costmap_2d::{Voxel,Obstacle}Layer | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| robot_radius | 0.28 (dari 0.35) | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| depth_scan di costmap | DIMATIKAN (obstacle hantu lantai) | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Behavior tree XML | path absolut navigate_to_pose_w_replanning_and_recovery.xml | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Recovery behaviors | spin, backup, drive_on_heading, wait | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Smoother | nav2_smoother::SimpleSmoother | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Format plugin | :: (costmap/controller/smoother/waypoint), / (smac/behaviors) | src/amr_slam/config/nav2_params.yaml | Terverifikasi dari file |
| Topic cmd_vel | /cmd_vel (remap dihapus, mode demo) | src/amr_slam/launch/nav2.launch.py | Terverifikasi dari file |
| Action | /navigate_to_pose (nav2_msgs/NavigateToPose) | src/amr_slam/launch/nav2.launch.py | Terverifikasi dari file |
| Status pengujian | Robot bergerak otonom (mode demo, 19-Jun) | handover | Catatan/progress (perlu validasi sumber) |
| Bukti runtime tersedia | log error 8 gerbang (progress) | docs/root_cause_analysis_nav_lokalisasi.md | Terverifikasi dari file |
| Bukti runtime kurang | video navigasi, log /cmd_vel saat goal, screenshot RViz path | - | Tidak ditemukan di repo/file saat ini |
