#!/usr/bin/env python3
import rclpy
import time 
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

class CollisionTester(Node):
    def __init__(self):
        super().__init__('collision_tester')
        self.scene_pub = self.create_publisher(PlanningScene, '/planning_scene',10)
        time.sleep(1.0)
        print('碰撞测试开始')
        print("="*50)
    def add_wall_of_boxes(self):
        scene =PlanningScene()
        scene.is_diff = True
        positions= [
            (0.4,0.0,0.3),
            (0.4,0.0,0.5),
            (0.4,0.0,0.7),
            (0.4,-0.1,0.5),
            (0.4,0.1,0.5),
        ]    
        for i,(x,y,z)in enumerate(positions):
            obj = CollisionObject()
            obj.id = f'wall_box_{i}'
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.ADD
            box = SolidPrimitive()
            box.type = SolidPrimitive.BOX
            box.dimensions = [0.08,0.08,0.08]
            pose = Pose()
            pose.position.x = x
            pose.position.y = y
            pose.position.z = z
            pose.orientation.w = 1.0
            obj.primitives.append(box)
            obj.primitive_poses.append(pose)
            scene.world.collision_objects.append(obj)
            print(f'添加box{i+1}:位置（{x:.1f},{y:.1f},{z:.1f}）')
        self.scene_pub.publish(scene)
        print("墙已生成")
        print("尝试机械臂穿过")
        return len(positions)
    def clean_all(self):
        scene =PlanningScene()
        scene.is_diff = True
        for i in range(5):
            obj = CollisionObject()
            obj.id = f'wall_box_{i}'
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.REMOVE
            scene.world.collision_objects.append(obj)
        self.scene_pub.publish(scene)
        print("墙已清除") 

def main():
    rclpy.init()
    tester = CollisionTester()
    try:
        box_count = tester.add_wall_of_boxes()
        print("\n"+"="*50)
        print("拖动并观察，30s")
        for i in range(30,0,-1):
            print(f'剩余时间：{i:2d}',end='\r')
            time.sleep(1)

        print()
        print("\n"+"="*50)
        tester.clean_all()
        print("结束测试")    
        print("="*50)
    except KeyboardInterrupt:
        print("\n 用户中断")
    finally:
        tester.clean_all()
        tester.destroy_node()
        rclpy.shutdown()
if __name__ =='__main__':
    main()            
