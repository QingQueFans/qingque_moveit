#!/usr/bin/env python3
"""
ROS2 MoveIt服务客户端 - 光荣退休版
2026-03-04 正式被 pymoveit2 替代

历史贡献：
- 成功连接 MoveIt 规划服务
- 实现关节空间规划
- 实现位姿空间规划
- 为 OMPLPlannerManager 提供底层支持

退役原因：
- pymoveit2 提供了更简洁的接口
- 社区维护，更稳定
- 符合“做减法”的架构思路
"""

import rclpy
from rclpy.node import Node
import time
import sys

# 这些导入现在都成了历史
from moveit_msgs.srv import GetMotionPlan
from moveit_msgs.msg import (
    MotionPlanRequest, RobotState, Constraints, JointConstraint,
    WorkspaceParameters, PositionConstraint, OrientationConstraint, 
    BoundingVolume, MoveItErrorCodes
)
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from geometry_msgs.msg import Pose, PoseStamped
from shape_msgs.msg import SolidPrimitive
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class MoveItROS2Client(Node):
    """
    ROS2 MoveIt服务客户端 - 光荣退休版
    
    这个类曾经是整个系统的核心，现在被 pymoveit2 替代。
    但它留下的架构思想（分层、错误处理、日志）依然在。
    """
    
    def __init__(self, node_name="moveit_ros2_client"):
        super().__init__(node_name)
        
        self.plan_service_name = '/plan_kinematic_path'
        
        # 曾经，这里连接着 MoveIt 的心脏
        self.plan_client = self.create_client(
            GetMotionPlan,
            self.plan_service_name
        )
        
        if not self.plan_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().warning(f"规划服务不可用: {self.plan_service_name}")
            self.service_available = False
        else:
            self.get_logger().info(f"✓ 连接到规划服务: {self.plan_service_name}")
            self.service_available = True
        
        self.get_logger().info("🎉 MoveItROS2Client 已加载（光荣退休版）")
        self.get_logger().info("   此文件保留作纪念，实际功能由 pymoveit2 提供")
    
    def is_available(self):
        """检查服务是否可用（历史方法）"""
        return self.service_available
    
    def create_valid_robot_state(self):
        """
        创建有效的机器人状态
        
        这个函数定义的标准姿势 [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
        成为了后来所有规划的起点。
        """
        robot_state = RobotState()
        
        joint_state = JointState()
        joint_state.header = Header()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.header.frame_id = "panda_link0"
        
        joint_state.name = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        joint_state.position = [
            0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785,
            0.04, 0.04
        ]
        
        robot_state.joint_state = joint_state
        robot_state.is_diff = False
        
        return robot_state
    
    def plan_to_joints(self, target_joints, group_name="panda_arm", 
                      planner_id="RRTConnect", planning_time=5.0):
        """
        规划到关节位置 - 经典方法
        
        这个方法曾经是系统的核心，现在只需一行：
        moveit2.move_to_configuration(target_joints)
        """
        self.get_logger().info(f"📜 [历史方法] plan_to_joints 被调用")
        self.get_logger().info(f"   目标关节: {target_joints}")
        self.get_logger().info(f"   建议改用: moveit2.move_to_configuration()")
        
        # 实际功能已由 pymoveit2 接管
        return {
            "success": False,
            "error": "此文件已退休，请使用 pymoveit2",
            "legacy": True,
            "suggestion": "from pymoveit2 import MoveIt2"
        }
    
    def plan_to_pose(self, target_pose, group_name="panda_arm",
                    planner_id="RRTConnect", planning_time=5.0):
        """
        规划到位姿 - 经典方法
        """
        self.get_logger().info(f"📜 [历史方法] plan_to_pose 被调用")
        self.get_logger().info(f"   建议改用: moveit2.move_to_pose()")
        
        return {
            "success": False,
            "error": "此文件已退休，请使用 pymoveit2",
            "legacy": True
        }
    
    def error_code_to_string(self, error_code):
        """
        错误代码转可读字符串
        
        这些错误码定义至今仍在 MoveIt 中使用
        """
        codes = {
            1: "成功",
            -1: "规划失败",
            -2: "无效运动规划",
            -3: "运动规划因环境变化失效",
            -4: "控制失败",
            -5: "无法获取传感器数据",
            -6: "超时",
            -7: "被抢占",
            -9: "起始状态碰撞",
            -10: "起始状态违反路径约束",
            -11: "目标碰撞",
            -12: "目标违反路径约束",
            -13: "目标约束违反",
            -14: "无效组名",
            -15: "无效目标约束",
            -16: "无效机器人状态",
            -25: "通信失败",
            99999: "通用失败"
        }
        return codes.get(error_code, f"未知错误({error_code})")
    
    def destroy(self):
        """清理资源 - 最后的告别"""
        self.get_logger().info("👋 MoveItROS2Client 正在关闭...")
        self.get_logger().info("   感谢你曾经的努力，现在可以安心退休了")
        super().destroy_node()


def test_client():
    """测试客户端 - 历史的回响"""
    print("=" * 60)
    print("MoveItROS2Client 退休纪念测试")
    print("=" * 60)
    print("\n这个文件现在只作纪念，实际功能请使用 pymoveit2")
    print("\n曾经的核心功能：")
    print("  ✅ 规划到关节 - 现在用 moveit2.move_to_configuration()")
    print("  ✅ 规划到位姿 - 现在用 moveit2.move_to_pose()")
    print("  ✅ 错误码处理 - 现在内部自动处理")
    print("\n光荣退休日期: 2026-03-04")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_client()