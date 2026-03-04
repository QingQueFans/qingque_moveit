
#!/usr/bin/env python3
"""
PlanningScene 客户端 - 简化版
提供 PlanningScene 的基础操作
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPlanningScene, ApplyPlanningScene
from moveit_msgs.msg import PlanningScene, RobotState
import time
from typing import Optional, List,Dict

class PlanningSceneClient(Node):
    """PlanningScene ROS 客户端 - 简化版"""
    '''
    def __init__(self):
        """初始化客户端"""
        if not rclpy.ok():
            rclpy.init()
        super().__init__('planning_scene_client')
        
        # 创建服务客户端
        self.get_scene = self.create_client(GetPlanningScene, '/get_planning_scene')
        self.apply_scene = self.create_client(ApplyPlanningScene, '/apply_planning_scene')
        self.scene_publisher = self.create_publisher(PlanningScene, '/planning_scene', 10)
        # 等待服务
        self._wait_for_services()
        '''
    def __init__(self):
        """初始化客户端"""
        if not rclpy.ok():
            rclpy.init()
        super().__init__('planning_scene_client')
        
        # 创建服务客户端
        self.get_scene = self.create_client(GetPlanningScene, '/get_planning_scene')
        self.apply_scene = self.create_client(ApplyPlanningScene, '/apply_planning_scene')
        
        # 关键：发布到 RViz 实际订阅的主题
        self.monitored_publisher = self.create_publisher(
            PlanningScene, 
            '/monitored_planning_scene',  # RViz 订阅这个！
            10
        )
        
        # 也可以继续发布到 /planning_scene（给其他订阅者）
        self.scene_publisher = self.create_publisher(PlanningScene, '/planning_scene', 10)
        
        # 等待服务
        self._wait_for_services()
    def _wait_for_services(self, timeout=5.0):
        """等待服务就绪"""
        start = time.time()
        
        for client, name in [(self.get_scene, '获取场景'), (self.apply_scene, '应用场景')]:
            while time.time() - start < timeout:
                if client.wait_for_service(timeout_sec=1.0):
                    self.get_logger().info(f'{name}服务就绪')
                    break
                else:
                    self.get_logger().warn(f'等待{name}服务...')
            else:
                self.get_logger().error(f'{name}服务超时')
                return False
        return True
    
    def get_current_scene(self) -> Optional[PlanningScene]:
        """获取当前场景"""
        req = GetPlanningScene.Request()
        req.components.components = (
            req.components.WORLD_OBJECT_NAMES |
            req.components.ROBOT_STATE |
            req.components.ALLOWED_COLLISION_MATRIX
        )
        
        try:
            future = self.get_scene.call_async(req)
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            
            if future.result():
                return future.result().scene
        except Exception as e:
            self.get_logger().error(f'获取场景失败: {e}')
        
        return None
    '''
    
      
    def apply_scene_update(self, scene: PlanningScene) -> bool:
        """应用场景更新"""
        scene.is_diff = True
        
        # 确保设置机器人模型名称（RViz 可能需要）
        if not hasattr(scene, 'robot_model_name') or not scene.robot_model_name:
            scene.robot_model_name = "panda"  # 根据您的机器人设置
        
        try:
            future = self.apply_scene.call_async(
                ApplyPlanningScene.Request(scene=scene)
            )
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            
            service_success = future.result() is not None
            
            # 发布到主题（确保 RViz 更新）
            if hasattr(self, 'scene_publisher'):
                # 多次发布确保接收
                for i in range(3):
                    self.scene_publisher.publish(scene)
                    # 使用 spin_once 确保消息发送
                    rclpy.spin_once(self, timeout_sec=0.01)
            
            return service_success
        except Exception as e:
            self.get_logger().error(f'应用场景失败: {e}')
            return False    
            '''
    def apply_scene_update(self, scene: PlanningScene) -> bool:
        """应用场景更新"""
        scene.is_diff = True
        
        # 确保设置必要的字段
        if not hasattr(scene, 'robot_model_name') or not scene.robot_model_name:
            scene.robot_model_name = "panda"
        
        try:
            future = self.apply_scene.call_async(
                ApplyPlanningScene.Request(scene=scene)
            )
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            
            service_success = future.result() is not None
            
            # 关键：先发布到 RViz 订阅的主题
            if hasattr(self, 'monitored_publisher'):
                for i in range(3):  # 多次发布确保接收
                    self.monitored_publisher.publish(scene)
                    rclpy.spin_once(self, timeout_sec=0.01)
            
            # 然后发布到其他主题
            if hasattr(self, 'scene_publisher'):
                self.scene_publisher.publish(scene)
            
            return service_success
        except Exception as e:
            self.get_logger().error(f'应用场景失败: {e}')
            return False
    def get_collision_objects(self) -> List[str]:
        """获取碰撞物体列表"""
        scene = self.get_current_scene()
        if scene and scene.world:
            return [obj.id for obj in scene.world.collision_objects]
        return []
    '''
    def clear_all_objects(self) -> bool:
        """清空所有物体"""
        scene = self.get_current_scene()
        if not scene:
            return False
        
        # 清空碰撞物体
        if scene.world:
            scene.world.collision_objects.clear()
        
        # 清空附着物体
        if scene.robot_state and scene.robot_state.attached_collision_objects:
            scene.robot_state.attached_collision_objects.clear()
        
        return self.apply_scene_update(scene)
    '''
    '''
    def clear_all_objects_with_rviz(self) -> bool:
        """清空所有物体，包括通知 RViz"""
        # 1. 首先通过服务清空
        success1 = self.clear_all_objects()
        
        # 2. 创建空场景并直接发布到主题
        from moveit_msgs.msg import PlanningScene, PlanningSceneWorld
        
        empty_scene = PlanningScene()
        empty_scene.is_diff = True
        empty_scene.world = PlanningSceneWorld()
        
        # 如果客户端有发布器，使用它
        if hasattr(self, 'scene_publisher'):
            for i in range(3):
                self.scene_publisher.publish(empty_scene)
                import time
                time.sleep(0.1)
        
        return success1
        '''
    def clear_all_objects(self) -> bool:
        """清空所有物体"""
        scene = self.get_current_scene()
        if not scene:
            return False
        
        # 清空碰撞物体
        if scene.world:
            for obj in scene.world.collision_objects:
                obj.operation = b'\x01'  # REMOVE
        
        # 清空附着物体
        if scene.robot_state and scene.robot_state.attached_collision_objects:
            scene.robot_state.attached_collision_objects.clear()
        
        scene.is_diff = True
        
        # 应用更新
        success = self.apply_scene_update(scene)
        
        # 额外同步到 RViz
        if success and hasattr(self, 'sync_with_rviz'):
            time.sleep(0.2)  # 等待一下
            self.sync_with_rviz(scene)
        
        return success
    #############################物体连接方法##################
    def attach_object(self, object_id: str, link_name: str, touch_links: List[str] = None) -> bool:
        """
        连接物体到机器人link（ROS2版本）
        与现有代码风格一致
        """
        try:
            from moveit_msgs.msg import AttachedCollisionObject, CollisionObject
            from moveit_msgs.srv import ApplyPlanningScene
            print(f"[场景] 连接物体 {object_id} 到 {link_name}")
            
            # 1. 创建AttachedCollisionObject
            attached_object = AttachedCollisionObject()
            attached_object.object.id = object_id
            attached_object.link_name = link_name
            
            # 2. 设置touch_links
            if touch_links:
                attached_object.touch_links = touch_links
            else:
                # 默认值（针对Panda）
                attached_object.touch_links = [
                    "panda_hand",
                    "panda_leftfinger",
                    "panda_rightfinger"
                ]
            
            # 3. 设置操作类型
            attached_object.object.operation = CollisionObject.ADD
            
            # 4. 创建PlanningScene消息（与get_planning_scene方法类似）
            scene_msg = PlanningScene()
            scene_msg.is_diff = True
            scene_msg.robot_state.is_diff = True
            scene_msg.robot_state.attached_collision_objects.append(attached_object)
            
            # 5. 使用现有的apply_scene服务客户端
            if not hasattr(self, 'apply_scene_client'):
                # 创建服务客户端（与get_scene_client类似）
                
                self.apply_scene_client = self.create_client(
                    ApplyPlanningScene, 
                    'apply_planning_scene'
                )
            
            # 6. 等待服务（与_get_scene方法类似）
            if not self.apply_scene_client.wait_for_service(timeout_sec=2.0):
                self.get_logger().warn("apply_planning_scene服务不可用")
                return False
            
            # 7. 创建请求
            request = ApplyPlanningScene.Request()
            request.scene = scene_msg
            
            # 8. 发送请求
            future = self.apply_scene_client.call_async(request)
            
            # 9. 等待响应（与_get_scene方法类似）
            rclpy.spin_until_future_complete(self, future)
            
            if future.result() is not None:
                response = future.result()
                if response.success:
                    self.get_logger().info(f"物体 {object_id} 已连接到 {link_name}")
                    return True
                else:
                    self.get_logger().error(f"连接失败: {response.error_message}")
            else:
                self.get_logger().error("服务调用失败")
            
            return False
            
        except Exception as e:
            self.get_logger().error(f"连接异常: {e}")
            return False
    
    def detach_object(self, object_id: str) -> bool:
        """
        断开物体连接（ROS2版本）
        """
        try:
            from moveit_msgs.msg import AttachedCollisionObject, CollisionObject
            from moveit_msgs.srv import ApplyPlanningScene
            self.get_logger().info(f"断开物体 {object_id} 的连接")
            
            # 1. 创建空的AttachedCollisionObject表示移除
            attached_object = AttachedCollisionObject()
            attached_object.object.id = object_id
            attached_object.object.operation = CollisionObject.REMOVE
            
            # 2. 创建PlanningScene消息
            scene_msg = PlanningScene()
            scene_msg.is_diff = True
            scene_msg.robot_state.is_diff = True
            scene_msg.robot_state.attached_collision_objects.append(attached_object)
            
            # 3. 使用现有的apply_scene服务客户端
            if not hasattr(self, 'apply_scene_client'):
                
                self.apply_scene_client = self.create_client(
                    ApplyPlanningScene, 
                    'apply_planning_scene'
                )
            
            # 4. 等待服务
            if not self.apply_scene_client.wait_for_service(timeout_sec=2.0):
                self.get_logger().warn("apply_planning_scene服务不可用")
                return False            # 5. 创建请求
            request = ApplyPlanningScene.Request()
            request.scene = scene_msg
            
            # 6. 发送请求
            future = self.apply_scene_client.call_async(request)
            
            # 7. 等待响应
            rclpy.spin_until_future_complete(self, future)
            
            if future.result() is not None:
                response = future.result()
                if response.success:
                    self.get_logger().info(f"物体 {object_id} 已断开连接")
                    return True
                else:
                    self.get_logger().error(f"断开失败: {response.error_message}")
            else:
                self.get_logger().error("服务调用失败")
            
            return False
            
        except Exception as e:
            self.get_logger().error(f"断开异常: {e}")
            return False
    
    def get_attached_objects(self) -> Dict:
        """
        获取当前连接的所有物体
        """
        try:
            # 使用现有的get_scene方法获取当前场景
            current_scene = self.get_planning_scene()
            
            attached_objects = {}
            for attached in current_scene.robot_state.attached_collision_objects:
                attached_objects[attached.object.id] = {
                    "link_name": attached.link_name,
                    "touch_links": attached.touch_links
                }
            
            return attached_objects
            
        except Exception as e:
            self.get_logger().error(f"获取连接物体异常: {e}")
            return {}
    
    def is_object_attached(self, object_id: str) -> bool:
        """
        检查物体是否已连接
        """
        attached_objects = self.get_attached_objects()
        return object_id in attached_objects
    def apply_scene_update(self, scene: PlanningScene) -> bool:
        """应用场景更新"""
        scene.is_diff = True
        
        # 确保设置机器人模型名称（RViz 可能需要）
        if not hasattr(scene, 'robot_model_name') or not scene.robot_model_name:
            scene.robot_model_name = "panda"  # 根据您的机器人设置
        
        try:
            future = self.apply_scene.call_async(
                ApplyPlanningScene.Request(scene=scene)
            )
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            
            service_success = future.result() is not None
            
            # 发布到主题（确保 RViz 更新）
            if hasattr(self, 'scene_publisher'):
                # 多次发布确保接收
                for i in range(3):
                    self.scene_publisher.publish(scene)
                    # 使用 spin_once 确保消息发送
                    rclpy.spin_once(self, timeout_sec=0.01)
            
            return service_success
        except Exception as e:
            self.get_logger().error(f'应用场景失败: {e}')
            return False
    def get_robot_state(self) -> Optional[RobotState]:
        """获取机器人状态"""
        scene = self.get_current_scene()
        return scene.robot_state if scene else None
    
    def print_scene_info(self):
        """打印场景信息"""
        scene = self.get_current_scene()
        if not scene:
            print("无法获取场景")
            return
        
        print("\n=== 场景信息 ===")
        
        # 碰撞物体
        if scene.world:
            print(f"碰撞物体: {len(scene.world.collision_objects)}个")
            for obj in scene.world.collision_objects:
                print(f"  - {obj.id}")
        
        # 机器人状态
        if scene.robot_state and scene.robot_state.joint_state:
            joints = scene.robot_state.joint_state
            print(f"关节数量: {len(joints.name)}")
        
        # ACM
        if scene.allowed_collision_matrix:
            print("有允许碰撞矩阵")
    
    def sync_with_rviz(self, scene: PlanningScene = None):
        """专门同步到 RViz 显示"""
        if scene is None:
            scene = self.get_current_scene()
            if not scene:
                return False
        
        scene.is_diff = True
        
        # 确保场景完整
        if not hasattr(scene, 'robot_model_name'):
            scene.robot_model_name = "panda"
        
        print("同步到 RViz...")
        
        # 1. 通过服务更新
        service_success = self.apply_scene_update(scene)
        
        # 2. 额外多次发布到 monitored 主题
        if hasattr(self, 'monitored_publisher'):
            import time
            for i in range(5):
                self.monitored_publisher.publish(scene)
                rclpy.spin_once(self, timeout_sec=0.01)
                time.sleep(0.05)
        
        return service_success
    def shutdown(self):
        """关闭客户端"""
        self.destroy_node()
        rclpy.shutdown()

# 使用示例
def demo():
    """演示使用"""
    client = PlanningSceneClient()
    
    print("获取场景信息...")
    client.print_scene_info()
    
    print(f"\n碰撞物体: {client.get_collision_objects()}")
    
    client.shutdown()



if __name__ == "__main__":
    demo()
