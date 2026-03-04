#!/usr/bin/env python3
"""
move_group_interface - MoveGroup接口模块
三级模块：运动规划、抓取任务、轨迹执行统一接口
完全基于一行调用接口构建
"""

from .planning_context import PlanningContext, get_planning_context
from .move_group import MoveGroup
from .trajectory_execution import (
    execute_trajectory,
    move_to_pose,
    move_to_joints,
    get_execution_stats,
    clear_trajectory_cache
)

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "MoveGroup接口模块，提供运动规划、抓取任务、轨迹执行一站式接口"

__all__ = [
    # 规划上下文（抓取任务主入口）
    'PlanningContext',
    'get_planning_context',
    
    # MoveGroup类（运动控制+抓取）
    'MoveGroup',
    
    # 轨迹执行一行调用接口
    'execute_trajectory',
    'move_to_pose',
    'move_to_joints',
    'get_execution_stats',
    'clear_trajectory_cache',
]