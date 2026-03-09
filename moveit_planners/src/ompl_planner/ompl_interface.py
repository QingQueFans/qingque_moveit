#!/usr/bin/env python3
"""
OMPL规划器接口 - pymoveit2 适配版
"""
import rclpy
from rclpy.node import Node
import time
import yaml
import os
import sys

from pymoveit2 import MoveIt2
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class OMPLInterface(Node):
    """
    OMPL规划器接口 - pymoveit2 适配版
    
    这个类现在作为 pymoveit2 的轻量封装，保持原有接口不变
    但底层实现由 pymoveit2 接管
    """
    
    def __init__(self, node_name="ompl_planner_interface"):
        super().__init__(node_name)
        
        # 配置路径
        self.config_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
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
        
        # 初始化 pymoveit2
        try:
            self.moveit2 = MoveIt2(
                node=self,
                joint_names=["panda_joint1", "panda_joint2", "panda_joint3",
                           "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"],
                base_link_name="panda_link0",
                end_effector_name="panda_hand",
                group_name="panda_arm"
            )
            self.planner_ready = True
            self.get_logger().info("✅ pymoveit2 规划器就绪")
            
            # 测试连接
            self._test_connection()
            
        except Exception as e:
            self.get_logger().error(f"初始化 pymoveit2 失败: {e}")
            self.planner_ready = False
        
        self.get_logger().info(f"OMPL规划器接口初始化完成")
        self.get_logger().info(f"真实规划: {'可用' if self.planner_ready else '模拟模式'}")
    
    def _load_config(self):
        """加载配置 - 保留原样"""
        try:
            workspace_path = os.environ.get('QINGFU_MOVEIT_PATH', 
                                        os.path.expanduser('~/qingfu_moveit/moveit_planners'))
            
            possible_paths = [
                "/home/diyuanqiongyu/qingfu_moveit/moveit_planners/config/ompl_planners.yaml",
                os.path.join(os.path.dirname(__file__), 
                            '..', '..', '..', 'config', 'ompl_planners.yaml'),
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
            
            self.get_logger().warning("未找到配置文件，使用默认配置")
            self._set_default_config()
            
        except Exception as e:
            self.get_logger().error(f"加载配置失败: {e}")
            self._set_default_config()
    
    def _set_default_config(self):
        """设置默认配置"""
        self.config = {
            'defaults': {
                'planner': 'rrt_connect',
                'group_name': 'panda_arm'
            },
            'planners': {
                'rrt_connect': {'moveit_id': 'RRTConnect'},
                'rrt_star': {'moveit_id': 'RRTstar'},
                'prm': {'moveit_id': 'PRM'}
            }
        }
    
    def _test_connection(self):
        """测试规划器连接"""
        try:
            test_joints = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
            
            # 用 plan 测试
            trajectory = self.moveit2.plan(
                joint_positions=test_joints,
                tolerance=0.01,
                weight=1.0
            )
            
            if trajectory is not None:
                self.get_logger().info(f"✅ 连接测试成功")
                return True
            else:
                self.get_logger().warning(f"⚠️ 连接测试失败")
                return False
            
        except Exception as e:
            self.get_logger().error(f"连接测试异常: {e}")
            return False
    
    def plan_sync(self, start_state, goal_state, algorithm=None, timeout=5.0):
        """同步执行规划 - 用 pymoveit2 的 plan 方法"""
        print("\n" + "="*60)
        print("[PLAN_SYNC] 开始执行")
        print(f"[PLAN_SYNC] goal_state: {goal_state}")
        print(f"[PLAN_SYNC] algorithm: {algorithm}")
        print("="*60)
        
        start_time = time.time()
        
        try:
            print("[PLAN_SYNC] 1. 进入 try 块")
            
            self.get_logger().info(
                f"开始规划: {algorithm or '默认算法'}, 超时={timeout}s"
            )
            
            print("[PLAN_SYNC] 2. 选择算法")
            if algorithm is None:
                algorithm = self.config['defaults']['planner']
            
            print(f"[PLAN_SYNC] 3. 选择的算法: {algorithm}")
            
            if algorithm not in self.config['planners']:
                print(f"[PLAN_SYNC] 算法不在配置中: {algorithm}")
                return {
                    "success": False,
                    "error": f"未知算法: {algorithm}",
                    "available_algorithms": list(self.config['planners'].keys()),
                    "error_code": -15
                }
            
            print("[PLAN_SYNC] 4. 设置 planner_id")
            self.moveit2.planner_id = self.config['planners'][algorithm].get('moveit_id', algorithm.upper())
            
            if self.planner_ready:
                print("[PLAN_SYNC] 5. planner_ready 为 True")
                
                success = False
                trajectory = None
                
                if 'joints' in goal_state and goal_state['joints']:
                    print(f"[PLAN_SYNC] 6. 关节模式，目标: {goal_state['joints']}")
                    
                    try:
                        print("[PLAN_SYNC] 7. 准备调用 moveit2.plan")
                        
                        # 这里打印一下 moveit2 对象的状态
                        print(f"[PLAN_SYNC] moveit2 对象: {self.moveit2}")
                        print(f"[PLAN_SYNC] moveit2.planner_id: {self.moveit2.planner_id}")
                        
                        import time
                        time.sleep(0.1)  # 小延时
                        
                        print("[PLAN_SYNC] 8. 正在调用 plan...")
                        
                        trajectory = self.moveit2.plan(
                            joint_positions=goal_state['joints'],
                            tolerance=0.01,
                            weight=1.0
                        )
                        
                        print(f"[PLAN_SYNC] 9. plan 返回: {trajectory}")
                        print(f"[PLAN_SYNC] 10. trajectory 类型: {type(trajectory)}")
                        
                        success = trajectory is not None
                        
                        if success:
                            print(f"[PLAN_SYNC] 11. 成功，轨迹点数: {len(trajectory.points)}")
                        else:
                            print("[PLAN_SYNC] 11. 失败，trajectory 为 None")
                            
                    except Exception as e:
                        print(f"[PLAN_SYNC] ❌ 规划异常: {e}")
                        import traceback
                        traceback.print_exc()
                        success = False
                        trajectory = None
                    
                elif 'pose' in goal_state and goal_state['pose']:
                    print("[PLAN_SYNC] 6. 位姿模式")
                    # ... 位姿处理代码 ...
                    
                else:
                    print("[PLAN_SYNC] 目标状态格式错误")
                    return {
                        "success": False,
                        "error": "目标状态必须包含joints或pose",
                        "goal_state": goal_state,
                        "error_code": -15
                    }
                
                print("[PLAN_SYNC] 12. 构建返回结果")
                
                result = {
                    "success": success,
                    "algorithm": algorithm,
                    "moveit_planner_id": self.moveit2.planner_id,
                    "planning_mode": "real",
                    "planning_time": time.time() - start_time,
                    "error_code": 1 if success else -1
                }
                
                if success and trajectory:
                    result["trajectory"] = trajectory
                    result["point_count"] = len(trajectory.points) if hasattr(trajectory, 'points') else 0
                
                print(f"[PLAN_SYNC] 13. 返回结果: success={success}")
                print("="*60 + "\n")
                
                return result
            
            else:
                print("[PLAN_SYNC] planner_ready 为 False，使用模拟模式")
                # ... 模拟模式代码 ...
                
        except Exception as e:
            print(f"[PLAN_SYNC] 顶层异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "algorithm": algorithm,
                "planning_time": time.time() - start_time,
                "planning_mode": "error",
                "error_code": -1
            }
        
    def _simulate_planning(self, goal_state, algorithm, timeout):
        """模拟规划（保留原样）"""
        import random
        
        simulated_time = min(timeout, random.uniform(0.5, 2.0))
        time.sleep(simulated_time)
        
        # 模拟轨迹
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
        traj = JointTrajectory()
        traj.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        point = JointTrajectoryPoint()
        if 'joints' in goal_state:
            point.positions = goal_state['joints']
        else:
            point.positions = [0.0] * 7
        point.time_from_start.sec = 2
        traj.points = [point]
        
        result = {
            "success": True,
            "algorithm": algorithm,
            "planning_time": simulated_time,
            "description": "模拟规划成功",
            "simulated": True,
            "trajectory": traj,
            "point_count": 1
        }
        
        return result
    
    def get_interface_status(self):
        """获取接口状态"""
        status = {
            "node_name": self.get_name(),
            "planner_ready": self.planner_ready,
            "planning_mode": "real" if self.planner_ready else "simulated",
            "active_algorithm": self.active_algorithm,
            "available_algorithms": list(self.config.get('planners', {}).keys()),
            "planning_stats": self.planning_stats.copy(),
            "config_file": self.config_file,
            "timestamp": time.time()
        }
        
        return status
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("OMPL接口节点正在关闭...")
        super().destroy_node()


# 测试函数
def test_interface():
    """测试规划器接口"""
    import rclpy
    
    print("测试 OMPL规划器接口 (pymoveit2版)...")
    
    rclpy.init()
    planner = OMPLInterface()
    
    # 测试状态获取
    status = planner.get_interface_status()
    print(f"\n规划器状态:")
    print(f"  规划模式: {status['planning_mode']}")
    
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