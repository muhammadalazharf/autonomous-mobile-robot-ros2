from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'amr_sensors'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Muhammad Al Azhar Faradis',
    maintainer_email='malazharfaradis@gmail.com',
    description='Sensor drivers, QoS contracts, and health-check for AMR',
    license='MIT',
    entry_points={
        'console_scripts': [
            'health_check = amr_sensors.health_check_node:main',
            'imu_merger = amr_sensors.imu_merger_node:main',
            'lidar_xy = amr_sensors.lidar_xy_node:main',
            'integration_check = amr_sensors.integration_check_node:main',
        ],
    },
)
