#!/usr/bin/env python3
"""
extract_rtabmap_images.py
=========================
Ekstrak gambar RGB + depth per-frame dari file database RTAB-Map (.db).

RTAB-Map menyimpan gambar setiap node di tabel `Data`:
  - kolom `image` : RGB (JPEG-compressed atau raw)
  - kolom `depth` : depth map (PNG 16-bit atau raw)

Output:
  <out>/<db_name>/
    rgb/   node_000001.jpg, node_000002.jpg, ...
    depth/ node_000001.png, node_000002.png, ...   (16-bit grayscale)
    poses.csv  (node_id, t_rel, x, y, yaw — buat sinkronisasi)

------------------------------------------------------------------
CARA PAKAI (di NUC, tidak butuh ROS):

  # Semua .db di ~/maps/, semua frame:
  python3 ~/amr_starter/scripts/extract_rtabmap_images.py

  # Satu file saja:
  python3 ~/amr_starter/scripts/extract_rtabmap_images.py \
      --single ~/maps/lab_demo_18jun.db

  # Ambil 1 dari setiap 10 frame (hemat space):
  python3 ~/amr_starter/scripts/extract_rtabmap_images.py --stride 10

  # Hanya RGB (lewati depth):
  python3 ~/amr_starter/scripts/extract_rtabmap_images.py --no-depth

Output default: ~/hasil_ekstrak/images/<db_name>/
------------------------------------------------------------------
"""
import argparse
import csv
import math
import os
import sqlite3
import struct
import sys
from pathlib import Path


def decode_transform(blob):
    if blob is None or len(blob) < 48:
        return None
    try:
        v = struct.unpack_from('12f', blob, 0)
        tx, ty = v[3], v[7]
        yaw = math.atan2(v[4], v[0])
        return (round(tx, 4), round(ty, 4), round(math.degrees(yaw), 2))
    except Exception:
        return None


def table_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {r[0] for r in cur.fetchall()}


def column_names(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def looks_like_jpeg(b):
    return len(b) >= 3 and b[0] == 0xFF and b[1] == 0xD8 and b[2] == 0xFF


def looks_like_png(b):
    return len(b) >= 8 and b[:8] == b'\x89PNG\r\n\x1a\n'


def extract_one_db(db_path, out_root, stride=1, do_depth=True, limit=None):
    db_name = Path(db_path).stem
    size_mb = os.path.getsize(db_path) / 1e6
    print(f"\n[→] {Path(db_path).name}  ({size_mb:.1f} MB)")

    out_dir = Path(out_root) / db_name
    rgb_dir   = out_dir / 'rgb'
    depth_dir = out_dir / 'depth'
    rgb_dir.mkdir(parents=True, exist_ok=True)
    if do_depth:
        depth_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    except Exception as e:
        print(f"    [ERROR] tidak bisa buka: {e}")
        return 0

    try:
        tables = table_names(conn)
    except sqlite3.DatabaseError as e:
        print(f"    [SKIP] file rusak: {e}")
        conn.close()
        return 0

    if 'Data' not in tables or 'Node' not in tables:
        print(f"    [SKIP] tabel Data/Node tidak ditemukan")
        conn.close()
        return 0

    data_cols = column_names(conn, 'Data')
    has_image = 'image' in data_cols
    has_depth = 'depth' in data_cols
    if not has_image:
        print(f"    [SKIP] kolom 'image' tidak ada di tabel Data")
        conn.close()
        return 0

    cur = conn.cursor()
    cur.execute("SELECT id, stamp, pose FROM Node ORDER BY id")
    nodes = cur.fetchall()
    if not nodes:
        print(f"    [SKIP] tabel Node kosong")
        conn.close()
        return 0

    t0 = min((s for _, s, _ in nodes if s and s > 0), default=0)

    pose_csv = out_dir / 'poses.csv'
    pw = open(pose_csv, 'w', newline='')
    wcsv = csv.writer(pw)
    wcsv.writerow(['node_id', 't_rel_s', 'rgb_file', 'depth_file', 'x_m', 'y_m', 'yaw_deg'])

    n_rgb = n_depth = n_seen = 0
    select = 'id, image' + (', depth' if (do_depth and has_depth) else ', NULL')
    cur2 = conn.cursor()

    for i, (nid, stamp, pose_blob) in enumerate(nodes):
        if i % stride != 0:
            continue
        if limit and n_rgb >= limit:
            break

        cur2.execute(f"SELECT {select} FROM Data WHERE id=?", (nid,))
        row = cur2.fetchone()
        if not row:
            continue
        _, img_blob, depth_blob = row
        n_seen += 1
        rel_t = round(stamp - t0, 4) if (t0 and stamp) else 0.0
        dec = decode_transform(pose_blob)
        x, y, yaw = (dec if dec else ('', '', ''))

        rgb_name = depth_name = ''

        if img_blob:
            ext = 'jpg' if looks_like_jpeg(img_blob) else ('png' if looks_like_png(img_blob) else 'bin')
            rgb_name = f'node_{nid:06d}.{ext}'
            with open(rgb_dir / rgb_name, 'wb') as f:
                f.write(img_blob)
            n_rgb += 1

        if do_depth and depth_blob:
            ext = 'png' if looks_like_png(depth_blob) else ('jpg' if looks_like_jpeg(depth_blob) else 'bin')
            depth_name = f'node_{nid:06d}.{ext}'
            with open(depth_dir / depth_name, 'wb') as f:
                f.write(depth_blob)
            n_depth += 1

        wcsv.writerow([nid, rel_t, rgb_name, depth_name, x, y, yaw])

        if n_seen % 100 == 0:
            print(f"    ... {n_seen} node | RGB {n_rgb} | depth {n_depth}", end='\r')

    pw.close()
    conn.close()

    print(f"    [✓] {n_rgb} RGB, {n_depth} depth, poses.csv → {out_dir}")
    return n_rgb


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('maps_dir', nargs='?',
                    default=os.path.expanduser('~/maps'),
                    help='Folder berisi .db (default: ~/maps)')
    ap.add_argument('--out', default=os.path.expanduser('~/hasil_ekstrak/images'),
                    help='Folder output (default: ~/hasil_ekstrak/images)')
    ap.add_argument('--single', help='Proses satu .db saja')
    ap.add_argument('--stride', type=int, default=1,
                    help='Ambil 1 dari setiap N node (default 1 = semua)')
    ap.add_argument('--no-depth', action='store_true',
                    help='Lewati ekstraksi depth (hanya RGB)')
    ap.add_argument('--limit', type=int, default=None,
                    help='Maksimum frame per database (debug/preview)')
    args = ap.parse_args()

    out_root = os.path.expanduser(args.out)
    os.makedirs(out_root, exist_ok=True)

    if args.single:
        db_files = [Path(os.path.expanduser(args.single))]
    else:
        maps_dir = os.path.expanduser(args.maps_dir)
        db_files = sorted(Path(maps_dir).glob('*.db'))
        if not db_files:
            print(f"[ERROR] tidak ada .db di {maps_dir}")
            sys.exit(1)

    print('=' * 65)
    print(f'  EXTRACT RTAB-MAP IMAGES (RGB{"" if args.no_depth else " + DEPTH"})')
    print(f'  Input : {args.single or args.maps_dir}')
    print(f'  Output: {out_root}')
    print(f'  Total : {len(db_files)} file .db | stride={args.stride}'
          + (f' | limit={args.limit}' if args.limit else ''))
    print('=' * 65)

    total = 0
    for db in db_files:
        total += extract_one_db(str(db), out_root,
                                stride=args.stride,
                                do_depth=not args.no_depth,
                                limit=args.limit)

    print('\n' + '=' * 65)
    print(f'  SELESAI — total {total} frame RGB diekstrak')
    print(f'  Folder: {out_root}')
    print('=' * 65)


if __name__ == '__main__':
    main()
