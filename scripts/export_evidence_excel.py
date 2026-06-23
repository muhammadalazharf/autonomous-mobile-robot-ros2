#!/usr/bin/env python3
"""
export_evidence_excel.py
========================
Ekstrak rosbag2 menjadi DATA TIME-SERIES siap-Excel (ratusan baris) untuk
4 kategori bukti laporan AMR: SENSOR, MAPPING, LOKALISASI, AUTONOMOUS.

Beda dengan analyze_sensor_bag.py (yang fokus health summary + CSV mentah),
skrip ini:
  - Menambah stream yang dibutuhkan kategori AUTONOMOUS & LOKALISASI:
      /cmd_vel (Twist)                  -> kecepatan perintah otonom
      /rtabmap/localization_pose        -> pose lokalisasi + std deviasi
      /goal_pose (PoseStamped)          -> goal yang dikirim
  - Menggabungkan SEMUA stream ke SATU file .xlsx multi-sheet
    (satu sheet per topik + sheet RINGKASAN), jika openpyxl tersedia.
  - Selalu menulis CSV per stream (universal, buka langsung di Excel).

ROBUST: peran topik ditentukan dari TIPE pesan, bukan nama hardcoded —
tetap jalan walau nama topik sedikit berbeda.

------------------------------------------------------------------
CARA PAKAI (di NUC, setelah: source /opt/ros/humble/setup.bash +
            source ~/amr_starter/install/setup.bash):

  # Autonomous (bag yang sudah ada):
  python3 scripts/export_evidence_excel.py \
      ~/amr_starter/bags/demo_run2_23jun \
      --category autonomous \
      --out ~/amr_starter/docs/evidence/autonomous

  # Sensor / Mapping / Lokalisasi (bag dari record_sensor_evidence.sh):
  python3 scripts/export_evidence_excel.py \
      ~/mapping_evidence/mapping_sensor_<TS> \
      --category sensor \
      --out ~/amr_starter/docs/evidence/sensor

Output:
  <out>/<category>_evidence.xlsx     (multi-sheet, jika openpyxl ada)
  <out>/csv/<stream>.csv             (tiap stream, ratusan baris)
  <out>/<category>_RINGKASAN.csv     (jumlah pesan, rate, durasi tiap topik)

Dependensi opsional untuk .xlsx:
  pip install openpyxl
  (tanpa openpyxl tetap menghasilkan CSV — buka langsung di Excel.)
------------------------------------------------------------------
"""
import argparse
import csv
import math
import os
import sys
from collections import defaultdict

try:
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    import rosbag2_py
except ImportError as e:
    print("[ERROR] ROS 2 belum di-source. Jalankan:")
    print("  source /opt/ros/humble/setup.bash")
    print("  source ~/amr_starter/install/setup.bash")
    print(f"  (detail: {e})")
    sys.exit(1)


# ---------- helper ----------
def yaw_from_quat(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def open_reader(bag_path):
    storage = rosbag2_py.StorageOptions(uri=bag_path, storage_id='')
    converter = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr', output_serialization_format='cdr')
    reader = rosbag2_py.SequentialReader()
    reader.open(storage, converter)
    return reader


def resolve_roles(type_map):
    """Peran tiap topik dari tipe pesan (+ petunjuk nama)."""
    roles = {}
    for name, typ in type_map.items():
        short = typ.split('/')[-1]
        low = name.lower()
        if short == 'Imu':
            roles[name] = ('accel_raw' if 'accel' in low else
                           'gyro_raw' if 'gyro' in low else 'imu')
        elif short == 'Odometry':
            roles[name] = 'vio_odom' if 'rtabmap' in low else 'wheel_odom'
        elif short == 'OdomInfo':
            roles[name] = 'vio_quality'
        elif short == 'Info':                       # rtabmap_msgs/Info
            roles[name] = 'loop_closure'
        elif short == 'LaserScan' and 'depth' not in low:
            roles[name] = 'scan'
        elif short == 'Twist':
            roles[name] = 'cmd_vel'
        elif short == 'TwistStamped':
            roles[name] = 'cmd_vel_stamped'
        elif short == 'PoseWithCovarianceStamped':
            roles[name] = 'localization'
        elif short == 'PoseStamped':
            roles[name] = 'goal' if 'goal' in low else 'pose'
        elif short == 'Int32' and 'enc' in low:
            roles[name] = 'encoder'
    return roles


# header tiap stream
HEADERS = {
    'imu':          ['t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'],
    'accel_raw':    ['t', 'ax', 'ay', 'az'],
    'gyro_raw':     ['t', 'gx', 'gy', 'gz'],
    'wheel_odom':   ['t', 'x', 'y', 'yaw', 'vx', 'wz'],
    'vio_odom':     ['t', 'x', 'y', 'yaw', 'std_x', 'std_y', 'std_yaw'],
    'vio_quality':  ['t', 'inliers', 'matches', 'features', 'lost'],
    'loop_closure': ['t', 'loop_id', 'proximity_id'],
    'scan':         ['t', 'n_valid', 'range_min', 'range_max'],
    'cmd_vel':      ['t', 'vx', 'vy', 'wz'],
    'cmd_vel_stamped': ['t', 'vx', 'vy', 'wz'],
    'localization': ['t', 'x', 'y', 'yaw', 'std_x', 'std_y'],
    'goal':         ['t', 'frame', 'x', 'y', 'yaw'],
    'pose':         ['t', 'frame', 'x', 'y', 'yaw'],
    'encoder':      ['t', 'delta_ticks'],
}


def extract_row(role, m, rel_t):
    """Kembalikan satu baris data untuk stream tertentu (atau None)."""
    if role == 'imu':
        return [f'{rel_t:.4f}', m.linear_acceleration.x, m.linear_acceleration.y,
                m.linear_acceleration.z, m.angular_velocity.x,
                m.angular_velocity.y, m.angular_velocity.z]
    if role == 'accel_raw':
        return [f'{rel_t:.4f}', m.linear_acceleration.x,
                m.linear_acceleration.y, m.linear_acceleration.z]
    if role == 'gyro_raw':
        return [f'{rel_t:.4f}', m.angular_velocity.x,
                m.angular_velocity.y, m.angular_velocity.z]
    if role == 'wheel_odom':
        p = m.pose.pose
        return [f'{rel_t:.4f}', p.position.x, p.position.y,
                yaw_from_quat(p.orientation),
                m.twist.twist.linear.x, m.twist.twist.angular.z]
    if role == 'vio_odom':
        p = m.pose.pose
        c = m.pose.covariance
        return [f'{rel_t:.4f}', p.position.x, p.position.y,
                yaw_from_quat(p.orientation),
                math.sqrt(abs(c[0])), math.sqrt(abs(c[7])), math.sqrt(abs(c[35]))]
    if role == 'localization':
        p = m.pose.pose
        c = m.pose.covariance
        return [f'{rel_t:.4f}', p.position.x, p.position.y,
                yaw_from_quat(p.orientation),
                math.sqrt(abs(c[0])), math.sqrt(abs(c[7]))]
    if role == 'vio_quality':
        return [f'{rel_t:.4f}',
                getattr(m, 'inliers', ''), getattr(m, 'matches', ''),
                getattr(m, 'features', ''), getattr(m, 'lost', '')]
    if role == 'loop_closure':
        return [f'{rel_t:.4f}',
                getattr(m, 'loop_closure_id', ''),
                getattr(m, 'proximity_detection_id', '')]
    if role == 'scan':
        valid = [r for r in m.ranges
                 if not math.isinf(r) and not math.isnan(r) and r > 0]
        return [f'{rel_t:.4f}', len(valid),
                (min(valid) if valid else ''), (max(valid) if valid else '')]
    if role in ('cmd_vel', 'cmd_vel_stamped'):
        tw = m.twist if role == 'cmd_vel_stamped' else m
        return [f'{rel_t:.4f}', tw.linear.x, tw.linear.y, tw.angular.z]
    if role in ('goal', 'pose'):
        p = m.pose
        return [f'{rel_t:.4f}', m.header.frame_id, p.position.x, p.position.y,
                yaw_from_quat(p.orientation)]
    if role == 'encoder':
        return [f'{rel_t:.4f}', getattr(m, 'data', '')]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('bag', help='Folder rosbag2 (berisi metadata.yaml)')
    ap.add_argument('--category', default='evidence',
                    choices=['sensor', 'mapping', 'lokalisasi', 'autonomous', 'evidence'],
                    help='Label kategori untuk nama output')
    ap.add_argument('--out', default=None,
                    help='Folder output (default: <bag>/export)')
    args = ap.parse_args()

    bag_path = os.path.expanduser(args.bag)
    if not os.path.exists(os.path.join(bag_path, 'metadata.yaml')):
        print(f"[ERROR] Bukan folder rosbag2 (metadata.yaml tak ada): {bag_path}")
        sys.exit(1)

    out_dir = os.path.expanduser(args.out) if args.out else os.path.join(bag_path, 'export')
    csv_dir = os.path.join(out_dir, 'csv')
    os.makedirs(csv_dir, exist_ok=True)

    reader = open_reader(bag_path)
    type_map = {t.name: t.type for t in reader.get_all_topics_and_types()}
    roles = resolve_roles(type_map)

    msg_classes = {}
    for name in roles:
        try:
            msg_classes[name] = get_message(type_map[name])
        except Exception as e:
            print(f'[WARN] tipe tak dikenal {name} ({type_map[name]}): {e}')

    # data terkumpul per stream (role) — gabung topik berperan sama
    data = defaultdict(list)        # role -> list of rows
    counts = defaultdict(int)
    first_t, last_t = {}, {}

    t0 = None
    while reader.has_next():
        topic, raw, t_ns = reader.read_next()
        t = t_ns / 1e9
        if t0 is None:
            t0 = t
        rel_t = t - t0

        counts[topic] += 1
        if topic not in first_t:
            first_t[topic] = t
        last_t[topic] = t

        role = roles.get(topic)
        if role is None or topic not in msg_classes:
            continue
        try:
            m = deserialize_message(raw, msg_classes[topic])
        except Exception:
            continue
        row = extract_row(role, m, rel_t)
        if row is not None:
            data[role].append(row)

    # ---- tulis CSV per stream ----
    written = []
    for role, rows in sorted(data.items()):
        if not rows:
            continue
        path = os.path.join(csv_dir, f'{role}.csv')
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(HEADERS.get(role, ['t', 'data']))
            w.writerows(rows)
        written.append((role, len(rows), path))

    # ---- ringkasan kesehatan tiap topik ----
    summary_rows = []
    for topic in sorted(counts):
        n = counts[topic]
        dur = last_t[topic] - first_t[topic]
        rate = (n - 1) / dur if dur > 0 else 0.0
        summary_rows.append([topic, type_map.get(topic, ''), n,
                             f'{dur:.2f}', f'{rate:.2f}', roles.get(topic, '-')])
    summary_path = os.path.join(out_dir, f'{args.category}_RINGKASAN.csv')
    with open(summary_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['topik', 'tipe', 'jumlah_pesan', 'durasi_s', 'rate_hz', 'stream'])
        w.writerows(summary_rows)

    # ---- gabung ke .xlsx multi-sheet (jika openpyxl ada) ----
    xlsx_status = ''
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'RINGKASAN'
        ws.append(['topik', 'tipe', 'jumlah_pesan', 'durasi_s', 'rate_hz', 'stream'])
        for r in summary_rows:
            ws.append(r)
        for role, rows, _ in written:
            sheet = wb.create_sheet(title=role[:31])  # Excel batas 31 char
            sheet.append(HEADERS.get(role, ['t', 'data']))
            for r in rows:
                sheet.append(r)
        xlsx_path = os.path.join(out_dir, f'{args.category}_evidence.xlsx')
        wb.save(xlsx_path)
        xlsx_status = f'  .xlsx : {xlsx_path}'
    except ImportError:
        xlsx_status = ('  .xlsx : DILEWATI (openpyxl tak terpasang). '
                       'CSV sudah siap buka di Excel.\n'
                       '          Untuk .xlsx gabungan: pip install openpyxl')

    # ---- laporan ----
    print('=' * 60)
    print(f' EXPORT BUKTI [{args.category.upper()}] — {bag_path}')
    print('=' * 60)
    print(f' Output: {out_dir}')
    print(f' Ringkasan: {summary_path}')
    print(xlsx_status)
    print(' Stream CSV (ratusan baris time-series):')
    if written:
        for role, n, path in written:
            print(f'   - {role:16s} {n:6d} baris  -> csv/{role}.csv')
    else:
        print('   (tidak ada stream dikenal di bag ini — cek isi bag)')
    print('=' * 60)


if __name__ == '__main__':
    main()
