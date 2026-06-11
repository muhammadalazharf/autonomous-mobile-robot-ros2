#!/usr/bin/env python3
"""
analyze_sensor_bag.py
=====================
Ekstrak rosbag2 hasil record_sensor_evidence.sh menjadi CSV + ringkasan
statistik siap pakai untuk laporan (Metode Numerik & DCS SCADA).

Usage (di NUC, setelah source ROS 2 + workspace):
  python3 scripts/analyze_sensor_bag.py ~/mapping_evidence/run1_20260612_090000

Output (di dalam folder bag, subfolder analysis/):
  summary.txt        - kesehatan tiap topik: jumlah pesan, rate rata-rata,
                       gap maksimum (bukti "semua sensor aman")
  imu.csv            - t, ax, ay, az, gx, gy, gz       (IMU merge /imu/data)
  accel_raw.csv      - t, ax, ay, az                   (accel mentah D455)
  gyro_raw.csv       - t, gx, gy, gz                   (gyro mentah D455)
  vio_odom.csv       - t, x, y, yaw, std_x, std_y, std_yaw (pose VIO)
  vio_quality.csv    - t, inliers, matches, features, lost (kualitas tracking)
  loop_closure.csv   - t, loop_closure_id, proximity_id  (accepted bila >0)
  encoder.csv        - t, delta_ticks
  scan_stats.csv     - t, n_valid_points, range_min, range_max (LiDAR)

ROBUST: peran (role) tiap topik ditentukan dari TIPE pesan, bukan nama
topik hardcoded — jadi tetap jalan walau nama topik sedikit berbeda.

Catatan korelasi laporan:
  - Metode Numerik : integrasi odometri (Euler), kovarians/deviasi standar
    pose, RANSAC inliers, konvergensi ICP -> plot dari vio_*.csv
  - DCS SCADA      : pipeline akuisisi -> monitoring -> historian (bag) ->
    analisis; summary.txt = laporan kesehatan telemetri tiap "field device"
"""
import csv
import math
import os
import sys
from collections import defaultdict

from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py


def open_reader(bag_path):
    storage = rosbag2_py.StorageOptions(uri=bag_path, storage_id='')
    converter = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr', output_serialization_format='cdr')
    reader = rosbag2_py.SequentialReader()
    reader.open(storage, converter)
    return reader


def yaw_from_quat(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def g(msg, *paths, default=''):
    """Ambil atribut pertama yang ada; dukung jalur bertitik (mis. 'reg.inliers')."""
    for p in paths:
        obj = msg
        ok = True
        for part in p.split('.'):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                ok = False
                break
        if ok:
            return obj
    return default


def resolve_roles(topics_types):
    """Tentukan peran tiap topik dari tipe pesan + petunjuk nama."""
    roles = {}
    for name, typ in topics_types.items():
        short = typ.split('/')[-1]
        low = name.lower()
        if short == 'Imu':
            if 'accel' in low:
                roles[name] = 'accel_raw'
            elif 'gyro' in low:
                roles[name] = 'gyro_raw'
            else:
                roles[name] = 'imu'
        elif short == 'Odometry':
            roles[name] = 'vio_odom' if 'rtabmap' in low else 'wheel_odom'
        elif short == 'OdomInfo':
            roles[name] = 'vio_quality'
        elif short == 'Info':            # rtabmap_msgs/Info
            roles[name] = 'loop_closure'
        elif short == 'Int32' and 'enc' in low:
            roles[name] = 'encoder'
        elif short == 'LaserScan' and 'depth' not in low:
            roles[name] = 'scan'
    return roles


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    bag_path = os.path.expanduser(sys.argv[1])
    out_dir = os.path.join(bag_path, 'analysis')
    os.makedirs(out_dir, exist_ok=True)

    reader = open_reader(bag_path)
    type_map = {t.name: t.type for t in reader.get_all_topics_and_types()}
    roles = resolve_roles(type_map)
    msg_classes = {}
    for name in roles:
        try:
            msg_classes[name] = get_message(type_map[name])
        except Exception as e:
            print(f'[WARN] tipe tak dikenal {name} ({type_map[name]}): {e}')

    counts = defaultdict(int)
    first_t, last_t = {}, {}
    max_gap = defaultdict(float)

    writers, files = {}, []

    def W(fname, header):
        if fname not in writers:
            f = open(os.path.join(out_dir, fname), 'w', newline='')
            files.append(f)
            w = csv.writer(f)
            w.writerow(header)
            writers[fname] = w
        return writers[fname]

    t0 = None
    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        t = t_ns / 1e9
        if t0 is None:
            t0 = t
        rel_t = t - t0

        # statistik kesehatan untuk SEMUA topik (termasuk yang tak di-CSV)
        if topic in last_t:
            max_gap[topic] = max(max_gap[topic], t - last_t[topic])
        else:
            first_t[topic] = t
        last_t[topic] = t
        counts[topic] += 1

        role = roles.get(topic)
        if role is None or topic not in msg_classes:
            continue
        try:
            m = deserialize_message(data, msg_classes[topic])
        except Exception:
            continue

        if role == 'imu':
            W('imu.csv', ['t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']).writerow([
                f'{rel_t:.4f}',
                m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z,
                m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])
        elif role == 'accel_raw':
            W('accel_raw.csv', ['t', 'ax', 'ay', 'az']).writerow([
                f'{rel_t:.4f}',
                m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z])
        elif role == 'gyro_raw':
            W('gyro_raw.csv', ['t', 'gx', 'gy', 'gz']).writerow([
                f'{rel_t:.4f}',
                m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])
        elif role == 'vio_odom':
            cov = m.pose.covariance
            W('vio_odom.csv',
              ['t', 'x', 'y', 'yaw', 'std_x', 'std_y', 'std_yaw']).writerow([
                f'{rel_t:.4f}',
                m.pose.pose.position.x, m.pose.pose.position.y,
                f'{yaw_from_quat(m.pose.pose.orientation):.5f}',
                f'{math.sqrt(max(cov[0], 0.0)):.6f}',
                f'{math.sqrt(max(cov[7], 0.0)):.6f}',
                f'{math.sqrt(max(cov[35], 0.0)):.6f}'])
        elif role == 'vio_quality':
            W('vio_quality.csv',
              ['t', 'inliers', 'matches', 'features', 'lost']).writerow([
                f'{rel_t:.4f}',
                g(m, 'inliers', 'reg.inliers'),
                g(m, 'matches', 'reg.matches'),
                g(m, 'features'),
                int(bool(g(m, 'lost', default=False)))])
        elif role == 'loop_closure':
            W('loop_closure.csv',
              ['t', 'loop_closure_id', 'proximity_id']).writerow([
                f'{rel_t:.4f}',
                g(m, 'loop_closure_id'),
                g(m, 'proximity_detection_id')])
        elif role == 'encoder':
            W('encoder.csv', ['t', 'delta_ticks']).writerow([f'{rel_t:.4f}', m.data])
        elif role == 'scan':
            valid = [r for r in m.ranges if m.range_min <= r <= m.range_max]
            W('scan_stats.csv',
              ['t', 'n_valid_points', 'range_min_seen', 'range_max_seen']).writerow([
                f'{rel_t:.4f}', len(valid),
                f'{min(valid):.3f}' if valid else '',
                f'{max(valid):.3f}' if valid else ''])

    # ---- summary.txt: bukti kesehatan tiap topik ----
    summary_path = os.path.join(out_dir, 'summary.txt')
    with open(summary_path, 'w') as f:
        f.write('RINGKASAN KESEHATAN TELEMETRI SENSOR\n')
        f.write(f'Bag: {bag_path}\n\n')
        f.write(f'{"topik":44s} {"role":12s} {"pesan":>7s} '
                f'{"rate(Hz)":>9s} {"gap maks(s)":>12s}\n')
        f.write('-' * 88 + '\n')
        for topic in sorted(counts):
            dur = last_t[topic] - first_t[topic]
            rate = (counts[topic] - 1) / dur if dur > 0 else 0.0
            f.write(f'{topic:44s} {roles.get(topic, "-"):12s} '
                    f'{counts[topic]:7d} {rate:9.2f} {max_gap[topic]:12.3f}\n')
        f.write('\nInterpretasi cepat:\n')
        f.write('  /scan ~10Hz, /imu/data ~100-200Hz, /rtabmap/odom ~28Hz,\n')
        f.write('  gap maks kecil (<0.5s) = sensor sehat tanpa putus.\n')
        f.write('  Kegagalan mapping dengan telemetri sehat = akar masalah di\n')
        f.write('  lingkungan (textureless), BUKAN sensor/hardware.\n')

    for fh in files:
        fh.close()

    print(f'Selesai. Output di: {out_dir}\n')
    with open(summary_path) as f:
        print(f.read())


if __name__ == '__main__':
    main()
