#!/usr/bin/env python3
"""
trajectory_execution.py - 轨迹执行接口
二级模块：一行调用轨迹执行
完全复用你已有的一行调用接口
"""

# ========== 直接从你的轨迹执行器导入 ==========
# 这是你已经在 trajectory_executor.py 中实现的一行调用接口
from trajectory_execution import (
    execute_trajectory as _execute,
    move_to_pose as _move_to_pose,
    move_to_joints as _move_to_joints,
    get_execution_stats as _get_stats,
    clear_trajectory_cache as _clear_cache
)

# ========== 重新导出 ==========
# 保持接口一致性

def execute_trajectory(target, **kwargs):
    """
    一行调用：执行轨迹
    
    支持:
    - 物体ID: execute_trajectory("qingque")
    - 位姿: execute_trajectory([0.5,0,0.3,0,0,0,1])
    - 关节: execute_trajectory({"joints": [...]})
    """
    return _execute(target, **kwargs)


def move_to_pose(x, y, z, qx=0, qy=0, qz=0, qw=1, **kwargs):
    """快速移动到指定位姿"""
    return _move_to_pose(x, y, z, qx, qy, qz, qw, **kwargs)


def move_to_joints(joints, **kwargs):
    """快速移动到指定关节位置"""
    return _move_to_joints(joints, **kwargs)


def get_execution_stats():
    """获取执行统计信息"""
    return _get_stats()


def clear_trajectory_cache():
    """清空轨迹缓存"""
    return _clear_cache()


# ========== 版本信息 ==========
__all__ = [
    'execute_trajectory',
    'move_to_pose',
    'move_to_joints',
    'get_execution_stats',
    'clear_trajectory_cache'
]