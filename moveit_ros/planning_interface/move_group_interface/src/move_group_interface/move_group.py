#!/usr/bin/env python3
"""
move_group.py - MoveGroup类
二级模块：运动规划与执行接口
"""

from .planning_context import get_planning_context
from .trajectory_execution import execute_trajectory, move_to_pose, move_to_joints


class MoveGroup:
    """
    MoveGroup运动控制接口
    
    职责：
    1. 提供机械臂运动控制
    2. 委托规划上下文处理抓取任务
    """
    
    def __init__(self, group_name="panda_arm"):
        self.group_name = group_name
        self.planning_context = get_planning_context()
        print(f"[MoveGroup] ✅ 就绪 - {group_name}")
    
    # ========== 运动控制 ==========
    
    def move_to_pose(self, pose, use_cache=True, timeout=5.0):
        """移动到指定位姿"""
        return execute_trajectory(pose, use_cache=use_cache, timeout=timeout)
    
    def move_to_joints(self, joints, use_cache=True, timeout=5.0):
        """移动到指定关节位置"""
        return execute_trajectory({"joints": joints}, use_cache=use_cache, timeout=timeout)
    
    def move_to_object(self, object_id, use_cache=True, timeout=5.0):
        """移动到物体位置"""
        return execute_trajectory(object_id, use_cache=use_cache, timeout=timeout)
    
    # ========== 抓取任务 ==========
    
    def grasp(self, object_id, strategy="top_grasp", width_mm=None):
        """抓取物体 - 委托给规划上下文"""
        return self.planning_context.grasp_object(object_id, strategy, width_mm)
    
    def grasp_pose(self, pose, object_id="target", strategy="top_grasp", width_mm=50):
        """抓取指定位姿"""
        return self.planning_context.grasp_pose(pose, object_id, strategy, width_mm)
    
    # ========== 状态查询 ==========
    
    def get_status(self):
        """获取当前任务状态"""
        return self.planning_context.get_current_task_info()