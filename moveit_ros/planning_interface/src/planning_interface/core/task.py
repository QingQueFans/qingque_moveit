# planning_interface/src/planning_interface/core/task.py
"""
Task - 整个抓取任务
把 Stage 组合成完整的工作流
"""

import sys
import os
import time
from typing import Dict, Any, Optional, List, Union

# ========== 暴力引入路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

from ..stages.base import Stage
from ..stages.propagators.move_to import MoveTo
from ..stages.modifiers.attach import AttachObject
from ..stages.modifiers.modify_scene import ModifyScene
from ..containers.serial import SerialContainer
from ..knowledge.objects.cache import ObjectCache


# ========== 常量定义 ==========
PANDA_JOINT_NAMES = [
    "panda_joint1", "panda_joint2", "panda_joint3",
    "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
]


class Task:
    """
    整个抓取任务
    
    把 Stage 组合成完整的工作流
    对应 MTC 的 Task 概念
    """
    
    def __init__(self, name: str = "grasp_task"):
        """
        初始化 Task
        
        Args:
            name: 任务名称
        """
        self.name = name
        self.container = SerialContainer(name)
        self.object_cache = ObjectCache()
        
        # ===== 创建 ROS2 节点 =====
        import rclpy
        from rclpy.node import Node
        from pymoveit2 import MoveIt2
        from ps_objects.object_manager import ObjectManager
        
        if not rclpy.ok():
            rclpy.init()
        self.node = Node(f"{name}_node")
        
        # ===== 创建 moveit2 实例 =====
        self.moveit2 = MoveIt2(
            node=self.node,
            joint_names=PANDA_JOINT_NAMES,
            base_link_name="panda_link0",
            end_effector_name="panda_hand",
            group_name="panda_arm"
        )
        
        # ===== 传给 ObjectManager =====
        self.object_manager = ObjectManager(moveit2=self.moveit2)
        
        self.last_result = None
        self.start_time = None
        self.end_time = None
    
    # ========== 添加 Stage ==========
    
    def add(self, stage: Stage) -> 'Task':
        """添加 Stage 到任务"""
        self.container.add(stage)
        return self
    
    def add_stages(self, stages: List[Stage]) -> 'Task':
        """批量添加 Stage"""
        for stage in stages:
            self.container.add(stage)
        return self
    
    # ========== 执行任务 ==========
    
    def run(self) -> Dict[str, Any]:
        """执行整个任务"""
        self.start_time = time.time()
        self.last_result = self.container.run()
        self.end_time = time.time()
        return self.last_result
    
    # ========== 预定义任务 ==========
    
    def grasp_object(self, object_id: str, 
                     width_mm: Optional[float] = None,
                     strategy: str = "auto",
                     approach_distance: float = 0.1) -> Dict[str, Any]:
        """
        完整的抓取任务
        
        流程：
        1. 获取物体位姿（从缓存）
        2. 移动到预抓取位（approach）
        3. 移动到抓取位
        4. 抓取物体
        5. 撤退
        """
        print(f"\n🎯 [Task] 抓取物体: {object_id}")
        
        # 1. 获取物体位姿
        pose = self.object_cache.get_pose(object_id)
        if not pose:
            print(f"❌ 缓存中未找到物体: {object_id}")
            return {"success": False, "error": f"缓存中未找到物体: {object_id}"}
        
        print(f"✅ 获取到位姿: {pose[:3]}")
            
        # 计算预抓取位（沿z轴后退）
        pre_pose = pose.copy()
        pre_pose[2] += approach_distance  # 抬高
        
        # 2. 清空容器
        self.container = SerialContainer(f"{self.name}_container")
        
        # 3. 添加 Stage
        # 移动到预抓取位
        self.add(MoveTo("move_to_pre").set_target(pre_pose))
        
        # 移动到抓取位
        self.add(MoveTo("move_to_grasp").set_target(pose))
        
        # 抓取物体
        if width_mm:
            self.add(AttachObject("grasp").set_object(object_id).set_width(width_mm))
        else:
            self.add(AttachObject("grasp").set_object(object_id).set_strategy(strategy))
        
        # 撤退（可选）
        retreat_pose = pre_pose.copy()
        retreat_pose[2] += 0.1  # 再抬高一点
        self.add(MoveTo("retreat").set_target(retreat_pose))
        
        # 4. 执行任务
        result = self.run()
        
        # 5. 返回结果
        return {
            "success": result.get("success", False),
            "object_id": object_id,
            "stages": [s.to_dict() for s in self.container.stages],
            "total_time": self.get_duration(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def move_to_pose(self, pose: List[float], **kwargs) -> Dict[str, Any]:
        """简单移动任务"""
        self.container = SerialContainer(f"{self.name}_container")
        self.add(MoveTo("move").set_target(pose).configure(**kwargs))
        return self.run()
    
    def move_to_joints(self, joints: List[float], **kwargs) -> Dict[str, Any]:
        """移动到关节位置"""
        self.container = SerialContainer(f"{self.name}_container")
        self.add(MoveTo("move").set_target({"joints": joints}).configure(**kwargs))
        return self.run()
    
    def add_object(self, object_id: str, position: List[float], 
                   size: List[float], **kwargs) -> Dict[str, Any]:
        """添加立方体任务"""
        self.container = SerialContainer(f"{self.name}_container")
        self.add(ModifyScene("add").add_box(object_id, position, size))
        return self.run()
    
    def add_sphere(self, object_id: str, position: List[float], 
                   radius: float, orientation: Optional[List[float]] = None) -> Dict[str, Any]:
        """添加球体任务"""
        self.container = SerialContainer(f"{self.name}_container")
        stage = ModifyScene("add_sphere").add_sphere(
            object_id, position, radius, orientation
        )
        self.add(stage)
        return self.run()
    
    def add_cylinder(self, object_id: str, position: List[float],
                     radius: float, height: float,
                     orientation: Optional[List[float]] = None) -> Dict[str, Any]:
        """添加圆柱体任务"""
        self.container = SerialContainer(f"{self.name}_container")
        stage = ModifyScene("add_cylinder").add_cylinder(
            object_id, position, radius, height, orientation
        )
        self.add(stage)
        return self.run()
    
    def remove_object(self, object_id: str) -> Dict[str, Any]:
        """移除物体任务"""
        self.container = SerialContainer(f"{self.name}_container")
        self.add(ModifyScene("remove").remove(object_id))
        return self.run()
    def move_object(self, object_id: str, new_position: List[float],
                    new_orientation: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        移动物体到新位置
        
        Args:
            object_id: 物体ID
            new_position: 新位置 [x, y, z]
            new_orientation: 新方向 [qx, qy, qz, qw] (可选)
        
        Returns:
            结果字典
        """
        print(f"\n🎯 [Task] 移动物体: {object_id} -> {new_position}")
        
        try:
            # 调用 object_manager 的移动方法
            # 注意：你的 object_manager 已经加了 move_object_simple
            success = self.object_manager.move_object_simple(
                object_id, new_position, new_orientation
            )
            
            return {
                "success": success,
                "object_id": object_id,
                "new_position": new_position,
                "message": f"移动{'成功' if success else '失败'}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ [Task] 移动物体失败: {e}")
            return {
                "success": False,
                "object_id": object_id,
                "message": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }    
        
    def clear_scene(self) -> Dict[str, Any]:
        """清空场景任务"""
        self.container = SerialContainer(f"{self.name}_container")
        stage = ModifyScene("clear").remove_all()
        self.add(stage)
        return self.run()
    
    def list_objects(self) -> List[str]:
        """列出场景中所有物体"""
        return self.object_manager.list_objects()

    def get_object_info(self, object_id: str) -> Optional[Dict]:
        """获取物体详细信息"""
        return self.object_manager.get_object_info(object_id)
    def get_object_pose(self, object_id: str) -> Optional[List[float]]:
        """获取物体7维位姿 [x,y,z,qx,qy,qz,qw]"""
        return self.object_cache.get_pose(object_id)

    def get_object_dimensions(self, object_id: str) -> Optional[Dict]:
        """获取物体尺寸信息"""
        return self.object_cache.get_dimensions(object_id)    
    # ========== 状态查询 ==========
    
    def get_duration(self) -> float:
        """获取任务执行时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def get_stage_results(self) -> List[Dict]:
        """获取每个 Stage 的结果"""
        return [s.to_dict() for s in self.container.stages]
    
    def was_successful(self) -> bool:
        """任务是否成功"""
        return self.last_result.get("success", False) if self.last_result else False
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "success": self.was_successful(),
            "duration": self.get_duration(),
            "stages": self.get_stage_results()
        }
    
    def __repr__(self) -> str:
        status = "✓" if self.was_successful() else "✗" if self.last_result else "○"
        return f"Task(name='{self.name}', {status}, stages={len(self.container.stages)})"


# ========== 快捷函数 ==========

def grasp_object(object_id: str, **kwargs) -> Dict:
    """快捷抓取物体"""
    task = Task("grasp")
    return task.grasp_object(object_id, **kwargs)

def move_to_pose(pose: List[float], **kwargs) -> Dict:
    """快捷移动到位姿"""
    task = Task("move")
    return task.move_to_pose(pose, **kwargs)

def move_to_joints(joints: List[float], **kwargs) -> Dict:
    """快捷移动到关节"""
    task = Task("move")
    return task.move_to_joints(joints, **kwargs)

def add_box(object_id: str, position: List[float], size: List[float]) -> Dict:
    """快捷添加立方体"""
    task = Task("add")
    return task.add_object(object_id, position, size)
def add_sphere(object_id: str, position: List[float], radius: float) -> Dict:
    """快捷添加球体"""
    task = Task("add_sphere")
    return task.add_sphere(object_id, position, radius)

def add_cylinder(object_id: str, position: List[float], radius: float, height: float) -> Dict:
    """快捷添加圆柱体"""
    task = Task("add_cylinder")
    return task.add_cylinder(object_id, position, radius, height)

def get_object_pose(object_id: str) -> Optional[List[float]]:
    """快捷获取物体位姿"""
    task = Task("get_pose")
    return task.get_object_pose(object_id)

def get_object_dimensions(object_id: str) -> Optional[Dict]:
    """快捷获取物体尺寸"""
    task = Task("get_dimensions")
    return task.get_object_dimensions(object_id)
def remove_object(object_id: str) -> Dict:
    """快捷移除物体"""
    task = Task("remove")
    return task.remove_object(object_id)
def get_object_pose(object_id: str) -> Optional[List[float]]:
    """快捷获取物体位姿"""
    task = Task("get_pose")
    return task.get_object_pose(object_id)

def get_object_dimensions(object_id: str) -> Optional[Dict]:
    """快捷获取物体尺寸"""
    task = Task("get_dimensions")
    return task.get_object_dimensions(object_id)
# ===== 新增：移动物体的快捷函数 =====
def move_object(object_id: str, new_position: List[float], 
                new_orientation: Optional[List[float]] = None) -> Dict:
    """快捷移动物体到新位置"""
    task = Task("move_object")
    return task.move_object(object_id, new_position, new_orientation)

# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 Task ===\n")
    
    task = Task("test_task")
    print(f"创建 Task: {task}")
    
    # 测试抓取任务
    result = task.grasp_object("train_1")
    print(f"抓取结果: {result.get('success')}")
    
    # 测试移动任务
    result = task.move_to_pose([0.5, 0.0, 0.3, 0,0,0,1])
    print(f"移动结果: {result.get('success')}")
    
    # 显示调试信息
    print(f"\n调试信息: {task.to_dict()}")