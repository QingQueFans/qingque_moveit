#!/usr/bin/env python3
"""
清除墙
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject

class WallCleaner(Node):
    def __init__(self):
        super().__init__('wall_cleaner')
        self.scene_pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
    
    def clear_wall(self):
        """清除五个箱子的墙"""
        scene = PlanningScene()
        scene.is_diff = True
        
        # 清除所有我们可能创建的box
        for i in range(1, 6):
            obj = CollisionObject()
            obj.id = f"wall_box_{i}"
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.REMOVE
            scene.world.collision_objects.append(obj)
        
        # 也清除可能用其他名字创建的box
        other_names = ["box1", "box2", "box3", "box4", "box5"]
        for name in other_names:
            obj = CollisionObject()
            obj.id = name
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.REMOVE
            scene.world.collision_objects.append(obj)
        
        self.scene_pub.publish(scene)
        print("✅ 所有墙已从场景中清除")

def main():
    rclpy.init()
    cleaner = WallCleaner()
    
    try:
        print("🧹 清除五个箱子的墙")
        print("="*50)
        
        cleaner.clear_wall()
        
        print("\n墙已清除。在RViz中应该看不到箱子了。")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        cleaner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
