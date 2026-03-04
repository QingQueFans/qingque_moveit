#!/bin/bash
# 测试控制器连接

echo "=== 测试控制器连接 ==="
source /opt/ros/humble/setup.bash
cd ~/qingfu_moveit && source install/setup.bash

echo "1. 检查服务..."
ros2 service list | grep -i controller

echo "2. 检查Action服务..."
ros2 action list

echo "3. 直接测试控制器..."
# 创建一个简单的Python脚本测试连接
python3 -c "
import rclpy
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory

rclpy.init()
node = rclpy.create_node('test_client')

client = ActionClient(node, FollowJointTrajectory, '/joint_trajectory_controller/follow_joint_trajectory')
print('等待服务器...')
if client.wait_for_server(timeout_sec=5.0):
    print('✓ 控制器服务器就绪')
else:
    print('✗ 控制器服务器不可用')

node.destroy_node()
rclpy.shutdown()
"