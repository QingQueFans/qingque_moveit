#!/usr/bin/env python3
"""
约束检查器 - 检查状态是否满足各种约束条件
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import os
import json
import math

class ConstraintChecker:
    """约束检查器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化约束检查器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        
        # 支持的约束类型
        self.supported_constraints = [
            "position_constraint",
            "orientation_constraint", 
            "joint_constraint",
            "visibility_constraint",
            "distance_constraint",
            "collision_constraint",
            "workspace_constraint"
        ]
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 约束检查器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 约束检查器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 约束检查器: 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return float(value)
    
    def check_constraints(self, state_config: Dict[str, Any], 
                         constraints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检查状态是否满足约束条件
        
        Args:
            state_config: 状态配置
            constraints: 约束条件列表，如果为None则从state_config获取
            
        Returns:
            Dict: 约束检查结果
        """
        try:
            if constraints is None:
                constraints = state_config.get("constraints", [])
            
            if not constraints:
                return {
                    "satisfied": True,
                    "message": "未提供约束条件",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_constraints": 0,
                    "satisfied_constraints": 0,
                    "violated_constraints": 0,
                    "violations": []
                }
            
            results = {
                "state_id": state_config.get("id", "unknown"),
                "total_constraints": len(constraints),
                "satisfied_constraints": 0,
                "violated_constraints": 0,
                "violations": [],
                "constraint_details": [],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "satisfied": True
            }            # 检查每个约束
            for i, constraint in enumerate(constraints):
                constraint_result = self._check_single_constraint(state_config, constraint, i)
                results["constraint_details"].append(constraint_result)
                
                if constraint_result["satisfied"]:
                    results["satisfied_constraints"] += 1
                else:
                    results["violated_constraints"] += 1
                    results["satisfied"] = False
                    results["violations"].extend(constraint_result.get("violations", []))
            
            return results
            
        except Exception as e:
            return {
                "satisfied": False,
                "error": f"约束检查过程中发生错误: {str(e)}",
                "violations": [{"type": "check_error", "description": str(e)}]
            }
    
    def _check_single_constraint(self, state_config: Dict[str, Any], 
                                constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查单个约束条件"""
        constraint_type = constraint.get("type", "unknown")
        
        if constraint_type == "position_constraint":
            return self._check_position_constraint(state_config, constraint, index)
        elif constraint_type == "orientation_constraint":
            return self._check_orientation_constraint(state_config, constraint, index)
        elif constraint_type == "joint_constraint":
            return self._check_joint_constraint(state_config, constraint, index)
        elif constraint_type == "distance_constraint":
            return self._check_distance_constraint(state_config, constraint, index)
        elif constraint_type == "collision_constraint":
            return self._check_collision_constraint(state_config, constraint, index)
        elif constraint_type == "workspace_constraint":
            return self._check_workspace_constraint(state_config, constraint, index)
        else:
            return {
                "constraint_index": index,
                "constraint_type": constraint_type,
                "satisfied": False,
                "message": f"不支持的约束类型: {constraint_type}",
                "supported_types": self.supported_constraints
            }
    
    def _check_position_constraint(self, state_config: Dict[str, Any], 
                                  constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查位置约束"""
        try:            # 获取目标位置和容差
            target_position = self._ensure_float(constraint.get("target_position", [0, 0, 0]))
            tolerance = float(constraint.get("tolerance", 0.01))
            
            # 从状态中获取当前位置
            current_position = self._extract_position_from_state(state_config)
            
            # 计算距离
            distance = math.sqrt(
                sum((current_position[i] - target_position[i])**2 for i in range(3))
            )
            
            satisfied = distance <= tolerance
            
            result = {
                "constraint_index": index,
                "constraint_type": "position_constraint",
                "satisfied": satisfied,
                "current_position": current_position,
                "target_position": target_position,
                "distance": float(distance),
                "tolerance": float(tolerance),
                "violation_amount": max(0, float(distance - tolerance))
            }
            
            if not satisfied:
                result["violations"] = [{
                    "type": "position_constraint",
                    "severity": constraint.get("severity", "medium"),
                    "description": f"位置超出约束范围: 距离 {distance:.3f}m > 容差 {tolerance:.3f}m",
                    "suggestion": f"调整位置使其在目标位置 {target_position} 的 {tolerance:.3f}m 范围内"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "position_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"位置约束检查失败: {str(e)}"}]
            }
    
    def _check_orientation_constraint(self, state_config: Dict[str, Any], 
                                     constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查姿态约束"""
        try:
            # 获取目标姿态和容差
            target_orientation = self._ensure_float(constraint.get("target_orientation", [0, 0, 0, 1]))
            tolerance_angle = math.radians(float(constraint.get("tolerance_angle", 5.0)))  # 转换为弧度
            
            # 从状态中获取当前姿态
            current_orientation = self._extract_orientation_from_state(state_config)            # 计算四元数夹角
            dot_product = sum(current_orientation[i] * target_orientation[i] for i in range(4))
            dot_product = max(-1.0, min(1.0, dot_product))  # 确保在[-1, 1]范围内
            angle = 2 * math.acos(abs(dot_product))
            
            satisfied = angle <= tolerance_angle
            
            result = {
                "constraint_index": index,
                "constraint_type": "orientation_constraint",
                "satisfied": satisfied,
                "current_orientation": current_orientation,
                "target_orientation": target_orientation,
                "angle_difference": float(angle),
                "tolerance_angle": float(tolerance_angle),
                "violation_amount": max(0, float(angle - tolerance_angle))
            }
            
            if not satisfied:
                result["violations"] = [{
                    "type": "orientation_constraint",
                    "severity": constraint.get("severity", "medium"),
                    "description": f"姿态超出约束范围: 角度差 {math.degrees(angle):.1f}° > 容差 {math.degrees(tolerance_angle):.1f}°",
                    "suggestion": f"调整姿态使其接近目标姿态 {target_orientation}"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "orientation_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"姿态约束检查失败: {str(e)}"}]
            }
    
    def _check_joint_constraint(self, state_config: Dict[str, Any], 
                               constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查关节约束"""
        try:
            joint_state = state_config.get("joint_state")
            if not joint_state:
                return {
                    "constraint_index": index,
                    "constraint_type": "joint_constraint",
                    "satisfied": False,
                    "message": "状态中没有关节信息",
                    "violations": [{"type": "missing_data", "description": "缺少关节状态数据"}]
                }
            
            joint_state = self._ensure_float(joint_state)            # 获取约束参数
            target_joints = self._ensure_float(constraint.get("target_joints", []))
            tolerance = float(constraint.get("tolerance", 0.01))
            
            if len(target_joints) != len(joint_state):
                return {
                    "constraint_index": index,
                    "constraint_type": "joint_constraint",
                    "satisfied": False,
                    "message": f"关节维度不匹配: 状态有 {len(joint_state)} 个关节，约束有 {len(target_joints)} 个",
                    "violations": [{"type": "dimension_mismatch", "description": "关节维度不匹配"}]
                }
            
            # 检查每个关节
            max_violation = 0.0
            violated_joints = []
            
            for i, (current, target) in enumerate(zip(joint_state, target_joints)):
                diff = abs(current - target)
                if diff > tolerance:
                    max_violation = max(max_violation, diff)
                    violated_joints.append({
                        "joint_index": i,
                        "current_value": float(current),
                        "target_value": float(target),
                        "difference": float(diff)
                    })
            
            satisfied = len(violated_joints) == 0
            
            result = {
                "constraint_index": index,
                "constraint_type": "joint_constraint",
                "satisfied": satisfied,
                "joint_count": len(joint_state),
                "tolerance": float(tolerance),
                "max_violation": float(max_violation)
            }
            
            if not satisfied:
                result["violated_joints"] = violated_joints
                result["violations"] = [{
                    "type": "joint_constraint",
                    "severity": constraint.get("severity", "medium"),
                    "description": f"{len(violated_joints)} 个关节超出约束范围",
                    "suggestion": "调整关节角度以满足约束条件"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "joint_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"关节约束检查失败: {str(e)}"}]
            }
    
    def _check_distance_constraint(self, state_config: Dict[str, Any], 
                                  constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查距离约束"""
        try:            # 从缓存获取物体信息
            cache = self._load_cache()
            
            # 获取约束参数
            object1_id = constraint.get("object1", "robot")
            object2_id = constraint.get("object2")
            min_distance = float(constraint.get("min_distance", 0.0))
            max_distance = float(constraint.get("max_distance", float('inf')))
            
            if not object2_id:
                return {
                    "constraint_index": index,
                    "constraint_type": "distance_constraint",
                    "satisfied": False,
                    "message": "未指定第二个物体",
                    "violations": [{"type": "missing_data", "description": "缺少第二个物体ID"}]
                }
            
            # 获取物体位置
            if object1_id == "robot":
                pos1 = self._extract_position_from_state(state_config)
            elif object1_id in cache:
                obj1_data = cache[object1_id]
                pos1 = self._extract_position(obj1_data)
            else:
                return {
                    "constraint_index": index,
                    "constraint_type": "distance_constraint",
                    "satisfied": False,
                    "message": f"找不到物体: {object1_id}",
                    "violations": [{"type": "missing_object", "description": f"物体 {object1_id} 不存在"}]
                }
            
            if object2_id in cache:
                obj2_data = cache[object2_id]
                pos2 = self._extract_position(obj2_data)
            else:
                return {
                    "constraint_index": index,
                    "constraint_type": "distance_constraint",
                    "satisfied": False,
                    "message": f"找不到物体: {object2_id}",
                    "violations": [{"type": "missing_object", "description": f"物体 {object2_id} 不存在"}]
                }
            
           # 计算距离
            distance = math.sqrt(
                sum((pos1[i] - pos2[i])**2 for i in range(3))
            )
            
            # 检查距离是否在范围内
            satisfied = min_distance <= distance <= max_distance
            
            result = {
                "constraint_index": index,
                "constraint_type": "distance_constraint",
                "satisfied": satisfied,
                "object1": object1_id,
                "object2": object2_id,
                "distance": float(distance),
                "min_distance": float(min_distance),
                "max_distance": float(max_distance),
                "position1": pos1,
                "position2": pos2
            }
            
            if not satisfied:
                violation_type = "too_close" if distance < min_distance else "too_far"
                violation_desc = (
                    f"距离 {distance:.3f}m 小于最小距离 {min_distance:.3f}m" 
                    if distance < min_distance else
                    f"距离 {distance:.3f}m 大于最大距离 {max_distance:.3f}m"
                )
                
                result["violations"] = [{
                    "type": "distance_constraint",
                    "subtype": violation_type,
                    "severity": constraint.get("severity", "medium"),
                    "description": violation_desc,
                    "suggestion": f"调整 {object1_id} 和 {object2_id} 的相对位置"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "distance_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"距离约束检查失败: {str(e)}"}]
            }
    
    def _check_collision_constraint(self, state_config: Dict[str, Any], 
                                   constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查碰撞约束"""
        try:
            cache = self._load_cache()
            if not cache:
                return {
                    "constraint_index": index,
                    "constraint_type": "collision_constraint",
                    "satisfied": True,
                    "message": "场景为空，无需检查碰撞"
                }
            
            allowed_collisions = constraint.get("allowed_collisions", [])
            forbidden_collisions = constraint.get("forbidden_collisions", [])            # 简化处理：检查机器人是否与场景物体碰撞
            robot_position = self._extract_position_from_state(state_config)
            robot_size = [0.5, 0.5, 1.0]  # 简化的机器人包围盒
            
            collisions = []
            
            for obj_id, obj_data in cache.items():
                obj_position = self._extract_position(obj_data)
                obj_size = self._extract_size(obj_data)
                
                # 检查是否允许碰撞
                is_allowed = any(
                    (obj_id == allowed.get("object1") or obj_id == allowed.get("object2")) 
                    for allowed in allowed_collisions
                )
                
                if is_allowed:
                    continue
                
                # 检查碰撞
                collision = self._check_aabb_collision(
                    robot_position, robot_size,
                    obj_position, obj_size
                )
                
                if collision:
                    collisions.append(obj_id)
            
            satisfied = len(collisions) == 0
            
            result = {
                "constraint_index": index,
                "constraint_type": "collision_constraint",
                "satisfied": satisfied,
                "collisions_found": len(collisions),
                "allowed_collisions": len(allowed_collisions),
                "forbidden_collisions": len(forbidden_collisions)
            }
            
            if not satisfied:
                result["colliding_objects"] = collisions
                result["violations"] = [{
                    "type": "collision_constraint",
                    "severity": constraint.get("severity", "high"),
                    "description": f"与 {len(collisions)} 个物体发生碰撞: {', '.join(collisions[:3])}{'...' if len(collisions) > 3 else ''}",
                    "suggestion": "调整机器人位置避免碰撞，或将必要碰撞添加到允许碰撞列表"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "collision_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"碰撞约束检查失败: {str(e)}"}]
            }
    
    def _check_workspace_constraint(self, state_config: Dict[str, Any], 
                                   constraint: Dict[str, Any], index: int) -> Dict[str, Any]:
        """检查工作空间约束"""
        try:
            position = self._extract_position_from_state(state_config)
            
            # 获取工作空间边界
            workspace = constraint.get("workspace", {})
            min_bound = self._ensure_float(workspace.get("min", [-1, -1, 0]))
            max_bound = self._ensure_float(workspace.get("max", [1, 1, 2]))            # 检查是否在边界内
            in_workspace = True
            violations = []
            
            for i in range(3):
                if position[i] < min_bound[i]:
                    in_workspace = False
                    violations.append({
                        "axis": i,
                        "value": float(position[i]),
                        "min_bound": float(min_bound[i]),
                        "violation_amount": float(min_bound[i] - position[i])
                    })
                elif position[i] > max_bound[i]:
                    in_workspace = False
                    violations.append({
                        "axis": i,
                        "value": float(position[i]),
                        "max_bound": float(max_bound[i]),
                        "violation_amount": float(position[i] - max_bound[i])
                    })
            
            satisfied = in_workspace
            
            result = {
                "constraint_index": index,
                "constraint_type": "workspace_constraint",
                "satisfied": satisfied,
                "position": position,
                "workspace_min": min_bound,
                "workspace_max": max_bound
            }
            
            if not satisfied:
                result["violations_axes"] = violations
                result["violations"] = [{
                    "type": "workspace_constraint",
                    "severity": constraint.get("severity", "medium"),
                    "description": f"位置 {position} 超出工作空间边界",
                    "suggestion": f"将位置调整到边界内: [{min_bound}, {max_bound}]"
                }]
            
            return result
            
        except Exception as e:
            return {
                "constraint_index": index,
                "constraint_type": "workspace_constraint",
                "satisfied": False,
                "error": str(e),
                "violations": [{"type": "check_error", "description": f"工作空间约束检查失败: {str(e)}"}]
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
    
    def _extract_position_from_state(self, state_config: Dict[str, Any]) -> List[float]:
        """从状态配置中提取位置"""
        if "position" in state_config:
            return self._ensure_float(state_config["position"])
        elif "pose" in state_config and "position" in state_config["pose"]:
            return self._ensure_float(state_config["pose"]["position"])
        else:
            # 简化的默认位置
            return [0.0, 0.0, 0.5]
    
    def _extract_orientation_from_state(self, state_config: Dict[str, Any]) -> List[float]:
        """从状态配置中提取姿态"""
        if "orientation" in state_config:
            return self._ensure_float(state_config["orientation"])
        elif "pose" in state_config and "orientation" in state_config["pose"]:
            return self._ensure_float(state_config["pose"]["orientation"])
        else:            # 默认姿态（无旋转）
            return [0.0, 0.0, 0.0, 1.0]
    
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
    
    def load_constraints_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        """从文件加载约束条件"""
        try:
            with open(filepath, 'r') as f:
                if filepath.endswith('.json'):
                    data = json.load(f)
                    return data.get("constraints", [])
                else:
                    # 可以扩展支持其他格式
                    return []
        except Exception as e:
            print(f"[错误] 加载约束文件失败: {e}")
            return []
    
    def save_constraints_to_file(self, constraints: List[Dict[str, Any]], 
                               filepath: str) -> bool:
        """保存约束条件到文件"""
        try:
            data = {
                "constraints": constraints,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "constraint_count": len(constraints)
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"[错误] 保存约束文件失败: {e}")
            return False