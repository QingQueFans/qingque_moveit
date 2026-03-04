#!/usr/bin/env python3
"""
Panda夹爪控制器管理器
控制Panda机器人的夹爪开合 - 基于机械臂控制器的同步模式
"""
from typing import Dict, Any, Optional
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import GripperCommand
import time
import os
import json
import sys

# 添加当前模块路径
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
sys.path.insert(0, MODULE_ROOT)

print(f"[夹爪控制器] 模块路径: {MODULE_ROOT}")

class GripperControllerManager(Node):
    """Panda夹爪控制器管理器 - 控制夹爪开合"""
    
    def __init__(self):
        super().__init__('panda_gripper_controller')
        
        # 连接到Panda夹爪控制器
        self.gripper_client = ActionClient(
            self,
            GripperCommand,
            '/panda_hand_controller/gripper_cmd'  # Panda夹爪Action接口
        )
        
        # 可能的夹爪服务器
        self.possible_servers = [
            '/panda_hand_controller/gripper_cmd',
            '/franka_gripper/grasp',  # Franka Panda常用接口
            '/gripper_controller/gripper_action'
        ]
        
        # 夹爪状态
        self.gripper_ready = False
        self.current_width = 0.0  # 当前夹爪宽度
        self.current_effort = 0.0  # 当前夹持力
        self.active_server = None
        
        # 加载配置
        self.config_file = os.path.expanduser('~/.moveit_controllers/gripper_config.json')
        self._load_config()
        
        self.get_logger().info("Panda夹爪控制器初始化完成")
        
        # 自动检测服务器
        self._auto_discover_server()
    
    def _auto_discover_server(self):
        """自动发现夹爪控制器服务器 - 完全复制机械臂模式"""
        self.get_logger().info("自动发现夹爪控制器...")
        
        for server in self.possible_servers:
            try:
                temp_client = ActionClient(self, GripperCommand, server)
                if temp_client.wait_for_server(timeout_sec=1.0):
                    self.get_logger().info(f"✓ 找到夹爪控制器: {server}")
                    
                    if server != self.gripper_client._action_name:
                        self.get_logger().info(f"切换到夹爪控制器: {server}")
                        self.gripper_client = ActionClient(self, GripperCommand, server)
                    
                    self.gripper_ready = True
                    self.active_server = server
                    return
                    
            except Exception as e:
                self.get_logger().debug(f"检查夹爪控制器失败 {server}: {e}")
        
        self.get_logger().warning("未找到夹爪控制器服务器")
        self.gripper_ready = False
    
    def _load_config(self):
        """加载夹爪配置 - 基于机械臂配置模式"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # 默认Panda夹爪配置
            self.config = {
                "default_gripper": "panda_hand_controller",
                "grippers": {
                    "panda_hand_controller": {
                        "type": "GripperActionController",
                        "action_name": "/panda_hand_controller/gripper_cmd",
                        "joints": ["panda_finger_joint1", "panda_finger_joint2"],
                        "max_width": 0.04,
                        "min_width": 0.0,
                        "max_effort": 50.0
                    }
                }
            }
    
    def grasp_sync(self, width: float = 0.0, effort: float = 30.0) -> Dict:
        """同步执行夹爪闭合 - 完全复制机械臂的同步模式"""
        start_time = time.time()
        
        try:
            self.get_logger().info(f"夹爪闭合: width={width}m, effort={effort}N")
            
            # 同步等待服务器 - 与机械臂完全一致
            if not self.gripper_client.wait_for_server(timeout_sec=10.0):
                return {"success": False, "error": "夹爪控制器不可用"}
            
            # 创建夹爪命令
            goal_msg = GripperCommand.Goal()
            goal_msg.command.position = float(width)
            goal_msg.command.max_effort = float(effort)
            
            # 同步发送目标 - 完全复制机械臂模式
            future = self.gripper_client.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
            goal_handle = future.result()
            
            if not goal_handle or not goal_handle.accepted:
                return {"success": False, "error": "夹爪命令被拒绝"}            # 等待执行结果 - 与机械臂完全一致
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future, timeout_sec=10.0)
            result = result_future.result()
            
            exec_time = time.time() - start_time
            
            if result:
                self.current_width = width
                self.current_effort = effort
                
                return {
                    "success": True,
                    "result": "夹爪闭合完成",
                    "execution_time": exec_time,
                    "width": width,
                    "effort": effort,
                    "stalled": result.result.stalled,
                    "reached_goal": result.result.reached_goal
                }
            else:
                return {
                    "success": True,
                    "result": "夹爪执行完成（无明确结果）",
                    "execution_time": exec_time
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def release_sync(self, width: float = 0.04, effort: float = 10.0) -> Dict:
        """同步执行夹爪张开"""
        try:
            self.get_logger().info(f"夹爪张开: width={width}m")
            return self.grasp_sync(width, effort)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def move_gripper_sync(self, width: float, effort: float = 20.0) -> Dict:
        """移动夹爪到指定宽度"""
        try:
            self.get_logger().info(f"移动夹爪: width={width}m")
            return self.grasp_sync(width, effort)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_gripper_status(self) -> Dict:
        """获取夹爪状态 - 基于机械臂状态模式"""
        status = {
            "server_ready": self.gripper_ready,
            "active_server": self.active_server,
            "action_server": self.gripper_client._action_name if hasattr(self, 'gripper_client') else 'unknown',
            "current_width": self.current_width,
            "current_effort": self.current_effort,
            "timestamp": time.time(),
            "possible_servers": self.possible_servers
        }
        
        # 检查服务器是否真正就绪 - 与机械臂完全一致
        try:
            status["server_check"] = self.gripper_client.wait_for_server(timeout_sec=1.0)
        except:
            status["server_check"] = False
        
        return status
    
    def destroy_node(self):
        """清理资源 - 完全复制机械臂模式"""
        self.get_logger().info("夹爪控制器管理器正在关闭...")
        super().destroy_node()