#!/usr/bin/env python3
"""
MoveIt控制器管理器 - pymoveit2 版
"""
from typing import List, Dict, Any, Optional
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
import time
import os
import json
import sys

from pymoveit2 import MoveIt2

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
sys.path.insert(0, MODULE_ROOT)

print(f"[MoveIt控制器] 模块路径: {MODULE_ROOT}")

class MoveItControllerManager(Node):
    """
    MoveIt控制器管理器 - pymoveit2 版
    
    现在底层使用 pymoveit2 的 execute 方法
    保持原有接口不变
    """
    
    def __init__(self, moveit2: MoveIt2 = None):
        super().__init__('moveit_controller_manager')
        
        self.moveit2 = moveit2
        
        # 如果没有传入 moveit2，尝试创建
        if self.moveit2 is None:
            try:
                self.moveit2 = MoveIt2(
                    node=self,
                    joint_names=["panda_joint1", "panda_joint2", "panda_joint3",
                               "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"],
                    base_link_name="panda_link0",
                    end_effector_name="panda_hand",
                    group_name="panda_arm"
                )
            except Exception as e:
                self.get_logger().error(f"创建 MoveIt2 失败: {e}")
        
        # 保留原有状态变量
        self.controllers = {}
        self.active_controller = None
        self.server_ready = False
        
        # 加载配置（保留，可能用于信息查询）
        self.config_file = os.path.expanduser('~/.moveit_controllers/config.json')
        self._load_config()
        
        self.get_logger().info("MoveIt控制器管理器初始化完成 (pymoveit2版)")
    
    def _load_config(self):
        """加载控制器配置（保留原样，只作信息用）"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
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
                    }
                }
            }
    
    def execute_trajectory_sync(self, trajectory: JointTrajectory) -> Dict:
        """同步执行轨迹 - pymoveit2 正确用法"""
        start_time = time.time()
        
        try:
            if not self.moveit2:
                return {"success": False, "error": "moveit2 未初始化"}
            
            # 直接调用，不检查返回值
            self.moveit2.execute(
                trajectory=trajectory,
                controllers=['joint_trajectory_controller']
            )
            
            return {
                "success": True,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    def get_controller_status(self, controller_name: str = None) -> Dict:
        """
        获取控制器状态
        
        现在通过 pymoveit2 内部状态获取
        """
        status = {
            "controller": "panda_arm_controller",
            "server_ready": self.moveit2 is not None,
            "action_server": "/panda_arm_controller/follow_joint_trajectory",
            "timestamp": time.time(),
            "possible_servers": ["/panda_arm_controller/follow_joint_trajectory"],
            "using_pymoveit2": True
        }
        
        return status
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("MoveIt控制器管理器正在关闭...")
        super().destroy_node()


# 测试函数
def test_controller():
    """测试控制器"""
    import rclpy
    
    print("测试 MoveIt控制器管理器 (pymoveit2版)...")
    
    rclpy.init()
    controller = MoveItControllerManager()
    
    status = controller.get_controller_status()
    print(f"控制器状态: {status}")
    
    controller.destroy_node()
    rclpy.shutdown()
    
    return True


if __name__ == "__main__":
    test_controller()