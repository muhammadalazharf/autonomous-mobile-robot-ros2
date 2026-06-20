# 08 — Inventaris Database RTAB-Map

PENTING: file .db berada di `~/maps/` pada NUC, TIDAK ada di repo. Angka di bawah dari analisis laporan (.docx) + rtabmap-info. Untuk verifikasi ulang, jalankan `rtabmap-info <db>` di NUC.

| nama_db | path | status | nodes | keyframe | link | loop_closure | durasi | jarak_m | bbox_m2 | catatan | sumber |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lab_demo_18jun.db | ~/maps/ (NUC, tidak di repo) | valid (peta acuan demo) | 1846 | 448 | 1220 | 125 global + 648 proximity | 1012 s (~17 min) | 28.9 | - | PETA ACUAN; bersih, single session; layak bukti utama | Catatan/progress (perlu validasi sumber) (rtabmap-info; .db di NUC) |
| mapping_20260611_MASTER.db | ~/maps/ (NUC) | valid (terpadat agregat) | 1526 | - | 987 | 754 | - | - | - | Peta terpadat dari analisis 24 DB; layak bukti | Catatan/progress (perlu validasi sumber) |
| lab_vio_1620.db | ~/maps/ (NUC) | valid (eksploratif) | 758 | 316 | 760 | 130 | 13m23s | 43.511 | 45.706 | Lintasan terpanjang; LC relatif sedikit | Catatan/progress (perlu validasi sumber) |
| lab_remap3_220017.db | ~/maps/ (NUC) | valid | - | - | tertinggi | tertinggi | - | - | 27.3 | Link & LC tertinggi; eksplorasi agresif | Catatan/progress (perlu validasi sumber) |
| test.db | ~/maps/ (NUC) | valid (near-static) | - | - | 683 | 682 | - | 0.236 | 0.0 | Near-static (LC/link ~1.0); BUKAN bukti utama | Catatan/progress (perlu validasi sumber) |
| lab_final_malam_ini.db | ~/maps/ (NUC) | valid (near-static) | - | - | 215 | 215 | - | 0.167 | - | Near-static; bukan bukti utama | Catatan/progress (perlu validasi sumber) |
| lab_remap3_212606.db | ~/maps/ (NUC) | valid (anomali) | 884 | - | - | - | - | 1.941 | 0.005 | Anomali: banyak node gerak minim | Catatan/progress (perlu validasi sumber) |
