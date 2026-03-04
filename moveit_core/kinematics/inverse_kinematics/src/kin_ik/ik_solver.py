#!/usr/bin/env python3
"""
kin-ik: 基本逆运动学求解脚本
"""
import sys
import os
import argparse
import json
import time
import math
import numpy as np
from typing import List, Optional,Dict,Union,Tuple
# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)

# 1. 先设置 IK 模块路径（肯定正确）
IK_SRC = os.path.join(MODULE_ROOT, 'src')
sys.path.insert(0, IK_SRC)

# 2. 查找 moveit_core 根目录
# scripts -> inverse_kinematics -> kinematics -> moveit_core
MOVEIT_CORE_ROOT = os.path.join(SCRIPT_DIR, '..', '..', '..')
MOVEIT_CORE_ROOT = os.path.abspath(MOVEIT_CORE_ROOT)

# 3. 规划场景路径（保持原逻辑）
PLANNING_SCENE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
sys.path.insert(0, PLANNING_SCENE_SRC)

# 4. 缓存管理器路径
CACHE_MANAGER_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')
sys.path.insert(0, CACHE_MANAGER_SRC)

print(f"MOVEIT_CORE_ROOT: {MOVEIT_CORE_ROOT}")
try:
    from lma_predictor.lma_data_collector import LMADataCollector
    from lma_predictor.lma_model_trainer import LMAModelTrainer
    from lma_predictor.lma_predictor import LMAPredictor
    HAS_LMA = True
    print("[IKSolver] ✅ LMA组件导入成功")
except ImportError as e:
    HAS_LMA = False
    print(f"[IKSolver] ⚠️ LMA组件导入失败: {e}")
try:
    # 先导入规划场景（正确的）
    from ps_core.scene_client import PlanningSceneClient
    
    
    # 尝试导入缓存管理器
    try:
        from ps_cache import CachePathTools
        
    except ImportError as e:
        HAS_CACHE = False
        print(f"[警告] 缓存管理器导入失败: {e}")
    
    HAS_DEPENDENCIES = True
    print("✓ 成功导入所有依赖")
    try:
        from ml_seed_predictor import MLSeedPredictor
        HAS_ML = True
        print("[IKSolver] ✅ ML种子预测器导入成功")
    except ImportError as e:
        HAS_ML = False
        print(f"[IKSolver] ⚠️ ML种子预测器导入失败: {e}")    
except ImportError as e:
    print(f"[警告] 导入依赖失败: {e}")
    import traceback
    traceback.print_exc()
    HAS_DEPENDENCIES = False
    HAS_CACHE = False

# 在 ik_solver.py 文件的顶部，在 import 语句之后、类定义之前添加：


from pathlib import Path

def get_object_pose_directly(object_id: str) -> Optional[List[float]]:
    """
    直接读取缓存文件，绕过所有复杂逻辑
    返回: [x, y, z, qx, qy, qz, qw] 或 None
    """
    cache_dir = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects")
    
    if not cache_dir.exists():
        print(f"[直接读取] ❌ 缓存目录不存在: {cache_dir}")
        return None
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查ID
            file_id = data.get('data', {}).get('object_id')
            inner_id = data.get('data', {}).get('data', {}).get('id')
            
            if file_id == object_id or inner_id == object_id:
                print(f"[直接读取] ✅ 找到缓存文件: {cache_file.name}")
                
                pos = data['data']['data']['position']
                ori = data['data']['data']['orientation']
                pose = pos + ori
                
                print(f"[直接读取] 位置: {pos}")
                print(f"[直接读取] 方向: {ori}")
                return pose
                
        except Exception as e:
            print(f"[直接读取] 读取错误 {cache_file}: {e}")
            continue
    
    print(f"[直接读取] ❌ 未找到物体: {object_id}")
    return None
# ========== 其余代码保持原样 ==========
class IKSolver:
    """
    逆运动学求解器 - 核心类
    
    设计原则（遵循你的规范）：
    1. 必须接收scene_client用于场景交互
    2. 使用统一缓存机制
    3. 严格处理数据类型
    4. 提供一致的输出格式
    """
    
    def __init__(self, scene_client=None, robot_model: Optional[Dict] = None):
        """
        初始化IK求解器
        
        Args:
            scene_client: PlanningSceneClient实例（根据你的规范必须接收）
            robot_model: 机器人模型配置
        """
        self.client = scene_client  # 必须保存客户端
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        self._init_grasp_calculator()
        CachePathTools.initialize()
        # 机器人模型配置
        self.robot_model = robot_model or self._default_robot_model()
        
        # IK求解配置
        self.config = {
            "max_iterations": 100,          # 最大迭代次数
            "tolerance": 1e-4,              # 收敛容差
            "learning_rate": 0.1,           # 学习率
            "joint_limits": self.robot_model["joint_limits"],
            "damping": 0.01,                # 阻尼系数，避免奇异
        }
        
        # 结果缓存
        self.solution_cache = {}
        # ===== 【新增】初始化ML预测器 =====
        self.ml_predictor = None
        if HAS_ML:
            try:
                self.ml_predictor = MLSeedPredictor()
                self.ml_predictor.set_joint_limits(self.config["joint_limits"])
                stats = self.ml_predictor.get_stats()
                print(f"[IKSolver] ✅ ML种子预测器已加载")
                print(f"[IKSolver]   样本数: {stats['samples']}, 模型已训练: {stats['model_trained']}")
            except Exception as e:
                print(f"[IKSolver] ⚠️ ML种子预测器初始化失败: {e}")      
        # ===== 修改后 =====
            # ===== 在 __init__ 方法中 =====

            # ===== LMA专用ML系统 =====
            self.lma_data_collector = None
            self.lma_model_trainer = None
            self.lma_ml_predictor = None

            if HAS_LMA:
                try:
                    # 设置LMA数据目录
                    lma_data_dir = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data'
                    
                    # 初始化LMA组件
                    self.lma_data_collector = LMADataCollector(lma_data_dir)
                    self.lma_model_trainer = LMAModelTrainer(lma_data_dir)
                    self.lma_ml_predictor = LMAPredictor()
                    
                    # 设置关节限位
                    if hasattr(self.lma_ml_predictor, 'set_joint_limits'):
                        self.lma_ml_predictor.set_joint_limits(self.config["joint_limits"])
                    
                    # 获取统计信息
                    stats = self.lma_data_collector.get_stats()
                    print(f"[IKSolver] ✅ LMA专用ML系统已加载")
                    print(f"[IKSolver]   LMA样本数: {stats['count']}")
                    print(f"[IKSolver]   LMA数据目录: {lma_data_dir}")
                    
                except Exception as e:
                    print(f"[IKSolver] ⚠️ LMA专用ML初始化失败: {e}")
                    import traceback
                    traceback.print_exc()
                    self.lma_data_collector = None
                    self.lma_model_trainer = None
                    self.lma_ml_predictor = None

    def _init_grasp_calculator(self):
        """初始化抓取位姿计算器"""
        try:
            from .grasp_pose_calculator import GraspPoseCalculator
            self.grasp_calculator = GraspPoseCalculator()
            print(f"[IKSolver] ✅ 抓取位姿计算器已集成")
        except ImportError as e:
            print(f"[IKSolver] 抓取计算器导入失败: {e}")
            self.grasp_calculator = None
            
        # ========== 必须有的标准方法（你的规范） ==========
    def solve_and_cache(self, target_pose, robot_model):
        """求解IK并自动缓存"""
        # 1. 计算IK
        joint_solution = self.solve_ik(target_pose)
        
        # 2. 自动保存到缓存（一行代码！）
        cache_path = CachePathTools.ik_solution_to_cache(
            target_pose=target_pose,
            joint_solution=joint_solution,
            robot_model=robot_model,
            metadata={'solver': 'iterative', 'iterations': 50}
        )
        
        print(f"已保存到缓存: {cache_path}")
        return joint_solution, cache_path
    
    def load_cached_solution(self, target_pose, robot_model):
        """加载缓存的IK解"""
        # 计算应该的路径
        pose_data = {'position': target_pose[:3], 'orientation': target_pose[3:]}
        expected_path = CachePathTools.get_ik_solution_path(pose_data, robot_model)
        
        # 加载数据
        cached_data = CachePathTools.load_from_cache(expected_path)
        
        if cached_data:
            print(f"命中缓存: {expected_path}")
            return cached_data['data']['joint_solution']
        else:
            print("未找到缓存")
            return None
    def _load_cache(self) -> Dict:
        """加载缓存数据 - 完全按照你的规范实现"""
        if not os.path.exists(self.cache_file):
            print(f"[IK缓存] 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[IK缓存] 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[IK缓存] 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型 - ROS2兼容性"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if isinstance(value, (int, float, np.number)):
            return float(value)
        return value    # ========== 机器人模型方法 ==========
    
    def _default_robot_model(self) -> Dict:
        """Panda 7自由度机械臂模型 - 从官方URDF提取"""
        return {
            "name": "panda",
            "dh_parameters": [
                {"a": 0.0, "alpha": 0.0, "d": 0.333, "theta": 0.0},     # joint1
                {"a": 0.0, "alpha": -1.5708, "d": 0.0, "theta": 0.0},   # joint2
                {"a": 0.0, "alpha": 1.5708, "d": -0.316, "theta": 0.0}, # joint3
                {"a": 0.0825, "alpha": 1.5708, "d": 0.0, "theta": 0.0}, # joint4
                {"a": -0.0825, "alpha": -1.5708, "d": 0.384, "theta": 0.0}, # joint5
                {"a": 0.0, "alpha": 1.5708, "d": 0.0, "theta": 0.0},    # joint6
                {"a": 0.088, "alpha": 1.5708, "d": 0.0, "theta": 0.0},  # joint7
            ],
            "joint_limits": [
                [-2.9671, 2.9671],    # joint1
                [-1.8326, 1.8326],    # joint2
                [-2.9671, 2.9671],    # joint3
                [-3.1416, 0.0873],    # joint4
                [-2.9671, 2.9671],    # joint5
                [-0.0873, 3.8223],    # joint6
                [-2.9671, 2.9671],    # joint7
            ],
            "tool_transform": np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0.107],
                [0, 0, 0, 1]
            ])
        }
    def set_robot_model(self, model: Dict):
        """设置机器人模型"""
        self.robot_model = model
        self.config["joint_limits"] = model.get("joint_limits", self.config["joint_limits"])
        print(f"[IK求解器] 更新机器人模型: {model['name']}")
    
    # ========== 核心IK求解方法 ==========
    def solve(self, target_pose: Union[List, np.ndarray], 
            seed: Optional[List] = None,
            check_collision: bool = False,
            object_id: Optional[str] = None,
            context: Optional[Dict] = None,
            optimize: bool = True,
            max_attempts: int = 5) -> Dict:
        """
        逆运动学求解 - 带优化和验证
        """
        print(f"\n[IK调试] ====== 开始IK求解 ======")
        print(f"[IK调试] 目标位姿: {target_pose}")
        print(f"[IK调试] 物体ID: {object_id}")
        print(f"[IK调试] 机器人模型: {self.robot_model['name']}")
        print(f"[IK调试] 优化模式: {optimize}")
        # ===== 【新增】尝试次数计数和动态调整 =====
        if not hasattr(self, '_attempt_counter'):
            self._attempt_counter = {}  # 记录每个点位的尝试次数
        
        pose_key = tuple(round(x, 2) for x in target_pose[:3])
        self._attempt_counter[pose_key] = self._attempt_counter.get(pose_key, 0) + 1
        
        # 如果这个点位尝试太多次都没成功，扩大搜索范围
        if self._attempt_counter[pose_key] > 20:
            print(f"  ⚠️ 点位 {target_pose[:3]} 尝试超过20次，扩大搜索范围")
            # 在种子生成时添加更多随机性
            max_attempts = min(max_attempts * 2, 20)
        # ======================================        
        try:
            start_time = time.time()
            
            # 1. 确保数据类型正确
            print(f"[IK调试] 步骤1: 数据类型转换")
            target_pose = self._ensure_float(target_pose)
            print(f"[IK调试] 转换后: {target_pose}")
            
            # 2. 转换目标位姿为变换矩阵
            print(f"[IK调试] 步骤2: 位姿转矩阵")
            if isinstance(target_pose, list) and len(target_pose) == 7:
                T_target = self._pose_to_matrix(target_pose)
                target_pos = target_pose[:3]
                print(f"[IK调试] 目标位置: {target_pos}")
            elif isinstance(target_pose, np.ndarray) and target_pose.shape == (4, 4):
                T_target = target_pose
                target_pos = target_pose[:3, 3].tolist()
            else:
                raise ValueError("目标位姿必须是7元素列表或4x4矩阵")
            
            # 3. 初始化FK验证器
            print(f"[IK调试] 步骤3: 初始化FK验证器")
            HAS_FK = False
            fk_validator = None
            
            try:
                from kin_fk.fk_solver import FKSolver
                from kin_fk.pose_computer import PoseComputer
                print(f"[IK调试] FK模块导入成功")
                
                fk_solver = FKSolver(robot_model=self.robot_model)
                fk_validator = PoseComputer(fk_solver)
                HAS_FK = True
                print(f"[IK调试] FK验证器初始化成功")
            except Exception as e:
                print(f"[IK调试] ⚠️ FK验证器初始化失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 4. 如果指定了种子，直接求解
            if seed is not None and not optimize:
                print(f"[IK调试] 步骤4: 使用指定种子求解")
                print(f"[IK调试] 种子: {seed}")
                
                solution, iterations, error = self._solve_iterative(T_target, seed)
                solution = self._apply_joint_limits(solution)
                print(f"[IK调试] 求解完成: error={error}, iterations={iterations}")
                print(f"[IK调试] 解: {[round(s,4) for s in solution]}")
                
                if HAS_FK and fk_validator:
                    actual_pose = fk_validator.compute_end_effector(solution)
                    pos_error = np.linalg.norm(np.array(actual_pose["position"]) - np.array(target_pos))
                    print(f"[IK调试] FK验证: 位置误差={pos_error*1000:.2f}mm")
                else:
                    pos_error = 0.0
                    actual_pose = None
                
                return self._build_result(solution, error, iterations, start_time, 
                                        object_id, pos_error, actual_pose)
            
            # 5. 多解择优
            print(f"[IK调试] 步骤5: 多解择优 (max_attempts={max_attempts})")
            best_solution = None
            best_error = float('inf')
            best_fk_error = float('inf')
            best_iterations = 0
            solutions_tried = []
            solution_signatures = set()  # 新增：记录已经找到的解
            # 生成智能种子
            seeds = self._generate_smart_seeds(object_id, target_pose, max_attempts)
            print(f"[IK调试] 生成 {len(seeds)} 个种子")
            
            for i, current_seed in enumerate(seeds):
                print(f"[IK优化] 尝试种子 {i+1}/{len(seeds)}")
                print(f"[IK调试] 种子: {[round(s,4) for s in current_seed]}")
                
                try:
                    # 求解
                    solution, iterations, error = self._solve_iterative(T_target, current_seed)
                    solution = self._apply_joint_limits(solution)
                    # 检查这个解是否已经找到过
                    sol_sig = tuple(round(s, 2) for s in solution)
                    if sol_sig in solution_signatures:
                        print(f"  ⏭️ 跳过重复解 (已找到过)")
                        continue
                    solution_signatures.add(sol_sig)                    
                    # FK验证
                    if HAS_FK and fk_validator:
                        actual_pose = fk_validator.compute_end_effector(solution)
                        pos_error = np.linalg.norm(np.array(actual_pose["position"]) - np.array(target_pos))
                        print(f"[IK调试]   位置误差: {pos_error*1000:.2f}mm")
                    else:
                        pos_error = 0.0
                        actual_pose = None
                    
                    solutions_tried.append({
                        "solution": solution,
                        "pos_error": pos_error,
                        "iter_error": error,
                    })
                    
                    # 更新最佳解
                    if pos_error < best_fk_error - 0.001:
                        best_fk_error = pos_error
                        best_error = error
                        best_solution = solution
                        best_iterations = iterations
                        print(f"  ✅ 找到更好解，位置误差: {pos_error*1000:.2f}mm")
                    elif abs(pos_error - best_fk_error) < 0.001 and error < best_error:
                        best_error = error
                        best_solution = solution
                        best_iterations = iterations
                        print(f"  ✅ 找到相近解，迭代误差更小: {error:.6f}")
                        
                except Exception as e:
                    print(f"[IK调试]   种子求解失败: {e}")
                    continue
            
            # 6. 处理结果
            if best_solution is None and solutions_tried:
                print(f"[IK调试] 没有找到理想解，使用第一个")
                best_solution = solutions_tried[0]["solution"]
                best_fk_error = solutions_tried[0]["pos_error"]
                best_error = solutions_tried[0]["iter_error"]
            
            if best_solution is None:
                print(f"[IK调试] ❌ 所有种子求解失败")
                return {
                    "success": False,
                    "error": "所有种子求解失败",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "object_id": object_id
                }
            
            # 7. 最终验证
            print(f"[IK调试] 最佳解: {[round(s,4) for s in best_solution]}")
            if HAS_FK and fk_validator:
                final_pose = fk_validator.compute_end_effector(best_solution)
                final_pos_error = np.linalg.norm(np.array(final_pose["position"]) - np.array(target_pos))
                print(f"[IK调试] 最终位置误差: {final_pos_error*1000:.2f}mm")
            else:
                final_pos_error = 0.0
                final_pose = None
            
            # 8. 计算质量
            quality = self._calculate_solution_quality(best_solution, best_error)
            print(f"[IK调试] 解质量: {quality:.3f}")
            
            # 9. 保存缓存
            self._save_to_persistent_cache(
                target_pose=target_pose,
                joint_solution=best_solution,
                object_id=object_id,
                metadata={
                    "error": float(best_error),
                    "iterations": best_iterations,
                    "quality": quality,
                    "fk_error": float(final_pos_error),
                    "solver_method": "optimized",
                    "elapsed_time": time.time() - start_time
                }
            )
            
            elapsed_time = time.time() - start_time
            print(f"[IK调试] 总耗时: {elapsed_time:.3f}秒")
            print(f"[IK调试] ====== IK求解完成 ======\n")
            
            # 10. 返回结果
            return {
                "success": True,
                "solution": best_solution,
                "error": float(best_error),
                "iterations": best_iterations,
                "elapsed_time": elapsed_time,
                "quality": quality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "object_id": object_id,
                "verification": {
                    "fk_valid": final_pos_error < 0.01 if HAS_FK else True,
                    "position_error": float(final_pos_error),
                    "actual_pose": final_pose,
                    "target_pose": target_pos,
                    "error_mm": float(final_pos_error * 1000) if HAS_FK else 0
                } if HAS_FK else {},
                "optimization": {
                    "attempts": len(seeds),
                    "solutions_tried": len(solutions_tried),
                    "best_fk_error": float(best_fk_error * 1000) if HAS_FK else 0
                },
                "metadata": {
                    "robot_model": self.robot_model["name"],
                    "method": "optimized",
                    "object_id": object_id
                }
            }
            
        except Exception as e:
            print(f"[IK调试] ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "object_id": object_id
            }
    def _get_cached_solution(self, object_id: str) -> Optional[List[float]]:
        """从缓存中获取该物体的成功解作为种子"""
        try:
            import json
            from pathlib import Path
            
            cache_dir = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data")
            ik_cache_dir = cache_dir / "kinematics" / "ik_solutions"
            
            if not ik_cache_dir.exists():
                return None
            
            for cache_file in ik_cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get('data', {}).get('metadata', {})
                    cached_object_id = metadata.get('object_id')
                    
                    if cached_object_id == object_id:
                        print(f"[IKSolver] ✅ 从缓存找到物体 {object_id} 的解作为种子")
                        return data['data'].get('joint_solution')
                        
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            print(f"[IKSolver] 缓存查询错误: {e}")
            return None        
    def _generate_smart_seeds(self, object_id, target_pose, num_seeds=5):
        """生成智能种子 - 增强去重版"""
        seeds = []
        seed_signatures = set()  # 记录种子特征
        
        def get_seed_signature(seed):
            # 使用7个关节的精确值，但量化到0.05 rad
            return tuple(round(s, 2) for s in seed)
        
        # 1. 当前位置
        current = self.get_current_joints()
        if current and len(current) >= 7:
            sig = get_seed_signature(current)
            if sig not in seed_signatures:
                seeds.append(current)
                seed_signatures.add(sig)
                print(f"[种子] ✅ 当前位置")
        
        # 2. ML预测（带多种扰动）
        if self.ml_predictor:
            try:
                predicted = self.ml_predictor.predict(target_pose)
                if predicted is not None:
                    # 原始预测
                    sig = get_seed_signature(predicted)
                    if sig not in seed_signatures:
                        seeds.append(predicted)
                        seed_signatures.add(sig)
                        print(f"[ML] ✅ 预测种子")
                    
                    # 多个不同幅度的扰动
                    for scale in [0.03, 0.05, 0.08, 0.1]:
                        noise = np.random.normal(0, scale, 7)
                        new_seed = np.clip(np.array(predicted) + noise,
                                        [l[0] for l in self.config["joint_limits"]],
                                        [l[1] for l in self.config["joint_limits"]])
                        sig = get_seed_signature(new_seed)
                        if sig not in seed_signatures:
                            seeds.append(new_seed.tolist())
                            seed_signatures.add(sig)
                            print(f"[种子] 扰动(scale={scale})")
            except Exception as e:
                print(f"[ML] ⚠️ 种子生成失败: {e}")
        
        # 3. 缓存解
        if object_id:
            cached = self._get_cached_solution(object_id)
            if cached and len(cached) >= 7:
                sig = get_seed_signature(cached)
                if sig not in seed_signatures:
                    seeds.append(cached)
                    seed_signatures.add(sig)
                    print(f"[种子] ✅ 缓存解")
        
        # 4. 常用姿态（随机顺序）
        common_poses = [
            [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
            [0.0, 0.0, 0.0, -1.5, 0.0, 1.5, 0.0],
            [1.5, -1.0, 1.0, -2.0, 1.0, 2.0, 1.0],
            [-1.5, -1.0, -1.0, -2.0, -1.0, 2.0, -1.0],
        ]
        np.random.shuffle(common_poses)
        for pose in common_poses:
            sig = get_seed_signature(pose)
            if sig not in seed_signatures:
                seeds.append(pose)
                seed_signatures.add(sig)
                print(f"[种子] 常用姿态")
        
        print(f"[种子生成] 生成 {len(seeds)} 个唯一种子")
        return seeds[:num_seeds*2]

    def get_ml_stats(self):
        """获取ML预测器统计信息"""
        if not hasattr(self, 'ml_predictor') or self.ml_predictor is None:
            return {"available": False, "error": "ML predictor not initialized"}
        
        try:
            # 先尝试获取基础统计
            stats = self.ml_predictor.get_stats()
            
            # 尝试获取增强统计（如果有）
            if hasattr(self.ml_predictor, 'get_enhanced_stats'):
                enhanced = self.ml_predictor.get_enhanced_stats()
                stats['enhanced'] = enhanced
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    def get_current_joints(self):
        """获取当前关节位置"""
        try:
            import rclpy
            from sensor_msgs.msg import JointState
            import sys
            import os
            
            # 添加轨迹执行器路径
            trajectory_path = '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/move_group/trajectory_execution/src'
            if trajectory_path not in sys.path:
                sys.path.append(trajectory_path)
            
            # 方法1: 通过 TrajectoryExecutor
            try:
                from trajectory_execution import TrajectoryExecutor
                executor = TrajectoryExecutor()
                if hasattr(executor, 'get_current_joints'):
                    joints = executor.get_current_joints()
                    if joints and len(joints) >= 7:
                        print(f"[IKSolver] 从执行器获取当前关节: {[round(j,3) for j in joints[:3]]}...")
                        return joints
            except Exception as e:
                print(f"[IKSolver] 通过执行器获取失败: {e}")
            
            # 方法2: 直接监听 /joint_states 话题
            if not rclpy.ok():
                rclpy.init()
            
            from rclpy.node import Node
            
            class JointStateListener(Node):
                def __init__(self):
                    super().__init__('joint_state_listener')
                    self.joint_positions = None
                    self.sub = self.create_subscription(
                        JointState,
                        '/joint_states',
                        self.callback,
                        1
                    )
                
                def callback(self, msg):
                    # Panda的7个关节
                    joint_order = ['panda_joint1', 'panda_joint2', 'panda_joint3',
                                'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7']
                    
                    positions = [0.0] * 7
                    for i, name in enumerate(msg.name):
                        if name in joint_order:
                            idx = joint_order.index(name)
                            positions[idx] = msg.position[i]
                    
                    self.joint_positions = positions
                    self.get_logger().info(f"获取到关节位置: {[round(p,3) for p in positions[:3]]}...")
            
            listener = JointStateListener()
            
            # 等待消息
            for _ in range(10):
                rclpy.spin_once(listener, timeout_sec=0.1)
                if listener.joint_positions is not None:
                    joints = listener.joint_positions
                    listener.destroy_node()
                    return joints
            
            listener.destroy_node()
            return None
            
        except Exception as e:
            print(f"[IKSolver] 获取当前关节失败: {e}")
            return None    
    def _build_result(self, solution, error, iterations, start_time, 
                    object_id, pos_error, actual_pose):
        """构建结果（辅助函数）"""
        elapsed_time = time.time() - start_time
        quality = self._calculate_solution_quality(solution, error)
        
        return {
            "success": pos_error < 0.02,
            "solution": solution,
            "error": float(error),
            "iterations": iterations,
            "elapsed_time": elapsed_time,
            "quality": quality,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "object_id": object_id,
            "verification": {
                "fk_valid": pos_error < 0.01,
                "position_error": float(pos_error),
                "actual_pose": actual_pose,
                "error_mm": float(pos_error * 1000)
            },
            "metadata": {
                "robot_model": self.robot_model["name"],
                "method": "standard",
                "object_id": object_id
            }
        }
    def _save_to_persistent_cache(self, target_pose, joint_solution, object_id=None, metadata=None):
        """保存到持久化缓存（文件系统）"""
        try:
            # 创建 KinematicsCache 实例
            from ps_cache.kinematics_cache import KinematicsCache
            
            kin_cache = KinematicsCache()
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 添加物体ID到元数据
            if object_id:
                metadata['object_id'] = object_id
            
            # 使用 KinematicsCache.save_ik_solution
            cache_path = kin_cache.save_ik_solution(
                target_pose=target_pose,
                joint_solution=joint_solution,
                robot_model=self.robot_model["name"],
                metadata=metadata,
                object_id=object_id  # ← 传递object_id参数
            )
            
            if cache_path:
                print(f"[IK求解器] 持久化缓存已保存: {cache_path}")
                if object_id:
                    print(f"          关联物体: {object_id}")
            return cache_path
                    
        except Exception as e:
            print(f"[IK求解器] 保存持久化缓存失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    def solve_multiple(self, target_pose: List, 
                       num_solutions: int = 8,
                       check_collision: bool = False) -> Dict:
        """
        获取多个IK解
        
        Args:
            target_pose: 目标位姿
            num_solutions: 需要多少个解
            check_collision: 是否检查碰撞
            
        Returns:
            多个解的列表
        """
        solutions = []
        seeds = [self._get_random_seed() for _ in range(num_solutions * 2)]  # 生成更多种子
        
        for seed in seeds:
            if len(solutions) >= num_solutions:
                break
                
            result = self.solve(target_pose, seed, check_collision)
            if result["success"]:
                # 检查是否与已有解重复
                is_duplicate = False
                for existing in solutions:
                    if np.allclose(result["solution"], existing["solution"], atol=1e-3):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    solutions.append(result)
        
        return {
            "success": len(solutions) > 0,
            "solutions": solutions,
            "count": len(solutions),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    def solve_with_optimization(self, target_pose: Union[List, np.ndarray], 
                                object_id: Optional[str] = None,
                                num_attempts: int = 10,
                                check_collision: bool = False) -> Dict:
        """
        多解择优的IK求解 - 优化版（带综合评分 + 可执行性）
        """
        print(f"\n[IK优化] ====== 开始多解择优 ======")
        print(f"[IK优化] 目标: {target_pose[:3]}")
        print(f"[IK优化] 尝试次数: {num_attempts}")
        
        # 获取当前位置作为参考
        current_joints = self.get_current_joints()
        if current_joints:
            print(f"[IK优化] 当前位置: {[round(j,3) for j in current_joints[:3]]}...")
        
        best_solution = None
        best_score = float('inf')
        best_error = float('inf')
        solutions_tried = []
        
        # 生成种子
        seeds = self._generate_smart_seeds(object_id, target_pose, num_attempts)
        
        for i, seed in enumerate(seeds):
            print(f"[IK优化] 尝试 {i+1}/{len(seeds)}")
            
            result = self.solve(
                target_pose=target_pose,
                seed=seed,
                check_collision=check_collision,
                object_id=object_id,
                optimize=False
            )
            
            if result["success"]:
                error = result.get("verification", {}).get("position_error", 1.0)
                solution = result["solution"]
                
                # ===== 综合评分 =====
                score = 0.0
                
                # 1. 位置误差（首要目标）- 权重1000 (1mm = 1分)
                score += 1000 * error
                
                # 2. 关节运动距离（次要目标）- 优先选离当前位置近的
                joint_movement = 0
                if current_joints is not None:
                    joint_movement = np.linalg.norm(np.array(solution) - np.array(current_joints))
                    score += 1.0 * joint_movement  # 1rad运动 = 1分
                    print(f"     关节运动: {joint_movement:.3f} rad")
                
                # 3. 关节限位裕度（越靠近中心越好）
                limit_penalty = 0
                for j, (angle, limits) in enumerate(zip(solution, self.config["joint_limits"])):
                    center = (limits[0] + limits[1]) / 2
                    distance_to_center = abs(angle - center)
                    limit_penalty += distance_to_center
                score += 0.1 * limit_penalty
                
                # 4. 可操作性（避免奇异）
                try:
                    J = self._compute_jacobian(np.array(solution))
                    manipulability = np.sqrt(np.linalg.det(J @ J.T))
                    score -= 10 * min(manipulability, 1.0)
                except:
                    pass
                
                # ===== 新增：5. 可执行性分数（最重要！）=====
                feasibility = self._calculate_feasibility(solution)
                # 可行性越低，扣分越多（权重设大一点）
                score += 200 * (1 - feasibility)  # 可行性0.5时加100分，0.8时加40分
                print(f"     可执行性: {feasibility:.2f} (扣分: {200*(1-feasibility):.1f})")
                
                # ===== 新增：6. 极限警告 =====
                at_limit = False
                for j, (angle, limits) in enumerate(zip(solution, self.config["joint_limits"])):
                    if abs(angle - limits[0]) < 0.05 or abs(angle - limits[1]) < 0.05:
                        at_limit = True
                        print(f"      ⚠️ 关节{j+1}在极限位置: {angle:.3f}")
                        score += 500  # 严重扣分！
                        break
                
                solutions_tried.append({
                    "seed": seed,
                    "error": error,
                    "movement": joint_movement if current_joints else 0,
                    "feasibility": feasibility,
                    "score": score,
                    "solution": solution
                })
                
                print(f"     位置误差: {error*1000:.2f}mm, 可行性: {feasibility:.2f}, 综合得分: {score:.3f}")
                
                # 如果找到误差小且可行性高的解，直接返回
                if error < 0.03 and feasibility > 0.8:  # 30mm以内且可行性高
                    print(f"  ✅ 找到优质解！误差:{error*1000:.1f}mm, 可行性:{feasibility:.2f}")
                    best_solution = result
                    best_error = error
                    best_score = score
                    break
                
                if score < best_score:
                    best_score = score
                    best_error = error
                    best_solution = result
                    print(f"  ✅ 找到更好解，得分: {score:.3f}")
                    
                    if error < 0.005:  # 5mm内直接返回
                        print(f"[IK优化] 误差小于5mm，提前结束")
                        break
        
        if best_solution:
            # 最终检查可行性
            final_feasibility = self._calculate_feasibility(best_solution["solution"])
            print(f"[IK优化] 最优解误差: {best_error*1000:.2f}mm, 可行性: {final_feasibility:.2f}, 得分: {best_score:.3f}")
            
            # 如果可行性太低，给个警告
            if final_feasibility < 0.5:
                print(f"  ⚠️ 警告：最终解可行性较低，可能无法执行！")
            
            return best_solution
        else:
            return {"success": False, "error": "所有种子求解失败"}
    # ========== 内部实现方法 ==========
    
    def _pose_to_matrix(self, pose: List) -> np.ndarray:
        """将7元素位姿转换为4x4变换矩阵"""
        x, y, z, qx, qy, qz, qw = pose
        
        # 创建旋转矩阵
        R = np.array([
            [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
            [2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qx*qw)],
            [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)]
        ])
        
        # 创建变换矩阵
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [x, y, z]
        
        return T
    
    def _get_random_seed(self) -> List:
        """生成随机初始种子"""
        seed = []
        for limits in self.config["joint_limits"]:
            seed.append(np.random.uniform(limits[0], limits[1]))
        return seed
    
    def _solve_iterative(self, T_target: np.ndarray, 
                        seed: List) -> Tuple[List, int, float]:
        """迭代求解IK（基于雅可比矩阵）- 加入可执行性约束"""
        current_theta = np.array(seed)
        best_theta = current_theta.copy()
        best_error = float('inf')
        best_feasibility = float('-inf')  # 新增：记录最佳可执行性
        lambda_ = 0.01
        SAFE_MARGIN = 0.3  # 新增：安全余量（离极限至少0.3rad）
        
        for iteration in range(self.config["max_iterations"]):
            # 1. 计算当前正运动学
            T_current = self._forward_kinematics(current_theta)
            
            # 2. 计算误差
            error_pos = T_target[:3, 3] - T_current[:3, 3]
            R_error = T_target[:3, :3] @ T_current[:3, :3].T
            angle, axis = self._rotation_matrix_to_angle_axis(R_error)
            error_rot = axis * angle
            error = np.linalg.norm(error_pos) + np.linalg.norm(error_rot)
            
            # ===== 新增：计算可执行性分数 =====
            feasibility = self._calculate_feasibility(current_theta)
            
            # ===== 新增：综合评分（误差小 + 可执行性高）=====
            # 分数越高越好，-error 是负数，所以要找最大值
            score = -error + 0.1 * feasibility
            
            if score > best_feasibility:
                best_feasibility = score
                best_theta = current_theta.copy()
                best_error = error
                print(f"    [迭代] 找到更好解: 误差={error:.4f}, 可执行性={feasibility:.2f}")
            
            # 3. 检查收敛（误差小且安全）
            if error < self.config["tolerance"] and feasibility > 0.8:
                print(f"    ✅ 收敛于安全解: 误差={error:.4f}, 可执行性={feasibility:.2f}")
                return current_theta.tolist(), iteration + 1, error
            
            # 4. 计算雅可比矩阵
            J = self._compute_jacobian(current_theta)
            
            # 5. 阻尼最小二乘
            error_vec = np.concatenate([error_pos, error_rot])
            J_T = J.T
            A = J @ J_T + lambda_**2 * np.eye(6)
            delta_theta = J_T @ np.linalg.solve(A, error_vec)
            
            # ===== 新增：添加安全梯度 =====
            safety_gradient = self._compute_safety_gradient(current_theta)
            delta_theta += 0.05 * safety_gradient  # 向安全区域拉
            
            # 6. 更新关节角度
            current_theta += self.config["learning_rate"] * delta_theta
            
            # 7. 应用关节限制（强制保留安全余量）
            current_theta = self._safe_joint_limits(current_theta, SAFE_MARGIN)
        
        print(f"    ⚠️ 未收敛，返回最佳解: 误差={best_error:.4f}")
        return best_theta.tolist(), self.config["max_iterations"], best_error
    def _solve_iterative_with_feasibility(self, T_target: np.ndarray, seed: List) -> Tuple[List, int, float]:
        """迭代求解IK - 加入可执行性约束"""
        current_theta = np.array(seed)
        best_theta = current_theta.copy()
        best_error = float('inf')
        best_feasibility_score = float('-inf')
        lambda_ = 0.01
        error_history = []
        
        SAFE_MARGIN = 0.3  # 安全余量（rad）- 离极限至少0.3rad
        
        for iteration in range(self.config["max_iterations"]):
            # 1. 计算当前正运动学
            T_current = self._forward_kinematics(current_theta)
            
            # 2. 计算误差
            error_pos = T_target[:3, 3] - T_current[:3, 3]
            R_error = T_target[:3, :3] @ T_current[:3, :3].T
            angle, axis = self._rotation_matrix_to_angle_axis(R_error)
            error_rot = axis * angle
            error = np.linalg.norm(error_pos) + np.linalg.norm(error_rot)
            
            # 3. 计算可执行性分数
            feasibility_score = self._calculate_feasibility(current_theta)
            
            # 4. 综合评分（误差小 + 可执行性高）
            total_score = -error + 0.1 * feasibility_score  # 权衡
            
            if total_score > best_feasibility_score:
                best_feasibility_score = total_score
                best_theta = current_theta.copy()
                best_error = error
            
            # 5. 检查收敛（误差小且安全）
            if error < self.config["tolerance"] and feasibility_score > 0.8:
                return current_theta.tolist(), iteration + 1, error
            
            # 6. 计算雅可比
            J = self._compute_jacobian(current_theta)
            
            # 7. 计算更新量
            error_vec = np.concatenate([error_pos, error_rot])
            J_T = J.T
            A = J @ J_T + lambda_**2 * np.eye(6)
            delta_theta = J_T @ np.linalg.solve(A, error_vec)
            
            # 8. 添加安全约束梯度
            safety_gradient = self._compute_safety_gradient(current_theta)
            delta_theta += 0.05 * safety_gradient  # 向安全区域拉
            
            # 9. 自适应步长
            alpha = self._adaptive_step_size(error_history, iteration)
            current_theta += alpha * delta_theta
            
            # 10. 软约束（但保留安全余量）
            current_theta = self._safe_joint_limits(current_theta, SAFE_MARGIN)
            
            error_history.append(error)
        
        return best_theta.tolist(), self.config["max_iterations"], best_error

    def _calculate_feasibility(self, theta):
        """计算关节解的可执行性分数 (0-1)"""
        score = 1.0
        
        for i, (angle, limits) in enumerate(zip(theta, self.config["joint_limits"])):
            range_size = limits[1] - limits[0]
            
            # 到下限的距离
            dist_to_low = angle - limits[0]
            # 到上限的距离
            dist_to_high = limits[1] - angle
            
            # 如果太靠近极限，扣分
            if dist_to_low < 0.3:
                score *= (dist_to_low / 0.3)  # 越近分数越低
            if dist_to_high < 0.3:
                score *= (dist_to_high / 0.3)
            
            # 关节变化率（避免剧烈变化）
            if i > 0:
                diff = abs(theta[i] - theta[i-1])
                if diff > 1.0:  # 相邻关节变化太大
                    score *= 0.8
        
        return score

    def _compute_safety_gradient(self, theta):
        """计算向安全区域拉的梯度"""
        gradient = np.zeros_like(theta)
        
        for i, (angle, limits) in enumerate(zip(theta, self.config["joint_limits"])):
            center = (limits[0] + limits[1]) / 2
            
            # 如果靠近下限，向上拉
            if angle - limits[0] < 0.3:
                gradient[i] = 0.1 * (center - angle)
            # 如果靠近上限，向下拉
            elif limits[1] - angle < 0.3:
                gradient[i] = 0.1 * (center - angle)
        
        return gradient

    def _safe_joint_limits(self, theta, margin=0.3):
        """应用关节限制，强制保留安全余量"""
        safe_theta = theta.copy()
        
        for i, (angle, limits) in enumerate(zip(theta, self.config["joint_limits"])):
            range_size = limits[1] - limits[0]
            safe_low = limits[0] + margin
            safe_high = limits[1] - margin
            
            # 强制限制在安全区域内
            safe_theta[i] = np.clip(angle, safe_low, safe_high)
            
            # 如果被裁剪了，说明原来不安全
            if safe_theta[i] != angle:
                print(f"  ⚠️ 关节{i+1}从{angle:.3f}强制拉到安全区域{safe_theta[i]:.3f}")
        
        return safe_theta    
    def _forward_kinematics(self, theta: np.ndarray) -> np.ndarray:
        """正运动学计算（为IK服务）"""
        T = np.eye(4)
        dh_params = self.robot_model["dh_parameters"]
        
        for i, (t, dh) in enumerate(zip(theta, dh_params)):
            a, alpha, d, theta0 = dh["a"], dh["alpha"], dh["d"], dh["theta"]
            ct = math.cos(t + theta0)
            st = math.sin(t + theta0)
            ca = math.cos(alpha)
            sa = math.sin(alpha)
            
            Ti = np.array([
                [ct, -st*ca, st*sa, a*ct],
                [st, ct*ca, -ct*sa, a*st],
                [0, sa, ca, d],
                [0, 0, 0, 1]
            ])
            
            T = T @ Ti
        
        # 应用末端工具变换
        T = T @ self.robot_model["tool_transform"]
        
        return T
    
    def _compute_jacobian(self, theta: np.ndarray) -> np.ndarray:
        """计算几何雅可比矩阵"""
        n = len(theta)
        J = np.zeros((6, n))
        
        # 计算每个连杆的位置和z轴
        positions = []
        z_axes = []
        
        T = np.eye(4)
        for i, t in enumerate(theta):
            dh = self.robot_model["dh_parameters"][i]
            a, alpha, d, theta0 = dh["a"], dh["alpha"], dh["d"], dh["theta"]
            ct = math.cos(t + theta0)
            st = math.sin(t + theta0)
            ca = math.cos(alpha)
            sa = math.sin(alpha)
            
            Ti = np.array([
                [ct, -st*ca, st*sa, a*ct],
                [st, ct*ca, -ct*sa, a*st],
                [0, sa, ca, d],
                [0, 0, 0, 1]
            ])
            
            T = T @ Ti
            positions.append(T[:3, 3])
            z_axes.append(T[:3, 2])
        
        # 计算雅可比矩阵
        T_total = T @ self.robot_model["tool_transform"]
        p_end = T_total[:3, 3]
        
        for i in range(n):            # 位置部分：J_v = z_i × (p_end - p_i)
            z_i = z_axes[i]
            p_i = positions[i]
            J[:3, i] = np.cross(z_i, p_end - p_i)
            
            # 姿态部分：J_w = z_i
            J[3:, i] = z_i
        
        return J
    
    def _rotation_matrix_to_angle_axis(self, R: np.ndarray) -> Tuple[float, np.ndarray]:
        """将旋转矩阵转换为角度-轴表示"""
        angle = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
        
        if abs(angle) < 1e-10:
            return 0.0, np.array([0, 0, 1])
        
        axis = np.array([
            R[2, 1] - R[1, 2],
            R[0, 2] - R[2, 0],
            R[1, 0] - R[0, 1]
        ])
        axis = axis / (2 * math.sin(angle))
        
        return angle, axis
    
    def _apply_joint_limits(self, solution: List) -> List:
        """应用关节限制，但留5%余量以便规划"""
        limited = []
        margin = 0.05  # 5%余量
        
        for angle, limits in zip(solution, self.config["joint_limits"]):
            range_size = limits[1] - limits[0]
            safe_low = limits[0] + margin * range_size
            safe_high = limits[1] - margin * range_size
            
            # 如果在极限附近，拉回安全区域
            if angle < safe_low:
                angle = safe_low
            elif angle > safe_high:
                angle = safe_high
            else:
                angle = angle  # 保持不变
                
            limited.append(angle)
        
        return limited
    def _apply_joint_limits_vector(self, solution: np.ndarray, margin=0.3) -> np.ndarray:
        """应用关节限制，强制保留安全余量"""
        for i in range(len(solution)):
            limits = self.config["joint_limits"][i]
            safe_low = limits[0] + margin
            safe_high = limits[1] - margin
            solution[i] = max(safe_low, min(safe_high, solution[i]))
        return solution
    def solve_with_verification(self, target_pose, collect_both=True):
        """
        求解并用官方LMA验证，同时收集两种解
        """
        your_result = None
        lma_result = None
        
        # 1. 先用你的IK求解
        your_result = self.solve(target_pose, optimize=True)
        
        # 2. 如果有解，用官方LMA验证
        if your_result and your_result.get('success'):
            your_solution = your_result['solution']
            your_error = your_result.get('verification', {}).get('error_mm', 1000)
            
            print(f"\n[验证] 你的IK解: 误差 {your_error:.1f}mm")
            
            # 用你的解作为种子调用官方LMA
            lma_result = self.solve_with_moveit_simple(target_pose)
            # 注意：solve_with_moveit_simple 内部已经会用ML种子
            
            if lma_result.get('success'):
                lma_error = lma_result.get('error_mm', 1000)
                print(f"[验证] 官方LMA解: 误差 {lma_error:.1f}mm")
                
                # 3. 同时收集两种解
                if collect_both:
                    # 收集你的IK解（如果质量还行）
                    if your_error < 100:
                        self.ml_predictor.add_sample(
                            target_pose=target_pose,
                            successful_seed=your_solution,
                            error_mm=your_error,
                            object_id='your_ik'
                        )
                        print(f"  📚 已收集你的IK解")
                    
                    # 收集官方LMA解（如果质量好）
                    if lma_error < 80:
                        self.ml_predictor.add_sample(
                            target_pose=target_pose,
                            successful_seed=lma_result['solution'],
                            error_mm=lma_error,
                            object_id='lma_validated'
                        )
                        print(f"  📚 已收集官方LMA解")
        
        # 4. 返回最好的解
        best_solution = None
        best_error = 1000
        best_source = None
        
        if your_result and your_result.get('success'):
            your_error = your_result.get('verification', {}).get('error_mm', 1000)
            if your_error < best_error:
                best_error = your_error
                best_solution = your_result['solution']
                best_source = 'your_ik'
        
        if lma_result and lma_result.get('success'):
            lma_error = lma_result.get('error_mm', 1000)
            if lma_error < best_error:
                best_error = lma_error
                best_solution = lma_result['solution']
                best_source = 'lma'
        
        return {
            'success': best_solution is not None,
            'solution': best_solution,
            'error_mm': best_error,
            'source': best_source,
            'your_result': your_result,
            'lma_result': lma_result
        }    
    def _check_collision(self, solution: List) -> Dict:
        """检查碰撞（需要scene_client）"""
        if not self.client:
            return {"free": True, "message": "未启用碰撞检查"}
        
        # 这里可以调用scene_client的碰撞检查功能
        # 暂时返回模拟结果
        return {
            "free": np.random.random() > 0.1,  # 90%概率无碰撞
            "collisions": [],
            "message": "碰撞检查完成"
        }
    
    def _calculate_solution_quality(self, solution: List, error: float) -> float:
        """计算解的质量（0-1之间）"""
        # 1. 基于误差的质量
        error_quality = max(0, 1 - error / 0.1)  # 假设0.1m误差为边界
        
        # 2. 基于关节限制的质量（距离限制越远越好）
        limit_quality = 1.0
        for angle, limits in zip(solution, self.config["joint_limits"]):
            range_size = limits[1] - limits[0]
            distance_to_limit = min(angle - limits[0], limits[1] - angle)
            limit_quality *= max(0.1, distance_to_limit / (range_size / 2))
        
        # 3. 基于可操作性（暂时简化）
        manipulability = 1.0
        
        # 综合质量
        quality = 0.5 * error_quality + 0.3 * limit_quality + 0.2 * manipulability
        
        return min(1.0, max(0.0, quality))
    
    # ========== 工具方法 ==========
    def train_ml_model(self):
        """手动触发ML模型训练"""
        if self.ml_predictor:
            print("[ML] 开始手动训练...")
            success = self.ml_predictor.train()
            if success:
                print("[ML] ✅ 模型训练成功")
            else:
                print("[ML] ⚠️ 模型训练失败，可能需要更多数据")
            return success
        else:
            print("[ML] ❌ ML预测器未初始化")
            return False    
    def validate_solution(self, target_pose: List, solution: List) -> Dict:
        """验证IK解的正确性"""
        try:
            # 计算正运动学
            T_solution = self._forward_kinematics(np.array(solution))
            
            # 提取位置和姿态
            pos_solution = T_solution[:3, 3]
            rot_solution = T_solution[:3, :3]
            
            # 目标位姿
            T_target = self._pose_to_matrix(target_pose)
            pos_target = T_target[:3, 3]
            rot_target = T_target[:3, :3]
            
            # 计算误差
            pos_error = np.linalg.norm(pos_solution - pos_target)
            rot_error = np.arccos(max(-1.0, min(1.0, 
                (np.trace(rot_solution.T @ rot_target) - 1) / 2)))
            
            return {
                "valid": pos_error < 0.01 and rot_error < 0.1,  # 1cm, 0.1rad
                "position_error": float(pos_error),
                "orientation_error": float(rot_error),
                "position_threshold": 0.01,
                "orientation_threshold": 0.1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_solution_statistics(self) -> Dict:
        """获取求解器统计信息"""
        return {
            "cache_size": len(self.solution_cache),
            "robot_model": self.robot_model["name"],
            "config": self.config,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    # 在 IKSolver 类中添加这些方法

    def set_constraint_handler(self, constraint_handler):
        """设置约束处理器"""
        self.constraint_handler = constraint_handler
        print(f"[IK求解器] 已设置约束处理器，包含 {len(constraint_handler.constraints)} 个约束")

    def set_optimizer(self, optimizer):
        """设置优化器"""
        self.optimizer = optimizer
        print("[IK求解器] 已设置优化器")

    def solve_with_constraints(self, target_pose: List,
                            seed: Optional[List] = None,
                            check_collision: bool = False) -> Dict:
        """
        带约束的IK求解
        
        Args:
            target_pose: 目标位姿
            seed: 初始种子
            check_collision: 是否检查碰撞
        """
        if not hasattr(self, 'constraint_handler') or not self.constraint_handler:
            return self.solve(target_pose, seed, check_collision)
        
        try:
            # 1. 先求解无约束的IK
            base_result = self.solve(target_pose, seed, check_collision)
            
            if not base_result["success"]:
                return base_result
            
            # 2. 计算当前位姿
            base_solution = base_result["solution"]
            T_current = self._forward_kinematics(np.array(base_solution))
            
            # 3. 评估约束
            constraint_result = self.constraint_handler.evaluate_constraints(
                T_current, base_solution, self.robot_model)
            
            # 4. 如果约束不满足，尝试优化
            if not constraint_result["satisfied"] and hasattr(self, 'optimizer'):
                print(f"[约束IK] 约束不满足，尝试优化...")
                optimization_result = self.optimizer.optimize_solution(
                    base_solution, self, target_pose)
                
                if optimization_result["improvement"] > 0:
                    optimized_solution = optimization_result["optimized_solution"]
                    
                    # 重新评估约束
                    T_optimized = self._forward_kinematics(np.array(optimized_solution))
                    constraint_result = self.constraint_handler.evaluate_constraints(
                        T_optimized, optimized_solution, self.robot_model)
                    
                    if constraint_result["satisfied"]:
                        base_solution = optimized_solution
                        base_result["solution"] = optimized_solution
                        base_result["optimized"] = True
                        base_result["optimization_info"] = optimization_result
            
            # 5. 更新结果
            base_result["constraints"] = constraint_result
            base_result["constraints_satisfied"] = constraint_result["satisfied"]
            
            return base_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"带约束求解失败: {e}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    def solve_optimized(self, target_pose: List,
                    seed: Optional[List] = None,
                    check_collision: bool = False) -> Dict:
        """
        优化的IK求解
        
        Args:
            target_pose: 目标位姿
            seed: 初始种子
            check_collision: 是否检查碰撞
        """
        if not hasattr(self, 'optimizer') or not self.optimizer:
            return self.solve(target_pose, seed, check_collision)
        
        try:
            # 1. 先求解基本IK
            base_result = self.solve(target_pose, seed, check_collision)
            
            if not base_result["success"]:
                return base_result
            
            # 2. 优化解
            optimization_result = self.optimizer.optimize_solution(
                base_result["solution"], self, target_pose)
            
            # 3. 更新结果
            base_result["solution"] = optimization_result["optimized_solution"]
            base_result["optimized"] = True
            base_result["optimization_info"] = optimization_result
            base_result["initial_score"] = optimization_result["initial_score"]
            base_result["final_score"] = optimization_result["final_score"]
            base_result["improvement"] = optimization_result["improvement"]
            
            return base_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"优化求解失败: {e}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }    
    # ========== 新增：物体ID求解方法 ==========
    def solve_with_moveit_simple(self, target_pose: Union[List, np.ndarray]) -> Dict:
        """
        使用MoveIt官方IK服务（LMA求解器）
        支持双ML模式：优先用LMA专用ML，失败则用原ML
        """
        try:
            import rclpy
            from rclpy.node import Node
            from moveit_msgs.srv import GetPositionIK
            from geometry_msgs.msg import Pose, Point, Quaternion
            import numpy as np  # ← 添加这行！
            
            print(f"\n[MoveIt IK] 调用IK服务...")
            
            if not rclpy.ok():
                rclpy.init()
            
            node = Node('temp_ik_client')
            cli = node.create_client(GetPositionIK, '/compute_ik')
            
            if not cli.wait_for_service(timeout_sec=2.0):
                node.destroy_node()
                return {"success": False, "error": "IK服务不可用"}
            
            # 准备请求
            req = GetPositionIK.Request()
            req.ik_request.group_name = "panda_arm"
            
            # 目标位姿
            req.ik_request.pose_stamped.header.frame_id = "panda_link0"
            req.ik_request.pose_stamped.pose.position.x = target_pose[0]
            req.ik_request.pose_stamped.pose.position.y = target_pose[1]
            req.ik_request.pose_stamped.pose.position.z = target_pose[2]
            req.ik_request.pose_stamped.pose.orientation.x = target_pose[3]
            req.ik_request.pose_stamped.pose.orientation.y = target_pose[4]
            req.ik_request.pose_stamped.pose.orientation.z = target_pose[5]
            req.ik_request.pose_stamped.pose.orientation.w = target_pose[6]
            
            # 设置完整的关节名称（包括手指关节）
            joint_names = [
                'panda_joint1', 'panda_joint2', 'panda_joint3',
                'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
                'panda_finger_joint1', 'panda_finger_joint2'
            ]
            req.ik_request.robot_state.joint_state.name = joint_names
            
            # ===== 双ML策略（修复版）=====
            ml_seed_used = None
            ml_source = None
            full_seed = None
            
            # 1. 优先用LMA专用ML（如果存在）
            if hasattr(self, 'lma_ml_predictor') and self.lma_ml_predictor:
                try:
                    result = self.lma_ml_predictor.predict(target_pose)
                    # 根据返回类型处理
                    if isinstance(result, tuple) and len(result) == 2:
                        ml_seed, uncertainty = result
                    else:
                        ml_seed = result
                        uncertainty = 0.5
                    
                    if ml_seed is not None and all(v is not None for v in ml_seed):
                        ml_seed_used = ml_seed
                        ml_source = f"LMA专用ML"
                        valid_seed = [float(x) if x is not None else 0.0 for x in ml_seed]
                        full_seed = valid_seed + [0.04, 0.04]
                        req.ik_request.robot_state.joint_state.position = [float(x) for x in full_seed]
                        print(f"  [LMA-ML] 使用LMA专用种子: {[round(s,3) for s in ml_seed[:3]]}...")
                except Exception as e:
                    print(f"  [LMA-ML] 预测失败: {e}")
            
            # 2. 如果没有LMA专用ML或预测失败，用原ML
            if full_seed is None and self.ml_predictor:
                try:
                    # 原ML可能返回单个值或元组
                    ml_seed = self.ml_predictor.predict(target_pose)
                    if isinstance(ml_seed, tuple):
                        ml_seed = ml_seed[0]  # 取第一个元素
                    
                    if ml_seed is not None and all(v is not None for v in ml_seed):
                        ml_seed_used = ml_seed
                        ml_source = "原ML"
                        valid_seed = [float(x) if x is not None else 0.0 for x in ml_seed]
                        full_seed = valid_seed + [0.04, 0.04]
                        req.ik_request.robot_state.joint_state.position = [float(x) for x in full_seed]
                        print(f"  [原ML] 使用原ML种子: {[round(s,3) for s in ml_seed[:3]]}...")
                except Exception as e:
                    print(f"  [原ML] 预测失败: {e}")
            
            # 3. 如果都没有，用零种子
            if full_seed is None:
                zero_seed = [0.0] * 7 + [0.04, 0.04]
                req.ik_request.robot_state.joint_state.position = zero_seed
                print(f"  [默认] 使用零种子")
            
            # 调用IK服务
            future = cli.call_async(req)
            rclpy.spin_until_future_complete(node, future)
            
            if future.result() and future.result().error_code.val == 1:
                # 只取前7个关节（去掉手指关节）
                full_solution = list(future.result().solution.joint_state.position)
                solution = full_solution[:7]
                
                # 验证
                from kin_fk.fk_solver import FKSolver
                fk = FKSolver(robot_model=self.robot_model)
                actual = fk.compute_pose_list(solution)
                error = np.linalg.norm(np.array(actual[:3]) - np.array(target_pose[:3]))
                error_mm = error * 1000
                
                print(f"  ✅ MoveIt解误差: {error_mm:.2f}mm")
                if ml_source:
                    print(f"  📊 种子来源: {ml_source}")
                
                # ===== 收集LMA成功案例 =====
                # ===== 收集LMA成功案例（带扰动）=====
                if error_mm < 300:  # 阈值400mm
                    if hasattr(self, 'lma_data_collector') and self.lma_data_collector:
                        # 1. 添加原始解
                        self.lma_data_collector.add_sample(
                            target_pose=target_pose,
                            solution=solution,
                            error_mm=error_mm,
                            seed_used=ml_seed_used,
                            metadata={
                                'ml_source': ml_source,
                                'method': 'moveit_ik',
                                'region': self._get_region(target_pose)
                            }
                        )
                        
                        # 2. 如果是高质量解 (<300mm)，添加扰动版本增加多样性
                        if error_mm < 200:
                            for j in range(2):  # 添加2个扰动
                                # 生成小扰动 (±0.03 rad)
                                noise = np.random.normal(0, 0.03, 7)
                                perturbed = np.array(solution) + noise
                                
                                # 应用关节限位
                                for k in range(7):
                                    perturbed[k] = np.clip(
                                        perturbed[k],
                                        self.config["joint_limits"][k][0],
                                        self.config["joint_limits"][k][1]
                                    )
                                
                                # 验证扰动解
                                from kin_fk.fk_solver import FKSolver
                                fk = FKSolver(robot_model=self.robot_model)
                                actual = fk.compute_pose_list(perturbed.tolist())
                                pert_error = np.linalg.norm(np.array(actual[:3]) - np.array(target_pose[:3]))
                                pert_error_mm = pert_error * 1000
                                
                                # 如果误差没有显著变差，就收集
                                if pert_error_mm < error_mm * 1.2:  # 允许20%的误差增加
                                    self.lma_data_collector.add_sample(
                                        target_pose=target_pose,
                                        solution=perturbed.tolist(),
                                        error_mm=pert_error_mm,
                                        seed_used=solution,
                                        metadata={
                                            'ml_source': ml_source,
                                            'method': 'moveit_ik_perturbed',
                                            'original_error': error_mm,
                                            'region': self._get_region(target_pose)
                                        }
                                    )
                                    print(f"      ➕ 添加扰动{j+1}: {pert_error_mm:.1f}mm")
                        
                        # 自动训练（如果样本数达到阈值）
                        stats = self.lma_data_collector.get_stats()
                        if stats['count'] % 10 == 0 and stats['count'] >= 5:
                            if hasattr(self, 'lma_model_trainer') and self.lma_model_trainer:
                                print(f"  🔄 自动训练LMA模型...")
                                X, y, weights = self.lma_data_collector.get_weighted_training_data()
                                self.lma_model_trainer.train(X, y, weights)
                                
                node.destroy_node()
                return {
                    "success": True,
                    "solution": solution,
                    "error": error,
                    "error_mm": error_mm,
                    "method": "moveit_ik",
                    "ml_source": ml_source,
                    "ml_seed_used": ml_seed_used is not None,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            node.destroy_node()
            return {"success": False, "error": "IK求解失败"}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    # 添加辅助方法
    def _get_region(self, pose):
        """获取点位所属区域"""
        x, y, z = pose[:3]
        r = np.sqrt(x**2 + y**2)
        if r < 0.4:
            return "near"
        elif r < 0.6:
            return "mid"
        else:
            return "far"        
    def solve_for_object(self, object_id, grasp_strategy='top', seed=None, 
                        check_collision=False, save_to_cache=True, 
                        offset_distance=0.05, **kwargs):
        """为特定物体求解IK（优化版）"""
        print(f"\n[IKSolver] 通过物体ID求解: {object_id}")
        print(f"  抓取策略: {grasp_strategy}")
        
        try:
            # 1. 获取或计算抓取位姿
            grasp_pose = self._get_grasp_pose_for_object(object_id, grasp_strategy, offset_distance=offset_distance)
            if grasp_pose is None:
                return {
                    "success": False,
                    "error": f"无法为物体 {object_id} 计算抓取位姿",
                    "object_id": object_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            print(f"✅ 抓取位姿: {[round(x, 4) for x in grasp_pose[:3]]}...")
            
            # 2. 使用优化版本求解
            num_attempts = kwargs.get('num_attempts', 8)
            
            result = self.solve_with_optimization(
                target_pose=grasp_pose,
                object_id=object_id,
                num_attempts=num_attempts,
                check_collision=check_collision
            )
            
            # 3. 如果优化求解失败，回退到原始方法
            if not result.get("success", False):
                print(f"[IKSolver] ⚠️ 优化求解失败，尝试原始方法")
                
                solve_params = {
                    'target_pose': grasp_pose,
                    'seed': seed,
                    'check_collision': check_collision,
                    'object_id': object_id
                }
                
                for key in ['max_attempts', 'timeout', 'tolerance', 'return_all', 'verbose']:
                    if key in kwargs:
                        solve_params[key] = kwargs[key]
                
                result = self.solve(**solve_params)
            
            # 4. 添加物体信息
            if isinstance(result, dict):
                result["object_id"] = object_id
                result["grasp_strategy"] = grasp_strategy
                result["grasp_pose"] = grasp_pose
                result["offset_distance"] = offset_distance
                
            # 5. 【新增】记录成功案例给ML - 动态阈值版
            if result.get("success", False) and self.ml_predictor:
                error = result.get("verification", {}).get("error_mm", 1000)
                print(f"[DEBUG] 抓取成功！误差: {error}mm")
                
                # 获取当前样本数
                stats = self.ml_predictor.get_stats()
                current_samples = stats.get('samples', 0)
                
                # 在 solve_for_object 方法中，找到阈值判断部分
                if current_samples < 50:
                    threshold = 200
                    phase = "🚀 快速积累期"
                elif current_samples < 80:
                    threshold = 150
                    phase = "📊 质量提升期"
                elif current_samples < 120:
                    threshold = 120
                    phase = "🎯 精化期"
                elif current_samples < 200:
                    threshold = 100
                    phase = "💎 高质量期"
                else:  # 现在306个样本
                    threshold = 80   # 收紧到80mm
                    phase = "⚡ 超精期"
                
                if error < threshold:
                    print(f"[DEBUG] {phase} 误差{error}mm < {threshold}，学习！")
                    self.ml_predictor.add_sample(
                        target_pose=grasp_pose,
                        successful_seed=result["solution"],
                        error_mm=error,
                        object_id=object_id
                    )
                    stats = self.ml_predictor.get_stats()
                    print(f"[ML] ✅ 已学习成功案例，样本数: {stats['samples']} (当前阶段: {phase})")
                else:
                    print(f"[DEBUG] {phase} 误差{error}mm >= {threshold}，不学习")
            return result
        except Exception as e:
            print(f"[IKSolver] 物体求解错误: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "object_id": object_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    def _get_grasp_pose_for_object(self, object_id: str, grasp_strategy: str,
                                offset_distance=0.05, **kwargs) -> Optional[List[float]]:
        """获取物体的抓取位姿 - 总是从缓存动态读取"""
        
        print(f"\n[IKSolver] 获取物体 {object_id} 的抓取位姿")
        print(f"  策略: {grasp_strategy}")   
        print(f"  偏移: {offset_distance}m")
        
        # ========== 1. 尝试抓取计算器 ==========
        if self.grasp_calculator:
            try:
                print(f"[IKSolver] 使用抓取计算器...")
                grasp_pose = self.grasp_calculator.calculate_grasp_pose(
                    object_id=object_id,
                    grasp_strategy=grasp_strategy,
                    offset_distance=offset_distance
                )
                
                if grasp_pose:
                    print(f"[IKSolver] ✅ 抓取计算器成功")
                    return grasp_pose
                else:
                    print(f"[IKSolver] ⚠️ 抓取计算器返回None")
                    
            except Exception as e:
                print(f"[IKSolver] ❌ 抓取计算器异常: {e}")
        
        # ========== 2. 直接读取缓存文件 ==========
        print(f"[IKSolver] 直接读取缓存文件...")
        cache_pose = get_object_pose_directly(object_id)
        
        if cache_pose:
            print(f"[IKSolver] ✅ 缓存读取成功")
            print(f"  位置: {cache_pose[:3]}")
            print(f"  方向: {cache_pose[3:]}")
            return cache_pose
        
        # ========== 3. 所有方法都失败 ==========
        print(f"[IKSolver] ❌❌❌ 严重错误：无法获取物体 {object_id} 的位姿")
        print(f"[IKSolver] 可能的原因:")
        print(f"  1. 物体 {object_id} 不存在于场景中")
        print(f"  2. 缓存文件丢失或损坏")
        print(f"  3. 缓存路径错误")
        print(f"[IKSolver] 使用紧急备用位姿 [999, 999, 999]")
        
        # 返回明显错误的位置，便于调试
        emergency_pose = [999.0, 999.0, 999.0, 0.0, 0.0, 0.0, 1.0]
        return emergency_pose
    
    def _get_cached_pose_by_object_id(self, object_id: str) -> Optional[List[float]]:
        """从IK缓存中通过物体ID查找位姿"""
        try:
            if not hasattr(self, '_ik_cache'):
                return None
            
            # 复用轨迹执行器的逻辑
            import json
            from pathlib import Path
            
            cache_dir = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data")
            ik_cache_dir = cache_dir / "kinematics" / "ik_solutions"
            
            if not ik_cache_dir.exists():
                return None
            
            for cache_file in ik_cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get('data', {}).get('metadata', {})
                    cached_object_id = metadata.get('object_id')
                    
                    if cached_object_id == object_id:
                        print(f"[IKSolver] ✅ 从IK缓存找到物体 {object_id}")
                        return data['data'].get('target_pose')
                        
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            print(f"[IKSolver] 缓存查询错误: {e}")
            return None
    
    # ========== 新增：批量求解方法 ==========
    
    def solve_for_multiple_objects(self,
                                  object_ids: List[str],
                                  grasp_strategy: str = "top",
                                  **kwargs) -> Dict:
        """为多个物体求解IK"""
        results = []
        successful = 0
        
        print(f"[IKSolver] 批量求解 {len(object_ids)} 个物体")
        
        for object_id in object_ids:
            print(f"\n[进度] 处理物体: {object_id} ({successful+1}/{len(object_ids)})")
            
            result = self.solve_for_object(
                object_id=object_id,
                grasp_strategy=grasp_strategy,
                **kwargs
            )
            
            results.append(result)
            if result.get("success", False):
                successful += 1
        
        return {
            "success": successful > 0,
            "total_objects": len(object_ids),
            "successful": successful,
            "failed": len(object_ids) - successful,
            "success_rate": successful / len(object_ids) if object_ids else 0,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }       
    def _matrix_to_quat(self, R):
        """旋转矩阵转四元数（辅助函数）"""
        qw = math.sqrt(max(0, 1 + R[0,0] + R[1,1] + R[2,2])) / 2
        qx = math.sqrt(max(0, 1 + R[0,0] - R[1,1] - R[2,2])) / 2
        qy = math.sqrt(max(0, 1 - R[0,0] + R[1,1] - R[2,2])) / 2
        qz = math.sqrt(max(0, 1 - R[0,0] - R[1,1] + R[2,2])) / 2
        
        # 确定符号
        qx = qx * (1 if R[2,1] - R[1,2] >= 0 else -1)
        qy = qy * (1 if R[0,2] - R[2,0] >= 0 else -1)
        qz = qz * (1 if R[1,0] - R[0,1] >= 0 else -1)
        
        return [qx, qy, qz, qw]    
# 在 ik_solver.py 文件末尾添加：

# ========== 一行调用接口 ==========

class IKSolverFacade:
    """
    IK求解器外观类 - 提供一行调用接口
    
    设计原则：
    1. 与轨迹执行器相同的一行调用体验
    2. 支持多种输入格式
    3. 自动处理缓存和错误
    """
    
    _instance = None
    
   
    @classmethod
    def solve(cls, target, use_moveit=False, **kwargs):
        """
        一行调用：求解逆运动学
        
        参数：
        target: 可以是：
            - 字符串: 物体ID ("box")
            - 列表: 位姿 [x,y,z,qx,qy,qz,qw]
            - 字典: {"pose": [...], "object_id": "...", "joints": [...]}
        
        use_moveit: 是否使用MoveIt官方求解器（高精度）
        
        **kwargs: 可选参数
            - seed: 初始种子
            - grasp_strategy: 抓取策略
            - use_cache: 是否使用缓存
            - check_collision: 检查碰撞
            - save_to_cache: 保存到缓存
            
        返回：
            标准化结果字典
        """
        # 获取或创建单例
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        # 传递use_moveit参数
        return cls._instance._solve_internal(target, use_moveit=use_moveit, **kwargs)
        
    @classmethod
    def _create_instance(cls):
        """创建内部实例"""
        solver = _IKSolverFacade()
        solver._setup()
        return solver


class _IKSolverFacade:
    """内部实现类"""
    
    def _setup(self):
        """初始化"""
        try:
            from ps_core.scene_client import PlanningSceneClient
            client = PlanningSceneClient()
            
            # 创建IK求解器实例
            self.ik_solver = IKSolver(client)
            
            print("[IKSolverFacade] 就绪")
        except Exception as e:
            print(f"[IKSolverFacade] 初始化失败: {e}")
            self.ik_solver = None
    
    def _solve_internal(self, target, use_moveit=False, **kwargs):
        """内部求解逻辑"""
        try:
            # 解析输入
            parsed_target = self._parse_target(target)
            
            # 如果要求用MoveIt且是位姿模式
            if use_moveit and "pose" in parsed_target:
                result = self.ik_solver.solve_with_moveit_simple(parsed_target["pose"])
                return self._standardize_output(result, target)
            
            # 使用缓存
            use_cache = kwargs.get('use_cache', True)
            
            if use_cache and hasattr(self.ik_solver, 'solve_for_object'):
                # 使用增强的物体ID求解
                result = self._solve_with_cache(parsed_target, **kwargs)
            else:
                # 使用原始求解
                result = self._solve_direct(parsed_target, **kwargs)
            
            # 标准化输出
            return self._standardize_output(result, target)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _parse_target(self, target):
        """解析多种输入格式"""
        if isinstance(target, str):
            # 字符串：物体ID
            return {"object_id": target}
        
        elif isinstance(target, (list, tuple)):
            if len(target) == 7:
                # 7元素列表：位姿
                return {"pose": target}
            elif len(target) == 3:
                # 3元素列表：位置，添加默认方向
                return {"pose": list(target) + [0.0, 0.0, 0.0, 1.0]}
        
        elif isinstance(target, dict):
            # 字典：已经解析好的格式
            return target
        
        raise ValueError(f"不支持的输入类型: {type(target)}")
    
    def _solve_with_cache(self, target, **kwargs):
        """使用缓存的求解"""
        if "object_id" in target:
            # 物体ID模式
            return self.ik_solver.solve_for_object(
                object_id=target["object_id"],
                grasp_strategy=kwargs.get('grasp_strategy', 'top'),
                seed=kwargs.get('seed'),
                check_collision=kwargs.get('check_collision', False),
                save_to_cache=kwargs.get('save_to_cache', True),
                offset_distance=kwargs.get('offset', 0.05)
            )
        elif "pose" in target:
            # 位姿模式
            return self.ik_solver.solve(
                target_pose=target["pose"],
                seed=kwargs.get('seed'),
                check_collision=kwargs.get('check_collision', False),
                object_id=kwargs.get('object_id'),
                save_to_cache=kwargs.get('save_to_cache', True)
            )
        else:            # 回退到直接求解
            return self._solve_direct(target, **kwargs)
    
    def _solve_direct(self, target, **kwargs):
        """直接求解"""
        if "pose" not in target:
            raise ValueError("直接求解需要位姿输入")
        
        return self.ik_solver.solve(
            target_pose=target["pose"],
            seed=kwargs.get('seed'),
            check_collision=kwargs.get('check_collision', False),
            **{k: v for k, v in kwargs.items() if k not in ['seed', 'check_collision']}
        )
    
    def _standardize_output(self, result, original_target):
        """标准化输出"""
        if not isinstance(result, dict):
            result = {"success": False, "error": "返回结果不是字典"}
        
        # 确保有标准字段
        result.setdefault("success", False)
        result.setdefault("timestamp", self._get_timestamp())
        
        # 添加目标信息
        if isinstance(original_target, str):
            result["object_id"] = original_target
        elif isinstance(original_target, dict) and "object_id" in original_target:
            result["object_id"] = original_target["object_id"]
        
        return result
    
    def _get_timestamp(self):
        """获取时间戳"""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 全局便捷函数 ==========

def solve_ik(target, **kwargs):
    """
    全局便捷函数 - 一行调用IK求解
    
    示例：
    result = solve_ik("box", grasp_strategy="top")
    result = solve_ik([0.5, 0.0, 0.3, 0,0,0,1], save_to_cache=True)
    result = solve_ik({"pose": [0.6,0.1,0.2,0,0,0,1], "object_id": "coke_can_01"})
    """
    return IKSolverFacade.solve(target, **kwargs)


def solve_for_object(object_id, **kwargs):
    """
    快速求解物体的IK
    
    示例：
    result = solve_for_object("box")
    result = solve_for_object("coke_can_01", grasp_strategy="side", offset=0.03)
    """
    return solve_ik(object_id, **kwargs)


def solve_pose(x, y, z, qx=0, qy=0, qz=0, qw=1, **kwargs):
    """
    快速求解位姿的IK
    
    示例：
    result = solve_pose(0.5, 0.0, 0.3)
    result = solve_pose(0.6, 0.1, 0.2, 0,0,0,1, object_id="test")
    """
    return solve_ik([x, y, z, qx, qy, qz, qw], **kwargs)


def batch_solve_ik(targets, **kwargs):
    """
    批量求解IK
    
    示例：
    results = batch_solve_ik(["box", "coke_can_01", "test_cube"])
    results = batch_solve_ik([
        {"object_id": "box", "grasp_strategy": "top"},
        {"object_id": "coke_can_01", "grasp_strategy": "side"}
    ])
    """
    facade = IKSolverFacade._create_instance()
    
    results = []
    for target in targets:
        result = facade._solve_internal(target, **kwargs)
        results.append(result)
    
    return {
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success", False)),
        "results": results,
        "timestamp": facade._get_timestamp()
    }


def get_ik_solver_stats():
    """获取IK求解器统计信息"""
    facade = IKSolverFacade._create_instance()
    
    if hasattr(facade.ik_solver, 'get_cache_stats'):
        stats = facade.ik_solver.get_cache_stats()
        return stats
    elif hasattr(facade.ik_solver, '_cache_stats'):
        return facade.ik_solver._cache_stats
    
    return {"message": "统计信息不可用"}


def clear_ik_cache():
    """清空IK缓存"""
    facade = IKSolverFacade._create_instance()
    
    if hasattr(facade.ik_solver, 'clear_cache'):
        return facade.ik_solver.clear_cache()
    
    return {"success": False, "error": "清空缓存方法不可用"}