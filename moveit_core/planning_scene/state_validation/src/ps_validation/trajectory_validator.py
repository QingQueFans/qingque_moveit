#!/usr/bin/env python3
"""
轨迹验证器 - 验证轨迹（状态序列）的连续性和可行性
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import os
import json
import math

class TrajectoryValidator:
    """轨迹验证器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化轨迹验证器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        
        # 默认验证参数
        self.default_params = {
            "max_joint_velocity": 1.0,      # 最大关节速度 (rad/s)
            "max_joint_acceleration": 2.0,  # 最大关节加速度 (rad/s²)
            "max_position_error": 0.01,     # 最大位置误差 (m)
            "max_orientation_error": 0.1,   # 最大姿态误差 (rad)
            "time_resolution": 0.01,        # 时间分辨率 (s)
            "min_sampling_points": 10       # 最小采样点数
        }
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 轨迹验证器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 轨迹验证器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 轨迹验证器: 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return float(value)
    
    def validate_trajectory(self, trajectory_config: Dict[str, Any], 
                           validation_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        验证轨迹
        
        Args:
            trajectory_config: 轨迹配置
            validation_params: 验证参数
            
        Returns:
            Dict: 轨迹验证结果
        """
        try:
            # 合并默认参数和用户参数
            params = self.default_params.copy()
            if validation_params:
                params.update(validation_params)
            
            # 提取轨迹数据
            trajectory = self._extract_trajectory_data(trajectory_config)
            
            if not trajectory["states"]:
                return {
                    "valid": False,
                    "error": "轨迹中没有状态数据",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            results = {
                "trajectory_id": trajectory_config.get("id", "unknown"),
                "total_points": len(trajectory["states"]),
                "has_timing": trajectory["has_timing"],
                "has_joint_velocities": trajectory["has_joint_velocities"],
                "has_joint_accelerations": trajectory["has_joint_accelerations"],
                "validation_params": params,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid": True,
                "violations": []
            }            # 执行各项验证
            validation_functions = [
                ("continuity", self._check_continuity),
                ("joint_limits", self._check_joint_limits_trajectory),
                ("velocity_limits", self._check_velocity_limits),
                ("acceleration_limits", self._check_acceleration_limits),
                ("collision", self._check_collision_trajectory),
                ("smoothness", self._check_smoothness),
                ("timing", self._check_timing),
            ]
            
            for check_name, check_func in validation_functions:
                if check_name in params.get("checks", ["all"]):
                    check_result = check_func(trajectory, params)
                    
                    if not check_result.get("valid", True):
                        results["valid"] = False
                    
                    results[f"{check_name}_result"] = check_result
                    
                    # 收集违规信息
                    if "violations" in check_result:
                        for violation in check_result["violations"]:
                            violation["check_type"] = check_name
                            results["violations"].append(violation)
            
            # 计算轨迹质量指标
            quality_metrics = self._calculate_quality_metrics(trajectory, params)
            results["quality_metrics"] = quality_metrics
            
            # 生成总结报告
            summary = self._generate_summary(results)
            results["summary"] = summary
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"轨迹验证过程中发生错误: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _extract_trajectory_data(self, trajectory_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取轨迹数据"""
        states = trajectory_config.get("states", [])
        waypoints = trajectory_config.get("waypoints", [])
        
        # 如果提供了waypoints，转换为states格式
        if waypoints and not states:
            states = []
            for i, wp in enumerate(waypoints):
                state = {
                    "id": f"waypoint_{i}",
                    "position": wp.get("position"),
                    "orientation": wp.get("orientation"),
                    "joint_state": wp.get("joint_state"),
                    "time_from_start": wp.get("time", i * 0.1)  # 默认时间间隔0.1s
                }
                states.append(state)
        
        # 提取时间信息
        has_timing = all("time_from_start" in state for state in states)        # 提取关节速度信息
        has_joint_velocities = all("joint_velocity" in state for state in states)
        
        # 提取关节加速度信息
        has_joint_accelerations = all("joint_acceleration" in state for state in states)
        
        # 确保数据格式正确
        processed_states = []
        for i, state in enumerate(states):
            processed_state = {
                "index": i,
                "joint_state": self._ensure_float(state.get("joint_state", [])),
                "position": self._ensure_float(state.get("position", [0, 0, 0])),
                "orientation": self._ensure_float(state.get("orientation", [0, 0, 0, 1])),
                "time_from_start": float(state.get("time_from_start", i * 0.1))
            }
            
            if "joint_velocity" in state:
                processed_state["joint_velocity"] = self._ensure_float(state["joint_velocity"])
            
            if "joint_acceleration" in state:
                processed_state["joint_acceleration"] = self._ensure_float(state["joint_acceleration"])
            
            processed_states.append(processed_state)
        
        return {
            "states": processed_states,
            "has_timing": has_timing,
            "has_joint_velocities": has_joint_velocities,
            "has_joint_accelerations": has_joint_accelerations,
            "joint_dof": len(processed_states[0]["joint_state"]) if processed_states else 0
        }
    
    def _check_continuity(self, trajectory: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """检查轨迹连续性"""
        violations = []
        states = trajectory["states"]
        
        if len(states) < 2:
            return {
                "valid": True,
                "check_type": "continuity",
                "message": "轨迹点太少，无法检查连续性"
            }
        
        max_joint_discontinuity = 0.0
        max_position_discontinuity = 0.0
        
        for i in range(len(states) - 1):
            state1 = states[i]
            state2 = states[i + 1]
            
            # 检查关节连续性
            if state1["joint_state"] and state2["joint_state"]:
                joint_diff = self._calculate_joint_difference(
                    state1["joint_state"], 
                    state2["joint_state"]
                )
                
                if joint_diff > params["max_position_error"] * 10:  # 放宽关节连续性阈值
                    max_joint_discontinuity = max(max_joint_discontinuity, joint_diff)
                    
                    violations.append({
                        "type": "joint_discontinuity",
                        "severity": "medium",
                        "segment": [i, i + 1],
                        "joint_difference": float(joint_diff),
                        "threshold": float(params["max_position_error"] * 10),
                        "description": f"轨迹段 [{i},{i+1}] 关节变化过大: {joint_diff:.3f} rad"
                    })            # 检查位置连续性
            pos_diff = self._calculate_position_difference(
                state1["position"],
                state2["position"]
            )
            
            if pos_diff > params["max_position_error"]:
                max_position_discontinuity = max(max_position_discontinuity, pos_diff)
                
                violations.append({
                    "type": "position_discontinuity",
                    "severity": "medium",
                    "segment": [i, i + 1],
                    "position_difference": float(pos_diff),
                    "threshold": float(params["max_position_error"]),
                    "description": f"轨迹段 [{i},{i+1}] 位置变化过大: {pos_diff:.3f} m"
                })
        
        return {
            "valid": len(violations) == 0,
            "check_type": "continuity",
            "violations": violations,
            "max_joint_discontinuity": float(max_joint_discontinuity),
            "max_position_discontinuity": float(max_position_discontinuity),
            "segments_checked": len(states) - 1
        }
    
    def _check_joint_limits_trajectory(self, trajectory: Dict[str, Any], 
                                      params: Dict[str, Any]) -> Dict[str, Any]:
        """检查轨迹中的关节限位"""
        violations = []
        states = trajectory["states"]
        
        # 简化的关节限位检查
        lower_limits = [-3.14] * trajectory["joint_dof"]
        upper_limits = [3.14] * trajectory["joint_dof"]
        
        limit_violations_count = 0
        
        for i, state in enumerate(states):
            joint_state = state["joint_state"]
            
            for j, joint_value in enumerate(joint_state):
                if joint_value < lower_limits[j]:
                    limit_violations_count += 1
                    
                    if len(violations) < 5:  # 只报告前5个违规
                        violations.append({
                            "type": "joint_limit_violation",
                            "severity": "high",
                            "state_index": i,
                            "joint_index": j,
                            "joint_value": float(joint_value),
                            "limit": float(lower_limits[j]),
                            "limit_type": "lower",
                            "description": f"状态 {i} 关节 {j} 超出下限: {joint_value:.3f} < {lower_limits[j]:.3f}"
                        })
                
                elif joint_value > upper_limits[j]:
                    limit_violations_count += 1
                    
                    if len(violations) < 5:
                        violations.append({
                            "type": "joint_limit_violation",
                            "severity": "high",
                            "state_index": i,
                            "joint_index": j,
                            "joint_value": float(joint_value),
                            "limit": float(upper_limits[j]),
                            "limit_type": "upper",
                            "description": f"状态 {i} 关节 {j} 超出上限: {joint_value:.3f} > {upper_limits[j]:.3f}"
                        })
        
        return {
            "valid": limit_violations_count == 0,
            "check_type": "joint_limits",
            "violations": violations,
            "total_violations": limit_violations_count,
            "states_checked": len(states),
            "joints_checked_per_state": trajectory["joint_dof"]
        }
    
    def _check_velocity_limits(self, trajectory: Dict[str, Any], 
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """检查关节速度限制"""
        violations = []
        states = trajectory["states"]
        
        if not trajectory["has_timing"] or len(states) < 2:
            return {
                "valid": True,
                "check_type": "velocity_limits",
                "message": "缺少时间信息，无法检查速度"
            }
        
        max_velocity_violation = 0.0
        
        for i in range(len(states) - 1):
            state1 = states[i]
            state2 = states[i + 1]
            
            dt = state2["time_from_start"] - state1["time_from_start"]
            
            if dt <= 0:
                continue            # 计算关节速度
            if state1["joint_state"] and state2["joint_state"]:
                for j in range(len(state1["joint_state"])):
                    dq = state2["joint_state"][j] - state1["joint_state"][j]
                    velocity = abs(dq / dt)
                    
                    if velocity > params["max_joint_velocity"]:
                        max_velocity_violation = max(max_velocity_violation, velocity)
                        
                        if len(violations) < 3:  # 只报告前3个违规
                            violations.append({
                                "type": "velocity_limit_violation",
                                "severity": "medium",
                                "segment": [i, i + 1],
                                "joint_index": j,
                                "velocity": float(velocity),
                                "limit": float(params["max_joint_velocity"]),
                                "time_interval": float(dt),
                                "description": f"轨迹段 [{i},{i+1}] 关节 {j} 速度超出限制: {velocity:.3f} rad/s > {params['max_joint_velocity']:.3f} rad/s"
                            })
        
        return {
            "valid": len(violations) == 0,
            "check_type": "velocity_limits",
            "violations": violations,
            "max_velocity_violation": float(max_velocity_violation),
            "velocity_limit": float(params["max_joint_velocity"])
        }
    
    def _check_acceleration_limits(self, trajectory: Dict[str, Any], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """检查关节加速度限制"""
        violations = []
        states = trajectory["states"]
        
        if not trajectory["has_timing"] or len(states) < 3:
            return {
                "valid": True,
                "check_type": "acceleration_limits",
                "message": "需要至少3个带时间戳的状态来检查加速度"
            }
        
        max_acceleration_violation = 0.0
        
        for i in range(1, len(states) - 1):
            state0 = states[i - 1]
            state1 = states[i]
            state2 = states[i + 1]
            
            dt1 = state1["time_from_start"] - state0["time_from_start"]
            dt2 = state2["time_from_start"] - state1["time_from_start"]
            
            if dt1 <= 0 or dt2 <= 0:
                continue
            
            # 使用中心差分法计算加速度
            if state0["joint_state"] and state1["joint_state"] and state2["joint_state"]:
                for j in range(len(state1["joint_state"])):
                    v1 = (state1["joint_state"][j] - state0["joint_state"][j]) / dt1
                    v2 = (state2["joint_state"][j] - state1["joint_state"][j]) / dt2
                    
                    acceleration = abs((v2 - v1) / ((dt1 + dt2) / 2))
                    
                    if acceleration > params["max_joint_acceleration"]:
                        max_acceleration_violation = max(max_acceleration_violation, acceleration)
                        
                        if len(violations) < 3:
                            violations.append({
                                "type": "acceleration_limit_violation",
                                "severity": "medium",
                                "state_index": i,
                                "joint_index": j,
                                "acceleration": float(acceleration),
                                "limit": float(params["max_joint_acceleration"]),
                                "description": f"状态 {i} 关节 {j} 加速度超出限制: {acceleration:.3f} rad/s² > {params['max_joint_acceleration']:.3f} rad/s²"
                            })
        
        return {
            "valid": len(violations) == 0,
            "check_type": "acceleration_limits",
            "violations": violations,
            "max_acceleration_violation": float(max_acceleration_violation),
            "acceleration_limit": float(params["max_joint_acceleration"])
        }
    
    def _check_collision_trajectory(self, trajectory: Dict[str, Any], 
                                   params: Dict[str, Any]) -> Dict[str, Any]:
        """检查轨迹中的碰撞"""
        violations = []
        states = trajectory["states"]        
        # 从缓存获取物体信息
        cache = self._load_cache()
        
        if not cache:
            return {
                "valid": True,
                "check_type": "collision",
                "message": "场景为空，无需检查碰撞"
            }
        
        collision_states = []
        
        for i, state in enumerate(states):
            # 简化的碰撞检查：检查机器人是否与场景物体碰撞
            robot_position = state["position"]
            robot_size = [0.5, 0.5, 1.0]  # 简化的机器人包围盒
            
            colliding_objects = []
            
            for obj_id, obj_data in cache.items():
                obj_position = self._extract_position(obj_data)
                obj_size = self._extract_size(obj_data)
                
                collision = self._check_aabb_collision(
                    robot_position, robot_size,
                    obj_position, obj_size
                )
                
                if collision:
                    colliding_objects.append(obj_id)
            
            if colliding_objects:
                collision_states.append(i)
                
                violations.append({
                    "type": "trajectory_collision",
                    "severity": "high",
                    "state_index": i,
                    "colliding_objects": colliding_objects,
                    "robot_position": robot_position,
                    "description": f"状态 {i} 与 {len(colliding_objects)} 个物体发生碰撞: {', '.join(colliding_objects[:2])}{'...' if len(colliding_objects) > 2 else ''}"
                })
                
                # 只报告前5个碰撞状态
                if len(violations) >= 5:
                    break
        
        return {
            "valid": len(collision_states) == 0,
            "check_type": "collision",
            "violations": violations,
            "collision_states": collision_states,
            "total_collision_states": len(collision_states),
            "scene_objects": len(cache)
        }
    
    def _check_smoothness(self, trajectory: Dict[str, Any], 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """检查轨迹平滑性"""
        violations = []
        states = trajectory["states"]
        
        if len(states) < 3:
            return {
                "valid": True,
                "check_type": "smoothness",
                "message": "需要至少3个状态来检查平滑性"
            }
        
        # 计算关节变化的二阶差分（曲率）
        max_curvature = 0.0
        
        for j in range(trajectory["joint_dof"]):
            joint_values = [state["joint_state"][j] for state in states]            # 计算二阶差分
            curvatures = []
            for i in range(1, len(joint_values) - 1):
                curvature = abs(joint_values[i+1] - 2*joint_values[i] + joint_values[i-1])
                curvatures.append(curvature)
            
            if curvatures:
                joint_max_curvature = max(curvatures)
                max_curvature = max(max_curvature, joint_max_curvature)
                
                if joint_max_curvature > 0.5:  # 曲率阈值
                    violations.append({
                        "type": "smoothness_violation",
                        "severity": "low",
                        "joint_index": j,
                        "max_curvature": float(joint_max_curvature),
                        "threshold": 0.5,
                        "description": f"关节 {j} 轨迹不够平滑，最大曲率: {joint_max_curvature:.3f}"
                    })
        
        return {
            "valid": len(violations) == 0,
            "check_type": "smoothness",
            "violations": violations,
            "max_curvature": float(max_curvature),
            "joints_checked": trajectory["joint_dof"]
        }
    
    def _check_timing(self, trajectory: Dict[str, Any], 
                     params: Dict[str, Any]) -> Dict[str, Any]:
        """检查时间参数"""
        violations = []
        states = trajectory["states"]
        
        if not trajectory["has_timing"]:
            return {
                "valid": True,
                "check_type": "timing",
                "message": "轨迹没有时间信息"
            }
        
        # 检查时间是否单调递增
        for i in range(len(states) - 1):
            t1 = states[i]["time_from_start"]
            t2 = states[i + 1]["time_from_start"]
            
            if t2 <= t1:
                violations.append({
                    "type": "non_monotonic_time",
                    "severity": "medium",
                    "segment": [i, i + 1],
                    "time1": float(t1),
                    "time2": float(t2),
                    "description": f"时间非单调递增: t[{i}]={t1:.3f}s, t[{i+1}]={t2:.3f}s"
                })
        
        # 检查时间间隔是否合理
        if len(states) >= 2:
            total_time = states[-1]["time_from_start"] - states[0]["time_from_start"]
            avg_interval = total_time / (len(states) - 1)
            
            if avg_interval < params["time_resolution"]:
                violations.append({
                    "type": "high_frequency_sampling",
                    "severity": "low",
                    "average_interval": float(avg_interval),
                    "recommended_interval": float(params["time_resolution"]),
                    "description": f"采样频率过高: 平均间隔 {avg_interval:.3f}s < 推荐值 {params['time_resolution']:.3f}s"
                })
        
        return {
            "valid": len(violations) == 0,
            "check_type": "timing",
            "violations": violations,
            "total_time": float(states[-1]["time_from_start"] - states[0]["time_from_start"]) if states else 0.0,
            "state_count": len(states)
        }
    
    def _calculate_quality_metrics(self, trajectory: Dict[str, Any], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """计算轨迹质量指标"""
        states = trajectory["states"]
        
        if len(states) < 2:
            return {
                "total_time": 0.0,
                "average_velocity": 0.0,
                "total_distance": 0.0,
                "message": "轨迹点太少，无法计算质量指标"
            }
        
        # 计算总时间
        total_time = states[-1]["time_from_start"] - states[0]["time_from_start"]        # 计算总路径长度（关节空间）
        total_joint_distance = 0.0
        for i in range(len(states) - 1):
            joint_distance = self._calculate_joint_difference(
                states[i]["joint_state"],
                states[i + 1]["joint_state"]
            )
            total_joint_distance += joint_distance
        
        # 计算总路径长度（笛卡尔空间）
        total_cartesian_distance = 0.0
        for i in range(len(states) - 1):
            cartesian_distance = self._calculate_position_difference(
                states[i]["position"],
                states[i + 1]["position"]
            )
            total_cartesian_distance += cartesian_distance
        
        # 计算平均速度
        average_joint_velocity = total_joint_distance / total_time if total_time > 0 else 0.0
        average_cartesian_velocity = total_cartesian_distance / total_time if total_time > 0 else 0.0
        
        # 计算平滑度指标
        smoothness_score = self._calculate_smoothness_score(states)
        
        return {
            "total_time": float(total_time),
            "state_count": len(states),
            "average_time_interval": float(total_time / (len(states) - 1)) if len(states) > 1 else 0.0,
            "total_joint_distance": float(total_joint_distance),
            "total_cartesian_distance": float(total_cartesian_distance),
            "average_joint_velocity": float(average_joint_velocity),
            "average_cartesian_velocity": float(average_cartesian_velocity),
            "smoothness_score": float(smoothness_score),
            "efficiency": float(total_cartesian_distance / total_joint_distance) if total_joint_distance > 0 else 0.0
        }
    
    def _calculate_smoothness_score(self, states: List[Dict]) -> float:
        """计算轨迹平滑度分数"""
        if len(states) < 3:
            return 1.0  # 无法计算，返回完美分数
        
        joint_curvatures = []
        
        for j in range(len(states[0]["joint_state"])):
            joint_values = [state["joint_state"][j] for state in states]
            
            # 计算二阶差分的平均值
            curvatures = []
            for i in range(1, len(joint_values) - 1):
                curvature = abs(joint_values[i+1] - 2*joint_values[i] + joint_values[i-1])
                curvatures.append(curvature)
            
            if curvatures:
                joint_curvatures.append(np.mean(curvatures))
        
        if not joint_curvatures:
            return 1.0
        
        # 将曲率转换为分数（0-1，越高越好）
        avg_curvature = np.mean(joint_curvatures)
        smoothness_score = 1.0 / (1.0 + avg_curvature * 10.0)
        
        return min(1.0, max(0.0, smoothness_score))
    
    def _generate_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证总结"""
        violations = validation_results.get("violations", [])
        quality_metrics = validation_results.get("quality_metrics", {})        # 按严重程度统计违规
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        type_counts = {}
        
        for violation in violations:
            severity = violation.get("severity", "medium")
            violation_type = violation.get("type", "unknown")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[violation_type] = type_counts.get(violation_type, 0) + 1
        
        # 评估轨迹质量
        total_violations = len(violations)
        smoothness_score = quality_metrics.get("smoothness_score", 1.0)
        
        if total_violations == 0:
            quality_rating = "excellent"
        elif severity_counts["high"] == 0 and total_violations <= 3:
            quality_rating = "good"
        elif severity_counts["high"] == 0:
            quality_rating = "fair"
        else:
            quality_rating = "poor"
        
        return {
            "trajectory_valid": validation_results["valid"],
            "quality_rating": quality_rating,
            "total_violations": total_violations,
            "severity_breakdown": severity_counts,
            "violation_types": type_counts,
            "smoothness_rating": "smooth" if smoothness_score > 0.8 else "acceptable" if smoothness_score > 0.5 else "rough",
            "efficiency_rating": "efficient" if quality_metrics.get("efficiency", 0) > 0.8 else "acceptable",
            "recommendations": self._generate_recommendations(violations, quality_metrics)
        }
    
    def _generate_recommendations(self, violations: List[Dict], 
                                 quality_metrics: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于违规的建议
        high_severity_violations = [v for v in violations if v.get("severity") == "high"]
        
        if high_severity_violations:
            collision_violations = [v for v in high_severity_violations if "collision" in v.get("type", "")]
            joint_limit_violations = [v for v in high_severity_violations if "joint_limit" in v.get("type", "")]
            
            if collision_violations:
                recommendations.append("修复碰撞问题：调整轨迹以避免与场景物体碰撞")
            
            if joint_limit_violations:
                recommendations.append("修复关节限位违规：确保所有关节角度在允许范围内")
        
        # 基于质量的建议
        smoothness_score = quality_metrics.get("smoothness_score", 1.0)
        if smoothness_score < 0.6:
            recommendations.append("提高轨迹平滑度：增加中间点或使用平滑插值")
        
        efficiency = quality_metrics.get("efficiency", 0)
        if efficiency < 0.5:
            recommendations.append("提高轨迹效率：优化路径以减少不必要的关节运动")        # 通用建议
        if not recommendations:
            recommendations.append("轨迹质量良好，无需特殊改进")
        
        return recommendations
    
    def _calculate_joint_difference(self, joints1: List[float], joints2: List[float]) -> float:
        """计算关节空间距离"""
        if not joints1 or not joints2 or len(joints1) != len(joints2):
            return float('inf')
        
        diff = sum((j1 - j2)**2 for j1, j2 in zip(joints1, joints2))
        return math.sqrt(diff)
    
    def _calculate_position_difference(self, pos1: List[float], pos2: List[float]) -> float:
        """计算位置距离"""
        if len(pos1) != 3 or len(pos2) != 3:
            return float('inf')
        
        diff = sum((p1 - p2)**2 for p1, p2 in zip(pos1, pos2))
        return math.sqrt(diff)
    
    def _check_aabb_collision(self, pos1: List[float], size1: List[float],
                             pos2: List[float], size2: List[float]) -> bool:
        """轴对齐包围盒碰撞检测"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dz = abs(pos1[2] - pos2[2])
        
        tx = size1[0]/2 + size2[0]/2
        ty = size1[1]/2 + size2[1]/2
        tz = size1[2]/2 + size2[2]/2
        
        return dx < tx and dy < ty and dz < tz
    
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
            return [0.1, 0.1, 0.1]