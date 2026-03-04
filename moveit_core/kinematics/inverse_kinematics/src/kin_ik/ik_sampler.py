#!/usr/bin/env python3
"""
IK采样器 - 用于生成多种IK解
"""
import numpy as np
import random
from typing import List, Dict
from .ik_solver import IKSolver

class IKSampler:
    """IK解采样器"""
    
    def __init__(self, ik_solver: IKSolver):
        self.ik_solver = ik_solver
    
    def sample_workspace(self, num_samples: int = 100) -> List[Dict]:
        """在工作空间内采样"""
        solutions = []
        
        for _ in range(num_samples):
            # 随机生成目标位姿
            x = random.uniform(0.2, 0.8)
            y = random.uniform(-0.4, 0.4)
            z = random.uniform(0.1, 0.5)
            
            # 随机生成姿态
            from scipy.spatial.transform import Rotation
            rot = Rotation.random()
            quat = rot.as_quat()  # [x, y, z, w]
            
            target_pose = [x, y, z, quat[0], quat[1], quat[2], quat[3]]
            
            # 求解IK
            result = self.ik_solver.solve(target_pose)
            if result["success"]:
                solutions.append({
                    "pose": target_pose,
                    "joints": result["solution"],
                    "quality": result["quality"]
                })
        
        return solutions
    
    def sample_near_solution(self, base_solution: List, 
                           variance: float = 0.1) -> List[Dict]:
        """在已有解附近采样"""
        solutions = []
        
        for _ in range(10):  # 采样10个附近解
            # 添加随机扰动
            perturbed = base_solution.copy()
            for i in range(len(perturbed)):
                perturbed[i] += random.uniform(-variance, variance)
            
            # 计算正运动学得到位姿
            T = self.ik_solver._forward_kinematics(np.array(perturbed))
            
            # 提取位姿
            from scipy.spatial.transform import Rotation as R
            position = T[:3, 3]
            rotation = R.from_matrix(T[:3, :3])
            quat = rotation.as_quat()
            
            target_pose = [position[0], position[1], position[2],
                          quat[0], quat[1], quat[2], quat[3]]
            
            # 用IK验证
            result = self.ik_solver.solve(target_pose)
            if result["success"]:
                solutions.append({
                    "original": base_solution,
                    "perturbed": perturbed,
                    "ik_solution": result["solution"],
                    "consistency": np.allclose(perturbed, result["solution"], atol=0.01)
                })
        
        return solutions