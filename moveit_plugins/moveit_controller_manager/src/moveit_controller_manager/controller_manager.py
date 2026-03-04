#!/usr/bin/env python3
"""
MoveIt控制器管理器插件
连接MoveIt轨迹执行器到ROS2控制器
"""
from typing import List, Dict, Any, Optional
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory
import time
import os
import json
import sys

# 添加当前模块路径
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
sys.path.insert(0, MODULE_ROOT)

print(f"[MoveIt控制器] 模块路径: {MODULE_ROOT}")

class MoveItControllerManager(Node):
    """MoveIt控制器管理器 - 连接MoveIt到ROS2控制器"""
    
    def __init__(self):
        super().__init__('moveit_controller_manager')
        
        # 🔧 修改：连接到实际的panda控制器
        self.trajectory_client = ActionClient(
            self, 
            FollowJointTrajectory, 
            '/panda_arm_controller/follow_joint_trajectory'  # ❗️修改这里
        )
        
        # 也保留对其他控制器的支持
        self.possible_servers = [
            '/panda_arm_controller/follow_joint_trajectory',
            '/joint_trajectory_controller/follow_joint_trajectory',
            '/position_trajectory_controller/follow_joint_trajectory'
        ]
        
        # 控制器状态
        self.controllers = {}
        self.active_controller = None
        self.server_ready = False
        
        # 加载配置
        self.config_file = os.path.expanduser('~/.moveit_controllers/config.json')
        self._load_config()
        
        self.get_logger().info("MoveIt控制器管理器初始化完成")
        
        # 🔧 添加：自动检测可用服务器
        self._auto_discover_server()
    
    def _auto_discover_server(self):
        """自动发现可用的控制器服务器"""
        self.get_logger().info("自动发现控制器服务器...")
        
        # 创建临时客户端测试每个可能的服务器
        for server in self.possible_servers:
            try:
                temp_client = ActionClient(self, FollowJointTrajectory, server)
                if temp_client.wait_for_server(timeout_sec=1.0):
                    self.get_logger().info(f"✓ 找到可用控制器: {server}")
                    
                    # 如果当前客户端不是连接到这个服务器，重新创建
                    if server != self.trajectory_client._action_name:
                        self.get_logger().info(f"切换到控制器: {server}")
                        self.trajectory_client = ActionClient(self, FollowJointTrajectory, server)
                    
                    self.server_ready = True
                    self.active_controller = server
                    return
                else:
                    self.get_logger().debug(f"控制器不可用: {server}")
                    
            except Exception as e:
                self.get_logger().debug(f"检查控制器失败 {server}: {e}")
        
        self.get_logger().warning("未找到可用的控制器服务器")
        self.server_ready = False
    
    def _load_config(self):
        """加载控制器配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # 🔧 修改：使用panda的关节名
            self.config = {
                "default_controller": "panda_arm_controller",
                "controllers": {
                    "panda_arm_controller": {
                        "type": "FollowJointTrajectory",
                        "action_name": "/panda_arm_controller/follow_joint_trajectory",
                        "joints": [
                            "panda_joint1", "panda_joint2", "panda_joint3", 
                            "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
                        ]
                    },
                    "joint_trajectory_controller": {
                        "type": "FollowJointTrajectory",
                        "action_name": "/joint_trajectory_controller/follow_joint_trajectory",
                        "joints": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
                    }
                }
            }
    def execute_trajectory_sync(self, trajectory: JointTrajectory) -> Dict:
        """同步执行轨迹 - 避免异步问题"""
        import time
        start_time = time.time()
        
        try:
            self.get_logger().info(f"执行轨迹: {len(trajectory.points)}个点")
            
            # 同步等待服务器
            if not self.trajectory_client.wait_for_server(timeout_sec=10.0):
                return {"success": False, "error": "控制器服务器不可用"}
            
            # 创建目标
            goal_msg = FollowJointTrajectory.Goal()
            goal_msg.trajectory = trajectory
            
            # 同步发送目标
            future = self.trajectory_client.send_goal_async(goal_msg)
            
            # 等待发送完成
            rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
            goal_handle = future.result()
            
            if not goal_handle or not goal_handle.accepted:
                return {"success": False, "error": "目标被拒绝"}
            
            # 等待执行结果
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future, timeout_sec=15.0)
            result = result_future.result()
            
            exec_time = time.time() - start_time
            
            if result and hasattr(result, 'result'):
                if result.result.error_code == 0:
                    return {
                        "success": True,
                        "result": "轨迹执行完成",
                        "execution_time": exec_time,
                        "error_code": result.result.error_code,
                        "error_string": result.result.error_string if hasattr(result.result, 'error_string') else ""
                    }
                else:
                    return {
                        "success": False,
                        "error": f"控制器错误: {getattr(result.result, 'error_string', '未知')}",
                        "error_code": result.result.error_code,
                        "execution_time": exec_time
                    }
            else:
                return {
                    "success": True,
                    "result": "轨迹执行完成（无明确结果）",
                    "execution_time": exec_time
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    def get_controller_status(self, controller_name: str = None) -> Dict:
        """获取控制器状态"""
        status = {
            "controller": self.active_controller or "unknown",
            "server_ready": self.server_ready,
            "action_server": self.trajectory_client._action_name if hasattr(self, 'trajectory_client') else 'unknown',
            "timestamp": time.time(),
            "possible_servers": self.possible_servers
        }
        
        # 检查服务器是否真正就绪
        try:
            status["server_check"] = self.trajectory_client.wait_for_server(timeout_sec=1.0)
        except:
            status["server_check"] = False
        
        return status

    # 🔥 添加缺少的销毁方法（重要！）
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("MoveIt控制器管理器正在关闭...")
        super().destroy_node()