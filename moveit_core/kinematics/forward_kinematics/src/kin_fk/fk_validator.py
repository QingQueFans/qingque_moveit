#!/usr/bin/env python3
"""
fk_validator.py - 正运动学验证器
"""
import numpy as np
from typing import List, Dict, Optional
from .fk_solver import FKSolver

class FKValidator:
    """正运动学验证器"""
    
    def __init__(self, fk_solver: FKSolver):
        self.fk_solver = fk_solver
        self.validation_history = []
    
    def validate_solution(self, joint_angles: List[float], 
                          expected_pose: List[float],
                          tolerance: float = 0.01) -> Dict:
        """验证解的正确性"""
        actual_pose = self.fk_solver.compute_pose_list(joint_angles)
        
        # 计算位置误差
        pos_error = np.linalg.norm(
            np.array(actual_pose[:3]) - np.array(expected_pose[:3])
        )
        
        # 计算方向误差（简化的角度差）
        # 这里可以添加更精确的方向误差计算
        
        result = {
            "valid": pos_error < tolerance,
            "position_error": float(pos_error),
            "tolerance": tolerance,
            "joint_angles": joint_angles,
            "actual_pose": actual_pose,
            "expected_pose": expected_pose
        }
        
        self.validation_history.append(result)
        return result