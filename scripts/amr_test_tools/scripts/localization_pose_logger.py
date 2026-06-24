#!/usr/bin/env python3
import argparse
import csv
import math
import os
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped

from ros_helpers import ensure_dir, append_csv, now_iso, yaw_from_quaternion


class LocalizationLogger(Node):
    def __init__(self, args):
        super().__init__('localization_pose_logger')
        self.args = args
        self.count = 0
        self.first_time = None
        self.last_time = None
        self.last_pose = None
        self.last_cov = None
        self.pose_type = None
        self.samples = []   # raw time-series
        # Default RTAB-Map localization pose usually PoseWithCovarianceStamped.
        if args.msg_type == 'pose_stamped':
            self.sub = self.create_subscription(PoseStamped, args.pose_topic, self.pose_cb_stamped, 30)
        else:
            self.sub = self.create_subscription(PoseWithCovarianceStamped, args.pose_topic, self.pose_cb_cov, 30)

    def _store_pose(self, stamp, p, q, cov=None):
        now = time.time()
        if self.first_time is None:
            self.first_time = now
        self.last_time = now
        self.count += 1
        self.last_pose = {
            'x': float(p.x),
            'y': float(p.y),
            'z': float(p.z),
            'yaw': float(yaw_from_quaternion(q)),
        }
        self.last_cov = cov
        cx = cy = cyaw = ''
        if cov is not None and len(cov) >= 36:
            cx, cy, cyaw = float(cov[0]), float(cov[7]), float(cov[35])
        self.samples.append({
            't': now, 'x': float(p.x), 'y': float(p.y), 'z': float(p.z),
            'yaw': float(yaw_from_quaternion(q)),
            'cov_x': cx, 'cov_y': cy, 'cov_yaw': cyaw,
        })

    def pose_cb_cov(self, msg):
        self.pose_type = 'PoseWithCovarianceStamped'
        self._store_pose(msg.header.stamp, msg.pose.pose.position, msg.pose.pose.orientation, msg.pose.covariance)

    def pose_cb_stamped(self, msg):
        self.pose_type = 'PoseStamped'
        self._store_pose(msg.header.stamp, msg.pose.position, msg.pose.orientation, None)


def main():
    parser = argparse.ArgumentParser(description='Logger localization pose terhadap peta.')
    parser.add_argument('--trial', required=True, help='Kode uji, contoh L01')
    parser.add_argument('--map-file', default='', help='Nama file peta/database yang digunakan')
    parser.add_argument('--pose-topic', default='/rtabmap/localization_pose')
    parser.add_argument('--msg-type', choices=['pose_cov', 'pose_stamped'], default='pose_cov')
    parser.add_argument('--duration', type=float, default=30.0)
    parser.add_argument('--output', default='~/amr_test_results')
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    outdir = ensure_dir(args.output)
    rclpy.init()
    node = LocalizationLogger(args)

    print('\n=== LOCALIZATION TERHADAP PETA ===')
    print(f'Topic pose      : {args.pose_topic}')
    print(f'Message type    : {args.msg_type}')
    print(f'Durasi rekam    : {args.duration:.1f} s')
    print('Pastikan RTAB-Map localization sudah berjalan.')

    t0 = time.time()
    while rclpy.ok() and (time.time() - t0) < args.duration:
        rclpy.spin_once(node, timeout_sec=0.2)

    elapsed = max(time.time() - t0, 1e-6)
    rate = node.count / elapsed
    status = 'LOCK/POSE_RECEIVED' if node.count > 0 else 'NO_POSE_RECEIVED'
    pose = node.last_pose or {'x': None, 'y': None, 'z': None, 'yaw': None}

    cov_x = cov_y = cov_yaw = None
    if node.last_cov is not None and len(node.last_cov) >= 36:
        cov_x = node.last_cov[0]
        cov_y = node.last_cov[7]
        cov_yaw = node.last_cov[35]

    row = {
        'timestamp': now_iso(),
        'trial': args.trial,
        'map_file': args.map_file,
        'pose_topic': args.pose_topic,
        'message_type': node.pose_type or args.msg_type,
        'duration_s': round(elapsed, 3),
        'pose_message_count': node.count,
        'estimated_rate_hz': round(rate, 3),
        'status': status,
        'last_x_m': None if pose['x'] is None else round(pose['x'], 4),
        'last_y_m': None if pose['y'] is None else round(pose['y'], 4),
        'last_z_m': None if pose['z'] is None else round(pose['z'], 4),
        'last_yaw_rad': None if pose['yaw'] is None else round(pose['yaw'], 4),
        'cov_x': None if cov_x is None else round(float(cov_x), 8),
        'cov_y': None if cov_y is None else round(float(cov_y), 8),
        'cov_yaw': None if cov_yaw is None else round(float(cov_yaw), 8),
        'notes': args.notes,
    }

    header = list(row.keys())
    append_csv(os.path.join(outdir, 'localization_trials.csv'), header, row)

    # ---- RAW time-series (ratusan baris) untuk diproses sendiri ----
    raw_dir = ensure_dir(os.path.join(outdir, 'raw'))
    raw_path = os.path.join(raw_dir, f'loc_{args.trial}.csv')
    if node.samples:
        t0 = node.samples[0]['t']
        with open(raw_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['t_rel_s', 'x_m', 'y_m', 'z_m', 'yaw_rad',
                        'cov_x', 'cov_y', 'cov_yaw'])
            for s in node.samples:
                w.writerow([round(s['t'] - t0, 4), round(s['x'], 4),
                            round(s['y'], 4), round(s['z'], 4),
                            round(s['yaw'], 4), s['cov_x'], s['cov_y'], s['cov_yaw']])
        print('\nHasil summary :', os.path.join(outdir, 'localization_trials.csv'))
        print('Raw time-series:', raw_path, f'({len(node.samples)} baris)')
    else:
        print('\nHasil summary :', os.path.join(outdir, 'localization_trials.csv'))
        print('Raw time-series: (tidak ada pose diterima)')
    print(row)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
