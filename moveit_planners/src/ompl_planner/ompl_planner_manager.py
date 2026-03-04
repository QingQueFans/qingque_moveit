#!/usr/bin/env python3
"""
OMPL规划器管理器 - 集成真实MoveIt规划器
"""
import rclpy
from rclpy.node import Node
import time
import os
import sys

# 路径处理
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FILE_DIR)

try:
    from ompl_interface import OMPLInterface
    from ompl_algorithm_manager import OMPLAlgorithmManager
    HAS_MODULES = True
except ImportError as e:
    print(f"[OMPL管理器] 导入模块失败: {e}")
    HAS_MODULES = False

class OMPLPlannerManager(Node):
    """OMPL规划器管理器 - 管理真实和模拟规划器"""
    
    def __init__(self, node_name="ompl_planner_manager"):
        super().__init__(node_name)
        
        # 初始化组件
        self.interface = None
        self.algorithm_manager = None
        
        # 规划器状态
        self.manager_ready = False
        self.current_plan = None
        self.available_planners = []
        self.planning_mode = "unknown"  # real, simulated, mixed
        
        # 自动检测和初始化
        if HAS_MODULES:
            self._initialize_components()
        else:
            self.get_logger().error("无法加载规划器模块")
        
        self.get_logger().info("OMPL规划器管理器初始化完成")
        self.get_logger().info(f"规划模式: {self.planning_mode}")
    
    def _initialize_components(self):
        """初始化规划器组件"""
        self.get_logger().info("初始化OMPL规划器...")
        
        try:
            # 1. 初始化算法管理器
            self.algorithm_manager = OMPLAlgorithmManager()
            algorithms = self.algorithm_manager.get_available_algorithms()
            self.get_logger().info(f"✓ 找到算法配置: {algorithms}")
            
            # 2. 初始化规划器接口
            self.interface = OMPLInterface()
            interface_status = self.interface.get_interface_status()
            
            # 3. 确定规划模式
            if interface_status.get("planner_ready", False):
                self.planning_mode = "real"
                self.get_logger().info("✓ 真实规划模式就绪")
            else:
                self.planning_mode = "simulated"
                self.get_logger().warning("⚠️ 使用模拟规划模式")            
            # 4. 更新状态
            self.manager_ready = True
            self.available_planners = algorithms
            
            self.get_logger().info(f"✓ OMPL规划器初始化成功")
            self.get_logger().info(f"  可用算法: {algorithms}")
            self.get_logger().info(f"  规划模式: {self.planning_mode}")
            
        except Exception as e:
            self.get_logger().error(f"初始化失败: {e}")
            self.manager_ready = False
            self.planning_mode = "error"
    
    def plan_trajectory_sync(self, start_state, goal_state, **kwargs):
        """
        同步规划轨迹 - 支持真实和模拟模式
        
        Args:
            start_state: 起始状态
            goal_state: 目标状态
            **kwargs: 规划参数 (algorithm, timeout, planner_type等)
        
        Returns:
            规划结果，包含成功状态、轨迹、统计信息
        """
        start_time = time.time()
        
        try:
            self.get_logger().info("开始轨迹规划...")
            
            # 检查管理器状态
            if not self.manager_ready:
                return {
                    "success": False,
                    "error": "规划器管理器未就绪",
                    "stage": "initialization",
                    "manager_status": self.get_manager_status()
                }
            
            # 获取规划参数
            algorithm = kwargs.get('algorithm')
            timeout = kwargs.get('timeout', 5.0)
            force_simulated = kwargs.get('force_simulated', False)
            
            # 如果强制模拟模式，修改接口状态
            if force_simulated and hasattr(self.interface, 'planner_ready'):
                original_mode = self.planning_mode
                self.interface.planner_ready = False
                self.get_logger().info(f"强制使用模拟模式 (原模式: {original_mode})")
            
            # 使用接口进行规划
            result = self.interface.plan_sync(
                start_state=start_state,
                goal_state=goal_state,
                algorithm=algorithm,
                timeout=timeout
            )            # 恢复原始模式
            if force_simulated and hasattr(self.interface, 'planner_ready'):
                self.interface.planner_ready = (original_mode == "real")
            
            # 记录当前规划
            if result.get('success', False):
                self.current_plan = {
                    "trajectory": result.get('trajectory'),
                    "start_state": start_state,
                    "goal_state": goal_state,
                    "algorithm": result.get('algorithm', algorithm),
                    "planning_mode": result.get('planning_mode', 'unknown'),
                    "timestamp": time.time(),
                    "planning_time": result.get('planning_time', 0)
                }
            
            # 添加管理器特定信息
            result['manager_info'] = {
                "manager_node": self.get_name(),
                "planning_mode": self.planning_mode,
                "available_planners": self.available_planners,
                "planning_stage": "complete",
                "total_time": time.time() - start_time
            }
            
            return result
            
        except Exception as e:
            self.get_logger().error(f"轨迹规划失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "manager_info": {
                    "manager_node": self.get_name(),
                    "planning_stage": "failed",
                    "total_time": time.time() - start_time
                }
            }
    
    def switch_algorithm(self, algorithm_name, parameters=None):
        """切换规划算法"""
        try:
            self.get_logger().info(f"切换算法: {algorithm_name}")
            
            # 检查算法是否可用
            if algorithm_name not in self.available_planners:
                return {
                    "success": False,
                    "error": f"算法不可用: {algorithm_name}",
                    "available": self.available_planners
                }
            
            # 更新算法管理器
            if self.algorithm_manager:
                if parameters:
                    param_result = self.algorithm_manager.set_algorithm_parameters(
                        algorithm_name, parameters
                    )
                    if not param_result.get('success', True):
                        return param_result            # 更新接口的当前算法
            if self.interface:
                self.interface.active_algorithm = algorithm_name
            
            return {
                "success": True,
                "algorithm": algorithm_name,
                "planning_mode": self.planning_mode,
                "message": f"切换到{algorithm_name} ({self.planning_mode}模式)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_manager_status(self):
        """获取管理器状态"""
        interface_status = {}
        algorithm_status = {}
        
        if self.interface:
            interface_status = self.interface.get_interface_status()
        
        if self.algorithm_manager:
            algorithm_status = self.algorithm_manager.get_manager_status()
        
        status = {
            "manager": {
                "node_name": self.get_name(),
                "ready": self.manager_ready,
                "planning_mode": self.planning_mode,
                "available_planners": self.available_planners,
                "current_plan_exists": self.current_plan is not None
            },
            "interface": interface_status,
            "algorithm_manager": algorithm_status,
            "timestamp": time.time()
        }
        
        # 添加当前规划信息
        if self.current_plan:
            status["current_plan"] = {
                "algorithm": self.current_plan.get("algorithm"),
                "planning_mode": self.current_plan.get("planning_mode"),
                "timestamp": self.current_plan.get("timestamp"),
                "planning_time": self.current_plan.get("planning_time")
            }
        
        return status
    
    def get_planning_capabilities(self):
        """获取规划能力信息"""
        capabilities = {
            "planning_modes": ["real", "simulated"],
            "supported_algorithms": self.available_planners,
            "real_planning_available": self.planning_mode == "real",
            "features": {
                "pose_planning": True,
                "joint_planning": True,
                "collision_avoidance": self.planning_mode == "real",
                "trajectory_optimization": self.planning_mode == "real",
                "replanning": True
            },
            "limitations": {
                "simulated_mode": "生成近似轨迹，无碰撞检测",
                "requires_moveit": "真实模式需要MoveIt服务"
            }
        }
        
        return capabilities
    
    def test_planning_connection(self):
        """测试规划器连接"""
        test_cases = []
        
        # 测试1: 接口状态
        if self.interface:
            interface_status = self.interface.get_interface_status()
            test_cases.append({
                "test": "接口状态",
                "success": interface_status.get("planner_ready", False),
                "details": interface_status
            })        # 测试2: 算法管理器
        if self.algorithm_manager:
            algo_status = self.algorithm_manager.get_manager_status()
            test_cases.append({
                "test": "算法配置",
                "success": algo_status.get("algorithms_loaded", 0) > 0,
                "details": algo_status
            })
        
        # 测试3: 简单模拟规划
        try:
            test_goal = {"pose": {"position": [0.3, 0.1, 0.2], "orientation": [0,0,0,1]}}
            test_result = self.plan_trajectory_sync(
                start_state={"joints": [0]*7},
                goal_state=test_goal,
                algorithm="rrt_connect",
                timeout=2.0,
                force_simulated=True  # 强制模拟，避免真实服务问题
            )
            
            test_cases.append({
                "test": "模拟规划",
                "success": test_result.get("success", False),
                "mode": test_result.get("planning_mode", "unknown"),
                "time": test_result.get("planning_time", 0)
            })
        
        except Exception as e:
            test_cases.append({
                "test": "模拟规划",
                "success": False,
                "error": str(e)
            })
        
        # 汇总结果
        successful_tests = sum(1 for tc in test_cases if tc.get("success", False))
        
        return {
            "success": successful_tests == len(test_cases),
            "total_tests": len(test_cases),
            "successful_tests": successful_tests,
            "planning_mode": self.planning_mode,
            "tests": test_cases,
            "recommendation": self._get_recommendation(successful_tests, len(test_cases))
        }
    
    def _get_recommendation(self, successful, total):
        """根据测试结果给出建议"""
        if successful == total:
            return "✅ 规划器功能完整，可以开始使用"
        elif successful >= total * 0.7:
            return "⚠️  规划器基本可用，部分功能受限"
        elif successful > 0:
            return "⚠️  规划器功能受限，建议检查MoveIt服务"
        else:
            return "❌ 规划器不可用，请检查配置和依赖"
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("OMPL规划器管理器正在关闭...")
        
        if self.interface:
            self.interface.destroy_node()
        
        if self.algorithm_manager:
            self.algorithm_manager.destroy_node()
        
        super().destroy_node()


# 测试函数
def test_manager():
    """测试规划器管理器"""
    import rclpy
    
    print("测试OMPL规划器管理器...")
    
    rclpy.init()
    manager = OMPLPlannerManager()
    
    # 获取状态
    status = manager.get_manager_status()
    print(f"管理器状态: {status['manager']}")
    
    # 测试规划能力
    capabilities = manager.get_planning_capabilities()
    print(f"\n规划能力: {capabilities}")
    
    # 测试连接
    connection_test = manager.test_planning_connection()
    print(f"\n连接测试: {connection_test}")
    
    # 清理
    manager.destroy_node()
    rclpy.shutdown()
    
    return connection_test.get('success', False)


if __name__ == "__main__":
    success = test_manager()
    exit(0 if success else 1)