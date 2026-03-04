#!/usr/bin/env python3
"""
碰撞检查器 - 检查物体间和自碰撞（使用缓存数据）
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import sys
import os
import json

class CollisionChecker:
    """碰撞检查器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化碰撞检查器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 加载缓存失败: {e}")
            return {}
    
    def check_collision(self, object1_id: str, object2_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        检查两个物体是否碰撞（使用缓存数据）
        
        Args:
            object1_id: 第一个物体ID
            object2_id: 第二个物体ID
            
        Returns:
            Tuple[bool, Dict]: (是否碰撞, 碰撞详细信息)
        """
        try:
            # 从缓存获取物体数据
            cache = self._load_cache()
            
            if object1_id not in cache:
                print(f"[缓存] 物体 {object1_id} 不在缓存中")
                print(f"[缓存] 缓存中的物体: {list(cache.keys())}")
                return False, {"error": f"找不到物体: {object1_id}"}
            if object2_id not in cache:
                print(f"[缓存] 物体 {object2_id} 不在缓存中")
                return False, {"error": f"找不到物体: {object2_id}"}
            
            obj1_data = cache[object1_id]
            obj2_data = cache[object2_id]
            
            print(f"[碰撞检测] 使用缓存数据检查 {object1_id} ↔ {object2_id}")
            
            # 使用缓存数据进行碰撞检测
            collision, info = self._check_with_cached_data(obj1_data, obj2_data)
            
            result = {
                "collision": collision,
                "object1": object1_id,
                "object2": object2_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "details": info
            }
            
            return collision, result
            
        except Exception as e:
            print(f"[错误] 碰撞检测异常: {e}")
            import traceback
            traceback.print_exc()
            return False, {"error": str(e)}
    
    def _check_with_cached_data(self, obj1_data: Dict, obj2_data: Dict) -> Tuple[bool, Dict[str, Any]]:
        """
        使用缓存数据进行碰撞检测
        
        Args:
            obj1_data: 物体1的缓存数据
            obj2_data: 物体2的缓存数据
            
        Returns:
            Tuple[bool, Dict]: (是否碰撞, 碰撞信息)
        """
        # 提取位置和尺寸
        pos1 = self._extract_position(obj1_data)
        pos2 = self._extract_position(obj2_data)
        
        size1 = self._extract_size(obj1_data)
        size2 = self._extract_size(obj2_data)
        
        print(f"[碰撞计算] 物体1: 位置 {pos1}, 尺寸 {size1}")
        print(f"[碰撞计算] 物体2: 位置 {pos2}, 尺寸 {size2}")        
        # 轴对齐包围盒碰撞检测
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dz = abs(pos1[2] - pos2[2])
        
        tx = size1[0]/2 + size2[0]/2
        ty = size1[1]/2 + size2[1]/2
        tz = size1[2]/2 + size2[2]/2
        
        x_collision = dx < tx
        y_collision = dy < ty
        z_collision = dz < tz
        
        print(f"[碰撞计算] X轴: {dx:.3f} < {tx:.3f} ? {x_collision}")
        print(f"[碰撞计算] Y轴: {dy:.3f} < {ty:.3f} ? {y_collision}")
        print(f"[碰撞计算] Z轴: {dz:.3f} < {tz:.3f} ? {z_collision}")
        
        collision = x_collision and y_collision and z_collision
        print(f"[碰撞计算] 总体碰撞: {collision}")
        
        info = {
            "method": "cached_bounding_box",
            "position1": pos1,
            "position2": pos2,
            "size1": size1,
            "size2": size2,
            "distance_x": float(dx),
            "distance_y": float(dy),
            "distance_z": float(dz),
            "threshold_x": float(tx),
            "threshold_y": float(ty),
            "threshold_z": float(tz),
            "axis_collisions": {
                "x": x_collision,
                "y": y_collision,
                "z": z_collision
            }
        }
        
        return collision, info
    
    def _extract_position(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取位置"""
        if 'position' in obj_data:
            return obj_data['position']
        elif 'pose' in obj_data and 'position' in obj_data['pose']:
            return obj_data['pose']['position']
        else:
            print(f"[警告] 无法提取位置，使用默认值 [0,0,0]")
            return [0.0, 0.0, 0.0]
    
    def _extract_size(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取尺寸"""
        if 'dimensions' in obj_data:
            return obj_data['dimensions']
        elif 'size' in obj_data:
            return obj_data['size']
        else:
            print(f"[警告] 无法提取尺寸，使用默认值 [0.1,0.1,0.1]")
            return [0.1, 0.1, 0.1]
    
    def check_multiple_collisions(self, object_ids: List[str]) -> Dict[str, Any]:
        """
        检查多个物体间的碰撞
        
        Args:
            object_ids: 物体ID列表
            
        Returns:
            Dict: 碰撞检查结果
        """
        results = {
            "checked_objects": object_ids,
            "total_collisions": 0,
            "collision_pairs": [],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 检查所有物体对
        for i in range(len(object_ids)):
            for j in range(i + 1, len(object_ids)):
                obj1_id = object_ids[i]
                obj2_id = object_ids[j]
                
                collision, info = self.check_collision(obj1_id, obj2_id)
                
                if collision:
                    results["total_collisions"] += 1
                    results["collision_pairs"].append({
                        "object1": obj1_id,
                        "object2": obj2_id,
                        "details": info.get("details", {})
                    })
        
        return results
    
    def check_self_collision(self, composite_object_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        检查复合物体的自碰撞（部件间碰撞）
        
        Args:
            composite_object_id: 复合物体ID
            
        Returns:
            Tuple[bool, Dict]: (是否自碰撞, 详细信息)
        """        # 简化实现：目前不支持复合物体
        return False, {"error": "暂不支持复合物体自碰撞检测"}
    
    def check_scene_collisions(self, exclude_pairs: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        检查场景中所有物体间的碰撞
        
        Args:
            exclude_pairs: 要排除的物体对列表
            
        Returns:
            Dict: 场景碰撞检查结果
        """
        try:
            # 获取缓存中的所有物体
            cache = self._load_cache()
            object_ids = list(cache.keys())
            
            if len(object_ids) < 2:
                return {
                    "total_objects": len(object_ids),
                    "total_collisions": 0,
                    "collision_pairs": [],
                    "message": "物体太少，无法检查碰撞"
                }
            
            # 检查所有物体对
            results = self.check_multiple_collisions(object_ids)
            
            # 过滤排除的物体对
            if exclude_pairs:
                filtered_pairs = []
                for pair in results["collision_pairs"]:
                    obj_pair = (pair["object1"], pair["object2"])
                    reverse_pair = (pair["object2"], pair["object1"])
                    
                    if obj_pair not in exclude_pairs and reverse_pair not in exclude_pairs:
                        filtered_pairs.append(pair)
                
                results["collision_pairs"] = filtered_pairs
                results["total_collisions"] = len(filtered_pairs)
                results["excluded_pairs"] = exclude_pairs
            
            results["total_objects"] = len(object_ids)
            
            return results
            
        except Exception as e:
            return {"error": str(e)}

