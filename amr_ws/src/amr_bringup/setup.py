from setuptools import setup
import os
from glob import glob

package_name = 'amr_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Muhammad Al Azhar Faradis',
    maintainer_email='itssurabaya@todo.todo',
    description='Launch package for AMR',
    license='MIT',
    entry_points={
        'console_scripts': [],
    },
)