"""
Simpan peta 2D dari RTAB-Map ke file .pgm + .yaml (format standar Nav2).

Peta tersimpan di: ~/maps/[nama_yang_kamu_beri]
  - [nama].pgm  → gambar peta hitam-putih
  - [nama].yaml → metadata peta (resolusi, origin)
  - rtabmap.db  → database 3D RTAB-Map (backup otomatis)

Cara pakai (SAAT mapping masih jalan):
  ros2 launch amr_startup save_map.launch.py map_name:=lab_lantai1

Cara pakai ulang peta:
  ros2 launch amr_startup layer4_navigation.launch.py database_path:=~/maps/lab_lantai1/rtabmap.db
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from datetime import datetime


def generate_launch_description():

    default_name = f'map_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

    name_arg = DeclareLaunchArgument(
        'map_name', default_value=default_name,
        description='Nama peta (tanpa ekstensi)')

    map_dir = ['~/maps/', LaunchConfiguration('map_name')]

    # 1. Buat folder
    mkdir = ExecuteProcess(
        cmd=['mkdir', '-p', map_dir],
        output='screen',
    )

    # 2. Simpan .pgm + .yaml (peta 2D standar)
    save_pgm = TimerAction(
        period=1.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'run', 'nav2_map_server', 'map_saver_cli',
                    '-f', [map_dir[0], LaunchConfiguration('map_name'), '/', LaunchConfiguration('map_name')],
                    '--ros-args', '-p', 'save_map_timeout:=5000',
                ],
                output='screen',
            ),
        ],
    )

    # 3. Backup database .db
    backup_db = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'cp', '~/.ros/rtabmap.db',
                    [map_dir[0], LaunchConfiguration('map_name'), '/rtabmap.db'],
                ],
                output='screen',
            ),
        ],
    )

    return LaunchDescription([name_arg, mkdir, save_pgm, backup_db])
