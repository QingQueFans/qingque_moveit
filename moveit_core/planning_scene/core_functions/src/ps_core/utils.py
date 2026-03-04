#!/usr/bin/env python3
"""
工具函数 - 简化版
"""
from geometry_msgs.msg import Pose, Point, Quaternion

def create_pose(x=0.0, y=0.0, z=0.0, qx=0.0, qy=0.0, qz=0.0, qw=1.0) -> Pose:
    """创建位姿"""
    pose = Pose()
    pose.position = Point(x=x, y=y, z=z)
    pose.orientation = Quaternion(x=qx, y=qy, z=qz, w=qw)
    return pose

def print_pose(pose: Pose, name: str = "位姿"):
    """打印位姿"""
    print(f"{name}:")
    print(f"  位置: [{pose.position.x:.3f}, {pose.position.y:.3f}, {pose.position.z:.3f}]")
    print(f"  姿态: [{pose.orientation.x:.3f}, {pose.orientation.y:.3f}, "
          f"{pose.orientation.z:.3f}, {pose.orientation.w:.3f}]")

def list_to_string(lst: list) -> str:
    """列表转字符串"""
    return ', '.join(f'{x:.3f}' for x in lst)

def check_ros_running() -> bool:
    """检查 ROS 是否运行"""
    try:
        import rclpy
        return rclpy.ok()
    except:
        return False