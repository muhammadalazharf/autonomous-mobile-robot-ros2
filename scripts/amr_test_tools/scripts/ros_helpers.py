#!/usr/bin/env python3
import math
import os
import csv
from datetime import datetime


def ensure_dir(path: str) -> str:
    path = os.path.expanduser(path)
    os.makedirs(path, exist_ok=True)
    return path


def append_csv(path: str, header, row):
    path = os.path.expanduser(path)
    exists = os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def yaw_from_quaternion(q):
    # geometry_msgs/Quaternion -> yaw rad
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def dist2d(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default
