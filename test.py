#!/usr/bin/env python3
"""
测试关节数量一致性
"""
from trajectory_execution import TrajectoryExecutionManager

# 创建执行器
executor = TrajectoryExecutionManager()

# 测试1：检查默认关节数
print(f"测试1：轨迹执行器关节配置")
print(f"  从代码看：需要7个关节（panda_joint1..7）")

# 测试2：查看实际执行时的关节数
try:
    # 创建一个测试轨迹
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
    import rclpy
    
    trajectory = JointTrajectory()
    trajectory.joint_names = executor.robot_config.get("joint_names", [])
    print(f"  实际关节名称: {trajectory.joint_names}")
    print(f"  关节数量: {len(trajectory.joint_names)}")
    
except Exception as e:
    print(f"  错误: {e}")