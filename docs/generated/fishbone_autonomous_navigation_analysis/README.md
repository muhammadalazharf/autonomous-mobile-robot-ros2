# Fishbone Analysis — Autonomous Navigation AMR

_Generated: 2026-06-21 (read-only)_

## Tujuan
Analisis sebab-akibat (Ishikawa/Fishbone) faktor teknis yang mendukung **effect** utama:

> AMR berjalan otonom: global planner point-to-point dari pose robot menuju goal, dan local planner obstacle-avoidant menghindari rintangan.

## Cara membaca
- `fishbone_autonomous_navigation.md` — 12 bone (A-L) gaya systems-engineering (Requirement/Evidence/Dependency/Risk/Placement).
- `fishbone_autonomous_navigation.mmd` — diagram Mermaid (flowchart LR).
- `fishbone_bone_to_bab2_mapping.md` — peta bone -> subbab BAB II.
- `bab2_restructured_outline_from_fishbone.md` — kerangka BAB II.
- `bab2_subchapter_prompts.md` — prompt nulis tiap subbab.
- `bab2_evidence_matrix.{md,csv}` — matriks bukti.
- `autonomous_navigation_success_criteria.md` — kriteria sukses + status.
- `gap_and_missing_evidence_checklist.md` — bukti yang masih kurang.
- `fishbone_summary_for_report.md` — ringkasan siap tempel.

## Legenda status
- **[VF]** Terverifikasi dari file repo
- **[VL]** Terverifikasi dari database/log
- **[PG]** Berdasarkan catatan progress
- **[BT]** Belum terbukti (perlu bukti runtime)

> Prinsip: tidak ada klaim 'autonomous penuh' tanpa bukti runtime. Gap ditandai eksplisit.
