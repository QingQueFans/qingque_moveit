#!/usr/bin/env python3
# 操作常量（单字节字节串）
CO_ADD = b'\x00'      # 添加
CO_REMOVE = b'\x01'   # 移除  
CO_APPEND = b'\x02'   # 追加
CO_MOVE = b'\x03'     # 移动
"""
PlanningScene 管理器 - 简化版
"""
from moveit_msgs.msg import PlanningScene, CollisionObject
from geometry_msgs.msg import Pose
from shape_msgs.msg import SolidPrimitive

class PlanningSceneManager:
    """场景管理器 - 简化版"""
    
    def __init__(self, client):
        self.client = client
    '''
    def create_box(self, name: str, pose: Pose, size: list) -> CollisionObject:
        """创建立方体"""
        obj = CollisionObject()
        obj.id = name
        obj.operation = CollisionObject.ADD
        
        # 创建立方体
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = size  # [x, y, z]
        
        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        
        return obj
    '''
    '''
    def create_box(self, name: str, pose: Pose, size: list) -> CollisionObject:
        """创建立方体"""
        obj = CollisionObject()
        obj.id = name
        obj.operation = 0  # ← 直接使用整数 0 (ADD)，不要用 CollisionObject.ADD
        
        # 创建立方体
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = size  # [x, y, z]
        
        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        
        return obj

        
    def create_sphere(self, name: str, pose: Pose, radius: float) -> CollisionObject:
        """创建球体"""
        obj = CollisionObject()
        obj.id = name
        obj.operation = CollisionObject.ADD
        
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [radius]  # 半径
        
        obj.primitives.append(sphere)
        obj.primitive_poses.append(pose)
        
        return obj
    '''    
    def create_box(self, name: str, pose: Pose, size: list) -> CollisionObject:
        """创建立方体"""
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        
        # 关键：设置参考坐标系
        obj.header.frame_id = "world"  # 或 "panda_link0"，根据您的机器人
        
        # 创建立方体
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = size  # [x, y, z]
        
        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        
        return obj

    def create_sphere(self, name: str, pose: Pose, radius: float) -> CollisionObject:
        """创建球体"""
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD 操作 (字节串)
        
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [radius]  # 半径
        
        obj.primitives.append(sphere)
        obj.primitive_poses.append(pose)
        
        return obj

    def remove_object(self, name: str) -> bool:
        """移除物体"""
        scene = self.client.get_current_scene()
        if not scene or not scene.world:
            return False
        
        # 查找物体
        for i, obj in enumerate(scene.world.collision_objects):
            if obj.id == name:
                # 设置为 REMOVE 操作 (字节串)
                obj.operation = b'\x01'  # REMOVE 操作
                return self.client.apply_scene_update(scene)
        
        return False
    '''
    def add_box(self, name: str, position: list, size: list) -> bool:
        """添加立方体到场景"""
        pose = Pose()
        pose.position.x = position[0]
        pose.position.y = position[1]
        pose.position.z = position[2]
        pose.orientation.w = 1.0
        
        box = self.create_box(name, pose, size)
        
        scene = self.client.get_current_scene()
        if not scene:
            return False
        
        if not scene.world:
            from moveit_msgs.msg import PlanningSceneWorld
            scene.world = PlanningSceneWorld()
        
        scene.world.collision_objects.append(box)
        return self.client.apply_scene_update(scene)
        '''
    def add_box(self, name: str, position: list, size: list) -> bool:
        """添加立方体到场景"""
        print(f"[DEBUG] 添加盒子: {name}, 位置={position}, 尺寸={size}")
        
        pose = Pose()
        pose.position.x = position[0]
        pose.position.y = position[1]
        pose.position.z = position[2]
        pose.orientation.w = 1.0
        
        print(f"[DEBUG] 创建位姿: x={pose.position.x}, y={pose.position.y}, z={pose.position.z}")
        
        box = self.create_box(name, pose, size)
        print(f"[DEBUG] 创建碰撞物体: ID={box.id}, 操作类型={box.operation}")
        
        scene = self.client.get_current_scene()
        if not scene:
            print("[ERROR] 无法获取当前场景")
            return False
        
        print(f"[DEBUG] 获取场景成功")
        
        if not scene.world:
            from moveit_msgs.msg import PlanningSceneWorld
            scene.world = PlanningSceneWorld()
            print(f"[DEBUG] 创建新的 PlanningSceneWorld")
        
        print(f"[DEBUG] 添加前物体数量: {len(scene.world.collision_objects)}")
        scene.world.collision_objects.append(box)
        print(f"[DEBUG] 添加后物体数量: {len(scene.world.collision_objects)}")
        
        # 确保 scene.is_diff = True
        scene.is_diff = True
        print(f"[DEBUG] scene.is_diff = {scene.is_diff}")
        
        result = self.client.apply_scene_update(scene)
        print(f"[DEBUG] 应用场景更新结果: {result}")
        
        """添加立方体到场景"""
        # ... 前面的代码不变 ...
        
        print(f"[DEBUG] 调用 apply_scene_update...")
        result = self.client.apply_scene_update(scene)
        print(f"[DEBUG] 返回结果: {result}")
        
        # 立即重新获取场景验证
        import time
        time.sleep(0.2)  # 等待更新
        scene_check = self.client.get_current_scene()
        if scene_check and scene_check.world:
            print(f"[DEBUG] 验证: 场景中有 {len(scene_check.world.collision_objects)} 个物体")
        
        
        return result
    '''
    def remove_object(self, name: str) -> bool:
        """移除物体"""
        scene = self.client.get_current_scene()
        if not scene or not scene.world:
            return False
        
        # 查找物体
        for i, obj in enumerate(scene.world.collision_objects):
            if obj.id == name:
                # 设置为移除
                obj.operation = CollisionObject.REMOVE
                return self.client.apply_scene_update(scene)
        
        return False
    '''
    def list_objects(self):
        """列出所有物体"""
        objects = self.client.get_collision_objects()
        print(f"场景中有 {len(objects)} 个物体:")
        for obj in objects:
            print(f"  - {obj}")