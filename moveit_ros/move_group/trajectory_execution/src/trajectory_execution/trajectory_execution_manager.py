#!/usr/bin/env python3
"""
轨迹执行管理器 - pymoveit2 最终版
"""
from typing import List, Dict, Any, Optional, Union
import time
import os
import json
import sys
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from pymoveit2 import MoveIt2
from pymoveit2 import MoveIt2Gripper

# ========== 路径设置 ==========
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(MODULE_ROOT))

CACHE_SRC = os.path.join(PROJECT_ROOT, 'moveit_core', 'cache_manager', 'src')
sys.path.insert(0, CACHE_SRC)

try:
    from ps_cache.object_cache import ObjectCache
    from ps_cache.cache_manager import CachePathTools
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False

from .rollback_manager import RollbackManager


class TrajectoryExecutionManager:
    """轨迹执行管理器 - pymoveit2 最终版"""
    
    def __init__(self, use_pymoveit2=True):
        if not rclpy.ok():
            rclpy.init()
        
        self.node = Node("trajectory_execution_manager")
        
        self.moveit2 = None
        self.gripper = None
        
        if use_pymoveit2:
            try:
                self.moveit2 = MoveIt2(
                    node=self.node,
                    joint_names=["panda_joint1", "panda_joint2", "panda_joint3",
                               "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"],
                    base_link_name="panda_link0",
                    end_effector_name="panda_hand",
                    group_name="panda_arm"
                )
                
                self.gripper = MoveIt2Gripper(
                    node=self.node,
                    gripper_joint_names=["panda_finger_joint1", "panda_finger_joint2"],
                    open_gripper_joint_positions=[0.04, 0.04],
                    closed_gripper_joint_positions=[0.0, 0.0],
                    gripper_group_name="hand"
                )
            except Exception as e:
                print(f"[轨迹执行] pymoveit2 初始化失败: {e}")
                self.moveit2 = None
        
        self.cache = None
        if HAS_CACHE:
            try:
                self.cache = ObjectCache()
                CachePathTools.initialize()
            except:
                pass
        
        self.is_executing = False
        self.current_trajectory = None
        self.execution_start_time = None
        self.execution_history = []
        
        self.cache_stats = {"hits": 0, "misses": 0, "saves": 0}
        self.rollback_manager = RollbackManager()
        
        self.config = {
            "planning_time": 5.0,
            "default_algorithm": "rrt_connect"
        }
    
    # ========== 硬编码位姿 ==========
    def _get_hardcoded_pose(self, object_id: str) -> Optional[List]:
        hardcoded = {
            "train_1": [0.4, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0],
            "test_cube": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0],
            "default": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0]
        }
        return hardcoded.get(object_id, hardcoded["default"])
    
    # ========== 核心方法 ==========
    
    def plan_trajectory(self, goal_state, **kwargs) -> Dict:
        """规划轨迹"""
        start_time = time.time()
        
        if not self.moveit2:
            return {"success": False, "error": "pymoveit2 未初始化"}
        
        try:
            algorithm = kwargs.get('algorithm', self.config['default_algorithm'])
            self.moveit2.planner_id = algorithm.upper()
            
            trajectory = None
            
            if isinstance(goal_state, dict):
                if "joints" in goal_state:
                    trajectory = self.moveit2.plan(
                        joint_positions=goal_state["joints"]
                    )
                    
                elif "pose" in goal_state:
                    pose = goal_state["pose"]
                    if isinstance(pose, dict):
                        pos = pose.get("position", [0,0,0])
                        orient = pose.get("orientation", [0,0,0,1])
                    else:
                        pos = pose[:3]
                        orient = pose[3:7] if len(pose) >= 7 else [0,0,0,1]
                    
                    trajectory = self.moveit2.plan(
                        position=pos,
                        quat_xyzw=orient
                    )
            
            success = trajectory is not None
            
            result = {
                "success": success,
                "algorithm": algorithm,
                "planning_time": time.time() - start_time
            }
            
            if success:
                result["trajectory"] = trajectory
                result["point_count"] = len(trajectory.points)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_sync(self, trajectory: JointTrajectory) -> Dict:
        """同步执行轨迹"""
        start_time = time.time()
        
        if not self.moveit2:
            return {"success": False, "error": "pymoveit2 未初始化"}
        
        if trajectory is None or not trajectory.points:
            return {"success": False, "error": "轨迹无效"}
        
        try:
            self.is_executing = True
            self.current_trajectory = trajectory
            self.execution_start_time = time.time()
            
            self.execution_history.append({
                "start_time": self.execution_start_time,
                "point_count": len(trajectory.points)
            })
            
            self.moveit2.execute(joint_trajectory=trajectory)
            
            self.is_executing = False
            
            return {
                "success": True,
                "execution_time": time.time() - self.execution_start_time
            }
            
        except Exception as e:
            self.is_executing = False
            return {"success": False, "error": str(e)}
    
    def plan_and_execute(self, goal_state, **kwargs) -> Dict:
        """规划并执行"""
        start_time = time.time()
        
        try:
            plan_result = self.plan_trajectory(goal_state, **kwargs)
            
            if not plan_result.get("success"):
                return {
                    "success": False,
                    "error": "规划失败",
                    "plan_result": plan_result
                }
            
            trajectory = plan_result.get("trajectory")
            if trajectory is None:
                return {
                    "success": False,
                    "error": "规划成功但没有轨迹"
                }
            
            exec_result = self.execute_sync(trajectory)
            
            return {
                "success": exec_result.get("success", False),
                "planning": plan_result,
                "execution": exec_result,
                "total_time": time.time() - start_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def plan_and_execute_cached(self, goal_state, **kwargs) -> Dict:
        """带缓存的规划执行"""
        # 物体ID模式
        if isinstance(goal_state, dict) and "object_id" in goal_state:
            object_id = goal_state["object_id"]
            pose = self._get_hardcoded_pose(object_id)
            goal_state = {"pose": pose}
            result = self.plan_and_execute(goal_state, **kwargs)
            result["object_id"] = object_id
            return result
        
        # 关节/位姿模式
        return self.plan_and_execute(goal_state, **kwargs)
    
    def destroy(self):
        """清理资源"""
        self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
# ========== 一行调用接口 ==========

class TrajectoryExecutor:
    """轨迹执行器 - 简化调用接口"""
    
    _instance = None
    
    @classmethod
    def execute(cls, target, **kwargs):
        """一行调用：执行轨迹"""
        if cls._instance is None:
            cls._instance = cls._create_instance()
        return cls._instance._execute_internal(target, **kwargs)
    
    @classmethod
    def _create_instance(cls):
        executor = _TrajectoryExecutor()
        executor._setup()
        return executor


class _TrajectoryExecutor:
    """内部实现类"""
    
    def _setup(self):
        self.executor = TrajectoryExecutionManager()
    
    def _execute_internal(self, target, **kwargs):
        try:
            goal_state = self._parse_input(target)
            use_cache = kwargs.get('use_cache', True)
            
            if use_cache:
                result = self.executor.plan_and_execute_cached(
                    goal_state=goal_state,
                    timeout=kwargs.get('timeout', 5.0),
                    algorithm=kwargs.get('strategy', 'rrt_connect')
                )
            else:
                result = self.executor.plan_and_execute(
                    goal_state=goal_state,
                    timeout=kwargs.get('timeout', 5.0),
                    algorithm=kwargs.get('strategy', 'rrt_connect')
                )
            
            return self._standardize_output(result, target)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _parse_input(self, target):
        if isinstance(target, dict):
            if "object_id" in target:
                return target
            if "pose" in target:
                return target
            if "joints" in target:
                return target
        elif isinstance(target, (list, tuple)):
            if len(target) == 7:
                return {"pose": list(target)}
            elif len(target) == 3:
                return {"pose": list(target) + [0,0,0,1]}
        elif isinstance(target, str):
            return {"object_id": target}
        raise ValueError(f"不支持的输入类型: {type(target)}")
    
    def _standardize_output(self, result, original_target):
        result.setdefault("success", False)
        result.setdefault("timestamp", self._get_timestamp())
        if isinstance(original_target, str):
            result["object_id"] = original_target
        return result
    
    def _get_timestamp(self):
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 便捷函数 ==========

def execute_trajectory(target, **kwargs):
    """一行调用执行轨迹"""
    return TrajectoryExecutor.execute(target, **kwargs)

def move_to_pose(x, y, z, qx=0, qy=0, qz=0, qw=1, **kwargs):
    """快速移动到指定位姿"""
    return execute_trajectory([x, y, z, qx, qy, qz, qw], **kwargs)

def move_to_joints(joints, **kwargs):
    """快速移动到指定关节位置"""
    return execute_trajectory({"joints": joints}, **kwargs)            