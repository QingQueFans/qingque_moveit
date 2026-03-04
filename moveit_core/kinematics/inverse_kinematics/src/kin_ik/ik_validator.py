#!/usr/bin/env python3
"""
IK验证器 - 验证IK解的正确性和质量
"""
import numpy as np
from typing import List, Dict
from .ik_solver import IKSolver

class IKValidator:
    """IK解验证器"""
    
    def __init__(self, ik_solver: IKSolver):
        self.ik_solver = ik_solver
    
    def validate_solution(self, target_pose: List, 
                         solution: List) -> Dict:
        """全面验证IK解"""
        validation = {}
        
        # 1. 基本验证
        basic = self.ik_solver.validate_solution(target_pose, solution)
        validation.update(basic)
        
        # 2. 关节限制检查
        joint_valid, joint_info = self._check_joint_limits(solution)
        validation["joint_valid"] = joint_valid
        validation["joint_info"] = joint_info
        
        # 3. 奇异性检查
        singular, singular_info = self._check_singularity(solution)
        validation["singular"] = singular
        validation["singular_info"] = singular_info
        
        # 4. 可操作性检查
        manipulability = self._calculate_manipulability(solution)
        validation["manipulability"] = manipulability
        
        # 5. 综合评分
        validation["overall_score"] = self._calculate_overall_score(validation)
        
        return validation
    
    def _check_joint_limits(self, solution: List) -> tuple:
        """检查关节限制"""
        violations = []
        
        for i, (angle, limits) in enumerate(zip(solution, 
                self.ik_solver.config["joint_limits"])):
            if angle < limits[0] or angle > limits[1]:
                violations.append({
                    "joint": i,
                    "angle": angle,
                    "min": limits[0],
                    "max": limits[1],
                    "violation": min(abs(angle-limits[0]), abs(angle-limits[1]))
                })
        
        return len(violations) == 0, violations
    
    def _check_singularity(self, solution: List) -> tuple:
        """检查奇异性"""
        try:
            # 计算雅可比矩阵
            J = self.ik_solver._compute_jacobian(np.array(solution))
            
            # 计算行列式
            det = np.linalg.det(J[:3, :3])  # 位置雅可比的行列式
            
            singular = abs(det) < 1e-6
            info = {
                "determinant": float(det),
                "condition_number": float(np.linalg.cond(J)),
                "is_singular": singular
            }
            
            return singular, info
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def _calculate_manipulability(self, solution: List) -> float:
        """计算可操作性指标"""
        try:
            J = self.ik_solver._compute_jacobian(np.array(solution))
            # 可操作性 = sqrt(det(J * J^T))
            JJT = J @ J.T
            manipulability = np.sqrt(np.linalg.det(JJT))
            return float(manipulability)
        except:
            return 0.0
    
    def _calculate_overall_score(self, validation: Dict) -> float:
        """计算综合评分"""
        score = 0.0
        
        # 1. 基本有效性 (40%)
        if validation["valid"]:
            score += 0.4
        
        # 2. 关节限制 (20%)
        if validation["joint_valid"]:
            score += 0.2
        
        # 3. 非奇异 (20%)
        if not validation["singular"]:
            score += 0.2
        
        # 4. 可操作性 (20%)
        manipulability = validation["manipulability"]
        if manipulability > 0.1:  # 阈值
            score += 0.2 * min(1.0, manipulability / 0.5)
        
        return score