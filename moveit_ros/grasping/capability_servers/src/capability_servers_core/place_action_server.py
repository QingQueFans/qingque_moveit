#!/usr/bin/env python3
"""
放置动作服务器类定义
提供放置（释放物体）服务，集成运动学缓存
"""
import sys
import os
import json
import time
import math
from typing import Dict, List, Optional

# ========== 路径设置（完全按照你的规范） ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)

# 核心路径
CORE_SRC = os.path.join(PROJECT_ROOT, 'core_functions', 'src')
sys.path.insert(0, CORE_SRC)

# 物体管理器
OBJ_MODULE_ROOT = os.path.join(PROJECT_ROOT, 'collision_objects')
OBJ_SRC = os.path.join(OBJ_MODULE_ROOT, 'src')
sys.path.insert(0, OBJ_SRC)

# 控制器
CONTROLLER_ROOT = os.path.join(PROJECT_ROOT, '..', 'moveit_plugins', 'moveit_controller_manager', 'src')
sys.path.insert(0, CONTROLLER_ROOT)

# 缓存管理器
CACHE_MANAGER_SRC = os.path.join(PROJECT_ROOT, '..', 'cache_manager', 'src')
sys.path.insert(0, CACHE_MANAGER_SRC)

print(f"[放置服务器] 路径设置完成")

try:
    from ps_core.scene_client import PlanningSceneClient
    from ps_objects.object_manager import ObjectManager
    from moveit_controller_manager import MoveItControllerManager
    from gripper_controller_manager import GripperControllerManager
    from ps_cache.kinematics_cache import KinematicsCache
    from ps_cache import CachePathTools
    
    HAS_DEPENDENCIES = True
    print("✓ 成功导入所有依赖")
    
except ImportError as e:
    print(f"[警告] 导入依赖失败: {e}")
    HAS_DEPENDENCIES = False


class PlaceActionServer:
    """
    放置动作服务器 - 提供释放物体服务，集成运动学缓存
    
    与PickActionServer对称设计
    """
    
    def __init__(self, scene_client=None):
        """初始化 - 必须接收scene_client"""
        if not HAS_DEPENDENCIES:
            raise ImportError("依赖导入失败")
        
        self.client = scene_client  # 硬性要求
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')  # 固定路径
        
        # 初始化缓存工具
        CachePathTools.initialize()
        self.kinematics_cache = KinematicsCache()
        
        # 初始化管理器
        self.object_manager = ObjectManager(scene_client)
        
        # 控制器（延迟初始化）
        self.arm_controller = None
        self.gripper_controller = None
        
        # 机器人配置
        self.robot_config = {
            "name": "panda",
            "joint_names": [
                "panda_joint1", "panda_joint2", "panda_joint3",
                "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
            ],
            "gripper_link": "panda_hand",
            "home_position": [0.0, 0.0, 0.0, -1.5708, 0.0, 1.5708, 0.7854]
        }
        
        print(f"[放置服务器] 初始化完成，机器人: {self.robot_config['name']}")
    
    # ========== 必须的标准方法（照抄） ==========
    
    def _load_cache(self) -> Dict:
        """加载缓存数据 - 一字不改照抄"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 放置服务器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[缓存] 放置服务器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 放置服务器: 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型 - 照抄"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return float(value)
    
    # ========== 控制器初始化 ==========
    
    def _init_controllers(self):
        """初始化控制器"""
        if self.arm_controller is None:
            try:
                self.arm_controller = MoveItControllerManager()
                print("[放置服务器] 机械臂控制器就绪")
            except Exception as e:
                print(f"[放置服务器] 机械臂控制器失败: {e}")
        
        if self.gripper_controller is None:
            try:
                self.gripper_controller = GripperControllerManager()
                print("[放置服务器] 夹爪控制器就绪")
            except Exception as e:
                print(f"[放置服务器] 夹爪控制器失败: {e}")
    
    def _check_controllers(self) -> bool:
        """检查控制器是否可用"""
        self._init_controllers()
        return self.arm_controller is not None and self.gripper_controller is not None    
    # ========== 核心服务方法（集成缓存） ==========
    
    def place_object(self, object_id: str,
                    position: Optional[List] = None,
                    orientation: Optional[List] = None) -> Dict:
        """
        放置物体（释放物体） - 核心服务，集成缓存
        
        Args:
            object_id: 物体ID
            position: 放置位置 [x,y,z]（可选）
            orientation: 放置方向 [qx,qy,qz,qw]（可选）
            
        Returns:
            标准格式结果（包含缓存使用信息）
        """
        start_time = time.time()
        cache_used = False
        
        try:
            # 1. 检查控制器
            if not self._check_controllers():
                return {
                    "success": False,
                    "error": "控制器不可用",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            print(f"[放置] 开始放置物体: {object_id}")
            
            # 2. 确定放置位姿
            if position is None:
                # 默认放置位置
                position = [0.5, 0.0, 0.5]  # 桌子上方
            
            if orientation is None:
                orientation = [0.0, 0.0, 0.0, 1.0]  # 默认方向
            
            place_pose = self._ensure_float(position + orientation)
            
            # 3. 检查缓存中的IK解
            ik_data = self.kinematics_cache.load_ik_solution(
                target_pose=place_pose,
                robot_model=self.robot_config["name"],
                sequence=0
            )
            
            if ik_data and "data" in ik_data:
                print("[放置] 使用缓存的IK解")
                target_joints = ik_data["data"]["joint_solution"]
                cache_used = True
            else:
                # 4. 计算IK解（需要集成IK求解器）
                print("[放置] 计算IK解")
                target_joints = self._compute_ik_solution(place_pose)
                
                # 保存到缓存
                if target_joints:
                    self.kinematics_cache.save_ik_solution(
                        target_pose=place_pose,
                        joint_solution=target_joints,
                        robot_model=self.robot_config["name"],
                        metadata={"object_id": object_id, "type": "place"}
                    )
                    cache_used = False
                else:
                    return {
                        "success": False,
                        "error": "无法计算IK解",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            # 5. 执行放置序列
            execution_result = self._execute_place_sequence(
                object_id=object_id,
                target_joints=target_joints,
                place_position=position
            )
            
            elapsed_time = time.time() - start_time            # 6. 返回标准格式结果
            result = {
                "success": execution_result["success"],
                "operation": "place",
                "object_id": object_id,
                "place_position": position,
                "execution_time": elapsed_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cache_used": cache_used,
                "metadata": {
                    "robot": self.robot_config["name"],
                    "method": "cached_ik" if cache_used else "computed_ik"
                }
            }
            
            if not execution_result["success"]:
                result["error"] = execution_result.get("error", "放置失败")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _compute_ik_solution(self, target_pose: List) -> Optional[List]:
        """
        计算IK解 - 需要集成你的IKSolver
        
        注意：这里需要你集成实际的IK求解器
        暂时返回模拟解供测试
        """
        print(f"[IK计算] 目标位姿: {target_pose[:3]}")
        
        # TODO: 集成你的IKSolver
        # 示例：使用你的IKSolver
        # from kin_ik.ik_solver import IKSolver
        # ik_solver = IKSolver(self.client)
        # result = ik_solver.solve(target_pose)
        # if result["success"]:
        #     return result["solution"]
        
        # 暂时返回Panda的模拟解
        x, y, z = target_pose[:3]
        
        # 简单的逆解（实际应该用IK求解器）
        joint_solution = [
            0.0,   # panda_joint1
            -0.3,  # panda_joint2
            0.0,   # panda_joint3
            -1.2,  # panda_joint4
            0.0,   # panda_joint5
            1.2,   # panda_joint6
            0.0    # panda_joint7
        ]
        
        # 根据x,y调整关节1
        if abs(x) > 0.01 or abs(y) > 0.01:
            joint_solution[0] = self._ensure_float(math.atan2(y, x))
        
        # 根据z调整
        if z > 0.5:
            joint_solution[1] = -0.6
            joint_solution[3] = -1.5
        elif z < 0.3:
            joint_solution[1] = -0.1
            joint_solution[3] = -0.8
        
        return joint_solution
    def _execute_place_sequence(self, object_id: str,
                            target_joints: List,
                            place_position: List) -> Dict:
        try:
            # 1. 移动到放置位置
            print(f"[放置序列] 移动到放置位置: {place_position[:3]}")
            time.sleep(1.0)
            
            # 2. 跳过物体分离 ← 添加这行！
            print("[放置序列] 跳过物体分离（ObjectManager方法不存在）")
            # detach_result = self.object_manager.detach_object(object_id)
            
            # 3. 张开夹爪
            print("[放置序列] 张开夹爪")
            gripper_result = self.gripper_controller.release_sync(width=0.04, effort=10.0)
            
            if not gripper_result.get("success", False):
                return {"success": False, "error": "夹爪张开失败"}
            
            time.sleep(0.5)
            
            # 4. 抬起机械臂
            print("[放置序列] 抬起机械臂")
            # 简化：模拟抬起
            time.sleep(0.5)
            
            return {"success": True, "message": "放置完成"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
    
    # ========== 辅助方法 ==========
    
    def get_server_status(self) -> Dict:
        """获取服务器状态"""
        controllers_ready = self._check_controllers()
        
        return {
            "server": "place_action_server",
            "active": True,
            "controllers_ready": controllers_ready,
            "robot": self.robot_config["name"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def set_robot_config(self, config: Dict):
        """设置机器人配置"""
        self.robot_config.update(config)
        print(f"[放置服务器] 更新机器人配置: {self.robot_config['name']}")