# 06 — Panduan Sistem Keselamatan (Failover)

Sistem keselamatan yang memastikan robot berhenti dengan aman ketika terjadi
kegagalan sensor, hilangnya koneksi kendali, atau kondisi tak terduga lainnya.

---

## 1. Mengapa Sistem Ini Diperlukan

Robot seberat beberapa kilogram yang bergerak tanpa kendali dapat merusak
peralatan maupun melukai orang. Kegagalan yang paling berbahaya adalah kegagalan
yang **tidak menimbulkan pesan error** — sistem tampak normal, padahal kendali
sudah terputus.

**Contoh nyata pada proyek ini:** ketika koneksi Bluetooth joystick terputus,
`joy_node` **tetap** mengulang perintah terakhir karena parameter
`autorepeat_rate`. Akibatnya robot terus melaju dengan perintah lama, sementara
pengendali sudah tidak terhubung sama sekali.

---

## 2. Lapisan Keselamatan

Sistem menerapkan beberapa lapisan pengaman yang saling melengkapi:

```
┌─────────────────────────────────────────────┐
│  Lapisan 1 — Deadman Switch (R1)            │  paling cepat: dilepas → berhenti
├─────────────────────────────────────────────┤
│  Lapisan 2 — Watchdog (/joy, /cmd_vel)      │  data hilang → berhenti
├─────────────────────────────────────────────┤
│  Lapisan 3 — Arbiter Failover               │  memilih sumber kendali
├─────────────────────────────────────────────┤
│  Lapisan 4 — Slew-Rate Limiter              │  mencegah lonjakan arus
└─────────────────────────────────────────────┘
```

---

## 3. Lapisan 1 — Deadman Switch

Tombol **R1** pada joystick harus **ditahan terus-menerus** agar robot mau
bergerak. Begitu dilepas, motor langsung berhenti.

```
DEADMAN_BTN = 5      # tombol R1 pada PS4/PS5
AXIS_VEL    = 1      # stik kiri, sumbu atas-bawah
AXIS_STEER  = 3      # stik kanan, sumbu kiri-kanan
```

**Alasan perancangan:** bila pengendali terjatuh atau operator melepaskan
genggaman karena panik, robot berhenti seketika. Ini pengaman paling cepat
karena tidak bergantung pada timer atau perangkat lunak lain.

---

## 4. Lapisan 2 — Watchdog

Watchdog memantau apakah data kendali masih mengalir. Bila terhenti melebihi
batas waktu, motor dihentikan.

| Watchdog | Topic dipantau | Batas waktu | Tindakan |
|---|---|---|---|
| Joystick | `/joy` | 500 ms | Hentikan motor, keluar dari mode manual |
| Autonomous | `/cmd_vel` | 500 ms | Hentikan motor |

```cpp
if (manual_override_) {
  auto joy_elapsed_ms = (now - last_joy_time_).nanoseconds() / 1000000;
  if (joy_elapsed_ms > joy_timeout_ms) {
    manual_override_ = false;
    last_velocity_   = 0;
    send_command(0, STEER_TRIM);        // hentikan motor
    RCLCPP_WARN(get_logger(), "[WATCHDOG] /joy timeout");
  }
}
```

### ⚠️ `autorepeat_rate` harus 0

```python
# amr_bringup/config/joy_params.yaml
autorepeat_rate: 0.0    # WAJIB 0 — jangan diubah
```

**Alasan:** bila lebih dari 0, `joy_node` akan terus menerbitkan pesan terakhir
meskipun perangkat sudah terputus. Akibatnya watchdog **tidak pernah mendeteksi**
hilangnya data, dan robot terus bergerak tanpa kendali.

Ini pelajaran penting: sebuah mekanisme pengaman dapat dilumpuhkan oleh
konfigurasi lain yang tampak tidak berhubungan.

---

## 5. Lapisan 3 — Arbiter Failover

Package `amr_failover` menentukan **sumber perintah gerak mana** yang diteruskan
ke motor pada satu waktu.

### Sumber kendali menurut prioritas

| Prioritas | Sumber | Kondisi aktif |
|---|---|---|
| 1 (tertinggi) | **Emergency Stop** | Kondisi darurat — mengabaikan semua sumber lain |
| 2 | **Joystick** | R1 ditahan — operator mengambil alih |
| 3 | **SLAM / Nav2** | Mode otonom, lokalisasi sehat |
| 4 (terendah) | **Visual Regression** | Cadangan bila lokalisasi SLAM gagal |

### Prinsip perancangan

- **Operator selalu dapat mengambil alih.** Menekan R1 kapan pun akan langsung
  memutus kendali otonom.
- **Kegagalan mengarah ke berhenti (*fail-safe*).** Bila sumber kendali tidak
  jelas atau data hilang, tindakan bawaannya adalah berhenti — bukan melanjutkan.
- **Degradasi bertahap.** Bila lokalisasi SLAM gagal, sistem beralih ke navigasi
  visual cadangan alih-alih berhenti total.

```bash
ros2 launch amr_failover failover.launch.py
```

---

## 6. Lapisan 4 — Slew-Rate Limiter

Membatasi seberapa cepat nilai PWM boleh berubah antar-pesan.

```cpp
#define MAX_PWM_STEP 250

int apply_slew(int target) {
  int delta = target - last_velocity_;
  if (delta >  MAX_PWM_STEP) delta =  MAX_PWM_STEP;
  if (delta < -MAX_PWM_STEP) delta = -MAX_PWM_STEP;
  last_velocity_ += delta;
  return last_velocity_;
}
```

**Tujuan:** mencegah *motor plugging* — lonjakan arus ketika motor yang masih
berputar tiba-tiba diberi tegangan berlawanan arah. Dengan pembatas ini,
transisi maju → mundur melewati nol secara bertahap:

```
V: 4000 → 3750 → 3500 → … → 250 → 0 → -250 → … → -4000
```

**Hasil sebenarnya:** pembatas ini bekerja sesuai rancangan (terbukti dari log),
namun **gangguan koneksi masih terjadi**. Transien EMI ternyata tetap cukup kuat
meskipun perubahan PWM sudah dilandaikan. Penyelesaian tuntas memerlukan
perbaikan di sisi perangkat keras — lihat
[03_HARDWARE_GUIDE.md](03_HARDWARE_GUIDE.md) Bagian 6.

---

## 7. Prosedur Darurat

| Situasi | Tindakan |
|---|---|
| Robot bergerak tak terkendali | Lepas R1; bila gagal, **cabut catu daya motor** |
| Robot menuju rintangan | Tekan R1 dan belokkan menjauh (ambil alih manual) |
| NUC mati mendadak | Motor berhenti sendiri (tidak ada perintah masuk) |
| Bluetooth terputus | Watchdog menghentikan motor dalam 500 ms |

### Menghentikan seluruh sistem

```bash
pkill -f "ros2 launch"

# Bila perlu, hentikan node spesifik:
pkill -f stm32_bridge
```

---

## 8. Menguji Sistem Keselamatan

Fitur keselamatan **harus diuji dalam kondisi gagal yang sesungguhnya**, bukan
sekadar diasumsikan bekerja.

| Pengujian | Cara | Hasil yang diharapkan |
|---|---|---|
| Deadman switch | Jalankan robot, lepas R1 | Berhenti seketika |
| Watchdog joystick | Matikan Bluetooth saat robot bergerak | Berhenti dalam 500 ms |
| Watchdog cmd_vel | Hentikan Nav2 saat navigasi berjalan | Berhenti dalam 500 ms |
| Slew limiter | Banting stik maju → mundur, amati log | PWM berubah bertahap, bukan melompat |
| Pengambilalihan | Tekan R1 saat mode otonom | Kendali berpindah ke manual |

> **Catatan dari pengalaman:** watchdog pernah dinyatakan "sudah dipasang"
> padahal tidak berfungsi, karena tidak pernah diuji dengan benar-benar memutus
> Bluetooth. Selalu uji dengan mensimulasikan kegagalan yang nyata.

---

## 9. Keterbatasan yang Diketahui

Dicatat secara terbuka agar tidak menimbulkan rasa aman yang keliru:

1. **Tidak ada tombol emergency stop fisik.** Saat ini penghentian bergantung
   pada perangkat lunak dan joystick. Penambahan tombol E-stop berbasis relai
   yang memutus daya motor secara langsung sangat disarankan.
2. **Gangguan EMI belum tuntas.** Mitigasi perangkat lunak mengurangi, tetapi
   tidak menghilangkan, gangguan saat motor mundur.
3. **Watchdog bergantung pada aliran data.** Bila sebuah node "menggantung"
   (*hang*) namun tetap menerbitkan data, watchdog tidak akan mendeteksinya.

---

**Lanjut:** [07_TROUBLESHOOTING.md](07_TROUBLESHOOTING.md) untuk pemecahan
masalah.
