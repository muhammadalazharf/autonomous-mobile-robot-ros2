# PROTOKOL KOLABORASI — AMR (Tim: Al Azhar & Mervi)

**Dibuat:** 8 Juni 2026
**Status:** 🔒 ATURAN MUTLAK — wajib dipatuhi setiap sesi kerja, oleh siapapun (Claude Code / manusia) yang menyentuh workspace NUC

> Dokumen ini adalah SOP anti-tabrakan konfigurasi antara progress
> Al Azhar (`muhammadalazharf/autonomous-mobile-robot-ros2`,
> branch `claude/brave-newton-6zvS4`) dan Mervi
> (`Mervs111/autonomous-mobile-robot-ros2`). Tujuannya: mencegah
> NUC mengalami error tak diketahui akibat tumpang-tindih config dari
> dua sumber yang berbeda tanpa koordinasi.

---

## ATURAN MUTLAK (urut prioritas)

### 1️⃣ SELALU CEK REPO MERVI DULU SEBELUM EKSEKUSI APAPUN
Sebelum melakukan perubahan config/parameter/launch file apapun di
workspace lokal NUC, **WAJIB** cek dulu:
```bash
git clone --depth 1 https://github.com/Mervs111/autonomous-mobile-robot-ros2.git /tmp/mervi_repo
cd /tmp/mervi_repo && git log --oneline -10
```
Bandingkan dengan progress kita. Tujuan: tahu apakah Mervi sudah
mengubah sesuatu yang relevan **lebih dulu**, supaya kita tidak
menimpa/bentrok tanpa sadar.

> **Baseline terakhir dicek (8 Juni 2026):**
> commit `b58d6fe` — "docs: integrasikan handover 7 Juni 2026 sebagai
> dokumen resmi" (2026-06-08 00:49:57 +0700)

### 2️⃣ KOLABORASI — BUKAN OVERWRITE SEPIHAK
Kalau ditemukan Mervi sudah update config/fix yang relevan dengan apa
yang sedang kita kerjakan:
- **JANGAN langsung timpa** dengan versi kita
- Diskusikan dulu dengan user (Al Azhar) — beri tahu apa yang Mervi
  sudah lakukan, apa bedanya dengan rencana kita, dan minta keputusan
  mana yang dipakai / digabung
- Tujuan akhir: **satu sumber kebenaran** (`origin/claude/brave-newton-6zvS4`
  di NUC) yang konsisten untuk kedua belah pihak

### 3️⃣ CATAT SETIAP KALI KITA LEBIH DULU UPDATE
Kalau progress kita **mendahului** Mervi (kita update config/fix duluan),
WAJIB dicatat di log internal (lihat Bagian "LOG UPDATE KITA" di bawah)
agar:
- Saat user minta dibuatkan **handover untuk Mervi**, materinya sudah siap
- Tidak ada progress kita yang "hilang" dari radar tim

### 4️⃣ REPO MERVI = READ-ONLY, MONITORING SAJA
- **JANGAN PERNAH** push/edit/PR ke `Mervs111/autonomous-mobile-robot-ros2`
- Clone ke `/tmp/` untuk dibaca, lalu **hapus** setelah selesai cek
  (`rm -rf /tmp/mervi_repo`) — jangan biarkan menumpuk
- Fungsinya murni untuk **monitoring progress harian** Mervi, supaya
  kita tahu arah perubahan dia tanpa perlu nunggu dia lapor manual

---

## WORKFLOW STANDAR SEBELUM SETIAP SESI KERJA

```
┌─────────────────────────────────────────────────────────┐
│ 1. Clone/fetch repo Mervi → cek commit log terbaru       │
│    (bandingkan timestamp dgn baseline terakhir di sini)  │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        │                                   │
   Mervi ADA update baru             Mervi TIDAK ada update
   relevan dgn rencana kita          relevan
        │                                   │
        ▼                                   ▼
┌──────────────────────┐         ┌─────────────────────┐
│ STOP. Laporkan ke    │         │ Lanjut eksekusi      │
│ user: apa yg Mervi   │         │ rencana kita seperti │
│ ubah, beda dgn       │         │ biasa.               │
│ rencana kita, minta  │         │                      │
│ keputusan user.      │         │ Update baseline      │
└──────────────────────┘         │ commit di dok ini    │
                                  │ setelah selesai.     │
                                  └─────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Eksekusi perubahan di branch claude/brave-newton-6zvS4│
│ 3. Catat di "LOG UPDATE KITA" kalau kita mendahului Mervi│
│ 4. Update baseline commit Mervi di dokumen ini           │
└─────────────────────────────────────────────────────────┘
```

---

## LOG UPDATE KITA (untuk bahan handover ke Mervi nanti)

> Diisi setiap kali kita melakukan update config/fix yang BELUM ada
> di repo Mervi pada saat itu — supaya gampang disusun jadi handover
> ketika user minta.

| Tanggal | Update kita | Status di repo Mervi saat itu | Commit kita |
|---|---|---|---|
| 8 Juni 2026 | 7 fix introspeksi VIO/loop closure (`Odom/MaxVariance`→0.05, `Vis/MinInliers`→8, `Odom/ResetCountdown`→5, `Kp/MaxFeatures`/`Kp/DetectorStrategy` baru, `Rtabmap/DetectionRate`→2.0, `cloud_max_depth`→5.0, `scripts/fresh_mapping.sh`) | Repo Mervi masih pakai nilai LAMA yang sama persis dgn bug kita (`MaxVariance:0.01`, `MinInliers:2`, `ResetCountdown:1`, `STMSize:30`, `cloud_max_depth:4.0`, tanpa `Kp/*`) — belum fix | `e850fca` |
| 8 Juni 2026 | Fix audit param `Odom/MaxVariance` dipindah dari node `rtabmap` → `rgbd_odometry` (bug salah node, silently ignored) | Mervi punya commit serupa `8a993f0` di repo dia (riwayat sempat sinkron/bercabang — SHA `3d69411` identik di kedua repo) | `8a993f0` (di branch kita, hasil audit independen) |
| 8 Juni 2026 | Merge param `Mem/STMSize: 30→10`, `Grid/NoiseFilteringRadius: 0.5` dari sesi NUC 7 Juni (terbukti VIO stabil) | Repo Mervi masih `Mem/STMSize: 30` — belum merge nilai yang terbukti dari sesi 7 Juni | `702021b` |

**Yang SUDAH ada sama persis di kedua repo (tidak perlu di-handover, sudah konvergen):**
- Exposure tuning RealSense (`rgb_camera.gain: 64`, `exposure: 156`, `temporal_filter`, `spatial_filter`) — identik di `sensors_launch.py` kedua repo
- Commit `3d69411` "Fix VIO tracking for low-texture lab environment" — SHA identik, riwayat development sempat sinkron

---

## CARA UPDATE BASELINE SETELAH CEK REPO MERVI

Setiap kali selesai cek repo Mervi, update baris ini dengan commit SHA
+ tanggal terbaru yang ditemukan:

```
Baseline terakhir dicek: [TANGGAL] — commit [SHA] "[pesan commit]"
```

Supaya sesi berikutnya tahu sampai mana progress Mervi yang sudah
"diketahui" dan tidak perlu cek ulang dari nol kalau belum ada
perubahan baru.

---

## CATATAN PENTING LAIN

- Kedua repo memakai **branch utama yang berbeda**: kita di
  `claude/brave-newton-6zvS4`, Mervi kemungkinan di `main`. Saat
  membandingkan, selalu sebutkan branch eksplisit.
- Riwayat development kedua tim **sempat bercabang lalu konvergen**
  (bukti: SHA `3d69411` identik). Ini wajar karena base awal project
  sama — tapi artinya **konflik konfigurasi sangat mungkin terjadi**
  kalau tidak dikoordinasikan, karena keduanya mengedit file yang
  sama (`rtabmap_mapping.launch.py`, `rtabmap_mapping.yaml`,
  `sensors_launch.py`).
