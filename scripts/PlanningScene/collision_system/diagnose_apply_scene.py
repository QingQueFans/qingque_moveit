# fixed_apply_scene.py
#!/usr/bin/env python3
"""
修复 apply_scene 方法
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import ApplyPlanningScene
from moveit_msgs.msg import PlanningScene, PlanningSceneWorld, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

class SceneFixer(Node):
    def __init__(self):
        super().__init__('scene_fixer')
        self.client = self.create_client(ApplyPlanningScene, '/apply_planning_scene')
        
        self.test_different_methods()
    
    def test_different_methods(self):
        """测试不同的场景更新方法"""
        print("测试不同的场景更新方法...")
        
        methods = [
            self.method1_simple_object,
            self.method2_with_robot_state,
            self.method3_full_scene,
            self.method4_using_move_group  # 可能需要不同的服务
        ]
        
        for i, method in enumerate(methods):
            print(f"\n方法 {i+1}: {method.__name__}")
            try:
                if method():
                    print("✅ 成功！")
                    break
            except Exception as e:
                print(f"❌ 失败: {e}")
    
    def method1_simple_object(self):
        """方法1：最简单的物体添加"""
        scene = PlanningScene()
        scene.is_diff = True
        
        # 创建物体
        obj = CollisionObject()
        obj.id = "test_box_1"
        obj.operation = CollisionObject.ADD
        
        # 创建立方体
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.1, 0.1, 0.1]
        
        pose = Pose()
        pose.position.x = 0.5
        pose.position.y = 0.0
        pose.position.z = 0.5
        
        obj.primitives = [box]
        obj.primitive_poses = [pose]
        obj.header.frame_id = "world"  # 重要：设置坐标系
        
        # 添加到世界
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(obj)
        
        return self.send_scene(scene)
    
    def method2_with_robot_state(self):
        """方法2：包含机器人状态的场景"""
        from sensor_msgs.msg import JointState
        from moveit_msgs.msg import RobotState
        
        scene = PlanningScene()
        scene.is_diff = True
        
        # 设置机器人状态（即使为空）
        robot_state = RobotState()
        joint_state = JointState()
        joint_state.name = ["panda_joint1", "panda_joint2", "panda_joint3"]
        joint_state.position = [0.0, 0.0, 0.0]
        robot_state.joint_state = joint_state
        
        scene.robot_state = robot_state
        
        # 添加物体
        obj = CollisionObject()
        obj.id = "test_box_2"
        obj.operation = CollisionObject.ADD
        obj.header.frame_id = "panda_link0"  # 使用机器人基坐标系
        
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.05, 0.05, 0.05]
        
        pose = Pose()
        pose.position.x = 0.3
        pose.position.y = 0.0
        pose.position.z = 0.3
        
        obj.primitives = [box]
        obj.primitive_poses = [pose]
        
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(obj)
        
        return self.send_scene(scene)
    
    def method3_full_scene(self):
        """方法3：完整场景设置"""
        scene = PlanningScene()
        scene.is_diff = False  # 完整场景，不是差异# 设置场景名称
        scene.name = "test_scene"
        
        # 设置机器人模型
        scene.robot_model_name = "panda"
        
        # 添加物体
        obj = CollisionObject()
        obj.id = "test_box_3"
        obj.operation = CollisionObject.ADD
        obj.header.frame_id = "world"
        
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.2, 0.2, 0.1]
        
        pose = Pose()
        pose.position.x = 0.4
        pose.position.y = 0.1
        pose.position.z = 0.05
        
        obj.primitives = [box]
        obj.primitive_poses = [pose]
        
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(obj)
        
        return self.send_scene(scene)
    
    def method4_using_move_group(self):
        """方法4：通过 move_group 服务"""
        # 尝试使用不同的服务
        print("尝试使用 /move_group/apply_planning_scene")
        
        # 重新创建客户端
        self.client = self.create_client(
            ApplyPlanningScene, 
            '/move_group/apply_planning_scene'
        )
        
        if not self.client.wait_for_service(timeout_sec=3.0):
            print("  /move_group/apply_planning_scene 不可用")
            return False
        
        return self.method1_simple_object()
    
    def send_scene(self, scene):
        """发送场景并检查结果"""
        request = ApplyPlanningScene.Request()
        request.scene = scene
        
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            result = future.result()
            print(f"  返回结果: success={result.success}")
            
            # 如果有错误信息，打印它
            if hasattr(result, 'error_message') and result.error_message:
                print(f"  错误信息: {result.error_message}")
            
            return result.success
        return False

def main():
    rclpy.init()
    fixer = SceneFixer()
    rclpy.shutdown()

if __name__ == '__main__':
    main()