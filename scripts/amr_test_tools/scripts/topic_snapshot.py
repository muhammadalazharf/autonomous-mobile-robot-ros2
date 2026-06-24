#!/usr/bin/env python3
import argparse
import os
import subprocess
from ros_helpers import ensure_dir, append_csv, now_iso


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=10).strip()
    except Exception as e:
        return f'ERROR: {e}'


def main():
    parser = argparse.ArgumentParser(description='Snapshot topic penting ROS 2 AMR.')
    parser.add_argument('--output', default='~/amr_test_results')
    args = parser.parse_args()
    outdir = ensure_dir(args.output)
    topics = {
        '/scan': 'RPLiDAR C1 LaserScan',
        '/odom': 'Odometry robot',
        '/cmd_vel': 'Command velocity',
        '/imu/data': 'IMU fused data',
        '/rtabmap/localization_pose': 'RTAB-Map localization pose',
        '/plan': 'Navigation2 global path',
    }
    header = ['timestamp', 'topic', 'fungsi', 'type_result', 'hz_result', 'notes']
    for topic, fungsi in topics.items():
        type_result = run(f'ros2 topic type {topic}')
        hz_result = run(f'timeout 5 ros2 topic hz {topic}')
        row = {
            'timestamp': now_iso(),
            'topic': topic,
            'fungsi': fungsi,
            'type_result': type_result,
            'hz_result': hz_result.replace('\n', ' | '),
            'notes': '',
        }
        append_csv(os.path.join(outdir, 'topic_snapshot.csv'), header, row)
    print('Snapshot topic tersimpan:', os.path.join(outdir, 'topic_snapshot.csv'))


if __name__ == '__main__':
    main()
