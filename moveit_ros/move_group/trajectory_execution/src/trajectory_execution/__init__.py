#!/usr/bin/env python3
"""
轨迹执行包
"""

from .trajectory_execution_manager import TrajectoryExecutionManager
from .trajectory_execution_manager import TrajectoryExecutor

# ========== 包装函数 ==========

def execute_trajectory(target, **kwargs):
    """执行轨迹（兼容旧接口）"""
    return TrajectoryExecutor.execute(target, **kwargs)

def move_to_pose(x, y, z, qx=0, qy=0, qz=0, qw=1, **kwargs):
    """移动到指定位姿"""
    return TrajectoryExecutor.execute([x, y, z, qx, qy, qz, qw], **kwargs)

def move_to_joints(joints, **kwargs):
    """移动到指定关节"""
    return TrajectoryExecutor.execute({"joints": joints}, **kwargs)

def get_execution_stats():
    """获取缓存统计"""
    executor = TrajectoryExecutor()
    if hasattr(executor, '_instance') and hasattr(executor._instance, 'executor'):
        return executor._instance.executor.get_cache_stats()
    return {"hits": 0, "misses": 0, "saves": 0}

def clear_trajectory_cache():
    """清空缓存"""
    executor = TrajectoryExecutor()
    if hasattr(executor, '_instance') and hasattr(executor._instance, 'executor'):
        return executor._instance.executor.clear_cache()
    return {"success": False}

# ========== 导出 ==========

__all__ = [
    'TrajectoryExecutionManager',
    'TrajectoryExecutor',
    'execute_trajectory',
    'move_to_pose',
    'move_to_joints',
    'get_execution_stats',
    'clear_trajectory_cache',
]