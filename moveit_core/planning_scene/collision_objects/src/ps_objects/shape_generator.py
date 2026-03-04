#!/usr/bin/env python3
"""
形状生成器 - 简化可靠版本
"""
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose, Point, Quaternion
from typing import List, Tuple, Optional, Dict

class ShapeGenerator:
    """形状生成器 - 简单可靠版本"""
    
    # 形状类型常量
    BOX = SolidPrimitive.BOX
    SPHERE = SolidPrimitive.SPHERE
    CYLINDER = SolidPrimitive.CYLINDER
    CONE = SolidPrimitive.CONE
    
    def __init__(self):
        pass
    
    def create_box(self, 
                  name: str, 
                  position: List[float], 
                  size: List[float],
                  orientation: Optional[List[float]] = None) -> CollisionObject:
        """
        创建立方体
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置
            size: [length, width, height] 尺寸
            orientation: [qx, qy, qz, qw] 姿态（可选）
            
        Returns:
            CollisionObject: 立方体物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD（字节串！）
        obj.header.frame_id = "world"
        
        # 创建立方体形状
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = size[:3]  # 确保只有3个值
        
        # 创建位姿
        pose = Pose()
        pose.position = Point(x=position[0], y=position[1], z=position[2])
        
        if orientation and len(orientation) == 4:
            pose.orientation = Quaternion(
                x=orientation[0], y=orientation[1],
                z=orientation[2], w=orientation[3]
            )
        else:
            pose.orientation = Quaternion(w=1.0)  # 默认姿态
        
        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        
        return obj
    
    def create_sphere(self,
                     name: str,
                     position: List[float],
                     radius: float,
                     orientation: Optional[List[float]] = None) -> CollisionObject:
        """
        创建球体
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置
            radius: 半径
            orientation: [qx, qy, qz, qw] 姿态（可选，对球体意义不大）
            
        Returns:
            CollisionObject: 球体物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        obj.header.frame_id = "world"        
        # 创建球体形状
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [radius]  # 半径
        
        # 创建位姿
        pose = Pose()
        pose.position = Point(x=position[0], y=position[1], z=position[2])
        
        if orientation and len(orientation) == 4:
            pose.orientation = Quaternion(
                x=orientation[0], y=orientation[1],
                z=orientation[2], w=orientation[3]
            )
        else:
            pose.orientation = Quaternion(w=1.0)
        
        obj.primitives.append(sphere)
        obj.primitive_poses.append(pose)
        
        return obj
    
    def create_cylinder(self,
                       name: str,
                       position: List[float],
                       radius: float,
                       height: float,
                       orientation: Optional[List[float]] = None) -> CollisionObject:
        """
        创建圆柱体
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置
            radius: 半径
            height: 高度
            orientation: [qx, qy, qz, qw] 姿态
            
        Returns:
            CollisionObject: 圆柱体物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        obj.header.frame_id = "world"
        
        # 创建圆柱体形状
        cylinder = SolidPrimitive()
        cylinder.type = SolidPrimitive.CYLINDER
        cylinder.dimensions = [radius, height]  # 半径, 高度
        
        # 创建位姿
        pose = Pose()
        pose.position = Point(x=position[0], y=position[1], z=position[2])
        
        if orientation and len(orientation) == 4:
            pose.orientation = Quaternion(
                x=orientation[0], y=orientation[1],
                z=orientation[2], w=orientation[3]
            )
        else:
            pose.orientation = Quaternion(w=1.0)
        
        obj.primitives.append(cylinder)
        obj.primitive_poses.append(pose)
        
        return obj
    
    def create_cone(self,
                   name: str,
                   position: List[float],
                   radius: float,
                   height: float,
                   orientation: Optional[List[float]] = None) -> CollisionObject:
        """
        创建圆锥体
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置
            radius: 底面半径
            height: 高度
            orientation: [qx, qy, qz, qw] 姿态
            
        Returns:
            CollisionObject: 圆锥体物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        obj.header.frame_id = "world"
        
        # 创建圆锥体形状
        cone = SolidPrimitive()
        cone.type = SolidPrimitive.CONE
        cone.dimensions = [radius, height]  # 半径, 高度
        
        # 创建位姿
        pose = Pose()
        pose.position = Point(x=position[0], y=position[1], z=position[2])
        
        if orientation and len(orientation) == 4:
            pose.orientation = Quaternion(
                x=orientation[0], y=orientation[1],
                z=orientation[2], w=orientation[3]
            )
        else:
            pose.orientation = Quaternion(w=1.0)
        
        obj.primitives.append(cone)
        obj.primitive_poses.append(pose)
        
        return obj
    
    def create_table(self,
                    name: str,
                    position: List[float],
                    size: List[float]) -> CollisionObject:
        """
        创建桌子（简化版本，实际是立方体）
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置（z是桌子高度的一半）
            size: [length, width, height] 尺寸
            
        Returns:
            CollisionObject: 桌子物体
        """
        return self.create_box(name, position, size)
    
    def create_obstacle(self,
                       name: str,
                       position: List[float],
                       size: List[float]) -> CollisionObject:
        """
        创建障碍物（简化版本）
        
        Args:
            name: 物体名称
            position: [x, y, z] 位置
            size: [length, width, height] 尺寸
            
        Returns:
            CollisionObject: 障碍物物体
        """
        return self.create_box(name, position, size)
    '''
    def create_composite(self,
                        name: str,
                        shapes: List[Tuple[str, List, List]]) -> CollisionObject:
        """
        创建复合形状（多个基本形状的组合）
        
        Args:
            name: 物体名称
            shapes: 形状列表，每个元素是 (type, position, dimensions)
                    type: 'box', 'sphere', 'cylinder', 'cone'
                    position: [x, y, z]
                    dimensions: 尺寸列表（根据类型不同）
                    
        Returns:
            CollisionObject: 复合物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        obj.header.frame_id = "world"
        
        for shape_type, position, dimensions in shapes:
            primitive = SolidPrimitive()
            pose = Pose()
            pose.position = Point(x=position[0], y=position[1], z=position[2])
            pose.orientation = Quaternion(w=1.0)
            
            if shape_type == 'box':
                primitive.type = SolidPrimitive.BOX
                primitive.dimensions = dimensions[:3]
            elif shape_type == 'sphere':
                primitive.type = SolidPrimitive.SPHERE
                primitive.dimensions = [dimensions[0]]  # 半径
            elif shape_type == 'cylinder':
                primitive.type = SolidPrimitive.CYLINDER
                primitive.dimensions = [dimensions[0], dimensions[1]]  # 半径, 高度
            elif shape_type == 'cone':
                primitive.type = SolidPrimitive.CONE
                primitive.dimensions = [dimensions[0], dimensions[1]]  # 半径, 高度
            else:
                continue  # 跳过未知类型
            
            obj.primitives.append(primitive)
            obj.primitive_poses.append(pose)
        
        return obj
    '''
    def create_composite(self,
                        name: str,
                        shape_defs: List[Dict]) -> CollisionObject:
        """
        创建复合形状 - 复用已有函数的版本
        
        Args:
            name: 物体名称
            shape_defs: 形状定义列表，每个元素是字典：
                    {
                        'type': 'box'/'sphere'/'cylinder'/'cone',
                        'position': [x, y, z],
                        'size': [...]  # 对于box
                        'radius': ...   # 对于sphere/cylinder/cone
                        'height': ...   # 对于cylinder/cone
                        'orientation': [qx, qy, qz, qw]  # 可选
                    }
                        
        Returns:
            CollisionObject: 复合物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'  # ADD
        obj.header.frame_id = "world"
        
        for i, shape_def in enumerate(shape_defs):
            shape_type = shape_def.get('type')
            position = shape_def.get('position', [0, 0, 0])
            orientation = shape_def.get('orientation')
            
            if shape_type == 'box':
                size = shape_def.get('size', [0.1, 0.1, 0.1])
                temp_box = self.create_box(
                    name=f"{name}_part{i}",  # 临时名称
                    position=position,
                    size=size,
                    orientation=orientation
                )
                
            elif shape_type == 'sphere':
                radius = shape_def.get('radius', 0.1)
                temp_sphere = self.create_sphere(
                    name=f"{name}_part{i}",
                    position=position,
                    radius=radius,
                    orientation=orientation
                )
                
            elif shape_type == 'cylinder':
                radius = shape_def.get('radius', 0.1)
                height = shape_def.get('height', 0.2)
                temp_cylinder = self.create_cylinder(
                    name=f"{name}_part{i}",
                    position=position,
                    radius=radius,
                    height=height,
                    orientation=orientation
                )
                
            elif shape_type == 'cone':
                radius = shape_def.get('radius', 0.1)
                height = shape_def.get('height', 0.2)
                temp_cone = self.create_cone(
                    name=f"{name}_part{i}",
                    position=position,
                    radius=radius,
                    height=height,
                    orientation=orientation
                )
                
            else:
                continue  # 跳过未知类型
            
            # 获取刚刚创建的临时物体的形状
            temp_obj = locals().get(f'temp_{shape_type}')
            if temp_obj and temp_obj.primitives:
                obj.primitives.extend(temp_obj.primitives)
                obj.primitive_poses.extend(temp_obj.primitive_poses)
        
        return obj        

    def create_composite_simple(self,
                            name: str,
                            shape_objects: List[CollisionObject]) -> CollisionObject:
        """
        从已有形状对象创建复合形状（简化版）
        
        Args:
            name: 物体名称
            shape_objects: 已有的 CollisionObject 列表
                        
        Returns:
            CollisionObject: 复合物体
        """
        obj = CollisionObject()
        obj.id = name
        obj.operation = b'\x00'
        obj.header.frame_id = "world"
        
        for shape_obj in shape_objects:
            # 合并所有形状
            obj.primitives.extend(shape_obj.primitives)
            obj.primitive_poses.extend(shape_obj.primitive_poses)
        
        return obj

    def print_shape_info(self, obj: CollisionObject):
        """
        打印形状信息
        
        Args:
            obj: CollisionObject 实例
        """
        print(f"物体: {obj.id}")
        print(f"  操作: {obj.operation}")
        print(f"  参考坐标系: {obj.header.frame_id}")
        print(f"  形状数量: {len(obj.primitives)}")
        
        for i, (prim, pose) in enumerate(zip(obj.primitives, obj.primitive_poses)):
            shape_type = self._get_shape_type_name(prim.type)
            print(f"  形状 {i+1}: {shape_type}")
            print(f"    位置: [{pose.position.x:.3f}, {pose.position.y:.3f}, {pose.position.z:.3f}]")
            print(f"    尺寸: {prim.dimensions}")
    
    def _get_shape_type_name(self, shape_type: int) -> str:
        """获取形状类型名称"""
        type_names = {
            SolidPrimitive.BOX: "立方体",
            SolidPrimitive.SPHERE: "球体",
            SolidPrimitive.CYLINDER: "圆柱体",
            SolidPrimitive.CONE: "圆锥体"
        }
        return type_names.get(shape_type, f"未知({shape_type})")