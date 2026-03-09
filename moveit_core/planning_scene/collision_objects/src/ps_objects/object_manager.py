#!/usr/bin/env python3
"""
物体管理器 - pymoveit2 版
"""

from typing import List, Optional, Dict, Any
import time
import json
import os
import sys
import rclpy

# ========== 路径处理 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)
MOVEIT_CORE_ROOT = os.path.dirname(PROJECT_ROOT)
MOVEIT_CORE_ROOT = os.path.dirname(MOVEIT_CORE_ROOT)

# 添加路径
CORE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
sys.path.insert(0, CORE_SRC)
CACHE_MANAGER_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')
sys.path.insert(0, CACHE_MANAGER_SRC)
sys.path.insert(0, MODULE_ROOT)

# ========== 导入 ==========
# 缓存系统
try:
    from ps_cache.cache_manager import CachePathTools
    from ps_cache.object_cache import ObjectCache
    HAS_UNIFIED_CACHE = True
except ImportError:
    HAS_UNIFIED_CACHE = False

# pymoveit2
try:
    from pymoveit2 import MoveIt2
    from pymoveit2 import MoveIt2Gripper
    HAS_PYMOVEIT = True
except ImportError:
    HAS_PYMOVEIT = False


class ObjectManager:
    """碰撞物体管理器 - pymoveit2 版"""
    
    def __init__(self, moveit2: MoveIt2 = None):
        self.moveit2 = moveit2
        
        if self.moveit2 is None and HAS_PYMOVEIT:
            try:
                if not rclpy.ok():
                    rclpy.init()
                from rclpy.node import Node
                node = Node("object_manager_node")
                self.moveit2 = MoveIt2(
                    node=node,
                    joint_names=["panda_joint1", "panda_joint2", "panda_joint3",
                                 "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"],
                    base_link_name="panda_link0",
                    end_effector_name="panda_hand",
                    group_name="panda_arm"
                )
            except Exception as e:
                print(f"[ObjectManager] 创建 MoveIt2 失败: {e}")
        
        # 缓存系统
        self.unified_cache_manager = None
        if HAS_UNIFIED_CACHE:
            try:
                self.unified_cache_manager = ObjectCache()
            except Exception:
                pass
        
        self._init_cache()
    
    # ========== 缓存系统 ==========
    
    def _init_cache(self):
        home_dir = os.path.expanduser("~")
        cache_dir = os.path.join(home_dir, ".planning_scene_cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = os.path.join(cache_dir, "objects.json")
        self.object_cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.object_cache, f, indent=2)
        except:
            pass
    
    def _extract_object_data(self, collision_object) -> Dict[str, Any]:
        data = {
            'id': collision_object.id,
            'operation': 'ADD' if getattr(collision_object, 'operation', b'\x00') == b'\x00' else 'REMOVE',
            'frame_id': collision_object.header.frame_id if hasattr(collision_object.header, 'frame_id') else '',
            'cached_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if hasattr(collision_object, 'primitives') and collision_object.primitives:
            primitive = collision_object.primitives[0]
            data['primitive_type'] = int(primitive.type)
            if hasattr(primitive, 'dimensions'):
                data['dimensions'] = [float(d) for d in primitive.dimensions]
            type_map = {1: 'box', 2: 'sphere', 3: 'cylinder', 4: 'cone'}
            data['type'] = type_map.get(data['primitive_type'], 'unknown')
        
        if hasattr(collision_object, 'primitive_poses') and collision_object.primitive_poses:
            pose = collision_object.primitive_poses[0]
            data['position'] = [
                float(pose.position.x),
                float(pose.position.y),
                float(pose.position.z)
            ]
            data['orientation'] = [
                float(pose.orientation.x),
                float(pose.orientation.y),
                float(pose.orientation.z),
                float(pose.orientation.w)
            ]
        
        return data
    
    def _save_object_to_unified_cache(self, collision_object) -> str:
        if not self.unified_cache_manager:
            return ""
        try:
            object_data = self._extract_object_data(collision_object)
            object_type = object_data.get('type', 'mesh')
            cache_path = self.unified_cache_manager.save_object_info(
                object_id=collision_object.id,
                object_data=object_data,
                object_type=object_type
            )
            return cache_path
        except Exception:
            return ""
    
    # ========== pymoveit2 核心方法 ==========
    
    def add_object_simple(self, collision_object) -> bool:
        """添加物体 - 用 pymoveit2 实现（返回 None 版本）"""
        if not self.moveit2:
            print("[错误] moveit2 未初始化")
            return False
        
        try:
            obj_id = collision_object.id
            
            # 提取位置和姿态
            if collision_object.primitive_poses:
                pose = collision_object.primitive_poses[0]
                position = (pose.position.x, pose.position.y, pose.position.z)
                quat = (pose.orientation.x, pose.orientation.y, 
                       pose.orientation.z, pose.orientation.w)
            else:
                position = (0.0, 0.0, 0.0)
                quat = (0.0, 0.0, 0.0, 1.0)
            
            if not collision_object.primitives:
                print("[错误] 没有 primitive 信息")
                return False
            
            primitive = collision_object.primitives[0]
            
            # pymoveit2 返回 None，所以只能假设成功
            # 真正的成功与否需要通过其他方式验证
            if primitive.type == 1:  # BOX
                size = tuple(primitive.dimensions[:3]) if primitive.dimensions else (0.1, 0.1, 0.1)
                self.moveit2.add_collision_box(
                    id=obj_id,
                    size=size,
                    position=position,
                    quat_xyzw=quat,
                    frame_id="world"
                )
                
            elif primitive.type == 2:  # SPHERE
                radius = primitive.dimensions[0] if primitive.dimensions else 0.05
                self.moveit2.add_collision_sphere(
                    id=obj_id,
                    radius=radius,
                    position=position,
                    quat_xyzw=quat,
                    frame_id="world"
                )
                
            elif primitive.type == 3:  # CYLINDER
                height = primitive.dimensions[0] if len(primitive.dimensions) > 0 else 0.1
                radius = primitive.dimensions[1] if len(primitive.dimensions) > 1 else 0.05
                self.moveit2.add_collision_cylinder(
                    id=obj_id,
                    height=height,
                    radius=radius,
                    position=position,
                    quat_xyzw=quat,
                    frame_id="world"
                )
                
            elif primitive.type == 4:  # CONE
                height = primitive.dimensions[0] if len(primitive.dimensions) > 0 else 0.1
                radius = primitive.dimensions[1] if len(primitive.dimensions) > 1 else 0.05
                self.moveit2.add_collision_cone(
                    id=obj_id,
                    height=height,
                    radius=radius,
                    position=position,
                    quat_xyzw=quat,
                    frame_id="world"
                )
                
            else:
                print(f"[错误] 不支持的 primitive 类型: {primitive.type}")
                return False
            
            # 由于 pymoveit2 返回 None，我们假设成功
            # 可以稍后通过验证来确认
            time.sleep(0.2)  # 给点时间让场景更新
            
            # 保存到缓存
            self._save_object_to_unified_cache(collision_object)
            self.object_cache[obj_id] = self._extract_object_data(collision_object)
            self._save_cache()
            print(f"[物体] ✓ 添加成功: {obj_id}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 添加物体失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_object_simple(self, object_id: str) -> bool:
        try:
            # 1. 从场景移除
            self.moveit2.remove_collision_object(object_id)
            time.sleep(0.2)
            
            # 2. 从本地缓存删除
            if object_id in self.object_cache:
                del self.object_cache[object_id]
                self._save_cache()
            
            # 3. 从统一缓存删除 ✅ 现在能用了
            if self.unified_cache_manager:
                self.unified_cache_manager.remove_object(object_id)
            
            return True
        except Exception as e:
            print(f"[ObjectManager] 移除物体失败: {e}")
            return False
    def remove_objects_simple(self, object_ids: List[str]) -> bool:
        success_all = True
        for obj_id in object_ids:
            if not self.remove_object_simple(obj_id):
                success_all = False
        return success_all
    def move_object_simple(self, object_id: str, new_position: List[float], 
                        new_orientation: Optional[List[float]] = None) -> bool:
        """移动物体 - 用删除后添加实现"""
        try:
            print(f"[ObjectManager] 移动物体: {object_id} -> {new_position}")
            
            # 1. 从缓存获取物体信息
            obj_info = self.get_object_info(object_id)
            if not obj_info:
                print(f"[错误] 找不到物体 {object_id} 的信息")
                return False
            
            # 2. 删除原物体（场景和缓存）
            if not self.remove_object_simple(object_id):
                print(f"[错误] 删除原物体失败")
                return False
            
            # 3. 准备新位置的物体数据
            obj_info['position'] = new_position
            if new_orientation:
                obj_info['orientation'] = new_orientation
            else:
                obj_info['orientation'] = [0, 0, 0, 1]
            
            # 4. 重新添加物体
            from moveit_msgs.msg import CollisionObject
            from shape_msgs.msg import SolidPrimitive
            from geometry_msgs.msg import Pose
            
            # 创建碰撞物体
            obj = CollisionObject()
            obj.id = object_id
            obj.operation = b'\x00'  # ADD
            obj.header.frame_id = "world"
            
            # 创建 primitive
            primitive = SolidPrimitive()
            obj_type = obj_info.get('type', 'box')
            
            if obj_type == 'box':
                primitive.type = SolidPrimitive.BOX
                primitive.dimensions = obj_info.get('dimensions', [0.1, 0.1, 0.1])
            elif obj_type == 'sphere':
                primitive.type = SolidPrimitive.SPHERE
                primitive.dimensions = [obj_info.get('radius', 0.05)]
            elif obj_type == 'cylinder':
                primitive.type = SolidPrimitive.CYLINDER
                primitive.dimensions = [
                    obj_info.get('height', 0.1),
                    obj_info.get('radius', 0.05)
                ]
            
            obj.primitives = [primitive]
            
            # 设置位姿
            pose = Pose()
            pose.position.x = new_position[0]
            pose.position.y = new_position[1]
            pose.position.z = new_position[2]
            
            orient = obj_info.get('orientation', [0,0,0,1])
            pose.orientation.x = orient[0]
            pose.orientation.y = orient[1]
            pose.orientation.z = orient[2]
            pose.orientation.w = orient[3]
            
            obj.primitive_poses = [pose]
            
            # 5. 添加到场景（复用 add_object_simple）
            success = self.add_object_simple(obj)
            
            if success:
                print(f"[ObjectManager] ✓ 移动成功: {object_id}")
            else:
                print(f"[ObjectManager] ✗ 移动失败: {object_id}")
            
            return success
            
        except Exception as e:
            print(f"[ObjectManager] 移动物体失败: {e}")
            import traceback
            traceback.print_exc()
            return False    
    def clear_all_objects(self) -> bool:
        if not self.moveit2:
            return False
        try:
            self.moveit2.clear_all_collision_objects()
            time.sleep(0.2)
            self.object_cache.clear()
            self._save_cache()
            return True
        except Exception:
            return False
    
    # ========== 查询方法 ==========
    
    def list_objects(self) -> List[str]:
        return list(self.object_cache.keys())
    
    def get_object_info(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.object_cache.get(object_id)
    
    def get_object_from_cache(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.object_cache.get(object_id)
    
    def list_cached_objects(self) -> List[str]:
        return list(self.object_cache.keys())
    
    def clear_cache(self):
        self.object_cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
    
    def show_cache_info(self):
        print(f"[缓存] 缓存物体数量: {len(self.object_cache)}")
        for obj_id, data in self.object_cache.items():
            print(f"  - {obj_id}: {data.get('type', 'unknown')}")
    
    def check_unified_cache_status(self):
        if not self.unified_cache_manager:
            return {"available": False, "message": "统一缓存管理器不可用"}
        try:
            cache_root = CachePathTools.get_cache_root()
            return {"available": True, "cache_root": str(cache_root)}
        except Exception as e:
            return {"available": False, "message": str(e)}


# ========== 外观类（一行调用接口） ==========
class ObjectManagerFacade:
    _instance = None
    _moveit2_instance = None
    
    @classmethod
    def initialize(cls, moveit2=None):
        cls._moveit2_instance = moveit2
    
    @classmethod
    def get_manager(cls):
        if cls._instance is None:
            cls._instance = cls._create_instance()
        return cls._instance
    
    @classmethod
    def _create_instance(cls):
        try:
            manager = ObjectManager(cls._moveit2_instance)
            return manager
        except Exception as e:
            print(f"[ObjectManagerFacade] 初始化失败: {e}")
            return None
    
    @classmethod
    def add_object(cls, object_data, **kwargs):
        manager = cls.get_manager()
        if not manager:
            return {"success": False, "error": "管理器未初始化"}
        try:
            collision_object = cls._parse_object_data(object_data, **kwargs)
            success = manager.add_object_simple(collision_object)
            return {
                "success": success,
                "object_id": collision_object.id,
                "timestamp": cls._get_timestamp()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @classmethod
    def _parse_object_data(cls, data, **kwargs):
        from moveit_msgs.msg import CollisionObject
        from shape_msgs.msg import SolidPrimitive
        from geometry_msgs.msg import Pose
        
        obj = CollisionObject()
        
        if isinstance(data, CollisionObject):
            return data
        
        elif isinstance(data, dict):
            obj.id = data.get("id", kwargs.get("object_id", "object"))
            
            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.BOX
            primitive.dimensions = data.get("dimensions", kwargs.get("dimensions", [0.1, 0.1, 0.1]))
            
            obj.primitives = [primitive]
            
            pose = Pose()
            position = data.get("position", kwargs.get("position", [0.5, 0.3, 0.4]))
            orientation = data.get("orientation", kwargs.get("orientation", [0.0, 0.0, 0.0, 1.0]))
            
            pose.position.x = position[0]
            pose.position.y = position[1]
            pose.position.z = position[2]
            pose.orientation.x = orientation[0]
            pose.orientation.y = orientation[1]
            pose.orientation.z = orientation[2]
            pose.orientation.w = orientation[3]
            
            obj.primitive_poses = [pose]
            obj.operation = b'\x00'
            obj.header.frame_id = "world"
            
            return obj
        
        elif isinstance(data, (list, tuple)) and len(data) >= 3:
            obj.id = kwargs.get("object_id", f"object_{int(time.time())}")
            
            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.BOX
            
            if len(data) >= 6:
                primitive.dimensions = list(data[3:6])
            else:
                primitive.dimensions = kwargs.get("dimensions", [0.1, 0.1, 0.1])
            
            obj.primitives = [primitive]
            
            pose = Pose()
            pose.position.x = data[0]
            pose.position.y = data[1]
            pose.position.z = data[2]
            pose.orientation.x = kwargs.get("qx", 0.0)
            pose.orientation.y = kwargs.get("qy", 0.0)
            pose.orientation.z = kwargs.get("qz", 0.0)
            pose.orientation.w = kwargs.get("qw", 1.0)
            
            obj.primitive_poses = [pose]
            obj.operation = b'\x00'
            obj.header.frame_id = "world"
            
            return obj
        
        else:
            raise ValueError(f"不支持的输入类型: {type(data)}")
    
    @classmethod
    def _get_timestamp(cls):
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 全局便捷函数 ==========
_facade_initialized = False

def init_object_manager(moveit2=None):
    ObjectManagerFacade.initialize(moveit2)
    global _facade_initialized
    _facade_initialized = True
    return ObjectManagerFacade.get_manager()

def add_object(object_data, **kwargs):
    return ObjectManagerFacade.add_object(object_data, **kwargs)

def remove_object(object_id):
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    success = manager.remove_object_simple(object_id)
    return {"success": success, "object_id": object_id}

def list_objects():
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return []
    objects = manager.list_objects()
    cached_objects = manager.list_cached_objects()
    return {"scene_objects": objects, "cached_objects": cached_objects}

def clear_all_objects():
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    success = manager.clear_all_objects()
    return {"success": success}

def create_box(object_id, x, y, z, width=0.1, height=0.1, depth=0.1):
    return add_object({
        "id": object_id,
        "position": [x, y, z],
        "dimensions": [width, height, depth]
    })

def create_sphere(object_id, x, y, z, radius=0.05):
    return add_object({
        "id": object_id,
        "type": "sphere",
        "position": [x, y, z],
        "radius": radius
    })