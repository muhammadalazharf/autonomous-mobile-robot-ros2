# 07 — Odometry & Kalibrasi

Data uji 5 jarak (odom vs meteran) + parameter & hasil regresi.

| percobaan | jarak_aktual_cm | jarak_odom_m | odom_cm | rasio_real_per_odom | catatan |
|---|---|---|---|---|---|
| 1 | 22 | 0.5 | 50 | 0.44 | uji odom-vs-meteran 14-Jun |
| 2 | 41 | 1.0 | 100 | 0.41 | uji odom-vs-meteran 14-Jun |
| 3 | 61 | 1.5 | 150 | 0.4067 | uji odom-vs-meteran 14-Jun |
| 4 | 81 | 2.0 | 200 | 0.405 | uji odom-vs-meteran 14-Jun |
| 5 | 96 | 2.5 | 250 | 0.384 | uji odom-vs-meteran 14-Jun |


## Parameter & Hasil Kalibrasi (terverifikasi dari amr_full.launch.py)

| Item | Nilai |
|---|---|
| Sumber odometry | Encoder PG45 (model bicycle Ackermann) |
| Wheel radius | 0.0775 m |
| Wheelbase | 0.500 m |
| PPR awal (teoretis) | 1496 |
| PPR hasil kalibrasi | 3858 |
| dist_per_tick | 0.3255 -> 0.1262 mm |
| Faktor over-report | 2.58x |
| Fit regresi | real = 0.3877 x odom (proporsional) |
| R^2 | 0.998 |

## Rumus
- dist_per_tick = 2*pi*wheel_radius / PPR
- vx = delta_dist / dt
- delta_theta = (vx / wheelbase) * tan(steering) * dt
- x += delta_dist*cos(theta+dtheta/2); y += delta_dist*sin(theta+dtheta/2)

## Kesimpulan
Odometry awal over-report 2.58x; setelah koreksi PPR ke 3858, pembacaan konsisten terhadap jarak nyata (R^2=0.998). Mendukung kompetensi Metode Numerik (regresi least-squares).

## Data eksperimen tambahan (upload, di luar repo)
- data_euler_odom.csv (442 baris; t,V_target,V_smooth,V_euler,galat) -> analisis prediksi Euler vs /odom aktual
- jalan_maju.zip (8 CSV odom uji jarak 2026-06-14)
- Hasil_Test_ODOMETRI_VS_REALTIME.docx
- Lokasi: `/root/.claude/uploads/1c5c71b5-862a-5513-8e43-27a9bf37e720` (status: Data eksperimen (upload, di luar repo))

