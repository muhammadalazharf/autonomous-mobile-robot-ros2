from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'amr_pose'

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
    description='Pose estimation — VIO, IMU fusion, optional EKF',
    license='MIT',
    entry_points={
        'console_scripts': [
            'encoder_odom = amr_pose.encoder_odom_node:main',
        ],
    },
)
