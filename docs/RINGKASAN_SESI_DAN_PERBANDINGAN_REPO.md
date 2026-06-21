# Ringkasan Sesi & Perbandingan Repo — Proyek AMR

**Tanggal ringkasan:** 21 Juni 2026
**Repo kamu:** `muhammadalazharf/autonomous-mobile-robot-ros2` — branch `claude/zealous-darwin-6l4bs5`
**Repo Mervi:** `Mervs111/autonomous-mobile-robot-ros2` — branch `main`

---

## BAGIAN 1 — Ringkasan Pekerjaan Sesi Ini (kronologis)

| # | Aktivitas | Hasil / Commit |
|---|-----------|----------------|
| 1 | Cek repo Mervi untuk handover 19 Juni | Ditemukan handover Nav2 BERHASIL (8 gerbang) `292f051` |
| 2 | Adopsi 4 fix Nav2 Mervi ke branch kamu | `76b1e99` (spin, BT XML absolut, matikan depth_scan, hapus remap cmd_vel) |
| 3 | Dokumen root cause analysis Nav2 + lokalisasi | `052e5d7` |
| 4 | Cek lagi repo Mervi → temukan fix steering `3d16e7d` (bench test) | Diagnosis awal (negasi velocity) DIBATALKAN |
| 5 | Adopsi fix steering Mervi (negasi `steer_rad`, bukan velocity) | `fec1ee5` |
| 6 | Laporan teknis final | `5fc2fd2` `LAPORAN_FINAL_PROYEK_AMR.md` |
| 7 | Suplemen progress untuk .docx | `3fa2e0a` `SUPLEMEN_PROGRESS_LAPORAN_AMR.md` |
| 8 | Briefing revisi laporan untuk Claude chat | `1a0614a` `BRIEFING_REVISI_LAPORAN_UNTUK_CLAUDE_CHAT.md` |
| 9 | Bank data + generator kerangka laporan | `252dbfe` `laporan_data_amr.py` + `laporan_scaffold.md` |
| 10 | Paket data raw / evidence package (57 file + ZIP) | `9df05c7` `docs/generated/raw_amr_evidence_package/` |
| 11 | Fishbone analysis autonomous navigation (12 file + ZIP) | `0c5296f` `docs/generated/fishbone_autonomous_navigation_analysis/` |

**Tema sesi:** dari *adopsi fix teknis Mervi* (Nav2 + steering) → *konsolidasi seluruh
progress menjadi paket dokumentasi & bukti* untuk penyusunan laporan final PjBL.

**Pelajaran kunci sesi:** selalu cek repo Mervi sebelum eksekusi — diagnosis steering
saya (negasi velocity) keliru; bench test Mervi membuktikan yang salah hanya tanda
kemudi. Adopsi fix teruji > teori.

---

## BAGIAN 2 — State Repo Kamu (branch `claude/zealous-darwin-6l4bs5`)

### Commit sesi ini (terbaru → lama)
```
0c5296f docs: fishbone analysis autonomous navigation -> kerangka BAB II
9df05c7 docs: paket data raw / bukti teknis AMR (evidence package)
252dbfe docs: bank data terkonsolidasi + generator kerangka laporan AMR
1a0614a docs: briefing self-contained untuk revisi laporan via Claude chat
3fa2e0a docs: suplemen progress untuk laporan final AMR
5fc2fd2 docs: laporan teknis final proyek AMR
fec1ee5 fix(bridge): negasi steer_rad - arah kemudi autonomous terbalik
052e5d7 docs: root cause analysis lengkap Nav2 + RTAB-Map lokalisasi
76b1e99 fix(nav2): apply 4 fix Mervi handover 19-Jun
9be5902 fix(rtabmap): samakan ambang localization dengan mapping (sesi sebelumnya)
99373ff fix(nav2): hapus plugin_lib_names + fix format plugin (sesi sebelumnya)
```

### Artefak dokumentasi (folder `docs/`)
- `LAPORAN_FINAL_PROYEK_AMR.md` — rekap teknis
- `SUPLEMEN_PROGRESS_LAPORAN_AMR.md` — suplemen untuk .docx
- `BRIEFING_REVISI_LAPORAN_UNTUK_CLAUDE_CHAT.md` — prompt revisi
- `laporan_data_amr.py` + `laporan_scaffold.md` — bank data + generator
- `root_cause_analysis_nav_lokalisasi.md`
- `generated/raw_amr_evidence_package/` (57 file) + ZIP
- `generated/fishbone_autonomous_navigation_analysis/` (12 file) + ZIP
- Laporan korelasi matkul (Metode Numerik, PCD, Sistem Kontrol Proses)

### Karakter repo kamu
**Kuat di dokumentasi & analisis** — fix teknis inti (Nav2, steering, lokalisasi)
selaras dengan Mervi, ditambah paket bukti/laporan yang TIDAK ada di repo Mervi.

---

## BAGIAN 3 — State Repo Mervi (branch `main`)

### Commit Mervi (terbaru → lama, ringkas)
```
75c86f3 (21 Jun) fix(nav2): filter LiDAR self-scan + smaller inflation
f7576ff (20 Jun) docs+feat: handover 21 Juni + bringup tmux satu-klik
a91d937 (20 Jun) feat: safety cap + minimal BT + helper scripts (perbaikan overshoot)
bfba43d (20 Jun) fix(nav2): all-odom navigation, smaller inflation, smaller radius
033212a (20 Jun) fix(scripts): topik localization_pose tanpa prefix /rtabmap
e134319 (20 Jun) fix(localization): loosen LoopThr 0.11->0.05, MinInliers 10->6, rate 2Hz
a9b5fcf (20 Jun) feat(scripts): log_localization.py - data lokalisasi real-time
3d16e7d (20 Jun) fix(bridge): flip steering sign (SUDAH diadopsi ke repo kamu)
fb6e2ae (20 Jun) docs: temuan heading/steering flip
0eee33d (20 Jun) docs: handover re-mapping 18 Juni (lab_demo_18jun.db)
292f051 (19 Jun) docs: handover Nav2 autonomous BERHASIL (8 fix)
... (9 gerbang Nav2 18-19 Jun, lokalisasi 17 Jun, kalibrasi 14 Jun, Plan A/B 12-13 Jun)
```

### Karakter repo Mervi
**Kuat di runtime & integrasi lapangan** — Mervi terus iterasi di NUC: filter
self-scan LiDAR, navigasi all-odom, safety cap anti-overshoot, bringup tmux satu-klik,
script logging lokalisasi.

---

## BAGIAN 4 — Perbandingan & Sinkronisasi

### Yang SUDAH selaras (sama di kedua repo)
| Fix | Repo kamu | Repo Mervi |
|-----|-----------|------------|
| Hapus plugin_lib_names | `99373ff` | `f423a03` |
| Format plugin :: vs / | `99373ff` | `d39c531`/`52b127d` |
| Behavior spin | `76b1e99` | `a1c0b66` |
| BT XML path absolut | `76b1e99` | `47dd6a0` |
| Matikan depth_scan costmap | `76b1e99` | `bd66131` |
| Hapus remap cmd_vel | `76b1e99` | `a90a3d8` |
| Ambang localization = mapping | `9be5902` (LoopThr 0.05, MinInliers 8) | `e134319` (LoopThr 0.05, MinInliers 6) |
| Flip steering sign | `fec1ee5` | `3d16e7d` |

### Yang HANYA ada di repo Mervi (BELUM di repo kamu) — perlu dipertimbangkan
| Commit | Isi | Relevansi |
|--------|-----|-----------|
| `75c86f3` | Filter LiDAR self-scan + inflation lebih kecil | Tinggi — hindari obstacle palsu dari badan robot |
| `bfba43d` | All-odom navigation + radius lebih kecil | Tinggi — mode navigasi alternatif |
| `a91d937` | Safety cap + minimal BT + helper scripts (anti-overshoot) | Tinggi — perbaikan overshoot |
| `f7576ff` | Bringup tmux satu-klik + handover 21 Juni | Sedang — kemudahan operasi |
| `a9b5fcf`/`033212a` | `log_localization.py` + fix topik localization_pose | Tinggi — **bisa jadi BUKTI runtime lokalisasi** yang selama ini jadi gap! |

> Catatan: `MinInliers` beda tipis — kamu 8, Mervi 6 (Mervi lebih longgar). Keduanya
> < 10 (fix loop rejection). Pilih sesuai hasil tes di NUC.

### Yang HANYA ada di repo kamu (BELUM di repo Mervi)
- Seluruh paket dokumentasi/analisis: `LAPORAN_FINAL`, `SUPLEMEN`, `BRIEFING`,
  `laporan_data_amr.py`, evidence package (57 file), fishbone analysis (12 file),
  laporan korelasi matkul.

---

## BAGIAN 5 — Rekomendasi Tindak Lanjut

1. **Sinkron dari Mervi (prioritas tinggi):**
   - `a9b5fcf` `log_localization.py` → langsung memberi **bukti runtime lokalisasi**
     (gap utama di fishbone Bone G & evidence package).
   - `75c86f3` filter LiDAR self-scan → cegah obstacle palsu badan robot (Bone I).
   - `a91d937` safety cap anti-overshoot → keandalan navigasi (Bone I/K).
2. **Verifikasi di NUC:** steering fix (`fec1ee5`) — pastikan belok kiri = kiri.
3. **Rekam bukti runtime** sesuai `gap_and_missing_evidence_checklist.md` (video
   navigasi, log /cmd_vel, screenshot path/costmap, log lokalisasi).
4. **Pertimbangkan:** apakah branch kamu mau merge perkembangan runtime Mervi 20-21
   Juni, atau tetap fokus dokumentasi (repo kamu = "dokumentasi", repo Mervi = "runtime").

---

## BAGIAN 6 — Status Akhir Proyek (jujur)

| Subsistem | Status | Bukti |
|-----------|--------|-------|
| Hardware/aktuator | Berfungsi | URDF, bridge (file) |
| Sensor (LiDAR/RGB-D/IMU/encoder) | Terbaca | config (file) + scan data |
| Odometry + kalibrasi | Tercapai | PPR 3858, R²=0.998 (file+data) |
| Mapping RTAB-Map | Tercapai | lab_demo_18jun.db (di NUC) |
| Localization | Lock tervalidasi; **bukti runtime** kini bisa via `log_localization.py` Mervi | progress |
| Nav2 global+local planner | Bringup sukses; robot otonom (demo) | progress; bukti runtime perlu video/log |
| Eksekusi STM32 | Berfungsi | bridge (file) |
| Safety/failover | Diimplementasi; demo dibypass | file |

**Inti:** pipeline autonomous tersambung penuh & terbukti menggerakkan robot (per
handover tim); yang tersisa = melengkapi **bukti runtime** untuk laporan final.
