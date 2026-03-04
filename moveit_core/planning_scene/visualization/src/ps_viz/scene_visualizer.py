#!/usr/bin/env python3
"""
场景可视化 - 可视化规划场景中的物体
"""
from typing import List, Dict, Any, Optional
import time
import numpy as np
import os
import json
import math

class SceneVisualizer:
    """场景可视化器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化场景可视化器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 场景可视化器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 场景可视化器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 场景可视化器: 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return float(value)
    
    def visualize_scene(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        可视化整个场景
        
        Args:
            options: 可视化选项
            
        Returns:
            Dict: 可视化结果
        """
        if options is None:
            options = {}
        
        try:
            cache = self._load_cache()
            
            if not cache:
                return {
                    "success": False,
                    "message": "场景为空，没有可可视化的物体",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 分析场景
            scene_analysis = self._analyze_scene(cache)            # 生成可视化数据
            viz_data = self._generate_viz_data(cache, options)
            
            result = {
                "success": True,
                "scene_analysis": scene_analysis,
                "visualization_data": viz_data,
                "options_used": options,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"可视化场景失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _analyze_scene(self, cache: Dict) -> Dict[str, Any]:
        """分析场景内容"""
        analysis = {
            "total_objects": len(cache),
            "object_types": {},
            "position_stats": {
                "min": [float('inf'), float('inf'), float('inf')],
                "max": [float('-inf'), float('-inf'), float('-inf')],
                "center": [0.0, 0.0, 0.0]
            },
            "size_stats": {
                "min_size": float('inf'),
                "max_size": float('inf'),
                "avg_size": 0.0
            }
        }
        
        positions = []
        sizes = []
        
        for obj_id, obj_data in cache.items():
            # 统计类型
            obj_type = obj_data.get('type', 'unknown')
            analysis["object_types"][obj_type] = analysis["object_types"].get(obj_type, 0) + 1
            
            # 提取位置和尺寸
            position = self._extract_position(obj_data)
            size = self._extract_size(obj_data)
            
            positions.append(position)
            sizes.append(np.mean(size))  # 使用平均尺寸
            
            # 更新位置统计
            for i in range(3):
                analysis["position_stats"]["min"][i] = min(analysis["position_stats"]["min"][i], position[i])
                analysis["position_stats"]["max"][i] = max(analysis["position_stats"]["max"][i], position[i])
        
        # 计算中心
        if positions:
            positions_array = np.array(positions)
            analysis["position_stats"]["center"] = np.mean(positions_array, axis=0).tolist()        # 计算尺寸统计
        if sizes:
            sizes_array = np.array(sizes)
            analysis["size_stats"]["min_size"] = float(np.min(sizes_array))
            analysis["size_stats"]["max_size"] = float(np.max(sizes_array))
            analysis["size_stats"]["avg_size"] = float(np.mean(sizes_array))
        
        return analysis
    
    def _generate_viz_data(self, cache: Dict, options: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化数据"""
        viz_data = {
            "objects": [],
            "bounding_box": {
                "min": [0, 0, 0],
                "max": [0, 0, 0],
                "center": [0, 0, 0]
            },
            "color_scheme": options.get("color_scheme", "type_based"),
            "view_type": options.get("view_type", "overview")
        }
        
        # 生成每个物体的可视化数据
        for obj_id, obj_data in cache.items():
            obj_viz = self._visualize_object(obj_id, obj_data, options)
            viz_data["objects"].append(obj_viz)
        
        # 计算整体包围盒
        if viz_data["objects"]:
            all_positions = []
            all_sizes = []
            
            for obj in viz_data["objects"]:
                all_positions.append(obj["position"])
                all_sizes.append(obj["size"])
            
            positions_array = np.array(all_positions)
            sizes_array = np.array(all_sizes)
            
            # 计算考虑物体尺寸的包围盒
            half_sizes = sizes_array / 2
            min_positions = positions_array - half_sizes
            max_positions = positions_array + half_sizes
            
            viz_data["bounding_box"]["min"] = np.min(min_positions, axis=0).tolist()
            viz_data["bounding_box"]["max"] = np.max(max_positions, axis=0).tolist()
            viz_data["bounding_box"]["center"] = ((np.array(viz_data["bounding_box"]["min"]) + 
                                                 np.array(viz_data["bounding_box"]["max"])) / 2).tolist()
        
        return viz_data
    
    def _visualize_object(self, obj_id: str, obj_data: Dict, options: Dict[str, Any]) -> Dict[str, Any]:
        """可视化单个物体"""
        obj_type = obj_data.get('type', 'unknown')
        position = self._extract_position(obj_data)
        size = self._extract_size(obj_data)
        orientation = obj_data.get('orientation', [0, 0, 0, 1])
        
        # 根据类型选择颜色
        colors = {
            'box': [1.0, 0.5, 0.0, 0.7],      # 橙色
            'sphere': [0.0, 0.8, 1.0, 0.7],    # 青色
            'cylinder': [0.5, 0.5, 0.5, 0.7],  # 灰色
            'cone': [0.8, 0.0, 0.8, 0.7],      # 紫色
            'mesh': [0.0, 1.0, 0.0, 0.7]       # 绿色
        }
        
        color = colors.get(obj_type, [0.7, 0.7, 0.7, 0.7])  # 默认灰色
        
        # 根据选项调整
        color_scheme = options.get("color_scheme", "type_based")
        if color_scheme == "random":
            # 生成随机但稳定的颜色
            import hashlib
            hash_obj = hashlib.md5(obj_id.encode())
            hash_int = int(hash_obj.hexdigest()[:8], 16)
            color = [
                (hash_int % 100) / 100.0,
                ((hash_int // 100) % 100) / 100.0,
                ((hash_int // 10000) % 100) / 100.0,
                0.7
            ]
        elif color_scheme == "size_based":
            # 根据尺寸着色（越大越红）
            avg_size = np.mean(size)
            normalized_size = min(1.0, avg_size / 0.5)# 假设0.5m为最大参考
            color = [normalized_size, 1.0 - normalized_size, 0.0, 0.7]
        
        return {
            "id": obj_id,
            "type": obj_type,
            "position": position,
            "size": size,
            "orientation": orientation,
            "color": color,
            "label": obj_id,
            "visible": True,
            "opacity": options.get("opacity", 0.7)
        }
    
    def visualize_workspace(self, workspace_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """可视化工作空间"""
        if workspace_config is None:
            workspace_config = {
                "type": "spherical",
                "center": [0, 0, 0.5],
                "radius": 1.0
            }
        
        viz_data = {
            "workspace": workspace_config,
            "visualization": {
                "type": workspace_config.get("type", "spherical"),
                "parameters": workspace_config,
                "color": [0.1, 0.1, 0.9, 0.2]  # 半透明蓝色
            }
        }
        
        return {
            "success": True,
            "workspace_data": viz_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _extract_position(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取位置"""
        if 'position' in obj_data:
            return self._ensure_float(obj_data['position'])
        elif 'pose' in obj_data and 'position' in obj_data['pose']:
            return self._ensure_float(obj_data['pose']['position'])
        else:
            return [0.0, 0.0, 0.0]
    
    def _extract_size(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取尺寸"""
        if 'dimensions' in obj_data:
            return self._ensure_float(obj_data['dimensions'])
        elif 'size' in obj_data:
            return self._ensure_float(obj_data['size'])
        else:
            # 根据类型估计尺寸
            obj_type = obj_data.get('type', 'unknown')
            if obj_type == 'box':
                return [0.2, 0.2, 0.2]
            elif obj_type == 'sphere':
                radius = float(obj_data.get('radius', 0.1))
                return [radius * 2, radius * 2, radius * 2]
            else:
                return [0.1, 0.1, 0.1]