#!/usr/bin/env python3
"""
最简化：真实添加Box到MoveIt规划场景
只做一件事：生成一个真实的碰撞Box
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose
import time

class SimpleBox(Node):
    def __init__(self):
        super().__init__('simple_box')
        # 只创建一个发布器
        self.pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        time.sleep(1)  # 等待连接
        
    def add_box(self):
        """添加一个Box到世界"""
        scene = PlanningScene()
        scene.is_diff = True
        
        # 创建碰撞物体
        obj = CollisionObject()
        obj.id = "my_real_box"  # 物体ID
        obj.header.frame_id = "world"  # 世界坐标系
        obj.operation = CollisionObject.ADD
        
        # 创建Box形状
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.1, 0.1, 0.1]  # 10cm立方体
        
        # 设置Box位置（世界坐标系）
        box_pose = Pose()
        box_pose.position.x = 0.4   # X位置
        box_pose.position.y = 0.0   # Y位置  
        box_pose.position.z = 0.5   # Z位置（离地面0.5米）
        box_pose.orientation.w = 1.0  # 无旋转
        
        # 添加到物体
        obj.primitives.append(box)
        obj.primitive_poses.append(box_pose)
        
        # 添加到场景
        scene.world.collision_objects.append(obj)
        
        # 发布
        self.pub.publish(scene)
        print("✅ 真实Box已添加到MoveIt规划场景")
        print("   位置: (0.4, 0.0, 0.5)")
        print("   尺寸: 0.1x0.1x0.1米")
        
    def remove_box(self):
        """移除Box"""
        scene = PlanningScene()
        scene.is_diff = True
        
        obj = CollisionObject()
        obj.id = "my_real_box"
        obj.header.frame_id = "world"
        obj.operation = CollisionObject.REMOVE
        
        scene.world.collision_objects.append(obj)
        self.pub.publish(scene)
        print("✅ Box已从规划场景移除")

def main():
    rclpy.init()
    box = SimpleBox()
    
    try:
        print("添加真实Box到MoveIt...")
        box.add_box()
        
        print("\n保持Box 10秒...")
        print("在RViz中应该能看到一个半透明的Box")
        print("尝试让机械臂碰撞它，MoveIt会检测到碰撞")
        
        for i in range(10, 0, -1):
            print(f"剩余: {i}秒")
            time.sleep(1)
            
    finally:
        print("\n清理...")
        box.remove_box()
        box.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
