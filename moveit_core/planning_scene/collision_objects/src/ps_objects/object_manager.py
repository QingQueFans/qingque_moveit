#!/usr/bin/env python3
"""
物体管理器 - 简化可靠版本（带文件缓存）
"""

from typing import List, Optional, Dict, Any
import time
import json
import os
import sys

# ========== 修复导入路径（与可执行脚本保持一致） ==========
# 基于您的脚本的路径计算逻辑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # ps_objects/
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)                # src/
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)              # collision_objects/
MOVEIT_CORE_ROOT = os.path.dirname(PROJECT_ROOT)         # planning_scene/
# 这里还需要再上一层才是 moveit_core！
MOVEIT_CORE_ROOT = os.path.dirname(MOVEIT_CORE_ROOT)     # moveit_core/

print(f"[ObjectManager路径计算]")
print(f"  文件: {__file__}")
print(f"  脚本目录: {SCRIPT_DIR}")
print(f"  模块根目录: {MODULE_ROOT}")
print(f"  项目根目录: {PROJECT_ROOT}")
print(f"  MoveIt核心根目录: {MOVEIT_CORE_ROOT}")

# 现在设置路径
# 1. 规划场景核心
CORE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
sys.path.insert(0, CORE_SRC)
print(f"  规划场景核心: {CORE_SRC}")

# 2. 缓存管理器
CACHE_MANAGER_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')
sys.path.insert(0, CACHE_MANAGER_SRC)
print(f"  缓存管理器: {CACHE_MANAGER_SRC}")

# 3. 添加当前模块的父目录（以便导入其他ps_objects模块）
sys.path.insert(0, MODULE_ROOT)
print(f"  当前模块路径: {MODULE_ROOT}")

# 现在尝试导入
try:
    from ps_core.scene_client import PlanningSceneClient
    print("[ObjectManager] ✓ 规划场景客户端已导入")
except ImportError as e:
    print(f"[ObjectManager] ✗ ps_core导入失败: {e}")
    # 尝试其他可能的路径
    try:
        # 如果ps_core在其他位置
        import sys
        for path in sys.path:
            print(f"  搜索路径: {path}")
    except:
        pass

try:
    from ps_cache.cache_manager import CachePathTools
    from ps_cache.object_cache import ObjectCache
    HAS_UNIFIED_CACHE = True
    print("[ObjectManager] ✓ 统一缓存系统已导入")
except ImportError as e:
    HAS_UNIFIED_CACHE = False
    print(f"[ObjectManager] ✗ ps_cache导入失败: {e}")

class ObjectManager:
    """碰撞物体管理器 - 简单可靠版本（带文件缓存）"""
    def __init__(self, scene_client):
        self.client = scene_client
        
        # 新的统一缓存（使用不同的属性名）
        if HAS_UNIFIED_CACHE:
            try:
                self.unified_cache_manager = ObjectCache()  # ⚠️ 改名！
                print("[缓存] ✓ 统一缓存系统就绪")
            except Exception as e:
                print(f"[缓存] ✗ 统一缓存初始化失败: {e}")
                self.unified_cache_manager = None
        else:
            self.unified_cache_manager = None
            
        # 原有的简单缓存初始化（保持不变，但不再使用）
        self._init_cache()    

###########################缓存系统的添加###############################        
    def _save_object_to_unified_cache(self, collision_object) -> str:
        """
        保存物体到统一缓存 - 修复版
        """
        # 使用正确的缓存管理器属性
        if not hasattr(self, 'unified_cache_manager') or not self.unified_cache_manager:
            print("[统一缓存] ⚠️ 统一缓存管理器不可用")
            return ""
        
        try:
            # 提取物体数据
            object_data = self._extract_object_data(collision_object)
            
            # 确定物体类型
            object_type = object_data.get('type', 'mesh')
            
            # ⚠️ 修复：使用 unified_cache_manager 而不是 object_cache
            cache_path = self.unified_cache_manager.save_object_info(
                object_id=collision_object.id,
                object_data=object_data,
                object_type=object_type
            )
            
            if cache_path:
                print(f"[统一缓存] ✅ 物体 '{collision_object.id}' 已保存到: {cache_path}")
                return cache_path
            else:
                print(f"[统一缓存] ❌ 保存失败: {collision_object.id}")
                return ""
                
        except Exception as e:
            print(f"[统一缓存] ❌ 异常: {e}")
            return ""
    def _save_object_to_unified_cache(self, collision_object) -> str:
        """
        保存物体到统一缓存 - 修复版
        """
        # 使用正确的缓存管理器属性
        if not hasattr(self, 'unified_cache_manager') or not self.unified_cache_manager:
            print("[统一缓存] ⚠️ 统一缓存管理器不可用")
            return ""
        
        try:
            # 提取物体数据
            object_data = self._extract_object_data(collision_object)
            
            # 确定物体类型
            object_type = object_data.get('type', 'mesh')
            
            # ⚠️ 修复：使用 unified_cache_manager 而不是 object_cache
            cache_path = self.unified_cache_manager.save_object_info(
                object_id=collision_object.id,
                object_data=object_data,
                object_type=object_type
            )
            
            if cache_path:
                print(f"[统一缓存] ✅ 物体 '{collision_object.id}' 已保存到: {cache_path}")
                return cache_path
            else:
                print(f"[统一缓存] ❌ 保存失败: {collision_object.id}")
                return ""
                
        except Exception as e:
            print(f"[统一缓存] ❌ 异常: {e}")
            return ""
    def load_object_from_unified_cache(self, object_id, object_type="mesh"):
        """从统一缓存加载物体"""
        # ⚠️ 修复：使用 unified_cache_manager
        if not hasattr(self, 'unified_cache_manager') or not self.unified_cache_manager:
            print("[缓存] ✗ 统一缓存管理器不可用")
            return None
        
        try:
            # ⚠️ 修复：使用 unified_cache_manager
            cached_data = self.unified_cache_manager.load_object_info(object_id, object_type)
            
            if cached_data:
                print(f"[统一缓存] ✅ 命中缓存: {object_id}")
                return cached_data['data']
            else:
                print(f"[统一缓存] ⚠️ 未找到缓存: {object_id}")
                return None
                
        except Exception as e:
            print(f"[统一缓存] ✗ 加载异常: {e}")
            return None
    def check_unified_cache_status(self):
        """检查统一缓存系统状态"""
        # ⚠️ 修复：检查 unified_cache_manager
        if not hasattr(self, 'unified_cache_manager') or not self.unified_cache_manager:
            return {
                "available": False,
                "message": "统一缓存管理器不可用"
            }
        
        try:
            from ps_cache.cache_manager import CachePathTools
            cache_root = CachePathTools.get_cache_root()
            
            return {
                "available": True,
                "cache_root": str(cache_root),
                "system": "unified_cache",
                "status": "ready",
                "manager_type": type(self.unified_cache_manager).__name__
            }
            
        except Exception as e:
            return {
                "available": False,
                "message": f"缓存系统错误: {str(e)}"
            }
    ############################        
    def _init_cache(self):
        """初始化缓存系统"""
        # 缓存文件路径（在用户home目录下）
        home_dir = os.path.expanduser("~")
        cache_dir = os.path.join(home_dir, ".planning_scene_cache")
        
        # 确保缓存目录存在
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        
        self.cache_file = os.path.join(cache_dir, "objects.json")
        self.object_cache = self._load_cache()
        
        
    
    def _load_cache(self) -> Dict:
        """从文件加载缓存"""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[缓存] 加载缓存失败: {e}")
            return {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.object_cache, f, indent=2)
        except Exception as e:
            print(f"[缓存] 保存缓存失败: {e}")
    
    def _extract_object_data(self, collision_object) -> Dict[str, Any]:
        """从CollisionObject提取可缓存的数据"""
        data = {
            'id': collision_object.id,
            'operation': 'ADD' if collision_object.operation == b'\x00' else 'REMOVE',
            'frame_id': collision_object.header.frame_id if hasattr(collision_object.header, 'frame_id') else '',
            'cached_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }        # 提取几何信息
        if hasattr(collision_object, 'primitives') and collision_object.primitives:
            primitive = collision_object.primitives[0]
            data['primitive_type'] = int(primitive.type)
            
            if hasattr(primitive, 'dimensions'):
                data['dimensions'] = [float(d) for d in primitive.dimensions]
            
            # 类型映射
            type_map = {1: 'box', 2: 'sphere', 3: 'cylinder', 4: 'cone'}
            data['type'] = type_map.get(data['primitive_type'], 'unknown')
        
        # 提取位姿信息
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
    
    def add_object_simple(self, collision_object) -> bool:
        """
        简单添加物体
        
        Args:
            collision_object: CollisionObject 实例
            
        Returns:
            bool: 是否成功
        """
        from moveit_msgs.msg import PlanningScene, PlanningSceneWorld
        
        # 创建场景更新
        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_model_name = "panda"  # 必须设置
        scene.world = PlanningSceneWorld()
        
        # 确保 operation 是字节串
        if not isinstance(collision_object.operation, bytes):
            collision_object.operation = b'\x00'  # ADD
        
        # 确保有 header.frame_id
        if not hasattr(collision_object.header, 'frame_id') or not collision_object.header.frame_id:
            collision_object.header.frame_id = "world"
        
        scene.world.collision_objects.append(collision_object)
        
        # 应用更新
        success = self.client.apply_scene_update(scene)
        
        # 如果成功，保存到缓存
        if success:
            try:
                cache_data = self._extract_object_data(collision_object)
                #self.object_cache[collision_object.id] = cache_data
                #self._save_cache()
                cache_path = self._save_object_to_unified_cache(collision_object)
                if cache_path:
                    print(f"[缓存] ✓ 已保存到统一缓存系统")                
                print(f"[缓存] 物体 '{collision_object.id}' 已缓存")
            except Exception as e:
                print(f"[缓存] 保存缓存失败: {e}")
        
        # 等待并同步显示
        if success:
            time.sleep(0.1)
            self._sync_to_rviz(scene)
        
        return success
    
    def remove_object_simple(self, object_id: str) -> bool:
        """
        简单移除物体 
        
        Args:
            object_id: 物体ID
            
        Returns:
            bool: 是否成功
        """
        from moveit_msgs.msg import PlanningScene, PlanningSceneWorld, CollisionObject        
        # 方法1：直接发送 REMOVE 命令（不查询当前状态）
        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_model_name = "panda"
        scene.world = PlanningSceneWorld()
        
        # 创建 REMOVE 命令
        remove_obj = CollisionObject()
        remove_obj.id = object_id
        remove_obj.operation = b'\x01'  # REMOVE（字节串！）
        remove_obj.header.frame_id = "world"
        
        scene.world.collision_objects.append(remove_obj)
        
        # 应用更新
        success = self.client.apply_scene_update(scene)
        
        # 从缓存删除
        if success and object_id in self.object_cache:
            del self.object_cache[object_id]
            self._save_cache()
            print(f"[缓存] 物体 '{object_id}' 已从缓存移除")
        
        # 方法2：再发送空场景确保清除
        if success:
            time.sleep(0.1)
            empty_scene = PlanningScene()
            empty_scene.is_diff = True
            empty_scene.robot_model_name = "panda"
            empty_scene.world = PlanningSceneWorld()
            
            success2 = self.client.apply_scene_update(empty_scene)
            
            # 同步显示
            self._sync_to_rviz(empty_scene)
        
        return success
    
    def remove_objects_simple(self, object_ids: List[str]) -> bool:
        """
        批量移除物体
        
        Args:
            object_ids: 物体ID列表
            
        Returns:
            bool: 是否成功
        """
        if not object_ids:
            return True
        
        from moveit_msgs.msg import PlanningScene, PlanningSceneWorld, CollisionObject
        
        # 创建包含所有 REMOVE 命令的场景
        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_model_name = "panda"
        scene.world = PlanningSceneWorld()
        
        for obj_id in object_ids:
            remove_obj = CollisionObject()
            remove_obj.id = obj_id
            remove_obj.operation = b'\x01'  # REMOVE
            remove_obj.header.frame_id = "world"
            scene.world.collision_objects.append(remove_obj)
        
        # 应用更新
        success = self.client.apply_scene_update(scene)
        
        # 从缓存删除
        if success:
            for obj_id in object_ids:
                if obj_id in self.object_cache:
                    del self.object_cache[obj_id]
            self._save_cache()
        
        # 发送空场景确保清除
        if success:
            time.sleep(0.2)
            empty_scene = PlanningScene()
            empty_scene.is_diff = True
            empty_scene.robot_model_name = "panda"
            empty_scene.world = PlanningSceneWorld()
            
            self.client.apply_scene_update(empty_scene)
            self._sync_to_rviz(empty_scene)
        
        return success
    
    def list_objects(self) -> List[str]:
        """
        列出所有物体
        
        Returns:
            List[str]: 物体ID列表
        """
        try:
            return self.client.get_collision_objects()
        except:
            return []
    
    def get_object_info(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物体详细信息
        
        Args:
            object_id: 物体ID
            
        Returns:
            Optional[Dict]: 物体信息字典
        """
        scene = self.client.get_current_scene()
        if not scene or not scene.world:
            return None
        
        for obj in scene.world.collision_objects:
            if obj.id == object_id:
                return {
                    'id': obj.id,
                    'operation': obj.operation,
                    'frame_id': obj.header.frame_id if hasattr(obj.header, 'frame_id') else None,
                    'primitive_count': len(obj.primitives) if hasattr(obj, 'primitives') else 0,
                    'pose_count': len(obj.primitive_poses) if hasattr(obj, 'primitive_poses') else 0
                }
        
        return None   
    # ========== 新增缓存相关方法 ==========
    
    def get_object_from_cache(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取物体完整信息
        
        Args:
            object_id: 物体ID
            
        Returns:
            Optional[Dict]: 缓存的物体信息，None表示不存在
        """
        return self.object_cache.get(object_id)
    
    def list_cached_objects(self) -> List[str]:
        """
        列出缓存中的所有物体
        
        Returns:
            List[str]: 物体ID列表
        """
        return list(self.object_cache.keys())
    
    def clear_cache(self):
        """清空本地缓存"""
        self.object_cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("[缓存] 缓存已清空")
    
    def show_cache_info(self):
        """显示缓存信息"""
        print(f"[缓存] 缓存文件: {self.cache_file}")
        print(f"[缓存] 缓存物体数量: {len(self.object_cache)}")
        for obj_id, data in self.object_cache.items():
            print(f"  - {obj_id}: {data.get('type', 'unknown')} at {data.get('position', [])}")
    
    # ========== 原有方法保持不变 ==========
    
    def clear_all_objects(self) -> bool:
        """
        清空所有物体
        
        Returns:
            bool: 是否成功
        """
        # 使用客户端的清空方法（已经优化过的）
        if hasattr(self.client, 'clear_all_objects'):
            success = self.client.clear_all_objects()
            
            # 清空缓存
            if success:
                self.clear_cache()
            
            # 额外同步显示
            if success:
                time.sleep(0.2)
                self._sync_empty_to_rviz()
            
            return success
        else:
            # 备用方法
            objects = self.list_objects()
            success = self.remove_objects_simple(objects)
            if success:
                self.clear_cache()
            return success
    
    def _sync_to_rviz(self, scene):
        """同步到 RViz 显示"""
        try:
            # 如果有 monitored_publisher，直接使用
            if hasattr(self.client, 'monitored_publisher'):
                for i in range(3):
                    self.client.monitored_publisher.publish(scene)
                    time.sleep(0.05)
        except:
            pass  # 忽略同步失败
    
    def _sync_empty_to_rviz(self):
        """同步空场景到 RViz"""
        from moveit_msgs.msg import PlanningScene, PlanningSceneWorld
        
        empty_scene = PlanningScene()
        empty_scene.is_diff = True
        empty_scene.robot_model_name = "panda"
        empty_scene.world = PlanningSceneWorld()
        
        self._sync_to_rviz(empty_scene)
# ========== 一行调用接口 ==========

class ObjectManagerFacade:
    """
    物体管理器外观类 - 提供一行调用接口
    """
    
    _instance = None
    
    @classmethod
    def get_manager(cls, scene_client=None):
        """获取或创建ObjectManager实例"""
        if cls._instance is None:
            cls._instance = cls._create_instance(scene_client)
        return cls._instance
    
    @classmethod
    def _create_instance(cls, scene_client):
        """创建内部实例"""
        try:
            from ps_core.scene_client import PlanningSceneClient
            if scene_client is None:
                scene_client = PlanningSceneClient()
            
            manager = ObjectManager(scene_client)
            print("[ObjectManagerFacade] ✅ 物体管理器就绪")
            return manager
        except Exception as e:
            print(f"[ObjectManagerFacade] ❌ 初始化失败: {e}")
            return None
    
    @classmethod
    def add_object(cls, object_data, **kwargs):
        """
        一行调用：添加物体
        
        参数：
        object_data: 可以是：
            - 字典: {"id": "box", "position": [0.5,0.3,0.4], "dimensions": [0.1,0.1,0.1]}
            - CollisionObject对象
            - 物体ID + 尺寸列表
        
        返回：
            标准化结果
        """
        manager = cls.get_manager()
        if not manager:
            return {"success": False, "error": "管理器未初始化"}
        
        try:
            # 解析输入
            collision_object = cls._parse_object_data(object_data, **kwargs)
            
            # 调用添加方法
            success = manager.add_object_simple(collision_object)
            
            return {
                "success": success,
                "object_id": collision_object.id,
                "timestamp": cls._get_timestamp()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": cls._get_timestamp()
            }
    
    @classmethod
    def _parse_object_data(cls, data, **kwargs):
        """解析多种输入格式为CollisionObject"""
        from moveit_msgs.msg import CollisionObject
        from shape_msgs.msg import SolidPrimitive
        from geometry_msgs.msg import Pose
        
        obj = CollisionObject()
        
        if isinstance(data, CollisionObject):
            # 已经是CollisionObject
            return data
        
        elif isinstance(data, dict):
            # 字典格式
            obj.id = data.get("id", kwargs.get("object_id", "object"))
            
            # 创建基本几何
            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.BOX
            primitive.dimensions = data.get("dimensions", kwargs.get("dimensions", [0.1, 0.1, 0.1]))
            
            obj.primitives = [primitive]
            
            # 创建位姿
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
            obj.operation = b'\x00'  # ADD
            obj.header.frame_id = "world"
            
            return obj
        
        elif isinstance(data, (list, tuple)) and len(data) >= 3:            # 简单列表：[x, y, z] 或 [x, y, z, width, height, depth]
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

def add_object(object_data, **kwargs):
    """
    一行调用：添加物体
    
    示例：
    add_object({"id": "box", "position": [0.5,0.3,0.4], "dimensions": [0.1,0.1,0.1]})
    add_object([0.5, 0.3, 0.4], object_id="box", dimensions=[0.1,0.1,0.1])
    add_object("box", position=[0.5,0.3,0.4], dimensions=[0.1,0.1,0.1])
    """
    facade = ObjectManagerFacade()
    return facade.add_object(object_data, **kwargs)

def remove_object(object_id):
    """移除物体"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    
    success = manager.remove_object_simple(object_id)
    return {
        "success": success,
        "object_id": object_id,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

def list_objects():
    """列出所有物体"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return []
    
    objects = manager.list_objects()
    cached_objects = manager.list_cached_objects()
    
    return {
        "scene_objects": objects,
        "cached_objects": cached_objects,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

def clear_all_objects():
    """清空所有物体"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    
    success = manager.clear_all_objects()
    return {
        "success": success,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

def get_object_info(object_id):
    """获取物体信息"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return None
    
    # 首先尝试从缓存获取
    cached_info = manager.get_object_from_cache(object_id)
    if cached_info:
        return {
            "source": "cache",
            "data": cached_info
        }    # 然后尝试从场景获取
    scene_info = manager.get_object_info(object_id)
    if scene_info:
        return {
            "source": "scene",
            "data": scene_info
        }
    
    return None

def show_cache_info():
    """显示缓存信息"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        print("❌ 管理器未初始化")
        return
    
    manager.show_cache_info()

def get_cache_status():
    """获取缓存状态"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"available": False, "message": "管理器未初始化"}
    
    if hasattr(manager, 'check_unified_cache_status'):
        return manager.check_unified_cache_status()
    
    return {
        "available": True,
        "message": "使用本地文件缓存",
        "cache_file": getattr(manager, 'cache_file', 'unknown')
    }


# ========== 高级便捷函数 ==========

def create_box(object_id, x, y, z, width=0.1, height=0.1, depth=0.1):
    """快速创建盒子"""
    return add_object({
        "id": object_id,
        "position": [x, y, z],
        "dimensions": [width, height, depth]
    })

def create_sphere(object_id, x, y, z, radius=0.05):
    """快速创建球体"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    
    from moveit_msgs.msg import CollisionObject
    from shape_msgs.msg import SolidPrimitive
    from geometry_msgs.msg import Pose
    
    obj = CollisionObject()
    obj.id = object_id
    obj.operation = b'\x00'
    obj.header.frame_id = "world"
    
    primitive = SolidPrimitive()
    primitive.type = SolidPrimitive.SPHERE
    primitive.dimensions = [radius]
    
    obj.primitives = [primitive]
    
    pose = Pose()
    pose.position.x = x
    pose.position.y = y
    pose.position.z = z
    pose.orientation.w = 1.0
    
    obj.primitive_poses = [pose]
    
    success = manager.add_object_simple(obj)
    return {
        "success": success,
        "object_id": object_id,
        "type": "sphere",
        "radius": radius,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

def remove_objects(object_ids):
    """批量移除物体"""
    manager = ObjectManagerFacade.get_manager()
    if not manager:
        return {"success": False, "error": "管理器未初始化"}
    
    success = manager.remove_objects_simple(object_ids)
    return {
        "success": success,
        "removed_count": len(object_ids),
        "object_ids": object_ids,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

def import_objects_from_json(json_file):
    """从JSON文件导入物体"""
    import json
    with open(json_file, 'r') as f:
        objects_data = json.load(f)
    
    results = []
    for obj_data in objects_data:
        result = add_object(obj_data)
        results.append(result)
    
    return {
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success", False)),
        "results": results,
        "timestamp": ObjectManagerFacade._get_timestamp()
    }

# ========== 测试代码 ==========

if __name__ == "__main__":
    print("=== 物体管理器一行调用接口测试（调试版） ===")
    
    print("\n[调试] 测试 create_box 函数...")
    
    # 直接测试 create_box 函数，不通过 facade
    try:
        # 导入必要的模块
        from moveit_msgs.msg import CollisionObject
        from shape_msgs.msg import SolidPrimitive
        from geometry_msgs.msg import Pose
        
        # 创建客户端和管理器
        from ps_core.scene_client import PlanningSceneClient
        client = PlanningSceneClient()
        
        from object_manager import ObjectManager
        manager = ObjectManager(client)
        
        print("✅ 管理器创建成功")
        
        # 清空场景
        print("清空场景...")
        manager.clear_all_objects()
        
        # 手动创建物体
        print("\n手动创建物体...")
        test_obj = CollisionObject()
        test_obj.id = "manual_box"
        test_obj.operation = b'\x00'
        test_obj.header.frame_id = "world"
        
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.1, 0.1, 0.1]
        test_obj.primitives = [box]
        
        pose = Pose()
        pose.position.x = 0.5
        pose.position.y = 0.3
        pose.position.z = 0.4
        pose.orientation.w = 1.0
        test_obj.primitive_poses = [pose]
        
        success = manager.add_object_simple(test_obj)
        print(f"手动添加结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 验证
        objects = manager.list_objects()
        print(f"当前物体: {objects}")
        
        if success and "manual_box" in objects:
            print("✅ 物体管理器核心功能正常")
            
            # 现在测试一行调用
            print("\n[调试] 测试一行调用接口...")
            
            
            
            result = create_box("facade_box", 0.5, 0.0, 0.3)
            print(f"create_box 结果: {result}")
            
            objects = manager.list_objects()
            print(f"添加后物体: {objects}")
            
        else:
            print("❌ 物体管理器核心功能有问题")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")