#!/usr/bin/env python3

"""
ros-start-execution: 轨迹执行脚本 - 稳定版本
"""
import sys
import os
import argparse
import json
import time
import numpy as np
import sys

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)

# 找到moveit_ros根目录
current_dir = os.path.dirname(PROJECT_ROOT)
while current_dir:
    dir_name = os.path.basename(current_dir)
    if dir_name == 'moveit_ros':
        MOVEIT_ROS_ROOT = current_dir
        MOVEIT_CORE_ROOT = os.path.join(os.path.dirname(current_dir), 'moveit_core')
        MOVEIT_PLUGINS_ROOT = os.path.join(os.path.dirname(current_dir), 'moveit_plugins')
        break
    current_dir = os.path.dirname(current_dir)

# 设置路径
PLANNING_SCENE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
MOVEIT_CONTROLLER_SRC = os.path.join(MOVEIT_PLUGINS_ROOT, 'moveit_controller_manager', 'src')
TRAJECTORY_EXECUTION_SRC = os.path.join(MODULE_ROOT, 'src')

sys.path.insert(0, TRAJECTORY_EXECUTION_SRC)
sys.path.insert(0, MOVEIT_CONTROLLER_SRC)
sys.path.insert(0, PLANNING_SCENE_SRC)

print(f"[轨迹执行] 路径设置:")
print(f"  当前模块: {TRAJECTORY_EXECUTION_SRC}")
print(f"  控制器管理器: {MOVEIT_CONTROLLER_SRC}")
print(f"  规划场景: {PLANNING_SCENE_SRC}")

# ========== 导入检查 ==========
try:
    from ps_core.scene_client import PlanningSceneClient

    from trajectory_execution import TrajectoryExecutionManager, ControllerManager
    
    import rclpy
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
    HAS_DEPENDENCIES = True
    print("✅ 所有依赖导入成功")
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    HAS_DEPENDENCIES = False
    sys.exit(1)
from moveit_controller_manager import MoveItControllerManager
