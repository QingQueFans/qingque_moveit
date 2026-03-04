#!/usr/bin/env python3
"""
轨迹可视化 - 可视化机器人轨迹
"""
from typing import List, Dict, Any, Optional
import time
import numpy as np
import os
import json
import math

class TrajectoryVisualizer:
    """轨迹可视化器"""
    
    def __init__(self, scene_client):
        """
        初始化轨迹可视化器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
    
    def visualize_trajectory(self, trajectory_data: Dict[str, Any], 
                           options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        可视化轨迹
        
        Args:
            trajectory_data: 轨迹数据
            options: 可视化选项
            
        Returns:
            Dict: 可视化结果
        """
        if options is None:
            options = {}
        
        try:
            # 提取轨迹点
            waypoints = self._extract_waypoints(trajectory_data)
            
            if not waypoints:
                return {
                    "success": False,
                    "message": "轨迹中没有有效的路径点",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 生成可视化数据
            viz_data = self._generate_trajectory_viz_data(waypoints, trajectory_data, options)
            
            # 分析轨迹
            analysis = self._analyze_trajectory(waypoints, trajectory_data)
            
            result = {
                "success": True,
                "waypoint_count": len(waypoints),
                "trajectory_analysis": analysis,
                "visualization_data": viz_data,
                "options_used": options,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"可视化轨迹失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _extract_waypoints(self, trajectory_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取轨迹点"""
        waypoints = []
        
        # 从不同格式中提取
        if "states" in trajectory_data:
            for i, state in enumerate(trajectory_data["states"]):
                waypoint = {
                    "index": i,
                    "position": state.get("position", [0, 0, 0]),
                    "orientation": state.get("orientation", [0, 0, 0, 1]),
                    "joint_state": state.get("joint_state", []),
                    "time": state.get("time_from_start", i * 0.1)
                }
                waypoints.append(waypoint)
        
        elif "waypoints" in trajectory_data:
            for i, wp in enumerate(trajectory_data["waypoints"]):
                waypoint = {
                    "index": i,
                    "position": wp.get("position", [0, 0, 0]),
                    "orientation": wp.get("orientation", [0, 0, 0, 1]),
                    "joint_state": wp.get("joint_state", []),
                    "time": wp.get("time", i * 0.1)
                }
                waypoints.append(waypoint)
        
        return waypoints
    
    def _generate_trajectory_viz_data(self, waypoints: List[Dict[str, Any]], 
                                    trajectory_data: Dict[str, Any], 
                                    options: Dict[str, Any]) -> Dict[str, Any]:
        """生成轨迹可视化数据"""
        viz_data = {
            "path_lines": [],
            "waypoints": [],
            "velocity_arrows": [],
            "acceleration_regions": [],
            "color_scheme": options.get("color_scheme", "sequential"),
            "show_velocity": options.get("show_velocity", True),
            "show_acceleration": options.get("show_acceleration", False)
        }
        
        # 生成路径线
        if len(waypoints) >= 2:
            path_viz = self._visualize_path(waypoints, options)
            viz_data["path_lines"].append(path_viz)        # 生成路径点
        for i, wp in enumerate(waypoints):
            if i % options.get("waypoint_sample_rate", 1) == 0:  # 采样显示
                wp_viz = self._visualize_waypoint(wp, i, options)
                viz_data["waypoints"].append(wp_viz)
        
        # 生成速度箭头
        if options.get("show_velocity", True) and len(waypoints) >= 2:
            velocity_viz = self._visualize_velocity(waypoints, options)
            viz_data["velocity_arrows"].extend(velocity_viz)
        
        return viz_data
    
    def _visualize_path(self, waypoints: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, Any]:
        """可视化路径线"""
        positions = [wp["position"] for wp in waypoints]
        
        # 计算路径颜色（根据速度或顺序）
        color_scheme = options.get("color_scheme", "sequential")
        
        if color_scheme == "velocity_based" and len(waypoints) >= 2:
            # 根据速度着色
            colors = []
            for i in range(len(positions) - 1):
                velocity = self._estimate_velocity(waypoints[i], waypoints[i + 1])
                normalized_vel = min(1.0, velocity / 2.0)  # 假设2.0为最大速度
                colors.append([normalized_vel, 1.0 - normalized_vel, 0.0, 0.7])
        else:
            # 顺序着色（从蓝到红）
            colors = []
            for i in range(len(positions) - 1):
                ratio = i / (len(positions) - 2) if len(positions) > 2 else 0.5
                colors.append([ratio, 0.0, 1.0 - ratio, 0.7])
        
        return {
            "id": "trajectory_path",
            "type": "multi_line",
            "segments": positions,
            "colors": colors,
            "thickness": options.get("path_thickness", 0.01),
            "label": "轨迹路径",
            "visible": True
        }
    
    def _visualize_waypoint(self, waypoint: Dict[str, Any], index: int, 
                          options: Dict[str, Any]) -> Dict[str, Any]:
        """可视化路径点"""
        position = waypoint["position"]
        
        # 根据索引着色
        color_index = index / max(1, options.get("total_waypoints", 100))
        color = [
            color_index,           # 红色分量
            0.0,                   # 绿色分量
            1.0 - color_index,     # 蓝色分量
            0.8                    # 透明度
        ]
        
        # 标记起点和终点
        if index == 0:
            label = "起点"
            color = [0.0, 1.0, 0.0, 1.0]  # 绿色
            size = 0.03
        elif index == options.get("total_waypoints", 100) - 1:
            label = "终点"
            color = [1.0, 0.0, 0.0, 1.0]  # 红色
            size = 0.03
        else:
            label = f"点 {index}"
            size = 0.02
        
        return {
            "id": f"waypoint_{index}",
            "type": "sphere",
            "position": position,
            "size": [size, size, size],
            "color": color,
            "label": label,
            "visible": options.get("show_waypoints", True)
        }
    
    def _visualize_velocity(self, waypoints: List[Dict[str, Any]], 
                          options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """可视化速度"""
        velocity_viz = []
        
        # 采样显示速度箭头
        sample_rate = max(1, len(waypoints) // 10)  # 最多显示10个箭头
        
        for i in range(0, len(waypoints) - 1, sample_rate):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]
            
            # 估计速度
            velocity = self._estimate_velocity(wp1, wp2)
            if velocity < 0.001:  # 忽略极小速度
                continue
            
            # 计算方向
            direction = [
                wp2["position"][0] - wp1["position"][0],
                wp2["position"][1] - wp1["position"][1],
                wp2["position"][2] - wp1["position"][2]
            ]
            
            # 归一化并缩放
            norm = math.sqrt(sum(d**2 for d in direction))
            if norm > 0:
                direction = [d/norm * min(0.1, velocity/5) for d in direction]            # 根据速度大小着色
            normalized_vel = min(1.0, velocity / 2.0)  # 假设2.0为最大速度
            color = [normalized_vel, 1.0 - normalized_vel, 0.0, 0.8]
            
            velocity_viz.append({
                "id": f"velocity_arrow_{i}",
                "type": "arrow",
                "position": wp1["position"],
                "direction": direction,
                "color": color,
                "thickness": 0.01,
                "label": f"速度: {velocity:.2f} m/s",
                "visible": True
            })
        
        return velocity_viz
    
    def _estimate_velocity(self, wp1: Dict[str, Any], wp2: Dict[str, Any]) -> float:
        """估计两点间的速度"""
        dt = wp2.get("time", 0) - wp1.get("time", 0)
        if dt <= 0:
            dt = 0.1  # 默认时间间隔
        
        # 计算位置距离
        pos1 = wp1["position"]
        pos2 = wp2["position"]
        distance = math.sqrt(sum((p2 - p1)**2 for p1, p2 in zip(pos1, pos2)))
        
        return distance / dt
    
    def _analyze_trajectory(self, waypoints: List[Dict[str, Any]], 
                          trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析轨迹"""
        if len(waypoints) < 2:
            return {"message": "轨迹点太少，无法分析"}
        
        analysis = {
            "total_waypoints": len(waypoints),
            "total_time": waypoints[-1].get("time", 0) - waypoints[0].get("time", 0),
            "total_distance": 0.0,
            "average_speed": 0.0,
            "max_speed": 0.0,
            "smoothness_score": 0.0
        }
        
        # 计算总距离
        total_distance = 0.0
        speeds = []
        
        for i in range(len(waypoints) - 1):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]
            
            # 距离
            pos1 = wp1["position"]
            pos2 = wp2["position"]
            distance = math.sqrt(sum((p2 - p1)**2 for p1, p2 in zip(pos1, pos2)))
            total_distance += distance
            
            # 速度
            dt = wp2.get("time", 0) - wp1.get("time", 0)
            if dt > 0:
                speed = distance / dt
                speeds.append(speed)
        
        analysis["total_distance"] = total_distance
        if speeds:
            analysis["average_speed"] = sum(speeds) / len(speeds)
            analysis["max_speed"] = max(speeds)
        
        # 计算平滑度（基于位置变化的三阶差分）
        if len(waypoints) >= 4:
            positions = [wp["position"] for wp in waypoints]
            jerk_estimate = 0.0
            for i in range(2, len(positions) - 2):
                # 简化的jerk估计
                jerk = sum(
                    abs(positions[i+1][j] - 3*positions[i][j] + 3*positions[i-1][j] - positions[i-2][j])
                    for j in range(3)
                )
                jerk_estimate += jerk
            
            analysis["smoothness_score"] = max(0.0, 1.0 - jerk_estimate / len(positions))
        
        return analysis