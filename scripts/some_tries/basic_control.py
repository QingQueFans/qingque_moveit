#!/usr/bin/env python3
"""
基础机械臂控制 - 已验证可用
使用ROS 2原生Action接口
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
import time

class BasicArmController(Node):
    """基础机械臂控制器"""
    
    def __init__(self):
        super().__init__('basic_arm_controller')
        
        # Panda关节名称
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6',
            'panda_joint7'
        ]
        
        # 创建动作客户端
        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/panda_arm_controller/follow_joint_trajectory'
        )
    
    def is_connected(self):
        """检查是否连接到控制器"""
        return self._action_client.wait_for_server(timeout_sec=3.0)
    
    def move_to_joints(self, joint_positions, duration=3.0):
        """
        移动机械臂到指定关节位置
        
        参数:
            joint_positions: 7个关节角度（弧度）
            duration: 运动时间（秒）
        """
        if not self.is_connected():
            self.get_logger().error("未连接到机械臂控制器")
            return False
        
        # 创建目标消息
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        # 创建轨迹点
        point = JointTrajectoryPoint()
        point.positions = joint_positions
        point.time_from_start.sec = int(duration)
        
        goal_msg.trajectory.points.append(point)
        
        # 发送并等待
        future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future)
        
        return future.result() is not None

# ============ 预定义位置 ============
PANDA_HOME = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
PANDA_POSITION_1 = [0.5, -0.785, 0.0, -2.0, 0.0, 1.571, 0.785]
PANDA_POSITION_2 = [-0.5, -0.785, 0.0, -2.356, 0.0, 2.0, 0.785]

def demo_sequence():
    """演示序列：Home → 位置1 → 位置2 → Home"""
    print("🤖 Panda机械臂控制演示")
    print("=" * 50)
    
    rclpy.init()
    controller = BasicArmController()
    
    try:
        # 检查连接
        print("检查连接...")
        if not controller.is_connected():
            print("❌ 请先启动Panda演示")
            print("运行: ros2 launch moveit_resources_panda_moveit_config demo.launch.py")
            return
        
        print("✅ 连接成功")
        
        # 演示序列
        positions = [
            ("Home", PANDA_HOME),
            ("位置1", PANDA_POSITION_1),
            ("位置2", PANDA_POSITION_2),
            ("返回Home", PANDA_HOME)
        ]
        
        for name, joints in positions:
            print(f"\n移动到: {name}")
            print(f"关节角度: {[round(j, 3) for j in joints]}")
            
            if controller.move_to_joints(joints, 4.0):
                print(f"✅ {name} 到达成功")
                if name != "返回Home":
                    time.sleep(2)  # 等待2秒
            else:
                print(f"❌ {name} 到达失败")
                break
        
        print("\n" + "=" * 50)
        print("🎉 演示完成！")
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    demo_sequence()
