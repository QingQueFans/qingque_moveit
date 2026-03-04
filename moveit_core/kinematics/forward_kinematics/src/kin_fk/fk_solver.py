#!/usr/bin/env python3
"""
fk_solver.py - 正运动学求解器
根据关节角度计算机械臂末端位姿
"""
import numpy as np
import math
from typing import List, Dict, Optional, Union

class FKSolver:
    """正运动学求解器"""
    
    def __init__(self, robot_model: Optional[Dict] = None):
        """
        初始化FK求解器
        
        Args:
            robot_model: 机器人模型配置（包含DH参数）
        """
        self.robot_model = robot_model or self._default_robot_model()
        print(f"[FKSolver] 初始化完成，使用机器人模型: {self.robot_model['name']}")
    
    def _default_robot_model(self) -> Dict:
        """默认Panda机器人模型（从URDF提取）"""
        return {
            "name": "panda",
            "dh_parameters": [
                {"a": 0.0, "alpha": 0.0, "d": 0.333, "theta": 0.0},
                {"a": 0.0, "alpha": -1.5708, "d": 0.0, "theta": 0.0},
                {"a": 0.0, "alpha": 1.5708, "d": -0.316, "theta": 0.0},
                {"a": 0.0825, "alpha": 1.5708, "d": 0.0, "theta": 0.0},
                {"a": -0.0825, "alpha": -1.5708, "d": 0.384, "theta": 0.0},
                {"a": 0.0, "alpha": 1.5708, "d": 0.0, "theta": 0.0},
                {"a": 0.088, "alpha": 1.5708, "d": 0.0, "theta": 0.0},
            ],
            "tool_transform": np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0.107],
                [0, 0, 0, 1]
            ])
        }
    
    def compute(self, joint_angles: List[float]) -> np.ndarray:
        """
        计算正运动学
        
        Args:
            joint_angles: 关节角度列表 [j1, j2, j3, j4, j5, j6, j7]
        
        Returns:
            4x4变换矩阵，表示末端执行器位姿
        """
        T = np.eye(4)
        dh_params = self.robot_model["dh_parameters"]
        
        for i, (theta, dh) in enumerate(zip(joint_angles, dh_params)):
            a, alpha, d, theta0 = dh["a"], dh["alpha"], dh["d"], dh["theta"]
            
            # 当前关节的变换矩阵
            Ti = self._dh_transform(theta + theta0, d, a, alpha)
            T = T @ Ti
            
            print(f"[FK] 关节{i+1}: {theta:.4f} rad, 当前位姿: {T[:3, 3]}")
        
        # 应用末端工具变换
        T = T @ self.robot_model["tool_transform"]
        
        return T
    
    def _dh_transform(self, theta: float, d: float, a: float, alpha: float) -> np.ndarray:
        """DH参数变换矩阵"""
        ct = math.cos(theta)
        st = math.sin(theta)
        ca = math.cos(alpha)
        sa = math.sin(alpha)
        
        return np.array([
            [ct, -st*ca, st*sa, a*ct],
            [st, ct*ca, -ct*sa, a*st],
            [0, sa, ca, d],
            [0, 0, 0, 1]
        ])
    
    def compute_pose_list(self, joint_angles: List[float]) -> List[float]:
        """返回位姿列表 [x,y,z,qx,qy,qz,qw]"""
        T = self.compute(joint_angles)
        return self._matrix_to_pose(T)
    
    def _matrix_to_pose(self, T: np.ndarray) -> List[float]:
        """变换矩阵转位姿列表"""
        # 提取位置
        x, y, z = T[:3, 3]
        
        # 提取旋转矩阵并转四元数
        R = T[:3, :3]
        qw = math.sqrt(1 + R[0,0] + R[1,1] + R[2,2]) / 2
        qx = (R[2,1] - R[1,2]) / (4 * qw)
        qy = (R[0,2] - R[2,0]) / (4 * qw)
        qz = (R[1,0] - R[0,1]) / (4 * qw)
        
        return [x, y, z, qx, qy, qz, qw]