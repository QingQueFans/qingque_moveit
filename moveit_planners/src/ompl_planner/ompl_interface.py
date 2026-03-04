#!/usr/bin/env python3
"""
OMPL规划器接口 - 最终修复版
适配修复后的MoveIt客户端
"""
import rclpy
from rclpy.node import Node
import time
import yaml
import os
import sys

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FILE_DIR)

try:
    from ros2_moveit_client import MoveItROS2Client
    HAS_MOVEIT_CLIENT = True
except ImportError as e:
    print(f"[OMPL接口] 导入MoveIt客户端失败: {e}")
    HAS_MOVEIT_CLIENT = False

class OMPLInterface(Node):
    """OMPL规划器接口 - 最终修复版"""
    
    def __init__(self, node_name="ompl_planner_interface_fixed"):
        super().__init__(node_name)
        
        # 配置路径
        self.config_dir = os.path.join(os.path.dirname(FILE_DIR), '..', '..', 'config')
        self.config_file = os.path.join(self.config_dir, 'ompl_planners.yaml')
        
        # 规划器状态
        self.planner_ready = False
        self.active_algorithm = "rrt_connect"
        self.planning_stats = {
            'total_plans': 0,
            'successful_plans': 0,
            'total_time': 0.0
        }
        
        # 加载配置
        self._load_config()
        
        # 初始化修复后的ROS2客户端
        self.moveit_client = None
        if HAS_MOVEIT_CLIENT:
            try:
                self.moveit_client = MoveItROS2Client()
                time.sleep(0.5)  # 给连接时间
                
                if self.moveit_client.is_available():
                    self.planner_ready = True
                    self.get_logger().info("✅ 真实MoveIt规划器就绪")
                    
                    # 测试连接
                    test_result = self._test_connection()
                    if test_result:
                        self.get_logger().info("✅ 规划器测试通过")
                    else:
                        self.get_logger().warning("⚠️ 规划器测试失败，但服务可用")
                else:
                    self.get_logger().warning("⚠️ MoveIt服务不可用，将使用模拟模式")
            except Exception as e:
                self.get_logger().error(f"初始化MoveIt客户端失败: {e}")
        else:
            self.get_logger().warning("⚠️ MoveIt客户端不可用，使用模拟模式")
        
        self.get_logger().info(f"OMPL规划器接口初始化完成")
        self.get_logger().info(f"真实规划: {'可用' if self.planner_ready else '模拟模式'}")
# 打开ompl_interface.py，找到_load_config方法附近
# 修改配置文件路径的计算方式：
    def _load_config(self):
        """加载配置 - 灵活版本"""
        try:
            # 方法1：从环境变量获取
            workspace_path = os.environ.get('QINGFU_MOVEIT_PATH', 
                                        os.path.expanduser('~/qingfu_moveit/moveit_planners'))
            
            # 方法2：自动检测
            possible_paths = [
                # 绝对路径
                "/home/diyuanqiongyu/qingfu_moveit/moveit_planners/config/ompl_planners.yaml",
                # 相对于当前文件
                os.path.join(os.path.dirname(__file__), 
                            '..', '..', '..', 'config', 'ompl_planners.yaml'),
                # 工作空间路径
                os.path.join(workspace_path, 'config', 'ompl_planners.yaml'),
            ]
            
            for config_path in possible_paths:
                config_path = os.path.abspath(config_path)
                if os.path.exists(config_path):
                    self.config_file = config_path
                    with open(config_path, 'r') as f:
                        self.config = yaml.safe_load(f)
                    
                    self.get_logger().info(f"✅ 加载配置文件: {config_path}")
                    planners = list(self.config.get('planners', {}).keys())
                    self.get_logger().info(f"可用算法: {planners}")
                    return
            
            # 如果没有找到配置文件
            self.get_logger().warning("未找到配置文件，使用默认配置")
            self._set_default_config()
            
        except Exception as e:
            self.get_logger().error(f"加载配置失败: {e}")
            self._set_default_config()

    
    def _test_connection(self):
        """测试规划器连接"""
        try:
            # 简单的测试规划
            test_joints = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
            result = self.moveit_client.plan_to_joints(
                test_joints,
                planning_time=2.0
            )
            
            success = result.get('success', False)
            if success:
                self.get_logger().info(f"✅ 连接测试成功，轨迹点数: {result.get('point_count', 0)}")
            else:
                self.get_logger().warning(f"⚠️ 连接测试失败: {result.get('error_message')}")
            
            return success
        except Exception as e:
            self.get_logger().error(f"连接测试异常: {e}")
            return False
    
    def plan_sync(self, start_state, goal_state, algorithm=None, timeout=5.0):
        """
        同步执行规划 - 使用修复后的MoveIt客户端
        
        Args:
            start_state: 起始状态 {joints: [], pose: {...}}
            goal_state: 目标状态 {joints: [], pose: {...}}
            algorithm: 规划算法名称
            timeout: 规划超时时间
        
        Returns:
            规划结果字典
        """
        start_time = time.time()
        
        try:
            self.get_logger().info(
                f"开始规划: {algorithm or '默认算法'}, 超时={timeout}s"
            )
            
            # 选择算法
            if algorithm is None:
                algorithm = self.config['defaults']['planner']
            
            if algorithm not in self.config['planners']:
                return {
                    "success": False,
                    "error": f"未知算法: {algorithm}",
                    "available_algorithms": list(self.config['planners'].keys()),
                    "error_code": -15  # 无效参数
                }
            
            # 获取MoveIt规划器ID
            planner_config = self.config['planners'][algorithm]
            moveit_planner_id = planner_config.get('moveit_id', algorithm.upper())
            group_name = self.config['defaults'].get('group_name', 'panda_arm')
            
            # 使用真实规划器
            if self.planner_ready and self.moveit_client:
                self.get_logger().info(f"使用真实MoveIt规划器: {moveit_planner_id}")
                
                result = None
                
                if 'joints' in goal_state and goal_state['joints']:
                    # 规划到关节位置
                    result = self.moveit_client.plan_to_joints(
                        target_joints=goal_state['joints'],
                        group_name=group_name,
                        planner_id=moveit_planner_id,
                        planning_time=timeout
                    )
                elif 'pose' in goal_state and goal_state['pose']:
                    # 尝试位姿规划（可能不完全支持）
                    result = self.moveit_client.plan_to_pose(
                        target_pose=goal_state['pose'],
                        group_name=group_name,
                        planner_id=moveit_planner_id,
                        planning_time=timeout
                    )
                else:
                    return {
                        "success": False,
                        "error": "目标状态必须包含joints或pose",
                        "goal_state": goal_state,
                        "error_code": -15  # 无效参数
                    }                # 更新统计信息
                self.planning_stats['total_plans'] += 1
                if result and result.get('success', False):
                    self.planning_stats['successful_plans'] += 1
                self.planning_stats['total_time'] += time.time() - start_time
                
                # 添加算法信息
                if result:
                    result["algorithm"] = algorithm
                    result["moveit_planner_id"] = moveit_planner_id
                    result["planning_mode"] = "real"
                    self.active_algorithm = algorithm
                
                return result if result else {
                    "success": False,
                    "error": "规划器返回空结果",
                    "error_code": -1
                }
            else:
               # 模拟模式
                self.get_logger().warning("使用模拟规划模式")
                result = self._simulate_planning(goal_state, algorithm, timeout)
                result["planning_mode"] = "simulated"
                result["error_code"] = 1 if result.get("success", False) else -1
                return result
            
        except Exception as e:
            self.get_logger().error(f"规划失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "algorithm": algorithm,
                "planning_time": time.time() - start_time,
                "planning_mode": "error",
                "error_code": -1
            }
    
    def _simulate_planning(self, goal_state, algorithm, timeout):
        """模拟规划（当真实规划器不可用时）"""
        # 简单的模拟规划
        import random
        
        simulated_time = min(timeout, random.uniform(0.5, 2.0))
        time.sleep(simulated_time)
        
        # 模拟成功
        result = {
            "success": True,
            "algorithm": algorithm,
            "planning_time": simulated_time,
            "description": "模拟规划成功",
            "simulated": True
        }
        
        return result
    
    def get_interface_status(self):
        """获取接口状态"""
        status = {
            "node_name": self.get_name(),
            "planner_ready": self.planner_ready,
            "planning_mode": "real" if (self.planner_ready and self.moveit_client) else "simulated",
            "active_algorithm": self.active_algorithm,
            "available_algorithms": list(self.config.get('planners', {}).keys()),
            "planning_stats": self.planning_stats.copy(),
            "config_file": self.config_file,
            "timestamp": time.time()
        }
        
        if self.moveit_client:
            status["moveit_service_available"] = self.moveit_client.is_available()
        
        return status
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("OMPL接口节点正在关闭...")
        
        if self.moveit_client:
            self.moveit_client.destroy()
        
        super().destroy_node()


# 测试函数
def test_interface():
    """测试修复后的规划器接口"""
    import rclpy
    
    print("测试修复版OMPL规划器接口...")
    
    rclpy.init()
    planner = OMPLInterface()
    
    # 测试状态获取
    status = planner.get_interface_status()
    print(f"\n规划器状态:")
    print(f"  规划模式: {status['planning_mode']}")
    print(f"  服务可用: {status.get('moveit_service_available', False)}")
    
    # 测试规划
    goal_state = {
        "joints": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
    }
    
    print(f"\n测试规划到关节: {goal_state['joints']}")
    result = planner.plan_sync(
        start_state={"joints": [0]*7},
        goal_state=goal_state,
        algorithm="rrt_connect",
        timeout=3.0
    )
    
    print(f"\n规划结果:")
    print(f"  成功: {result.get('success', False)}")
    print(f"  错误代码: {result.get('error_code', 'N/A')}")
    print(f"  规划模式: {result.get('planning_mode')}")
    print(f"  规划时间: {result.get('planning_time', 0):.2f}s")
    
    if result.get('success', False):
        print(f"  轨迹点数: {result.get('point_count', 0)}")
    
    planner.destroy_node()
    rclpy.shutdown()
    
    return result.get('success', False)


if __name__ == "__main__":
    success = test_interface()
    exit(0 if success else 1)