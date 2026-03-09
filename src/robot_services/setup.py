from setuptools import setup
import os
from glob import glob

package_name = 'robot_services'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='QingQue',
    maintainer_email='qingque@qq.com',
    description='Robot services for grasp/move/add/remove',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'grasp_service = robot_services.grasp_service:main'
        ],
    },
)