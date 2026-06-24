#!/usr/bin/env python3
import argparse
import math
import os
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry, Path

from ros_helpers import ensure_dir, append_csv, now_iso, yaw_from_quaternion, dist2d


class NavigationDemoLogger(Node):
    def __init__(self, args):
        super().__init__('navigation_demo_logger')
        self.args = args
        self.cmd_count = 0
        self.nonzero_cmd_count = 0
        self.cmd_linear_sum = 0.0
        self.cmd_angular_sum = 0.0
        self.cmd_linear_max = 0.0
        self.cmd_angular_max = 0.0
        self.path_count = 0
        self.last_path_len = 0
        self.odom_samples = []
        self.sub_cmd = self.create_subscription(Twist, args.cmd_topic, self.cmd_cb, 50)
        self.sub_odom = self.create_subscription(Odometry, args.odom_topic, self.odom_cb, 30)
        self.sub_path = self.create_subscription(Path, args.plan_topic, self.path_cb, 10)

    def cmd_cb(self, msg):
        lin = abs(float(msg.linear.x))
        ang = abs(float(msg.angular.z))
        self.cmd_count += 1
        self.cmd_linear_sum += lin
        self.cmd_angular_sum += ang
        self.cmd_linear_max = max(self.cmd_linear_max, lin)
        self.cmd_angular_max = max(self.cmd_angular_max, ang)
        if lin > self.args.cmd_threshold or ang > self.args.angular_threshold:
            self.nonzero_cmd_count += 1

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.odom_samples.append({'t': time.time(), 'x': float(p.x), 'y': float(p.y), 'yaw': yaw_from_quaternion(q)})

    def path_cb(self, msg):
        self.path_count += 1
        self.last_path_len = len(msg.poses)


def main():
    parser = argparse.ArgumentParser(description='Logger mode demo Navigation2 AMR.')
    parser.add_argument('--trial', required=True, help='Kode uji, contoh N01')
    parser.add_argument('--start-label', default='A')
    parser.add_argument('--goal-label', default='B')
    parser.add_argument('--duration', type=float, default=60.0)
    parser.add_argument('--cmd-topic', default='/cmd_vel')
    parser.add_argument('--odom-topic', default='/odom')
    parser.add_argument('--plan-topic', default='/plan')
    parser.add_argument('--output', default='~/amr_test_results')
    parser.add_argument('--status', default='mode_demo_diuji')
    parser.add_argument('--cmd-threshold', type=float, default=0.01)
    parser.add_argument('--angular-threshold', type=float, default=0.01)
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    outdir = ensure_dir(args.output)
    rclpy.init()
    node = NavigationDemoLogger(args)

    print('\n=== MODE DEMO NAVIGATION2 ===')
    print(f'Trial       : {args.trial}')
    print(f'Start/Goal  : {args.start_label} -> {args.goal_label}')
    print(f'Durasi      : {args.duration:.1f} s')
    print('Kirim Nav2 Goal dari RViz setelah logger berjalan.')

    t0 = time.time()
    while rclpy.ok() and (time.time() - t0) < args.duration:
        rclpy.spin_once(node, timeout_sec=0.2)

    elapsed = max(time.time() - t0, 1e-6)
    avg_lin = node.cmd_linear_sum / node.cmd_count if node.cmd_count else 0.0
    avg_ang = node.cmd_angular_sum / node.cmd_count if node.cmd_count else 0.0
    cmd_active = 'YA' if node.nonzero_cmd_count > 0 else 'TIDAK'
    global_path_received = 'YA' if node.path_count > 0 else 'TIDAK'

    odom_displacement = 0.0
    odom_path = 0.0
    if len(node.odom_samples) >= 2:
        first = node.odom_samples[0]
        last = node.odom_samples[-1]
        odom_displacement = dist2d(first['x'], first['y'], last['x'], last['y'])
        for a, b in zip(node.odom_samples[:-1], node.odom_samples[1:]):
            odom_path += dist2d(a['x'], a['y'], b['x'], b['y'])

    robot_moved = 'YA' if odom_displacement > 0.02 or odom_path > 0.05 else 'TIDAK'

    row = {
        'timestamp': now_iso(),
        'trial': args.trial,
        'start_label': args.start_label,
        'goal_label': args.goal_label,
        'duration_s': round(elapsed, 3),
        'plan_topic': args.plan_topic,
        'global_path_received': global_path_received,
        'path_message_count': node.path_count,
        'last_path_pose_count': node.last_path_len,
        'cmd_topic': args.cmd_topic,
        'cmd_message_count': node.cmd_count,
        'nonzero_cmd_count': node.nonzero_cmd_count,
        'cmd_vel_active': cmd_active,
        'avg_linear_x_abs_mps': round(avg_lin, 4),
        'max_linear_x_abs_mps': round(node.cmd_linear_max, 4),
        'avg_angular_z_abs_rps': round(avg_ang, 4),
        'max_angular_z_abs_rps': round(node.cmd_angular_max, 4),
        'odom_displacement_m': round(odom_displacement, 4),
        'odom_path_length_m': round(odom_path, 4),
        'robot_moved': robot_moved,
        'status': args.status,
        'notes': args.notes,
    }

    header = list(row.keys())
    append_csv(os.path.join(outdir, 'navigation_trials.csv'), header, row)
    print('\nHasil tersimpan:', os.path.join(outdir, 'navigation_trials.csv'))
    print(row)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
