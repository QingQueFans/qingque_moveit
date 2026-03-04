#!/usr/bin/env python3
"""
最简单的轨迹执行脚本
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import numpy as np
import time
import sys

def create_trajectory(points=1):
    """创建轨迹"""
    trajectory = JointTrajectory()
    trajectory.joint_names = [
        'panda_joint1', 'panda_joint2', 'panda_joint3',
        'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
    ]
    
    for i in range(points):
        point = JointTrajectoryPoint()
        point.positions = [0.1 * i] * 7  # 简单递增
        point.time_from_start.sec = i + 1
        trajectory.points.append(point)
    
    return trajectory

def main():
    print("=== 简单轨迹执行 ===")
    
    # 初始化
    rclpy.init()
    node = Node('simple_executor')
    
    try:
        # 连接到控制器
        print("1. 连接到控制器...")
        client = ActionClient(node, FollowJointTrajectory, 
                            '/panda_arm_controller/follow_joint_trajectory')
        
        if not client.wait_for_server(timeout_sec=10.0):
            print("❌ 控制器服务器不可用")
            return 1
        
        print("✅ 控制器就绪")
        
        # 创建轨迹
        print("2. 创建轨迹...")
        trajectory = create_trajectory(points=1)
        print(f"   关节: {trajectory.joint_names}")
        print(f"   点数: {len(trajectory.points)}")
        
        # 发送轨迹
        print("3. 发送轨迹...")
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory = trajectory
        
        start_time = time.time()
        future = client.send_goal_async(goal_msg)
        
        # 等待发送完成
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
        goal_handle = future.result()
        
        if not goal_handle:
            print("❌ 发送失败")
            return 1
        
        if goal_handle.accepted:
            print("✅ 轨迹被接受")
            
            # 等待结果
            print("4. 等待执行结果...")
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(node, result_future, timeout_sec=15.0)
            result = result_future.result()
            
            exec_time = time.time() - start_time
            
            if result:
                if hasattr(result.result, 'error_code') and result.result.error_code == 0:
                    print(f"✅ 执行成功！耗时: {exec_time:.2f}秒")
                    return 0
                else:
                    print(f"❌ 执行失败，错误码: {result.result.error_code}")
                    return 1
            else:
                print("❌ 未收到结果")
                return 1
        else:
            print("❌ 轨迹被拒绝")
            return 1
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    sys.exit(main())