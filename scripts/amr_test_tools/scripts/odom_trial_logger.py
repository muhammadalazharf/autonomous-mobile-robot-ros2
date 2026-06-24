#!/usr/bin/env python3
import argparse
import math
import os
import threading
import time

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

from ros_helpers import ensure_dir, append_csv, now_iso, yaw_from_quaternion, dist2d


class OdomTrialLogger(Node):
    def __init__(self, args):
        super().__init__('odom_trial_logger')
        self.args = args
        self.latest = None
        self.samples = []
        self.recording = False
        self.sub = self.create_subscription(Odometry, args.odom_topic, self.odom_cb, 30)

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        item = {
            't': time.time(),
            'x': float(p.x),
            'y': float(p.y),
            'yaw': float(yaw_from_quaternion(q)),
        }
        self.latest = item
        if self.recording:
            self.samples.append(item)


def main():
    parser = argparse.ArgumentParser(description='Logger validasi odometry AMR berbasis /odom.')
    parser.add_argument('--trial', required=True, help='Kode uji, contoh O01')
    parser.add_argument('--actual-distance', type=float, required=True, help='Jarak aktual dari meteran dalam meter')
    parser.add_argument('--odom-topic', default='/odom')
    parser.add_argument('--output', default='~/amr_test_results')
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    outdir = ensure_dir(args.output)
    rclpy.init()
    node = OdomTrialLogger(args)

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    print('\n=== VALIDASI ODOMETRY ===')
    print(f'Topic odom      : {args.odom_topic}')
    print(f'Trial           : {args.trial}')
    print(f'Jarak aktual    : {args.actual_distance:.3f} m')
    print('Tunggu pesan /odom masuk...')

    timeout = time.time() + 10
    while node.latest is None and time.time() < timeout:
        time.sleep(0.1)
    if node.latest is None:
        print('ERROR: Tidak ada pesan odometry diterima. Cek topic /odom dan node odometry.')
        rclpy.shutdown()
        return

    input('\nPosisikan robot di titik awal. Tekan ENTER untuk mulai rekam...')
    node.samples = []
    node.recording = True
    t_start = time.time()
    input('Gerakkan robot sampai titik akhir. Tekan ENTER untuk berhenti rekam...')
    node.recording = False
    t_end = time.time()

    if len(node.samples) < 2:
        print('ERROR: Sampel odom terlalu sedikit.')
        rclpy.shutdown()
        return

    first = node.samples[0]
    last = node.samples[-1]
    straight = dist2d(first['x'], first['y'], last['x'], last['y'])

    path_length = 0.0
    for a, b in zip(node.samples[:-1], node.samples[1:]):
        path_length += dist2d(a['x'], a['y'], b['x'], b['y'])

    actual = args.actual_distance
    error_m = abs(actual - straight)
    error_pct = (error_m / actual * 100.0) if actual != 0 else 0.0

    row = {
        'timestamp': now_iso(),
        'trial': args.trial,
        'actual_distance_m': round(actual, 4),
        'odom_straight_distance_m': round(straight, 4),
        'odom_path_length_m': round(path_length, 4),
        'error_m': round(error_m, 4),
        'error_pct': round(error_pct, 3),
        'duration_s': round(t_end - t_start, 3),
        'sample_count': len(node.samples),
        'start_x_m': round(first['x'], 4),
        'start_y_m': round(first['y'], 4),
        'end_x_m': round(last['x'], 4),
        'end_y_m': round(last['y'], 4),
        'start_yaw_rad': round(first['yaw'], 4),
        'end_yaw_rad': round(last['yaw'], 4),
        'odom_topic': args.odom_topic,
        'notes': args.notes,
    }

    header = list(row.keys())
    append_csv(os.path.join(outdir, 'odometry_trials.csv'), header, row)
    print('\nHasil tersimpan:', os.path.join(outdir, 'odometry_trials.csv'))
    print(row)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
