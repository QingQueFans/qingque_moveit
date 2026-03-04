#!/usr/bin/env python3
"""
IK约束处理器 - 处理各种运动学约束
"""
import numpy as np
from typing import List, Dict, Any, Callable
from scipy.spatial.transform import Rotation
import math

class IKConstraintHandler:
    """
    IK约束处理器
    
    处理各种运动学约束：
    1. 姿态约束（末端必须水平、垂直等）
    2. 位置约束（末端必须在平面、直线上）
    3. 关节约束（关节角度限制、速度限制）
    4. 避障约束
    """
    
    def __init__(self):
        self.constraints = []
        self.priority_weights = {}
    
    def add_orientation_constraint(self, constraint_type: str, 
                                  target_orientation: List = None,
                                  tolerance: float = 0.1):
        """添加姿态约束"""
        if constraint_type == "horizontal":
            # 末端执行器必须水平（z轴垂直）
            def horizontal_constraint(pose_matrix):
                z_axis = pose_matrix[:3, 2]
                vertical_error = 1.0 - abs(z_axis[2])  # z分量应该接近1或-1
                return vertical_error
            
            self.constraints.append({
                "type": "orientation",
                "subtype": "horizontal",
                "func": horizontal_constraint,
                "tolerance": tolerance,
                "weight": 1.0
            })
            
        elif constraint_type == "vertical":
            # 末端执行器必须垂直（z轴水平）
            def vertical_constraint(pose_matrix):
                z_axis = pose_matrix[:3, 2]
                horizontal_error = abs(z_axis[2])  # z分量应该接近0
                return horizontal_error
            
            self.constraints.append({
                "type": "orientation",
                "subtype": "vertical",
                "func": vertical_constraint,
                "tolerance": tolerance,
                "weight": 1.0
            })
            
        elif constraint_type == "fixed":
            # 固定姿态
            def fixed_constraint(pose_matrix):
                R_target = Rotation.from_quat(target_orientation).as_matrix()
                R_current = pose_matrix[:3, :3]
                R_error = R_target.T @ R_current
                angle_error = Rotation.from_matrix(R_error).magnitude()
                return angle_error
            
            self.constraints.append({
                "type": "orientation",
                "subtype": "fixed",
                "func": fixed_constraint,
                "target": target_orientation,
                "tolerance": tolerance,
                "weight": 1.0
            })
    
    def add_position_constraint(self, constraint_type: str,
                               plane_normal: List = None,
                               line_direction: List = None,
                               tolerance: float = 0.01):
        """添加位置约束"""
        if constraint_type == "plane":            # 末端必须在平面上
            normal = np.array(plane_normal) / np.linalg.norm(plane_normal)
            
            def plane_constraint(pose_matrix):
                position = pose_matrix[:3, 3]
                # 计算到平面的距离
                distance = np.dot(position, normal)
                return abs(distance)
            
            self.constraints.append({
                "type": "position",
                "subtype": "plane",
                "func": plane_constraint,
                "normal": normal.tolist(),
                "tolerance": tolerance,
                "weight": 1.0
            })
            
        elif constraint_type == "line":
            # 末端必须在直线上
            direction = np.array(line_direction) / np.linalg.norm(line_direction)
            
            def line_constraint(pose_matrix):
                position = pose_matrix[:3, 3]
                # 计算到直线的距离
                # 假设直线通过原点
                projection = np.dot(position, direction) * direction
                distance = np.linalg.norm(position - projection)
                return distance
            
            self.constraints.append({
                "type": "position",
                "subtype": "line",
                "func": line_constraint,
                "direction": direction.tolist(),
                "tolerance": tolerance,
                "weight": 1.0
            })
    
    def add_joint_constraint(self, joint_index: int,
                            min_angle: float = None,
                            max_angle: float = None,
                            preferred_angle: float = None,
                            weight: float = 0.1):
        """添加关节约束"""
        def joint_constraint(joint_angles):
            angle = joint_angles[joint_index]
            error = 0.0
            
            # 硬限制
            if min_angle is not None and angle < min_angle:
                error += (min_angle - angle) ** 2
            if max_angle is not None and angle > max_angle:
                error += (angle - max_angle) ** 2
            
            # 偏好角度（软约束）
            if preferred_angle is not None:
                error += weight * (angle - preferred_angle) ** 2
            
            return error
        
        self.constraints.append({
            "type": "joint",
            "subtype": "limit",
            "joint_index": joint_index,
            "func": joint_constraint,
            "min": min_angle,
            "max": max_angle,
            "preferred": preferred_angle,
            "weight": weight
        })
    
    def add_avoidance_constraint(self, obstacle_position: List,
                                obstacle_radius: float = 0.1,
                                safety_margin: float = 0.05):
        """添加避障约束"""
        obs_pos = np.array(obstacle_position)
        
        def avoidance_constraint(pose_matrix, joint_angles=None, 
                                robot_model=None):
            if joint_angles is None or robot_model is None:
                return 0.0            # 简化的避障约束：只检查末端与障碍物的距离
            end_position = pose_matrix[:3, 3]
            distance = np.linalg.norm(end_position - obs_pos)
            
            # 惩罚距离小于安全半径的情况
            if distance < obstacle_radius + safety_margin:
                penalty = (obstacle_radius + safety_margin - distance) ** 2
                return penalty * 10.0  # 较大的权重
            
            return 0.0
        
        self.constraints.append({
            "type": "avoidance",
            "subtype": "obstacle",
            "func": avoidance_constraint,
            "obstacle_position": obstacle_position,
            "obstacle_radius": obstacle_radius,
            "safety_margin": safety_margin,
            "weight": 10.0
        })
    
    def evaluate_constraints(self, pose_matrix: np.ndarray,
                           joint_angles: List = None,
                           robot_model: Dict = None) -> Dict:
        """评估所有约束"""
        total_error = 0.0
        constraint_results = []
        
        for i, constraint in enumerate(self.constraints):
            # 根据约束类型传递参数
            if constraint["type"] == "avoidance":
                error = constraint["func"](pose_matrix, joint_angles, robot_model)
            elif constraint["type"] == "joint":
                error = constraint["func"](joint_angles)
            else:
                error = constraint["func"](pose_matrix)
            
            # 应用权重
            weighted_error = error * constraint.get("weight", 1.0)
            total_error += weighted_error
            
            # 记录结果
            constraint_results.append({
                "index": i,
                "type": constraint["type"],
                "subtype": constraint.get("subtype", ""),
                "error": float(error),
                "weighted_error": float(weighted_error),
                "satisfied": error <= constraint.get("tolerance", 0.0),
                "tolerance": constraint.get("tolerance", 0.0)
            })
        
        # 计算满足度
        satisfied = all(r["satisfied"] for r in constraint_results 
                       if r["type"] in ["orientation", "position"])  # 硬约束
        
        return {
            "total_error": float(total_error),
            "satisfied": satisfied,
            "constraints": constraint_results,
            "hard_constraints_satisfied": satisfied,
            "soft_constraints_error": total_error
        }
    
    def get_constraint_jacobian(self, pose_matrix: np.ndarray,
                              joint_angles: List,
                              robot_model: Dict) -> np.ndarray:
        """计算约束的雅可比矩阵（数值法）"""
        n_joints = len(joint_angles)
        n_constraints = len([c for c in self.constraints 
                           if c["type"] in ["orientation", "position"]])
        
        if n_constraints == 0:
            return np.zeros((0, n_joints))
        
        J_constraint = np.zeros((n_constraints, n_joints))
        epsilon = 1e-6
        
        # 数值法计算雅可比
        constraint_idx = 0
        for i, constraint in enumerate(self.constraints):
            if constraint["type"] not in ["orientation", "position"]:
                continue
            
            # 当前约束值
            current_error = constraint["func"](pose_matrix)
            
            # 对每个关节计算梯度
            for j in range(n_joints):
                # 扰动关节角度
                joint_angles_perturbed = joint_angles.copy()
                joint_angles_perturbed[j] += epsilon                # 计算扰动后的正运动学
                # 这里需要正运动学计算，暂时简化
                # 实际应该调用FK求解器
                pose_perturbed = self._compute_forward_kinematics(
                    joint_angles_perturbed, robot_model)
                
                # 计算扰动后的约束值
                perturbed_error = constraint["func"](pose_perturbed)
                
                # 计算梯度
                gradient = (perturbed_error - current_error) / epsilon
                J_constraint[constraint_idx, j] = gradient
            
            constraint_idx += 1
        
        return J_constraint
    
    def _compute_forward_kinematics(self, joint_angles: List,
                                  robot_model: Dict) -> np.ndarray:
        """简化版正运动学计算（用于约束雅可比）"""
        # 这里应该调用FK模块，暂时用简化实现
        T = np.eye(4)
        dh_params = robot_model["dh_parameters"]
        
        for i, (angle, dh) in enumerate(zip(joint_angles, dh_params)):
            a, alpha, d, theta0 = dh["a"], dh["alpha"], dh["d"], dh["theta"]
            ct = math.cos(angle + theta0)
            st = math.sin(angle + theta0)
            ca = math.cos(alpha)
            sa = math.sin(alpha)
            
            Ti = np.array([
                [ct, -st*ca, st*sa, a*ct],
                [st, ct*ca, -ct*sa, a*st],
                [0, sa, ca, d],
                [0, 0, 0, 1]
            ])
            
            T = T @ Ti
        
        return T
    
    def clear_constraints(self):
        """清除所有约束"""
        self.constraints = []
        print("[约束处理器] 已清除所有约束")
    
    def get_constraint_info(self) -> Dict:
        """获取约束信息"""
        info = {
            "total_constraints": len(self.constraints),
            "by_type": {},
            "details": []
        }
        
        for i, constraint in enumerate(self.constraints):
            constraint_type = constraint["type"]
            if constraint_type not in info["by_type"]:
                info["by_type"][constraint_type] = 0
            info["by_type"][constraint_type] += 1
            
            info["details"].append({
                "index": i,
                "type": constraint_type,
                "subtype": constraint.get("subtype", ""),
                "weight": constraint.get("weight", 1.0),
                "tolerance": constraint.get("tolerance", 0.0)
            })
        
        return info