# planning_interface/src/planning_interface/stages/modifiers/modify_scene.py
"""
ModifyPlanningScene Stage - 添加/移除物体
"""

import sys
import os
import time
from typing import Dict, Any, Optional, List

# ========== 暴力引入路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

from ..base import Stage
from ps_objects.object_manager import ObjectManager
from ps_objects.shape_generator import ShapeGenerator


class ModifyScene(Stage):
    """
    修改规划场景 Stage
    
    负责：添加物体、移除物体
    """
    
    def __init__(self, name: str, object_manager=None):
        """
        初始化 ModifyScene Stage
        
        Args:
            name: Stage 名称
            object_manager: 物体管理器实例（可选）
        """
        super().__init__(name, "modifier")
        self.object_manager = object_manager or ObjectManager()
        self.shape_gen = ShapeGenerator()
        self.object_id = None
        self.operation = None  # 'add' 或 'remove'
    
    # ========== 添加物体 ==========
    
    def add_box(self, object_id: str, position: List[float], 
                size: List[float], orientation: Optional[List[float]] = None) -> 'ModifyScene':
        """设置添加立方体"""
        self.operation = 'add'
        self.object_id = object_id
        self.object_data = {
            'type': 'box',
            'position': position,
            'size': size,
            'orientation': orientation or [0, 0, 0, 1]
        }
        return self
    
    def add_sphere(self, object_id: str, position: List[float],
                   radius: float, orientation: Optional[List[float]] = None) -> 'ModifyScene':
        """设置添加球体"""
        self.operation = 'add'
        self.object_id = object_id
        self.object_data = {
            'type': 'sphere',
            'position': position,
            'radius': radius,
            'orientation': orientation or [0, 0, 0, 1]
        }
        return self
    
    def add_cylinder(self, object_id: str, position: List[float],
                     radius: float, height: float,
                     orientation: Optional[List[float]] = None) -> 'ModifyScene':
        """设置添加圆柱体"""
        self.operation = 'add'
        self.object_id = object_id
        self.object_data = {
            'type': 'cylinder',
            'position': position,
            'radius': radius,
            'height': height,
            'orientation': orientation or [0, 0, 0, 1]
        }
        return self
    
    # ========== 移除物体 ==========
    
    def remove(self, object_id: str) -> 'ModifyScene':
        """设置移除物体"""
        self.operation = 'remove'
        self.object_id = object_id
        return self
    
    def remove_all(self) -> 'ModifyScene':
        """设置移除所有物体"""
        self.operation = 'remove_all'
        return self
    
    # ========== 核心执行 ==========
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        执行场景修改
        """
        self.start_time = time.time()
        
        if not self.operation:
            self.last_error = "未设置操作，请先调用 add_xxx() 或 remove()"
            self.last_result = {"success": False, "error": self.last_error}
            return self.last_result
        
        try:
            if self.operation == 'add':
                self.last_result = self._do_add()
            elif self.operation == 'remove':
                self.last_result = self._do_remove()
            elif self.operation == 'remove_all':
                self.last_result = self._do_remove_all()
            else:
                self.last_result = {"success": False, "error": f"未知操作: {self.operation}"}
        
        except Exception as e:
            self.last_error = str(e)
            self.last_result = {"success": False, "error": str(e)}
        
        self.end_time = time.time()
        return self.last_result
    
    def _do_add(self) -> Dict:
        """执行添加物体"""
        obj_type = self.object_data['type']
        
        # ===== 确保所有数值都是 float =====
        position = [float(x) for x in self.object_data['position']]
        orientation = [float(x) for x in self.object_data['orientation']]
        
        if obj_type == 'box':
            size = [float(x) for x in self.object_data['size']]
            obj = self.shape_gen.create_box(
                name=self.object_id,
                position=position,
                size=size,
                orientation=orientation
            )
        elif obj_type == 'sphere':
            radius = float(self.object_data['radius'])
            obj = self.shape_gen.create_sphere(
                name=self.object_id,
                position=position,
                radius=radius,
                orientation=orientation
            )
        elif obj_type == 'cylinder':
            radius = float(self.object_data['radius'])
            height = float(self.object_data['height'])
            obj = self.shape_gen.create_cylinder(
                name=self.object_id,
                position=position,
                radius=radius,
                height=height,
                orientation=orientation
            )
        else:
            return {"success": False, "error": f"未知物体类型: {obj_type}"}
        
        success = self.object_manager.add_object_simple(obj)
        return {
            "success": success,
            "operation": "add",
            "object_id": self.object_id,
            "object_type": obj_type
        }
    
    def _do_remove(self) -> Dict:
        """执行移除物体"""
        success = self.object_manager.remove_object_simple(self.object_id)
        return {
            "success": success,
            "operation": "remove",
            "object_id": self.object_id
        }
    
    def _do_remove_all(self) -> Dict:
        """执行移除所有物体"""
        success = self.object_manager.clear_all_objects()
        return {
            "success": success,
            "operation": "remove_all"
        }
    
    # ========== 链式配置 ==========
    
    def set_object(self, object_id: str):
        """设置物体ID（用于移除）"""
        self.object_id = object_id
        self._target = object_id
        return self
    
    # ========== 静态工厂方法 ==========
    
    @classmethod
    def create_box(cls, object_id: str, position: List[float],
                   size: List[float], **kwargs) -> Dict:
        """一行调用：创建立方体"""
        stage = cls("static_add")
        stage.add_box(object_id, position, size, kwargs.get('orientation'))
        return stage.run()
    
    @classmethod
    def remove_object(cls, object_id: str) -> Dict:
        """一行调用：移除物体"""
        stage = cls("static_remove")
        stage.remove(object_id)
        return stage.run()
    
    @classmethod
    def clear_scene(cls) -> Dict:
        """一行调用：清空场景"""
        stage = cls("static_clear")
        stage.remove_all()
        return stage.run()
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["operation"] = self.operation
        base_dict["object_id"] = self.object_id
        if hasattr(self, 'object_data'):
            base_dict["object_data"] = self.object_data
        return base_dict


# ========== 快捷函数 ==========

def add_box(object_id: str, position: List[float], size: List[float], **kwargs) -> Dict:
    """快捷添加立方体"""
    return ModifyScene.create_box(object_id, position, size, **kwargs)

def remove_object(object_id: str) -> Dict:
    """快捷移除物体"""
    return ModifyScene.remove_object(object_id)

def clear_scene() -> Dict:
    """快捷清空场景"""
    return ModifyScene.clear_scene()


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 ModifyScene Stage ===\n")
    
    # 测试添加物体
    stage = ModifyScene("test_add")
    stage.add_box("test_box", [0.5, 0.0, 0.3], [0.1, 0.1, 0.1])
    result = stage.run()
    print(f"添加物体: {result.get('success')}")
    print(f"Stage: {stage}")
    
    # 测试链式调用
    result = (ModifyScene("chain_remove")
              .remove("test_box")
              .execute())
    print(f"移除物体: {result.get('success')}")
    
    # 测试静态方法
    result = ModifyScene.create_box("static_box", [0.6, 0.0, 0.3], [0.1, 0.1, 0.1])
    print(f"静态添加: {result.get('success')}")
    
    result = ModifyScene.remove_object("static_box")
    print(f"静态移除: {result.get('success')}")
    
    # 测试清空场景
    result = ModifyScene.clear_scene()
    print(f"清空场景: {result.get('success')}")
    
    # 显示调试信息
    print(f"\n调试信息: {stage.to_dict()}")