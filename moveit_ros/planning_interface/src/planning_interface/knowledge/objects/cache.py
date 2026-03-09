# planning_interface/src/planning_interface/knowledge/objects/cache.py
"""
物体缓存读写模块 - 包装你的 ObjectCache
"""

from typing import Optional, List, Dict, Any
from ps_cache.object_cache import ObjectCache as _ObjectCache


class ObjectCache:
    """
    物体缓存读写（包装你的实现）
    
    提供简单的 get_pose() 接口，供 stages 使用
    """
    
    def __init__(self):
        """初始化你的缓存系统"""
        self._cache = _ObjectCache()
        print("[Knowledge] 物体缓存就绪")
# knowledge/objects/cache.py

    def get_pose(self, object_id: str) -> Optional[List[float]]:
        """获取物体位姿 [x,y,z,qx,qy,qz,qw]"""
        obj = self._cache.load_object_info(object_id)
        
        print(f"[DEBUG] object_id = {object_id}")
        print(f"[DEBUG] obj type = {type(obj)}")
        print(f"[DEBUG] obj keys = {obj.keys() if obj else None}")
        
        if not obj:
            print(f"[DEBUG] 未找到物体 {object_id}")
            return None
        
        # 尝试多种可能的位置字段
        pos = None
        if 'position' in obj:
            pos = obj['position']
            print(f"[DEBUG] 找到 position: {pos}")
        elif 'pose' in obj:
            pose = obj['pose']
            if len(pose) >= 3:
                pos = pose[:3]
                print(f"[DEBUG] 从 pose 提取 position: {pos}")
        elif 'data' in obj and 'position' in obj['data']:
            pos = obj['data']['position']
            print(f"[DEBUG] 从 data.position 找到: {pos}")
        
        if pos is None:
            print(f"[DEBUG] 未找到位置信息")
            return None
        
        # 获取方向
        orient = None
        if 'orientation' in obj:
            orient = obj['orientation']
        elif 'pose' in obj and len(obj['pose']) >= 7:
            orient = obj['pose'][3:7]
        elif 'data' in obj and 'orientation' in obj['data']:
            orient = obj['data']['orientation']
        
        if orient is None:
            orient = [0, 0, 0, 1]
            print(f"[DEBUG] 使用默认方向")
        
        result = pos + orient
        print(f"[DEBUG] 返回位姿: {result}")
        return result
    def get_dimensions(self, object_id: str) -> Optional[Dict]:
        """
        获取物体尺寸信息
        
        Args:
            object_id: 物体ID
        
        Returns:
            根据物体类型返回不同格式：
            - box: {'type': 'box', 'size': [长, 宽, 高]}
            - sphere: {'type': 'sphere', 'radius': 半径}
            - cylinder: {'type': 'cylinder', 'radius': 半径, 'height': 高度}
        """
        print(f"[ObjectCache] 获取物体尺寸: {object_id}")
        
        obj = self._cache.load_object_info(object_id)
        if not obj:
            print(f"[ObjectCache] 未找到物体 {object_id}")
            return None
        
        print(f"[DEBUG] 尺寸查询 - obj keys: {obj.keys() if obj else None}")
        
        # 尝试多种可能的数据结构
        # 情况1：直接有 type 和 dimensions/radius/height
        obj_type = obj.get('type')
        
        if obj_type == 'box':
            dimensions = obj.get('dimensions') or obj.get('size')
            if dimensions:
                return {
                    'type': 'box',
                    'size': dimensions  # [长, 宽, 高]
                }
        
        elif obj_type == 'sphere':
            radius = obj.get('radius')
            if radius:
                return {
                    'type': 'sphere',
                    'radius': radius
                }
        
        elif obj_type == 'cylinder':
            radius = obj.get('radius')
            height = obj.get('height')
            if radius and height:
                return {
                    'type': 'cylinder',
                    'radius': radius,
                    'height': height
                }
        
        # 情况2：数据在 'data' 字段里
        if 'data' in obj and isinstance(obj['data'], dict):
            data = obj['data']
            obj_type = data.get('type')
            
            if obj_type == 'box':
                dimensions = data.get('dimensions') or data.get('size')
                if dimensions:
                    return {
                        'type': 'box',
                        'size': dimensions
                    }
            elif obj_type == 'sphere':
                radius = data.get('radius')
                if radius:
                    return {
                        'type': 'sphere',
                        'radius': radius
                    }
            elif obj_type == 'cylinder':
                radius = data.get('radius')
                height = data.get('height')
                if radius and height:
                    return {
                        'type': 'cylinder',
                        'radius': radius,
                        'height': height
                    }
        
        print(f"[ObjectCache] 未能提取尺寸信息: {object_id}")
        return None    
    def get_object_info(self, object_id: str) -> Optional[Dict[str, Any]]:
        """获取完整物体信息"""
        return self._cache.load_object_info(object_id)
    
    def get_all_objects(self) -> List[Dict[str, Any]]:
        """获取所有缓存的物体"""
        return self._cache.load_all_cached_objects()


# 快捷函数
def get_object_pose(object_id: str) -> Optional[List[float]]:
    """快捷获取物体位姿"""
    cache = ObjectCache()
    return cache.get_pose(object_id)
def get_object_dimensions(object_id: str) -> Optional[Dict]:
    """快捷获取物体尺寸"""
    cache = ObjectCache()
    return cache.get_dimensions(object_id)