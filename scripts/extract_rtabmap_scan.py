#!/usr/bin/env python3
"""
extract_rtabmap_scan.py
=======================
Ekstrak data mentah LiDAR scan per-frame dari file database RTAB-Map (.db).

RTAB-Map menyimpan scan di tabel `Data` kolom `scan`:
  - Data ter-compressed dengan zlib (header 4 byte ukuran asli + zlib stream)
  - Setelah decompressed: array float32 (X, Y) atau (X, Y, Z) atau (X, Y, I)
  - scan_info menyimpan format, max_points, max_range, local_transform

Output per database:
  <out>/<db_name>/
    scan_summary.csv          ← ringkasan per frame
                                (node_id, t_rel, n_points, range_min/max/mean)
    csv/
      node_000001.csv         ← raw point cloud: x_m, y_m, z_m, intensity,
                                                 range_m, angle_deg
      node_000002.csv
      ...

------------------------------------------------------------------
CARA PAKAI (di NUC, TANPA perlu ROS):

  # Semua .db:
  python3 ~/amr_starter/scripts/extract_rtabmap_scan.py

  # Satu file:
  python3 ~/amr_starter/scripts/extract_rtabmap_scan.py \
      --single ~/maps/lab_demo_18jun.db

  # Hemat space (1 dari 5 frame):
  python3 ~/amr_starter/scripts/extract_rtabmap_scan.py --stride 5

  # Preview 10 frame:
  python3 ~/amr_starter/scripts/extract_rtabmap_scan.py \
      --single ~/maps/lab_demo_18jun.db --limit 10
------------------------------------------------------------------
"""
import argparse
import csv
import math
import os
import sqlite3
import struct
import sys
import zlib
from pathlib import Path


# Format LaserScan di RTAB-Map (LaserScan::Format enum)
# (channels per point, name, has_z, has_intensity)
SCAN_FORMAT = {
    0:  (0, 'kUnknown',      False, False),
    1:  (2, 'kXY',           False, False),
    2:  (3, 'kXYI',          False, True),
    3:  (5, 'kXYNormal',     False, False),
    4:  (6, 'kXYINormal',    False, True),
    5:  (3, 'kXYZ',          True,  False),
    6:  (4, 'kXYZI',         True,  True),
    7:  (4, 'kXYZRGB',       True,  False),
    8:  (6, 'kXYZNormal',    True,  False),
    9:  (7, 'kXYZINormal',   True,  True),
    10: (7, 'kXYZRGBNormal', True,  False),
}


def decompress_blob(blob):
    """RTAB-Map compressData2: 4-byte size header + zlib stream. Fallback ke
    decompress langsung kalau header tidak ada."""
    if blob is None or len(blob) < 5:
        return None
    # Coba dengan 4-byte header
    try:
        return zlib.decompress(blob[4:])
    except zlib.error:
        pass
    # Coba tanpa header
    try:
        return zlib.decompress(blob)
    except zlib.error:
        pass
    # Sudah raw (tidak ter-compressed)
    return blob


def parse_scan_info(blob):
    """scan_info blob: format(i32) + max_pts(i32) + max_range(f32) + local_transform(12 f32)."""
    if blob is None or len(blob) < 8:
        return None
    try:
        # Coba dengan zlib decompress dulu
        data = decompress_blob(blob) or blob
        fmt, max_pts = struct.unpack_from('ii', data, 0)
        max_range = struct.unpack_from('f', data, 8)[0] if len(data) >= 12 else 0.0
        if fmt in SCAN_FORMAT:
            return {'format': fmt, 'max_pts': max_pts, 'max_range': max_range}
    except Exception:
        pass
    return None


def autodetect_stride(raw_bytes):
    """Cari stride float yang masuk akal (nilai dalam ±100m)."""
    n_floats = len(raw_bytes) // 4
    if n_floats < 4:
        return None
    for s in (2, 3, 4, 5, 6, 7):
        if n_floats % s != 0:
            continue
        n_pts = n_floats // s
        if n_pts < 4:
            continue
        try:
            sample = struct.unpack_from(f'{min(n_pts, 20) * s}f', raw_bytes, 0)
            if all(abs(v) < 100.0 and not math.isnan(v) and not math.isinf(v)
                   for v in sample):
                return s
        except struct.error:
            continue
    return None


def parse_scan_points(scan_blob, info):
    """Decompress + parse blob jadi list (x, y, z, intensity, range, angle_deg)."""
    raw = decompress_blob(scan_blob)
    if raw is None or len(raw) < 8:
        return []

    stride = None
    has_z = False
    has_i = False
    if info and info['format'] in SCAN_FORMAT:
        ch, _, has_z, has_i = SCAN_FORMAT[info['format']]
        if ch > 0:
            stride = ch

    if stride is None:
        stride = autodetect_stride(raw)
        if stride is None:
            return []
        # Heuristik z/intensity dari stride
        has_z = stride >= 3 and stride != 3  # stride 3 ambigu (XYI vs XYZ)
        has_i = stride in (3, 4, 6, 7)

    n_floats = len(raw) // 4
    n_pts = n_floats // stride
    points = []
    for i in range(n_pts):
        try:
            vals = struct.unpack_from(f'{stride}f', raw, i * stride * 4)
        except struct.error:
            break
        x = vals[0]
        y = vals[1]
        z = vals[2] if has_z and stride >= 3 else 0.0
        intensity = vals[-1] if has_i else 0.0
        # filter nilai invalid
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            continue
        r = math.hypot(x, y)
        ang = math.degrees(math.atan2(y, x))
        points.append((round(x, 4), round(y, 4), round(z, 4),
                       round(intensity, 2),
                       round(r, 4), round(ang, 2)))
    return points


def table_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {r[0] for r in cur.fetchall()}


def column_names(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def extract_one_db(db_path, out_root, stride=1, limit=None):
    db_name = Path(db_path).stem
    size_mb = os.path.getsize(db_path) / 1e6
    print(f"\n[→] {Path(db_path).name}  ({size_mb:.1f} MB)")

    out_dir = Path(out_root) / db_name
    csv_dir = out_dir / 'csv'
    csv_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 0

    try:
        tables = table_names(conn)
    except sqlite3.DatabaseError as e:
        print(f"    [SKIP] file rusak: {e}")
        conn.close()
        return 0

    if 'Data' not in tables or 'Node' not in tables:
        print(f"    [SKIP] tabel Data/Node tidak ada")
        conn.close()
        return 0

    data_cols = column_names(conn, 'Data')
    if 'scan' not in data_cols:
        print(f"    [SKIP] kolom 'scan' tidak ada")
        conn.close()
        return 0
    has_scan_info = 'scan_info' in data_cols

    cur = conn.cursor()
    cur.execute("SELECT id, stamp FROM Node ORDER BY id")
    nodes = cur.fetchall()
    if not nodes:
        conn.close()
        return 0

    t0 = min((s for _, s in nodes if s and s > 0), default=0)

    summary_path = out_dir / 'scan_summary.csv'
    sf = open(summary_path, 'w', newline='')
    sw = csv.writer(sf)
    sw.writerow(['node_id', 't_rel_s', 'csv_file', 'n_points',
                 'range_min', 'range_max', 'range_mean'])

    select = 'scan' + (', scan_info' if has_scan_info else ', NULL')
    cur2 = conn.cursor()

    n_done = 0
    n_empty = 0
    for i, (nid, stamp) in enumerate(nodes):
        if i % stride != 0:
            continue
        if limit and n_done >= limit:
            break

        cur2.execute(f"SELECT {select} FROM Data WHERE id=?", (nid,))
        row = cur2.fetchone()
        if not row:
            continue
        scan_blob, info_blob = row
        if scan_blob is None or len(scan_blob) < 8:
            n_empty += 1
            continue

        info = parse_scan_info(info_blob) if info_blob else None
        points = parse_scan_points(scan_blob, info)
        if not points:
            n_empty += 1
            continue

        rel_t = round(stamp - t0, 4) if (t0 and stamp) else 0.0

        # tulis CSV per frame
        fname = f'node_{nid:06d}.csv'
        with open(csv_dir / fname, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['x_m', 'y_m', 'z_m', 'intensity', 'range_m', 'angle_deg'])
            w.writerows(points)

        ranges = [p[4] for p in points if p[4] > 0]
        rmin = round(min(ranges), 4) if ranges else 0
        rmax = round(max(ranges), 4) if ranges else 0
        rmean = round(sum(ranges) / len(ranges), 4) if ranges else 0

        sw.writerow([nid, rel_t, fname, len(points), rmin, rmax, rmean])
        n_done += 1

        if n_done % 50 == 0:
            print(f"    ... {n_done} frame ditulis", end='\r')

    sf.close()
    conn.close()

    print(f"    [✓] {n_done} frame CSV ditulis"
          + (f" ({n_empty} frame kosong dilewati)" if n_empty else ""))
    print(f"        → {out_dir}")
    return n_done


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('maps_dir', nargs='?',
                    default=os.path.expanduser('~/maps'),
                    help='Folder berisi .db (default: ~/maps)')
    ap.add_argument('--out', default=os.path.expanduser('~/hasil_ekstrak/scans'),
                    help='Folder output (default: ~/hasil_ekstrak/scans)')
    ap.add_argument('--single', help='Proses satu .db saja')
    ap.add_argument('--stride', type=int, default=1,
                    help='Ambil 1 dari setiap N node (default 1 = semua)')
    ap.add_argument('--limit', type=int, default=None,
                    help='Maksimum frame per database')
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
    print(f'  EXTRACT RTAB-MAP LIDAR SCAN → CSV per-frame')
    print(f'  Input : {args.single or args.maps_dir}')
    print(f'  Output: {out_root}')
    print(f'  Total : {len(db_files)} file .db | stride={args.stride}'
          + (f' | limit={args.limit}' if args.limit else ''))
    print('=' * 65)

    total = 0
    for db in db_files:
        total += extract_one_db(str(db), out_root,
                                stride=args.stride,
                                limit=args.limit)

    print('\n' + '=' * 65)
    print(f'  SELESAI — total {total} frame scan diekstrak')
    print(f'  Folder: {out_root}')
    print('=' * 65)


if __name__ == '__main__':
    main()
