#!/usr/bin/env python3
"""
碰撞可视化 - 可视化碰撞检测结果
"""
from typing import List, Dict, Any, Optional, Tuple
import time
import numpy as np
import os
import json
import math

class CollisionVisualizer:
    """碰撞可视化器"""
    
    def __init__(self, scene_client):
        """
        初始化碰撞可视化器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 碰撞可视化器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 碰撞可视化器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 碰撞可视化器: 加载缓存失败: {e}")
            return {}
    
    def visualize_collisions(self, collision_results: Dict[str, Any], 
                           options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        可视化碰撞检测结果
        
        Args:
            collision_results: 碰撞检测结果
            options: 可视化选项
            
        Returns:
            Dict: 可视化结果
        """
        if options is None:
            options = {}
        
        try:
            # 从碰撞结果中提取信息
            collisions = collision_results.get("collisions", [])
            collision_pairs = collision_results.get("collision_pairs", [])
            
            if not collisions and not collision_pairs:
                return {
                    "success": True,
                    "message": "没有碰撞需要可视化",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 生成可视化数据
            viz_data = self._generate_collision_viz_data(collisions, collision_pairs, options)
            
            result = {
                "success": True,
                "collision_count": len(collisions) + len(collision_pairs),
                "visualization_data": viz_data,
                "options_used": options,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"可视化碰撞失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _generate_collision_viz_data(self, collisions: List[Dict], 
                                   collision_pairs: List[Dict], 
                                   options: Dict[str, Any]) -> Dict[str, Any]:
        """生成碰撞可视化数据"""
        viz_data = {
            "collision_points": [],
            "collision_regions": [],
            "collision_lines": [],
            "severity_colors": {
                "high": [1.0, 0.0, 0.0, 0.8],    # 红色
                "medium": [1.0, 0.5, 0.0, 0.8],   # 橙色
                "low": [1.0, 1.0, 0.0, 0.8]       # 黄色
            },
            "options": options
        }        # 处理碰撞点
        for i, collision in enumerate(collisions):
            if "position" in collision:
                point_viz = self._visualize_collision_point(collision, i)
                viz_data["collision_points"].append(point_viz)
        
        # 处理碰撞对
        for i, pair in enumerate(collision_pairs):
            if "object1" in pair and "object2" in pair:
                line_viz = self._visualize_collision_line(pair, i)
                viz_data["collision_lines"].append(line_viz)
                
                region_viz = self._visualize_collision_region(pair, i)
                viz_data["collision_regions"].append(region_viz)
        
        return viz_data
    
    def _visualize_collision_point(self, collision: Dict, index: int) -> Dict[str, Any]:
        """可视化碰撞点"""
        position = collision.get("position", [0, 0, 0])
        severity = collision.get("severity", "medium")
        penetration = collision.get("penetration_depth", 0.0)
        
        # 根据穿透深度调整大小
        size = max(0.01, min(0.1, penetration * 10))
        
        return {
            "id": f"collision_point_{index}",
            "type": "sphere",
            "position": position,
            "size": [size, size, size],
            "color": self._get_severity_color(severity),
            "label": f"碰撞点 {index}",
            "severity": severity,
            "penetration_depth": penetration,
            "visible": True
        }
    
    def _visualize_collision_line(self, pair: Dict, index: int) -> Dict[str, Any]:
        """可视化碰撞连线"""
        # 这里简化处理，实际应该从缓存获取物体位置
        pos1 = [0, 0, 0]
        pos2 = [0.5, 0, 0]
        
        # 计算中点
        midpoint = [(pos1[i] + pos2[i]) / 2 for i in range(3)]
        
        return {
            "id": f"collision_line_{index}",
            "type": "line",
            "start": pos1,
            "end": pos2,
            "color": [1.0, 0.0, 0.0, 0.6],  # 红色半透明
            "thickness": 0.02,
            "label": f"{pair.get('object1', 'obj1')} ↔ {pair.get('object2', 'obj2')}",
            "visible": True
        }
    
    def _visualize_collision_region(self, pair: Dict, index: int) -> Dict[str, Any]:
        """可视化碰撞区域"""
        # 简化：在碰撞对中点显示一个区域标记
        midpoint = [0.25, 0, 0]
        
        return {
            "id": f"collision_region_{index}",
            "type": "sphere",
            "position": midpoint,
            "size": [0.05, 0.05, 0.05],
            "color": [1.0, 0.0, 0.0, 0.3],  # 红色，更透明
            "label": f"碰撞区域 {index}",
            "visible": True,
            "wireframe": True  # 线框模式
        }
    
    def _get_severity_color(self, severity: str) -> List[float]:
        """获取严重程度对应的颜色"""
        colors = {
            "high": [1.0, 0.0, 0.0, 0.8],    # 红色
            "medium": [1.0, 0.5, 0.0, 0.8],   # 橙色
            "low": [1.0, 1.0, 0.0, 0.8]       # 黄色
        }
        return colors.get(severity, [1.0, 1.0, 1.0, 0.8])  # 默认白色