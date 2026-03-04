#!/usr/bin/env python3
"""
IK优化器 - 优化IK解的质量
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import random
import math
from .ik_solver import IKSolver

class IKOptimizer:
    """
    IK解优化器
    
    优化目标：
    1. 最小化关节运动（从初始姿态出发）
    2. 最大化可操作性
    3. 避免奇异位形
    4. 最小化能量/力矩
    5. 满足关节限制偏好
    """
    
    def __init__(self, ik_solver: IKSolver):
        self.ik_solver = ik_solver
        self.objective_weights = {
            "joint_movement": 0.3,      # 关节运动最小化
            "manipulability": 0.3,      # 可操作性最大化
            "singularity": 0.2,         # 奇异性避免
            "joint_preference": 0.1,    # 关节偏好
            "energy": 0.1               # 能量最小化
        }
        
        self.optimization_methods = [
            "gradient_descent",
            "random_search",
            "simulated_annealing"
        ]
        
        self.best_solution = None
        self.optimization_history = []
    
    def set_objective_weights(self, weights: Dict):
        """设置优化目标权重"""
        self.objective_weights.update(weights)
        # 确保权重和为1
        total = sum(self.objective_weights.values())
        if total > 0:
            for key in self.objective_weights:
                self.objective_weights[key] /= total
    
    def optimize_solution(self, initial_solution: List,
                         ik_solver: Any,
                         target_pose: List,
                         method: str = "gradient_descent",
                         max_iterations: int = 50) -> Dict:
        """
        优化IK解
        
        Args:
            initial_solution: 初始IK解
            ik_solver: IK求解器实例
            target_pose: 目标位姿
            method: 优化方法
            max_iterations: 最大迭代次数
        """
        if method not in self.optimization_methods:
            method = "gradient_descent"
        
        self.best_solution = initial_solution.copy()
        best_score = self._evaluate_solution(initial_solution, ik_solver)
        self.optimization_history = []
        
        if method == "gradient_descent":
            optimized = self._gradient_descent(
                initial_solution, ik_solver, target_pose, max_iterations)
        elif method == "random_search":
            optimized = self._random_search(
                initial_solution, ik_solver, target_pose, max_iterations)
        elif method == "simulated_annealing":
            optimized = self._simulated_annealing(
                initial_solution, ik_solver, target_pose, max_iterations)
        
        # 评估最终解
        final_score = self._evaluate_solution(optimized, ik_solver)
        
        return {
            "success": True,
            "initial_solution": initial_solution,
            "optimized_solution": optimized,
            "initial_score": best_score,
            "final_score": final_score,
            "improvement": final_score - best_score,
            "method": method,
            "iterations": len(self.optimization_history),
            "history": self.optimization_history
        }
    
    def _evaluate_solution(self, solution: List, ik_solver: Any) -> float:
        """评估解的分数（越高越好）"""
        score = 0.0
        
        # 1. 关节运动最小化（负向评分）
        if hasattr(ik_solver, 'current_joints') and ik_solver.current_joints:
            movement = np.linalg.norm(
                np.array(solution) - np.array(ik_solver.current_joints))
            score -= self.objective_weights["joint_movement"] * movement        # 2. 可操作性最大化
        manipulability = self._calculate_manipulability(solution, ik_solver)
        score += self.objective_weights["manipulability"] * manipulability
        
        # 3. 奇异性避免
        singularity_score = self._calculate_singularity_score(solution, ik_solver)
        score += self.objective_weights["singularity"] * singularity_score
        
        # 4. 关节偏好
        preference_score = self._calculate_joint_preference_score(solution, ik_solver)
        score += self.objective_weights["joint_preference"] * preference_score
        
        # 5. 能量最小化（简化：关节角度平方和）
        energy = sum(a*a for a in solution)
        score -= self.objective_weights["energy"] * energy * 0.1
        
        return score
    
    def _calculate_manipulability(self, solution: List, ik_solver: Any) -> float:
        """计算可操作性"""
        try:
            J = self.ik_solver._compute_jacobian(np.array(solution))
            JJT = J @ J.T
            det = np.linalg.det(JJT)
            
            if det <= 0:
                return 0.0
            
            # 可操作性 = sqrt(det(J*J^T))
            manipulability = math.sqrt(det)            # 归一化到[0, 1]，假设最大可操作性为1.0
            return min(1.0, manipulability / 1.0)
            
        except:
            return 0.0
    
    def _calculate_singularity_score(self, solution: List, ik_solver: Any) -> float:
        """计算奇异性得分（越高越好，1表示完全不奇异）"""
        try:
            J = self.ik_solver._compute_jacobian(np.array(solution))
            
            # 计算条件数（衡量矩阵病态程度）
            cond = np.linalg.cond(J)
            
            # 转换为得分：条件数越小越好
            # 假设条件数>100为奇异，<10为良好
            if cond > 100:
                return 0.0
            elif cond < 10:
                return 1.0
            else:
                return 1.0 - (cond - 10) / 90.0
                
        except:
            return 0.0
    
    def _calculate_joint_preference_score(self, solution: List, ik_solver: Any) -> float:
        """计算关节偏好得分"""
        score = 1.0
        
        # 检查关节是否接近限制
        joint_limits = ik_solver.config["joint_limits"]
        
        for i, (angle, limits) in enumerate(zip(solution, joint_limits)):
            range_size = limits[1] - limits[0]
            
            # 距离限制中心越近越好
            center = (limits[0] + limits[1]) / 2
            distance_to_center = abs(angle - center)
            
            # 标准化距离
            normalized_distance = distance_to_center / (range_size / 2)
            
            # 惩罚接近限制的解
            penalty = max(0, normalized_distance - 0.5) * 2  # [0, 1]
            score *= (1.0 - penalty * 0.5)  # 最多惩罚50%
        
        return max(0.0, score)
    
    def _gradient_descent(self, initial_solution: List,
                         ik_solver: Any,
                         target_pose: List,
                         max_iterations: int) -> List:
        """梯度下降优化"""
        current_solution = np.array(initial_solution.copy())
        learning_rate = 0.1
        momentum = 0.9
        velocity = np.zeros_like(current_solution)
        
        for iteration in range(max_iterations):
            # 计算梯度（数值法）
            gradient = self._compute_gradient(current_solution, ik_solver)
            
            # 动量更新
            velocity = momentum * velocity - learning_rate * gradient
            current_solution += velocity
            
            # 应用关节限制
            current_solution = self._apply_joint_limits(
                current_solution, ik_solver.config["joint_limits"])            # 记录历史
            score = self._evaluate_solution(current_solution.tolist(), ik_solver)
            self.optimization_history.append({
                "iteration": iteration,
                "solution": current_solution.tolist(),
                "score": score
            })
            
            # 更新最佳解
            if self.best_solution is None or score > self._evaluate_solution(
                self.best_solution, ik_solver):
                self.best_solution = current_solution.tolist()
            
            # 收敛检查
            if iteration > 10:
                recent_improvement = abs(
                    self.optimization_history[-1]["score"] - 
                    self.optimization_history[-5]["score"])
                if recent_improvement < 1e-6:
                    break
        
        return self.best_solution
    
    def _compute_gradient(self, solution: np.ndarray, ik_solver: Any) -> np.ndarray:
        """数值法计算梯度"""
        epsilon = 1e-6
        gradient = np.zeros_like(solution)
        base_score = self._evaluate_solution(solution.tolist(), ik_solver)
        
        for i in range(len(solution)):
            # 正向扰动
            solution_plus = solution.copy()
            solution_plus[i] += epsilon
            score_plus = self._evaluate_solution(solution_plus.tolist(), ik_solver)
            
            # 负向扰动
            solution_minus = solution.copy()
            solution_minus[i] -= epsilon
            score_minus = self._evaluate_solution(solution_minus.tolist(), ik_solver)
            
            # 中心差分
            gradient[i] = (score_plus - score_minus) / (2 * epsilon)
        
        return gradient
    
    def _random_search(self, initial_solution: List,
                      ik_solver: Any,
                      target_pose: List,
                      max_iterations: int) -> List:
        """随机搜索优化"""
        current_best = initial_solution.copy()
        best_score = self._evaluate_solution(current_best, ik_solver)
        
        for iteration in range(max_iterations):
            # 生成随机扰动
            candidate = current_best.copy()
            for i in range(len(candidate)):
                # 逐渐减小的搜索范围
                search_range = 0.1 * (1 - iteration / max_iterations)
                candidate[i] += random.uniform(-search_range, search_range)
            
            # 应用关节限制
            candidate = self._apply_joint_limits(
                candidate, ik_solver.config["joint_limits"])
            
            # 评估候选解
            candidate_score = self._evaluate_solution(candidate, ik_solver)
            
            # 记录历史
            self.optimization_history.append({
                "iteration": iteration,
                "solution": candidate,
                "score": candidate_score
            })
            
            # 更新最佳解
            if candidate_score > best_score:
                current_best = candidate
                best_score = candidate_score
        
        return current_best
    
    def _simulated_annealing(self, initial_solution: List,
                            ik_solver: Any,
                            target_pose: List,
                            max_iterations: int) -> List:
        """模拟退火优化"""
        current_solution = initial_solution.copy()
        current_score = self._evaluate_solution(current_solution, ik_solver)
        best_solution = current_solution.copy()
        best_score = current_score        # 退火参数
        temperature = 1.0
        cooling_rate = 0.95
        
        for iteration in range(max_iterations):
            # 生成新解
            new_solution = current_solution.copy()
            for i in range(len(new_solution)):
                # 温度相关的扰动范围
                perturbation = random.uniform(-0.1, 0.1) * temperature
                new_solution[i] += perturbation
            
            # 应用关节限制
            new_solution = self._apply_joint_limits(
                new_solution, ik_solver.config["joint_limits"])
            
            # 评估新解
            new_score = self._evaluate_solution(new_solution, ik_solver)
            
            # Metropolis准则
            delta_score = new_score - current_score
            if delta_score > 0 or random.random() < math.exp(delta_score / temperature):
                current_solution = new_solution
                current_score = new_score
            
            # 更新最佳解
            if current_score > best_score:
                best_solution = current_solution.copy()
                best_score = current_score
            
            # 记录历史
            self.optimization_history.append({
                "iteration": iteration,
                "temperature": temperature,
                "current_score": current_score,
                "best_score": best_score,
                "solution": current_solution
            })
            
            # 降温
            temperature *= cooling_rate
        
        return best_solution
    
    def _apply_joint_limits(self, solution: List, joint_limits: List) -> List:
        """应用关节限制"""
        limited = []
        for angle, limits in zip(solution, joint_limits):
            limited.append(max(limits[0], min(limits[1], angle)))
        return limited
    
    def get_optimization_summary(self) -> Dict:
        """获取优化过程总结"""
        if not self.optimization_history:
            return {"message": "没有优化历史"}
        
        scores = [h["score"] for h in self.optimization_history]
        
        return {
            "total_iterations": len(self.optimization_history),
            "initial_score": scores[0],
            "final_score": scores[-1],
            "improvement": scores[-1] - scores[0],
            "relative_improvement": (scores[-1] - scores[0]) / abs(scores[0]) if scores[0] != 0 else 0,
            "best_score": max(scores),
            "converged": len(scores) > 10 and abs(scores[-1] - scores[-5]) < 1e-6
        }