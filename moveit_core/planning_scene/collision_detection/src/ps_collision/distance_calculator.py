#!/usr/bin/env python3
"""
距离计算器 - 计算物体间最小距离（使用缓存数据）
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import math
import os
import json

class DistanceCalculator:
    """距离计算器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化距离计算器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    def _load_cache(self) -> Dict:
        """ 加载缓存数据 """
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 距离计算器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 距离计算器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 距离计算器: 加载缓存失败: {e}")
            return {}
    
    def compute_distance(self, object1_id: str, object2_id: str) -> Dict[str, Any]:
        """
        计算两个物体间的最小距离（使用缓存数据）
        
        Args:
            object1_id: 第一个物体ID
            object2_id: 第二个物体ID
            
        Returns:
            Dict: 距离计算结果
        """
        try:
            # 从缓存获取物体数据
            cache = self._load_cache()
            
            if object1_id not in cache:
                return {"error": f"找不到物体: {object1_id}", "source": "cache"}
            if object2_id not in cache:
                return {"error": f"找不到物体: {object2_id}", "source": "cache"}
            
            obj1_data = cache[object1_id]
            obj2_data = cache[object2_id]            # 提取位置
            pos1 = self._extract_position(obj1_data)
            pos2 = self._extract_position(obj2_data)
            
            # 提取尺寸
            size1 = self._extract_size(obj1_data)
            size2 = self._extract_size(obj2_data)
            
            print(f"[距离计算] 计算 {object1_id} ↔ {object2_id}")
            print(f"[距离计算] {object1_id}: 位置 {pos1}, 尺寸 {size1}")
            print(f"[距离计算] {object2_id}: 位置 {pos2}, 尺寸 {size2}")
            
            # 计算欧氏距离
            dx = pos2[0] - pos1[0]
            dy = pos2[1] - pos1[1]
            dz = pos2[2] - pos1[2]
            center_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # 对于立方体，计算最近点距离（考虑尺寸）
            # 计算各个轴上的最小距离
            dist_x = max(0, abs(dx) - (size1[0]/2 + size2[0]/2))
            dist_y = max(0, abs(dy) - (size1[1]/2 + size2[1]/2))
            dist_z = max(0, abs(dz) - (size1[2]/2 + size2[2]/2))
            
            # 表面间最小距离
            surface_distance = math.sqrt(dist_x*dist_x + dist_y*dist_y + dist_z*dist_z)
            
            # 如果是碰撞状态，距离为0
            collision = (
                abs(dx) < (size1[0]/2 + size2[0]/2) and
                abs(dy) < (size1[1]/2 + size2[1]/2) and
                abs(dz) < (size1[2]/2 + size2[2]/2)
            )
            
            if collision:
                surface_distance = 0.0
            
            result = {
                "object1": object1_id,
                "object2": object2_id,
                "center_distance": float(center_distance),
                "surface_distance": float(surface_distance),
                "position1": pos1,
                "position2": pos2,
                "size1": size1,
                "size2": size2,
                "distance_vector": [float(dx), float(dy), float(dz)],
                "distance_components": {
                    "x": float(dist_x),
                    "y": float(dist_y),
                    "z": float(dist_z)
                },
                "collision": collision,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "cache"
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "source": "cache"}
    
    def _extract_position(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取位置"""
        if 'position' in obj_data:
            return obj_data['position']
        elif 'pose' in obj_data and 'position' in obj_data['pose']:
            return obj_data['pose']['position']
        else:
            return [0.0, 0.0, 0.0]
    
    def _extract_size(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取尺寸"""
        if 'dimensions' in obj_data:
            return obj_data['dimensions']
        elif 'size' in obj_data:
            return obj_data['size']
        else:            # 根据类型估计尺寸
            obj_type = obj_data.get('type', 'unknown')
            if obj_type == 'box':
                return [0.2, 0.2, 0.2]
            elif obj_type == 'sphere':
                radius = obj_data.get('radius', 0.1)
                return [radius * 2, radius * 2, radius * 2]
            else:
                return [0.1, 0.1, 0.1]
    
    def compute_distances_matrix(self, object_ids: List[str]) -> Dict[str, Any]:
        """
        计算多个物体间的距离矩阵
        
        Args:
            object_ids: 物体ID列表
            
        Returns:
            Dict: 距离矩阵结果
        """
        n = len(object_ids)
        center_distances = np.full((n, n), np.nan)
        surface_distances = np.full((n, n), np.nan)
        collision_matrix = np.full((n, n), False)
        
        results = {}
        
        for i in range(n):
            for j in range(i + 1, n):
                obj1_id = object_ids[i]
                obj2_id = object_ids[j]
                
                distance_result = self.compute_distance(obj1_id, obj2_id)
                
                if "error" not in distance_result:
                    center_dist = distance_result.get("center_distance", np.nan)
                    surface_dist = distance_result.get("surface_distance", np.nan)
                    collision = distance_result.get("collision", False)
                    
                    center_distances[i, j] = center_dist
                    center_distances[j, i] = center_dist
                    surface_distances[i, j] = surface_dist
                    surface_distances[j, i] = surface_dist
                    collision_matrix[i, j] = collision
                    collision_matrix[j, i] = collision
                    
                    results[f"{obj1_id}_{obj2_id}"] = distance_result
        
        return {
            "object_ids": object_ids,
            "center_distance_matrix": center_distances.tolist(),
            "surface_distance_matrix": surface_distances.tolist(),
            "collision_matrix": collision_matrix.tolist(),
            "pairwise_results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "cache"
        }
    
    def find_nearest_objects(self, target_object_id: str, max_count: int = 5) -> List[Dict[str, Any]]:
        """
        查找距离目标物体最近的物体
        
        Args:
            target_object_id: 目标物体ID
            max_count: 返回的最多物体数量
            
        Returns:
            List[Dict]: 最近物体列表
        """
        try:            # 从缓存获取所有物体
            cache = self._load_cache()
            all_object_ids = list(cache.keys())
            
            if target_object_id not in all_object_ids:
                return [{"error": f"目标物体不存在: {target_object_id}"}]
            
            # 计算到所有物体的距离
            distances = []
            for obj_id in all_object_ids:
                if obj_id == target_object_id:
                    continue
                
                result = self.compute_distance(target_object_id, obj_id)
                if "error" not in result:
                    distances.append({
                        "object_id": obj_id,
                        "center_distance": result["center_distance"],
                        "surface_distance": result["surface_distance"],
                        "position": result["position2"],
                        "collision": result["collision"],
                        "distance_vector": result["distance_vector"]
                    })
            
            # 按表面距离排序
            distances.sort(key=lambda x: x["surface_distance"])
            
            # 返回最近的物体
            return distances[:max_count]
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def compute_distance_to_robot(self, object_id: str, robot_base_position: List[float] = None) -> Dict[str, Any]:
        """
        计算物体到机器人的距离
        
        Args:
            object_id: 物体ID
            robot_base_position: 机器人基座位置，默认为[0,0,0]
            
        Returns:
            Dict: 到机器人的距离
        """
        if robot_base_position is None:
            robot_base_position = [0.0, 0.0, 0.0]
        
        try:
            # 从缓存获取物体数据
            cache = self._load_cache()
            
            if object_id not in cache:
                return {"error": f"找不到物体: {object_id}"}
            
            obj_data = cache[object_id]
            
            # 提取物体位置
            obj_position = self._extract_position(obj_data)
            obj_size = self._extract_size(obj_data)
            
            # 计算距离
            dx = obj_position[0] - robot_base_position[0]
            dy = obj_position[1] - robot_base_position[1]
            dz = obj_position[2] - robot_base_position[2]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # 考虑物体尺寸的安全距离
            avg_size = np.mean(obj_size)
            safe_distance = distance - avg_size/2
            safe_distance = max(safe_distance, 0)
            
            result = {
                "object_id": object_id,
                "robot_base": robot_base_position,
                "object_position": obj_position,
                "distance": float(distance),
                "safe_distance": float(safe_distance),
                "estimated_object_size": float(avg_size),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_safe": safe_distance > 0.2  # 20cm安全阈值
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}

