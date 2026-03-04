#!/usr/bin/env python3
"""
状态验证器 - 验证规划场景中的状态有效性
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import os
import json
import math

class StateValidator:
    """状态验证器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化状态验证器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        
        # 默认关节限制（可以根据实际机器人配置修改）
        self.default_joint_limits = {
            "joint_limits": {
                "lower": [-3.14, -3.14, -3.14, -3.14, -3.14, -3.14],  # 6DOF机器人示例
                "upper": [3.14, 3.14, 3.14, 3.14, 3.14, 3.14]
            }
        }
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 状态验证器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 状态验证器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 状态验证器: 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型（RoS2兼容）"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return float(value)
    
    def validate_state(self, state_config: Dict[str, Any], 
                      checks: List[str] = None) -> Dict[str, Any]:
        """
        验证单个状态
        
        Args:
            state_config: 状态配置字典
            checks: 要执行的检查列表，默认为所有检查
            
        Returns:
            Dict: 验证结果
        """
        try:
            # 默认执行所有检查
            if checks is None:
                checks = ['collision', 'joint_limits', 'reachability', 'singularity']
            
            results = {
                "state_id": state_config.get("id", "unknown"),
                "state_type": state_config.get("type", "unknown"),
                "valid": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "checks_performed": checks,
                "violations": []
            }
            
            # 提取状态信息
            joint_state = state_config.get("joint_state")
            pose = state_config.get("pose")
            position = state_config.get("position")
            
            # 执行各项检查
            for check_type in checks:
                check_result = self._perform_check(check_type, state_config)
                
                if not check_result["valid"]:
                    results["valid"] = False
                    results["violations"].extend(check_result["violations"])
                
                results[check_type + "_check"] = check_result
            
            # 计算验证分数（有效性百分比）
            total_checks = len(checks)
            failed_checks = len(results["violations"])
            results["validation_score"] = max(0, 1.0 - failed_checks / total_checks)            # 添加修复建议
            if results["violations"]:
                results["suggestions"] = self._generate_suggestions(results["violations"])
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证过程中发生错误: {str(e)}",
                "violations": [{"type": "system_error", "description": str(e)}]
            }
    
    def _perform_check(self, check_type: str, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行特定的检查"""
        if check_type == "collision":
            return self._check_collision(state_config)
        elif check_type == "joint_limits":
            return self._check_joint_limits(state_config)
        elif check_type == "reachability":
            return self._check_reachability(state_config)
        elif check_type == "singularity":
            return self._check_singularity(state_config)
        elif check_type == "constraints":
            return self._check_constraints(state_config)
        else:
            return {
                "valid": True,
                "check_type": check_type,
                "violations": [],
                "message": f"未知检查类型: {check_type}"
            }
    
    def _check_collision(self, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查碰撞"""
        violations = []
        
        try:
            # 从缓存获取所有物体
            cache = self._load_cache()
            
            if not cache:
                return {
                    "valid": True,
                    "check_type": "collision",
                    "violations": violations,
                    "message": "场景为空，无法进行碰撞检查"
                }
            
            # 获取机器人位置（简化处理）
            robot_position = [0.0, 0.0, 0.0]  # 默认机器人基座位置
            if "robot_position" in state_config:
                robot_position = self._ensure_float(state_config["robot_position"])
            
            # 检查机器人是否与场景物体碰撞
            robot_size = [0.5, 0.5, 1.0]  # 简化的机器人包围盒
            
            for obj_id, obj_data in cache.items():
                obj_position = self._extract_position(obj_data)
                obj_size = self._extract_size(obj_data)
                
                # 轴对齐包围盒碰撞检测
                collision = self._check_aabb_collision(
                    robot_position, robot_size,
                    obj_position, obj_size
                )
                
                if collision:
                    violations.append({
                        "type": "collision",
                        "severity": "high",
                        "object1": "robot",
                        "object2": obj_id,
                        "description": f"机器人与物体 {obj_id} 发生碰撞",
                        "distance": 0.0,
                        "suggestion": f"调整机器人位置或移除物体 {obj_id}"
                    })
            
            return {
                "valid": len(violations) == 0,
                "check_type": "collision",
                "violations": violations,
                "collision_count": len(violations),
                "checked_objects": len(cache)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "check_type": "collision",
                "violations": [{
                    "type": "collision_check_error",
                    "severity": "medium",
                    "description": f"碰撞检查失败: {str(e)}"
                }]
            }
    
    def _check_joint_limits(self, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查关节限位"""
        violations = []
        
        try:
            joint_state = state_config.get("joint_state")
            
            if not joint_state:
                return {
                    "valid": True,
                    "check_type": "joint_limits",
                    "violations": [],
                    "message": "未提供关节状态，跳过关节限位检查"
                }            # 确保关节状态是浮点数列表
            joint_state = self._ensure_float(joint_state)
            
            # 使用默认或配置的关节限制
            joint_limits = state_config.get("joint_limits", self.default_joint_limits)
            lower_limits = self._ensure_float(joint_limits.get("lower", []))
            upper_limits = self._ensure_float(joint_limits.get("upper", []))
            
            if len(joint_state) != len(lower_limits) or len(joint_state) != len(upper_limits):
                return {
                    "valid": False,
                    "check_type": "joint_limits",
                    "violations": [{
                        "type": "joint_limit_config",
                        "severity": "medium",
                        "description": f"关节状态维度({len(joint_state)})与限制维度({len(lower_limits)}/{len(upper_limits)})不匹配"
                    }]
                }
            
            # 检查每个关节
            for i, (joint_value, lower, upper) in enumerate(zip(joint_state, lower_limits, upper_limits)):
                if joint_value < lower:
                    violations.append({
                        "type": "joint_limit",
                        "severity": "high",
                        "joint_index": i,
                        "joint_value": float(joint_value),
                        "limit_value": float(lower),
                        "limit_type": "lower",
                        "description": f"关节 {i} 超出下限: {joint_value:.3f} < {lower:.3f}",
                        "violation_amount": float(lower - joint_value),
                        "suggestion": f"增加关节 {i} 的角度至少 {lower - joint_value:.3f} 弧度"
                    })
                elif joint_value > upper:
                    violations.append({
                        "type": "joint_limit",
                        "severity": "high",
                        "joint_index": i,
                        "joint_value": float(joint_value),
                        "limit_value": float(upper),
                        "limit_type": "upper",
                        "description": f"关节 {i} 超出上限: {joint_value:.3f} > {upper:.3f}",
                        "violation_amount": float(joint_value - upper),
                        "suggestion": f"减少关节 {i} 的角度至少 {joint_value - upper:.3f} 弧度"
                    })
            
            return {
                "valid": len(violations) == 0,
                "check_type": "joint_limits",
                "violations": violations,
                "violated_joints": len(violations),
                "total_joints": len(joint_state)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "check_type": "joint_limits",
                "violations": [{
                    "type": "joint_limit_check_error",
                    "severity": "medium",
                    "description": f"关节限位检查失败: {str(e)}"
                }]
            }
    
    def _check_reachability(self, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查可达性"""
        violations = []
        
        try:
            # 简化的可达性检查：检查末端位置是否在工作空间内
            target_position = state_config.get("position")
            
            if not target_position:
                return {
                    "valid": True,
                    "check_type": "reachability",
                    "violations": [],
                    "message": "未提供目标位置，跳过可达性检查"
                }
            
            target_position = self._ensure_float(target_position)            # 简化的工作空间检查：半径为1.5米的球体
            workspace_center = [0.0, 0.0, 0.5]
            workspace_radius = 1.5
            
            distance = math.sqrt(
                (target_position[0] - workspace_center[0])**2 +
                (target_position[1] - workspace_center[1])**2 +
                (target_position[2] - workspace_center[2])**2
            )
            
            if distance > workspace_radius:
                violations.append({
                    "type": "reachability",
                    "severity": "medium",
                    "target_position": target_position,
                    "workspace_center": workspace_center,
                    "workspace_radius": float(workspace_radius),
                    "distance": float(distance),
                    "description": f"目标位置 {target_position} 超出工作空间 (距离: {distance:.3f}m > 半径: {workspace_radius:.1f}m)",
                    "suggestion": f"将目标位置调整到以 {workspace_center} 为中心，{workspace_radius:.1f}m 为半径的球体内"
                })
            
            return {
                "valid": len(violations) == 0,
                "check_type": "reachability",
                "violations": violations,
                "distance_to_center": float(distance),
                "workspace_radius": float(workspace_radius)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "check_type": "reachability",
                "violations": [{
                    "type": "reachability_check_error",
                    "severity": "medium",
                    "description": f"可达性检查失败: {str(e)}"
                }]
            }
    
    def _check_singularity(self, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查奇异点"""
        violations = []
        
        try:
            joint_state = state_config.get("joint_state")
            
            if not joint_state:
                return {
                    "valid": True,
                    "check_type": "singularity",
                    "violations": [],
                    "message": "未提供关节状态，跳过奇异点检查"
                }
            
            joint_state = self._ensure_float(joint_state)
            
            # 简化的奇异点检查：检查关节是否接近某些临界值
            # 这里检查第二个关节是否接近0（常见的奇异点）
            if len(joint_state) >= 2:
                joint2_value = joint_state[1]
                
                # 检查是否接近0（±0.1弧度范围内）
                if abs(joint2_value) < 0.1:
                    violations.append({
                        "type": "singularity",
                        "severity": "medium",
                        "joint_index": 1,
                        "joint_value": float(joint2_value),
                        "threshold": 0.1,
                        "description": f"关节 1 接近奇异点: {joint2_value:.3f} 太接近 0",
                        "suggestion": "调整关节 1 的角度使其远离 0（建议 > 0.2 弧度）"
                    })
            
            return {
                "valid": len(violations) == 0,
                "check_type": "singularity",
                "violations": violations,
                "joint_state": joint_state
            }
            
        except Exception as e:
            return {
                "valid": False,
                "check_type": "singularity",
                "violations": [{
                    "type": "singularity_check_error",
                    "severity": "medium",
                    "description": f"奇异点检查失败: {str(e)}"
                }]
            }
    
    def _check_constraints(self, state_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查约束"""
        violations = []
        
        try:
            constraints = state_config.get("constraints", [])
            
            if not constraints:
                return {
                    "valid": True,
                    "check_type": "constraints",
                    "violations": [],
                    "message": "未提供约束条件，跳过约束检查"
                }            # 这里可以扩展为检查各种类型的约束
            for i, constraint in enumerate(constraints):
                # 简化处理：只记录约束信息
                violations.append({
                    "type": "constraint_info",
                    "severity": "low",
                    "constraint_index": i,
                    "constraint_type": constraint.get("type", "unknown"),
                    "description": f"约束条件 {i}: {constraint.get('description', '无描述')}"
                })
            
            return {
                "valid": True,  # 约束检查不标记为无效，只是记录信息
                "check_type": "constraints",
                "violations": violations,
                "constraint_count": len(constraints)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "check_type": "constraints",
                "violations": [{
                    "type": "constraint_check_error",
                    "severity": "medium",
                    "description": f"约束检查失败: {str(e)}"
                }]
            }
    
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
        else:            # 根据类型估计尺寸
            obj_type = obj_data.get('type', 'unknown')
            if obj_type == 'box':
                return [0.2, 0.2, 0.2]
            elif obj_type == 'sphere':
                radius = float(obj_data.get('radius', 0.1))
                return [radius * 2, radius * 2, radius * 2]
            else:
                return [0.1, 0.1, 0.1]
    
    def _generate_suggestions(self, violations: List[Dict]) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        for violation in violations:
            if "suggestion" in violation:
                suggestions.append(violation["suggestion"])
        
        # 去重
        return list(set(suggestions))
    
    def validate_trajectory(self, trajectory_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证轨迹（状态序列）
        
        Args:
            trajectory_config: 轨迹配置
            
        Returns:
            Dict: 轨迹验证结果
        """
        try:
            states = trajectory_config.get("states", [])
            
            if not states:
                return {
                    "valid": False,
                    "error": "轨迹中没有任何状态",
                    "total_states": 0
                }
            
            results = {
                "trajectory_id": trajectory_config.get("id", "unknown"),
                "total_states": len(states),
                "valid_states": 0,
                "invalid_states": 0,
                "state_results": [],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid": True,
                "violations": []
            }           # 验证每个状态
            for i, state_config in enumerate(states):
                state_result = self.validate_state(state_config)
                results["state_results"].append(state_result)
                
                if state_result["valid"]:
                    results["valid_states"] += 1
                else:
                    results["invalid_states"] += 1
                    results["valid"] = False
                    
                    # 收集违规信息
                    for violation in state_result.get("violations", []):
                        violation_copy = violation.copy()
                        violation_copy["state_index"] = i
                        results["violations"].append(violation_copy)
            
            # 检查状态连续性（简化的检查）
            continuity_violations = self._check_trajectory_continuity(states)
            results["violations"].extend(continuity_violations)
            
            if continuity_violations:
                results["valid"] = False
            
            # 计算轨迹质量分数
            if len(states) > 0:
                results["trajectory_score"] = results["valid_states"] / len(states)
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"轨迹验证过程中发生错误: {str(e)}"
            }
    
    def _check_trajectory_continuity(self, states: List[Dict]) -> List[Dict]:
        """检查轨迹连续性"""
        violations = []
        
        if len(states) < 2:
            return violations
        
        for i in range(len(states) - 1):
            state1 = states[i]
            state2 = states[i + 1]
            
            joint_state1 = state1.get("joint_state")
            joint_state2 = state2.get("joint_state")
            
            if joint_state1 and joint_state2:
                joint_state1 = self._ensure_float(joint_state1)
                joint_state2 = self._ensure_float(joint_state2)
                
                if len(joint_state1) == len(joint_state2):
                    # 计算关节角度变化
                    changes = []
                    for j in range(len(joint_state1)):
                        change = abs(joint_state2[j] - joint_state1[j])
                        changes.append(change)
                    
                    max_change = max(changes)
                    
                    # 如果最大变化超过阈值（例如1弧度）
                    if max_change > 1.0:
                        violations.append({
                            "type": "continuity",
                            "severity": "medium",
                            "state_pair": [i, i + 1],
                            "max_joint_change": float(max_change),
                            "threshold": 1.0,
                            "description": f"状态 {i} 到 {i+1} 的关节变化过大: {max_change:.3f} > 1.0",
                            "suggestion": "添加中间状态或减小步长"
                        })
        
        return violations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        # 这里可以扩展为记录历史验证数据
        return {
            "validator_type": "state_validator",
            "cache_file": self.cache_file,
            "default_joint_dof": len(self.default_joint_limits["joint_limits"]["lower"]),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }