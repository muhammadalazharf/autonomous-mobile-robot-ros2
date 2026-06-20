# 13 — Visual Regression / Fallback

Path B fallback berbasis regresi depth + line segments LiDAR.

| item | nilai | bukti | status |
|---|---|---|---|
| Pendekatan | RandomForestRegressor (scikit-learn), tanpa CNN | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| Pipeline | data_collector -> train.py (offline) -> vr_inference | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| Input | depth image ROI (top 200, bottom 360), num_regions=9 | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| Statistik depth | fitur per region (modul feature_extractor) | src/amr_visual_regression/amr_visual_regression/feature_extractor.py | Terverifikasi dari file |
| Output | /cmd_vel_visual (linear.x + angular.z) | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| Safety | min_depth < 0.4 m -> velocity=0 | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| Param gerak | vx_max 0.4; steer_max 0.785 rad | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Terverifikasi dari file |
| LiDAR line segments | Split-and-Merge + RANSAC; /amr/line_segments | src/amr_visual_regression/amr_visual_regression/lidar_line_segments_node.py | Terverifikasi dari file |
| Alasan line segments | kritik dosen: dinding = entitas utuh, bukan titik diskrit | src/amr_visual_regression/amr_visual_regression/lidar_line_segments_node.py | Terverifikasi dari file |
| Hubungan failover | sumber state VISUAL_FALLBACK | src/amr_failover/amr_failover/failover_controller.py | Terverifikasi dari file |
| Status implementasi | Node ada; model .pkl perlu training; runtime perlu validasi | src/amr_visual_regression/amr_visual_regression/vr_inference_node.py | Catatan/progress (perlu validasi sumber) |
