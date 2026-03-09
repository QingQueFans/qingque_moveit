#!/usr/bin/env python3
"""
PlanningScene 客户端 - 壳子版
所有实现都转发给 pymoveit2，只留接口做情怀
"""
import rclpy
from rclpy.node import Node
from typing import Optional, List, Dict

class PlanningSceneClient(Node):
    """PlanningScene 客户端 - 只转发，不干活"""
    
    def __init__(self, moveit2, node_name="planning_scene_client"):
        """
        初始化客户端
        :param moveit2: 已经初始化好的 MoveIt2 实例
        """
        if not rclpy.ok():
            rclpy.init()
        super().__init__(node_name)
        
        self.moveit2 = moveit2
        self.get_logger().info("🤖 PlanningSceneClient 壳子版启动（实际干活的是 moveit2）")
    
    def get_current_scene(self):
        """获取当前场景"""
        return self.moveit2.planning_scene
    
    def apply_scene_update(self, scene):
        """应用场景更新"""
        # moveit2 内部自动处理，这里啥也不干
        self.get_logger().debug("apply_scene_update 被调用，但 moveit2 会自动处理")
        return True
    
    def get_collision_objects(self) -> List[str]:
        """获取碰撞物体列表"""
        # 如果有 planning_scene 就取，没有就返回空
        if hasattr(self.moveit2, 'planning_scene') and self.moveit2.planning_scene:
            scene = self.moveit2.planning_scene
            if hasattr(scene, 'world') and scene.world:
                return [obj.id for obj in scene.world.collision_objects]
        return []
    
    def clear_all_objects(self) -> bool:
        """清空所有物体"""
        return self.moveit2.clear_all_collision_objects()
    
    def attach_object(self, object_id: str, link_name: str, touch_links: List[str] = None) -> bool:
        """连接物体"""
        return self.moveit2.attach_collision_object(object_id, link_name, touch_links)
    
    def detach_object(self, object_id: str) -> bool:
        """断开物体"""
        return self.moveit2.detach_collision_object(object_id)
    
    def get_attached_objects(self) -> Dict:
        """获取当前连接的所有物体"""
        return self.moveit2.get_attached_objects() if hasattr(self.moveit2, 'get_attached_objects') else {}
    
    def is_object_attached(self, object_id: str) -> bool:
        """检查物体是否已连接"""
        attached = self.get_attached_objects()
        return object_id in attached
    
    def get_robot_state(self):
        """获取机器人状态"""
        return self.moveit2.joint_state if hasattr(self.moveit2, 'joint_state') else None
    
    def print_scene_info(self):
        """打印场景信息"""
        print("\n=== 场景信息（来自 moveit2）===")
        objects = self.get_collision_objects()
        print(f"碰撞物体: {len(objects)}个")
        for obj in objects:
            print(f"  - {obj}")
        
        attached = self.get_attached_objects()
        print(f"附着物体: {len(attached)}个")
        for obj_id in attached:
            print(f"  - {obj_id}")
    
    def sync_with_rviz(self, scene=None):
        """同步到 RViz"""
        self.get_logger().debug("sync_with_rviz 被调用，moveit2 已自动处理")
        return True
    
    def shutdown(self):
        """关闭客户端"""
        self.get_logger().info("PlanningSceneClient 壳子关闭")
        self.destroy_node()


def demo():
    """演示使用"""
    # 实际应该传入已经初始化好的 moveit2
    from pymoveit2 import MoveIt2
    
    moveit2 = MoveIt2(...)  # 需要实际参数
    client = PlanningSceneClient(moveit2)
    
    client.print_scene_info()
    client.shutdown()


if __name__ == "__main__":
    # 这个 demo 需要实际 moveit2 实例才能跑
    print("这个壳子需要外部传入 moveit2 实例使用")