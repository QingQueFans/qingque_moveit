#!/usr/bin/env python3
"""
Panda夹爪控制器管理器 - pymoveit2 版
"""
from typing import Dict, Any, Optional
import rclpy
from rclpy.node import Node
import time
import os
import json
import sys

from pymoveit2 import MoveIt2Gripper

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
sys.path.insert(0, MODULE_ROOT)

print(f"[夹爪控制器] 模块路径: {MODULE_ROOT}")

class GripperControllerManager(Node):
    """
    Panda夹爪控制器管理器 - pymoveit2 版
    
    底层使用 MoveIt2Gripper，保持原有接口不变
    """
    
    def __init__(self):
        super().__init__('panda_gripper_controller')
        
        # 初始化 pymoveit2 夹爪
        try:
            self.gripper = MoveIt2Gripper(
                node=self,
                gripper_joint_names=["panda_finger_joint1", "panda_finger_joint2"],
                open_gripper_joint_positions=[0.04, 0.04],
                closed_gripper_joint_positions=[0.0, 0.0],
                gripper_group_name="hand"
            )
            self.gripper_ready = True
            self.get_logger().info("✅ pymoveit2 夹爪控制器就绪")
        except Exception as e:
            self.get_logger().error(f"初始化夹爪失败: {e}")
            self.gripper_ready = False
        
        # 保留原有状态变量
        self.current_width = 0.0
        self.current_effort = 0.0
        self.active_server = "/panda_hand_controller/gripper_cmd"
        self.possible_servers = [
            '/panda_hand_controller/gripper_cmd',
            '/franka_gripper/grasp',
            '/gripper_controller/gripper_action'
        ]
        
        # 加载配置（保留，可能用于信息查询）
        self.config_file = os.path.expanduser('~/.moveit_controllers/gripper_config.json')
        self._load_config()
        
        self.get_logger().info("Panda夹爪控制器初始化完成 (pymoveit2版)")
    
    def _load_config(self):
        """加载夹爪配置（保留原样）"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
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
        """同步执行夹爪闭合 - pymoveit2 正确用法"""
        start_time = time.time()
        
        try:
            if not self.gripper:
                return {"success": False, "error": "夹爪未初始化"}
            
            # 根据宽度决定开合
            if width == 0.0:
                self.gripper.close()
            else:
                self.gripper.open() if width >= 0.04 else self.gripper.move_to_position(width)
            
            self.current_width = width
            self.current_effort = effort
            
            return {
                "success": True,
                "execution_time": time.time() - start_time,
                "width": width,
                "effort": effort
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
        """获取夹爪状态"""
        status = {
            "server_ready": self.gripper_ready,
            "active_server": self.active_server,
            "action_server": self.active_server,
            "current_width": self.current_width,
            "current_effort": self.current_effort,
            "timestamp": time.time(),
            "possible_servers": self.possible_servers,
            "using_pymoveit2": True,
            "is_open": self.gripper.is_open if self.gripper else None
        }
        
        return status
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("夹爪控制器管理器正在关闭...")
        super().destroy_node()


# 测试函数
def test_gripper():
    """测试夹爪控制器"""
    import rclpy
    
    print("测试夹爪控制器管理器 (pymoveit2版)...")
    
    rclpy.init()
    gripper = GripperControllerManager()
    
    status = gripper.get_gripper_status()
    print(f"夹爪状态: {status}")
    
    # 测试开合
    print("\n测试夹爪张开...")
    result = gripper.release_sync()
    print(f"结果: {result}")
    
    time.sleep(1)
    
    print("\n测试夹爪闭合...")
    result = gripper.grasp_sync()
    print(f"结果: {result}")
    
    gripper.destroy_node()
    rclpy.shutdown()
    
    return True


if __name__ == "__main__":
    test_gripper()