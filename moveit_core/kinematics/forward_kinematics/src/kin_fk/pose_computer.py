#!/usr/bin/env python3
"""
pose_computer.py - 位姿计算器
为FK求解器提供便捷的位姿计算接口
"""
import numpy as np
from typing import List, Optional, Union, Dict
from .fk_solver import FKSolver
import math
class PoseComputer:
    """位姿计算器 - FK求解器的高层接口"""
    
    def __init__(self, fk_solver: Optional[FKSolver] = None):
        self.fk_solver = fk_solver or FKSolver()
        self.cache = {}  # 缓存计算结果
        
    def compute_end_effector(self, joint_angles: List[float]) -> Dict:
        """计算末端执行器位姿（最常用）"""
        T = self.fk_solver.compute(joint_angles)
        return {
            "position": T[:3, 3].tolist(),
            "orientation": self._matrix_to_quat(T[:3, :3]),
            "matrix": T.tolist(),
            "joint_angles": joint_angles
        }
    
    def compute_link_pose(self, joint_angles: List[float], link_name: str) -> Dict:
        """计算指定连杆的位姿"""
        # 可以计算中间连杆的位姿，不只是末端
        pass
    
    def compute_multiple(self, joint_angles_list: List[List[float]]) -> List[Dict]:
        """批量计算多个关节配置的位姿"""
        results = []
        for joints in joint_angles_list:
            key = str(joints)
            if key in self.cache:
                results.append(self.cache[key])
            else:
                pose = self.compute_end_effector(joints)
                self.cache[key] = pose
                results.append(pose)
        return results
    
    def compare_poses(self, pose1: Dict, pose2: Dict) -> Dict:
        """比较两个位姿的差异"""
        pos1 = np.array(pose1["position"])
        pos2 = np.array(pose2["position"])
        return {
            "position_error": np.linalg.norm(pos1 - pos2),
            "orientation_error": self._orientation_error(pose1, pose2)
        }
    def _matrix_to_quat(self, R: np.ndarray) -> List[float]:
        """旋转矩阵转四元数"""
        qw = math.sqrt(max(0, 1 + R[0,0] + R[1,1] + R[2,2])) / 2
        qx = math.sqrt(max(0, 1 + R[0,0] - R[1,1] - R[2,2])) / 2
        qy = math.sqrt(max(0, 1 - R[0,0] + R[1,1] - R[2,2])) / 2
        qz = math.sqrt(max(0, 1 - R[0,0] - R[1,1] + R[2,2])) / 2
        
        # 确定符号
        qx = qx * (1 if R[2,1] - R[1,2] >= 0 else -1)
        qy = qy * (1 if R[0,2] - R[2,0] >= 0 else -1)
        qz = qz * (1 if R[1,0] - R[0,1] >= 0 else -1)
        
        return [qx, qy, qz, qw]    