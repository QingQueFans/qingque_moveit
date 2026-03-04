# planning_scene/core_functions/setup.py
from setuptools import setup, find_packages

setup(
    name='ps_core',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'rclpy',
        'moveit_msgs',
    ],
    entry_points={
        'console_scripts': [
            'ps-get-scene=ps_core.scripts.get_scene:main',
            'ps-set-state=ps_core.scripts.set_state:main',
            'ps-clear-scene=ps_core.scripts.clear_scene:main',
        ],
    },
)