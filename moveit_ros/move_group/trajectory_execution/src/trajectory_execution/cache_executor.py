# cached_executor.py
"""
轨迹执行器缓存包装器 - 基于你的项目结构
处理6关节IK解到7关节Panda的适配
"""

import sys
import os
import json
import time
import hashlib
import math
from typing import Dict, List, Optional, Union
from pathlib import Path

# ========== 路径设置（按照你的项目结构） ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
MOVE_GROUP_ROOT = os.path.dirname(MODULE_ROOT)
PROJECT_ROOT = os.path.dirname(MOVE_GROUP_ROOT)

# 添加缓存模块路径（基于你的夹爪控制器模式）
CACHE_SRC = os.path.join(PROJECT_ROOT, 'moveit_core', 'cache_manager', 'src')
sys.path.insert(0, CACHE_SRC)

try:
    from ps_cache import CachePathTools
    HAS_CACHE_DEPENDENCIES = True
    print("[缓存包装器] ✓ 缓存模块导入成功")
except ImportError as e:
    print(f"[缓存包装器] ✗ 缓存模块导入失败: {e}")
    HAS_CACHE_DEPENDENCIES = False


class CachedTrajectoryExecutor:
    """
    轨迹执行器缓存包装器
    
    职责：
    1. 为TrajectoryExecutionManager添加缓存功能
    2. 处理6关节IK解到7关节Panda的适配
    3. 管理IK解缓存（读取、保存、清理）
    4. 提供统计信息和调试功能
    """
    
    def __init__(self, base_executor, use_cache: bool = True):
        """
        初始化缓存包装器
        
        Args:
            base_executor: TrajectoryExecutionManager实例
            use_cache: 是否启用缓存
        """
        self._executor = base_executor
        self.use_cache = use_cache
        
        # 初始化缓存系统
        self._init_cache_system()
        
        # 缓存统计
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_saves": 0,
            "adaptations_6to7": 0,
            "total_time_saved": 0.0
        }
        
        # 7关节Panda配置（与轨迹执行器匹配）
        self.panda_joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        print("[缓存包装器] 初始化完成")
        print(f"  缓存启用: {use_cache}")
        print(f"  缓存目录: {self.ik_cache_dir}")
        print(f"  关节适配: 6→7（Panda机器人）")
    
    def _init_cache_system(self):
        """初始化缓存系统"""
        try:
            if HAS_CACHE_DEPENDENCIES:
                # 使用你的缓存工具初始化
                CachePathTools.initialize()
                cache_root = CachePathTools.get_cache_root()
                self.ik_cache_dir = cache_root / "kinematics" / "ik_solutions"
                print(f"[缓存包装器] 使用系统缓存: {self.ik_cache_dir}")
            else:
                # 备选：使用相对路径
                cache_root = Path.home() / '.planning_scene_cache'
                self.ik_cache_dir = cache_root / "kinematics" / "ik_solutions"
                print(f"[缓存包装器] 使用备选缓存: {self.ik_cache_dir}")
            
            # 确保目录存在
            self.ik_cache_dir.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            print(f"[缓存包装器] 缓存初始化失败: {e}")
            # 使用临时目录
            self.ik_cache_dir = Path("/tmp/ik_cache")
            self.ik_cache_dir.mkdir(exist_ok=True)
            print(f"[缓存包装器] 使用临时缓存: {self.ik_cache_dir}")
    
    def plan_and_execute_cached(self, start_state, goal_state, **kwargs):
        """
        带缓存的规划执行
        
        Args:
            start_state: 起始状态（关节角度或位姿）
            goal_state: 目标状态（关节角度或位姿）
            **kwargs: 其他参数
            
        Returns:
            执行结果字典
        """
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        try:
            print(f"\n[缓存包装器] 规划执行请求 #{self.stats['total_requests']}")
            
            # 1. 获取目标位姿
            target_pose = self._extract_target_pose(goal_state)
            print(f"  目标位姿: {self._format_pose(target_pose)}")
            
            # 2. 检查缓存
            cached_result = None
            if self.use_cache:
                cached_result = self._check_cache(target_pose)
                
                if cached_result and cached_result.get("success"):
                    print(f"  ✅ 缓存命中！使用缓存的关节解")
                    self.stats["cache_hits"] += 1                    
                    # 执行缓存的关节解
                    execution_result = self._execute_cached_solution(
                        cached_result["joint_solution"], 
                        **kwargs
                    )
                    
                    # 计算节省的时间
                    saved_time = time.time() - start_time
                    self.stats["total_time_saved"] += saved_time
                    
                    return self._format_result(
                        success=True,
                        execution_result=execution_result,
                        cache_info={
                            "hit": True,
                            "cache_key": cached_result.get("cache_key"),
                            "saved_time": saved_time
                        }
                    )
            
            # 3. 缓存未命中或禁用缓存
            print(f"  🔄 缓存未命中，调用原始规划器")
            self.stats["cache_misses"] += 1
            
            # 使用原始执行器规划
            planning_result = self._executor.plan_trajectory(
                start_state, goal_state, **kwargs
            )
            
            if not planning_result.get("success", False):
                return planning_result
            
            # 4. 执行规划结果
            if "trajectory" in planning_result:
                execution_result = self._executor.execute_sync(
                    planning_result["trajectory"]
                )
            else:
                # 如果没有轨迹，尝试从规划结果提取关节解
                joint_solution = self._extract_joints_from_plan(planning_result)
                if joint_solution:
                    execution_result = self._execute_cached_solution(
                        joint_solution, **kwargs
                    )
                else:
                    return {
                        "success": False,
                        "error": "无法从规划结果获取关节解",
                        "planning_result": planning_result
                    }
            
            # 5. 保存到缓存（如果成功）
            if (self.use_cache and execution_result.get("success") and 
                "joint_solution" in locals()):
                
                print(f"  💾 保存到缓存")
                save_success = self._save_to_cache(
                    target_pose=target_pose,
                    joint_solution=joint_solution,
                    planning_time=planning_result.get("elapsed_time", 0),
                    metadata={
                        "start_state": self._normalize_state(start_state),
                        "goal_state": self._normalize_state(goal_state),
                        "planning_params": kwargs
                    }
                )
                
                if save_success:
                    self.stats["cache_saves"] += 1
            
            return self._format_result(
                success=execution_result.get("success", False),
                start_time = start_time,
                planning_result=planning_result,
                execution_result=execution_result,
                cache_info={
                    "hit": False,
                    "saved": self.use_cache and save_success
                }
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cache_info": {"error": "执行异常"}
            }
    
    def _check_cache(self, target_pose):
        """检查缓存"""
        # 生成缓存键
        cache_key = self._generate_cache_key(target_pose)
        cache_file = self.ik_cache_dir / f"ik_{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取关节解（处理三层结构）
            joint_solution = self._extract_joints_from_cache(data)
            if not joint_solution:
                return None            # 适配6关节到7关节
            if len(joint_solution) == 6:
                print(f"  🔧 适配6关节→7关节")
                joint_solution = self._adapt_6to7_joints(joint_solution)
                self.stats["adaptations_6to7"] += 1
            
            return {
                "success": True,
                "joint_solution": joint_solution,
                "cache_key": cache_key,
                "cache_file": str(cache_file.name),
                "timestamp": data.get("saved_at", "")
            }
            
        except Exception as e:
            print(f"[缓存检查] 错误: {e}")
            return None
    
    def _adapt_6to7_joints(self, joints_6dof):
        """将6关节适配到7关节Panda"""
        # 方案：在关节5和6之间插入新关节（设为0）
        if len(joints_6dof) == 6:
            joints_7dof = [
                joints_6dof[0],  # 关节1
                joints_6dof[1],  # 关节2
                joints_6dof[2],  # 关节3
                joints_6dof[3],  # 关节4
                joints_6dof[4],  # 关节5
                0.0,            # 关节6（新增）
                joints_6dof[5]  # 关节7（原关节6）
            ]
            return joints_7dof
        return joints_6dof
    
    def _execute_cached_solution(self, joint_solution, **kwargs):
        """执行缓存的关节解"""
        # 确保有7个关节
        if len(joint_solution) != 7:
            joint_solution = self._ensure_7_joints(joint_solution)
        
        # 创建轨迹
        trajectory = self._create_trajectory(joint_solution)
        
        # 执行
        return self._executor.execute_sync(trajectory, **kwargs)
    
    def _create_trajectory(self, joints):
        """创建关节轨迹"""
        try:
            from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
            
            trajectory = JointTrajectory()
            trajectory.joint_names = self.panda_joint_names
            
            point = JointTrajectoryPoint()
            point.positions = joints[:7]  # 确保7个关节
            point.time_from_start.sec = 2
            
            trajectory.points = [point]
            return trajectory
            
        except ImportError:
            # 模拟轨迹（用于测试）
            class MockTrajectory:
                def __init__(self):
                    self.joint_names = self.panda_joint_names
                    self.points = [MockPoint(joints)]
            
            class MockPoint:
                def __init__(self, positions):
                    self.positions = positions
                    self.time_from_start = MockTime(2)
            
            class MockTime:
                def __init__(self, sec):
                    self.sec = sec
            
            return MockTrajectory()
    
    def _save_to_cache(self, target_pose, joint_solution, planning_time, metadata):
        """保存到缓存"""
        try:
            cache_key = self._generate_cache_key(target_pose)
            cache_file = self.ik_cache_dir / f"ik_{cache_key}.json"
            
            # 创建缓存数据（按照你的三层结构）
            cache_data = {
                "data": {
                    "target_pose": target_pose,
                    "joint_solution": joint_solution,
                    "robot_model": "panda",
                    "metadata": metadata,
                    "data": {  # 第三层
                        "joint_solution": joint_solution,
                        "target_pose": target_pose,
                        "type": "ik_solution",
                        "planning_time": planning_time
                    }
                },
                "metadata": metadata,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "filepath": str(cache_file)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"  ✅ 缓存保存成功: {cache_file.name}")
            return True
            
        except Exception as e:
            print(f"  ❌ 缓存保存失败: {e}")
            return False
    
    def _generate_cache_key(self, target_pose):
        """生成缓存键（与你的缓存文件一致）"""        # 归一化位姿数据
        norm_pose = [round(float(x), 6) for x in target_pose]
        pose_str = json.dumps(norm_pose, sort_keys=True)
        
        # MD5哈希（取前12位，匹配你的文件名）
        md5_hash = hashlib.md5(pose_str.encode()).hexdigest()
        return md5_hash[:12]
    
    def _extract_joints_from_cache(self, cache_data):
        """从缓存数据提取关节解（处理三层结构）"""
        try:
            # 第一层：直接尝试
            if "joint_solution" in cache_data:
                return cache_data["joint_solution"]
            
            # 第二层：data["joint_solution"]
            if "data" in cache_data:
                data_layer = cache_data["data"]
                if isinstance(data_layer, dict):
                    if "joint_solution" in data_layer:
                        return data_layer["joint_solution"]
                    
                    # 第三层：data["data"]["joint_solution"]
                    if ("data" in data_layer and 
                        isinstance(data_layer["data"], dict) and
                        "joint_solution" in data_layer["data"]):
                        return data_layer["data"]["joint_solution"]
            
            return None
            
        except Exception as e:
            print(f"[关节提取] 错误: {e}")
            return None
    
    def _extract_target_pose(self, goal_state):
        """从目标状态提取位姿"""
        if isinstance(goal_state, dict):
            if "pose" in goal_state:
                return goal_state["pose"]
            elif "position" in goal_state and "orientation" in goal_state:
                return goal_state["position"] + goal_state["orientation"]
        
        # 默认测试位姿
        return [0.5, 0.0, 0.2, 0.0, 0.0, 0.0, 1.0]
    
    def _normalize_state(self, state):
        """归一化状态数据"""
        if isinstance(state, (list, tuple)):
            return [round(float(x), 4) for x in state]
        elif isinstance(state, dict):
            return {k: self._normalize_state(v) for k, v in state.items()}
        else:
            return state
    
    def _format_pose(self, pose):
        """格式化位姿显示"""
        if len(pose) >= 3:
            return f"({pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f})"
        return str(pose)
    
    def _format_result(self, success, **kwargs):
        """格式化结果"""
        if start_time is None:
            start_time = time.time()
        result = {
            "success": success,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time": time.time() - start_time if 'start_time' in locals() else 0
        }
        result.update(kwargs)
        return result
    
    def get_stats(self):
        """获取缓存统计"""
        hit_rate = (self.stats["cache_hits"] / max(self.stats["total_requests"], 1)) * 100
        avg_time_saved = self.stats["total_time_saved"] / max(self.stats["cache_hits"], 1)
        
        return {
            "statistics": self.stats.copy(),
            "performance": {
                "hit_rate": f"{hit_rate:.1f}%",
                "avg_time_saved": f"{avg_time_saved:.2f}s",
                "adaptation_rate": f"{self.stats['adaptations_6to7']}次"
            }
        }
    
    def clear_cache(self):
        """清空缓存"""
        try:
            for cache_file in self.ik_cache_dir.glob("ik_*.json"):
                cache_file.unlink()
            
            self.stats = {k: 0 for k in self.stats}
            print(f"[缓存包装器] 缓存已清空")
            return {"success": True, "message": "缓存已清空"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# 便捷函数
def create_cached_executor(base_executor, use_cache=True):
    """创建缓存包装器"""
    return CachedTrajectoryExecutor(base_executor, use_cache)


if __name__ == "__main__":
    print("轨迹执行器缓存包装器")
    print("=" * 50)
    print("使用方法：")
    print("1. from cached_executor import create_cached_executor")
    print("2. cached_executor = create_cached_executor(original_executor)")
    print("3. result = cached_executor.plan_and_execute_cached(start, goal)")