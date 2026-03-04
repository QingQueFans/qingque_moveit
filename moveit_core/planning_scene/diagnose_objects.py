#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPlanningScene
import sys

class ObjectDiagnoser(Node):
    def __init__(self):
        super().__init__('object_diagnoser')
        self.cli = self.create_client(GetPlanningScene, '/get_planning_scene')
        
    def diagnose(self):
        while not self.cli.wait_for_service(timeout_sec=1.0):
            print('等待服务...')
        
        req = GetPlanningScene.Request()
        future = self.cli.call_async(req)
        
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            result = future.result()
            scene = result.scene
            
            print(f"场景中物体数量: {len(scene.world.collision_objects)}")
            print("=" * 60)
            
            for obj in scene.world.collision_objects:
                print(f"物体: {obj.id}")
                print(f"  类型: {obj.type}")
                print(f"  操作: {obj.operation}")
                print(f"  有 primitives 属性: {hasattr(obj, 'primitives')}")
                if hasattr(obj, 'primitives'):
                    print(f"  primitives 数量: {len(obj.primitives) if obj.primitives else 0}")
                    if obj.primitives and len(obj.primitives) > 0:
                        prim = obj.primitives[0]
                        print(f"    形状类型: {prim.type} (1=BOX)")
                        if hasattr(prim, 'dimensions'):
                            print(f"    尺寸: {prim.dimensions}")
                
                print(f"  有 primitive_poses 属性: {hasattr(obj, 'primitive_poses')}")
                if hasattr(obj, 'primitive_poses'):
                    print(f"  primitive_poses 数量: {len(obj.primitive_poses) if obj.primitive_poses else 0}")
                    if obj.primitive_poses and len(obj.primitive_poses) > 0:
                        pose = obj.primitive_poses[0]
                        print(f"    位置: ({pose.position.x:.3f}, {pose.position.y:.3f}, {pose.position.z:.3f})")
                
                print(f"  有 pose 属性: {hasattr(obj, 'pose')}")
                if hasattr(obj, 'pose') and obj.pose:
                    print(f"    整体位置: ({obj.pose.position.x:.3f}, {obj.pose.position.y:.3f}, {obj.pose.position.z:.3f})")
                
                print()
        else:
            print("获取场景失败")

def main():
    rclpy.init()
    node = ObjectDiagnoser()
    
    try:
        node.diagnose()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
