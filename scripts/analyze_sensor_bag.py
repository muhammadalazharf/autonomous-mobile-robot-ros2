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
  imu.csv            - t, ax, ay, az, gx, gy, gz       (dari /imu/data)
  accel_raw.csv      - t, ax, ay, az                   (accel mentah D455)
  vio_odom.csv       - t, x, y, yaw, std_x, std_y, std_yaw (dari /rtabmap/odom)
  vio_quality.csv    - t, inliers, matches, features, lost (dari /odom_info)
  loop_closure.csv   - t, loop_closure_id, proximity_id, highest_hypothesis
                       (dari /rtabmap/info) -> bukti accepted/rejected
  encoder.csv        - t, delta_ticks                  (dari /encoder)
  scan_stats.csv     - t, n_valid_points, range_min, range_max (dari /scan)

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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    bag_path = os.path.expanduser(sys.argv[1])
    out_dir = os.path.join(bag_path, 'analysis')
    os.makedirs(out_dir, exist_ok=True)

    reader = open_reader(bag_path)
    type_map = {t.name: t.type for t in reader.get_all_topics_and_types()}
    msg_classes = {}
    for name, typ in type_map.items():
        try:
            msg_classes[name] = get_message(typ)
        except Exception as e:  # tipe tidak terinstall di environment ini
            print(f'[WARN] lewati {name} ({typ}): {e}')

    # Statistik kesehatan per topik
    counts = defaultdict(int)
    first_t = {}
    last_t = {}
    max_gap = defaultdict(float)

    writers = {}
    files = []

    def get_writer(fname, header):
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

        if topic in last_t:
            max_gap[topic] = max(max_gap[topic], t - last_t[topic])
        else:
            first_t[topic] = t
        last_t[topic] = t
        counts[topic] += 1

        if topic not in msg_classes:
            continue
        try:
            msg = deserialize_message(data, msg_classes[topic])
        except Exception:
            continue

        if topic == '/imu/data':
            get_writer('imu.csv', ['t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']).writerow([
                f'{rel_t:.4f}',
                msg.linear_acceleration.x, msg.linear_acceleration.y,
                msg.linear_acceleration.z,
                msg.angular_velocity.x, msg.angular_velocity.y,
                msg.angular_velocity.z])

        elif topic == '/camera/camera/accel/sample':
            get_writer('accel_raw.csv', ['t', 'ax', 'ay', 'az']).writerow([
                f'{rel_t:.4f}',
                msg.linear_acceleration.x, msg.linear_acceleration.y,
                msg.linear_acceleration.z])

        elif topic == '/rtabmap/odom':
            cov = msg.pose.covariance
            get_writer('vio_odom.csv',
                       ['t', 'x', 'y', 'yaw', 'std_x', 'std_y', 'std_yaw']).writerow([
                f'{rel_t:.4f}',
                msg.pose.pose.position.x, msg.pose.pose.position.y,
                f'{yaw_from_quat(msg.pose.pose.orientation):.5f}',
                f'{math.sqrt(max(cov[0], 0.0)):.6f}',
                f'{math.sqrt(max(cov[7], 0.0)):.6f}',
                f'{math.sqrt(max(cov[35], 0.0)):.6f}'])

        elif topic == '/odom_info':
            # rtabmap_msgs/OdomInfo: telemetri kualitas tracking VIO
            reg = getattr(msg, 'reg', None)
            get_writer('vio_quality.csv',
                       ['t', 'inliers', 'matches', 'features', 'lost']).writerow([
                f'{rel_t:.4f}',
                getattr(reg, 'inliers', '') if reg else '',
                getattr(reg, 'matches', '') if reg else '',
                getattr(msg, 'features', ''),
                int(getattr(msg, 'lost', False))])

        elif topic == '/rtabmap/info':
            # rtabmap_msgs/Info: loop closure + statistik internal
            stats = dict(zip(getattr(msg, 'stats_keys', []),
                             getattr(msg, 'stats_values', [])))
            hyp = stats.get('Loop/Highest hypothesis value/', '')
            get_writer('loop_closure.csv',
                       ['t', 'loop_closure_id', 'proximity_id',
                        'highest_hypothesis']).writerow([
                f'{rel_t:.4f}',
                getattr(msg, 'loop_closure_id', ''),
                getattr(msg, 'proximity_detection_id', ''),
                hyp])

        elif topic == '/encoder':
            get_writer('encoder.csv', ['t', 'delta_ticks']).writerow(
                [f'{rel_t:.4f}', msg.data])

        elif topic == '/scan':
            valid = [r for r in msg.ranges
                     if msg.range_min <= r <= msg.range_max]
            get_writer('scan_stats.csv',
                       ['t', 'n_valid_points', 'range_min_seen',
                        'range_max_seen']).writerow([
                f'{rel_t:.4f}', len(valid),
                f'{min(valid):.3f}' if valid else '',
                f'{max(valid):.3f}' if valid else ''])

    # ---- summary.txt: bukti kesehatan tiap sensor ----
    summary_path = os.path.join(out_dir, 'summary.txt')
    with open(summary_path, 'w') as f:
        f.write('RINGKASAN KESEHATAN TELEMETRI SENSOR\n')
        f.write(f'Bag: {bag_path}\n')
        f.write(f'{"topik":42s} {"pesan":>8s} {"rate(Hz)":>9s} '
                f'{"gap maks(s)":>12s}\n')
        f.write('-' * 75 + '\n')
        for topic in sorted(counts):
            dur = last_t[topic] - first_t[topic]
            rate = (counts[topic] - 1) / dur if dur > 0 else 0.0
            f.write(f'{topic:42s} {counts[topic]:8d} {rate:9.2f} '
                    f'{max_gap[topic]:12.3f}\n')
        f.write('\nInterpretasi cepat:\n')
        f.write('  /scan ~10Hz, /imu/data ~100-200Hz, /rtabmap/odom ~28Hz,\n')
        f.write('  gap maks kecil (<0.5s) = sensor sehat tanpa putus.\n')
        f.write('  Kegagalan mapping dengan telemetri sehat menunjukkan\n')
        f.write('  akar masalah di lingkungan (textureless), bukan sensor.\n')

    for fh in files:
        fh.close()

    print(f'Selesai. Output di: {out_dir}')
    with open(summary_path) as f:
        print(f.read())


if __name__ == '__main__':
    main()
