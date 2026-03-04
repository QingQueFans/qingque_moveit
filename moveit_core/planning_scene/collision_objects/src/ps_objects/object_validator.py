#!/usr/bin/env python3
"""
物体验证器 - 简化可靠版本
"""
from typing import List, Dict, Any, Tuple, Optional
from moveit_msgs.msg import CollisionObject
import math

class ObjectValidator:
    """物体验证器 - 简单可靠版本"""
    
    def __init__(self, scene_client=None):
        """
        初始化验证器
        
        Args:
            scene_client: PlanningSceneClient 实例（可选）
        """
        self.client = scene_client
        self.min_size = 0.01  # 最小尺寸 (1cm)
        self.max_size = 10.0  # 最大尺寸 (10m)
    
    def validate_object(self, obj: CollisionObject) -> Tuple[bool, str]:
        """
        验证物体基本属性
        
        Args:
            obj: CollisionObject 实例
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 1. 检查 ID
        if not obj.id or not obj.id.strip():
            return False, "物体ID不能为空"
        
        # 2. 检查 operation 字段
        if not hasattr(obj, 'operation'):
            return False, "缺少 operation 字段"
        
        if not isinstance(obj.operation, bytes):
            return False, f"operation 必须是字节串，当前是 {type(obj.operation)}"
        
        # 3. 检查 frame_id
        if not hasattr(obj.header, 'frame_id') or not obj.header.frame_id:
            return False, "缺少参考坐标系 (frame_id)"
        
        # 4. 检查形状和位姿数量匹配
        prim_count = len(obj.primitives) if hasattr(obj, 'primitives') else 0
        pose_count = len(obj.primitive_poses) if hasattr(obj, 'primitive_poses') else 0
        
        if prim_count == 0:
            return False, "没有定义形状"
        
        if prim_count != pose_count:
            return False, f"形状数量({prim_count})和位姿数量({pose_count})不匹配"
        
        # 5. 检查每个形状
        for i, (prim, pose) in enumerate(zip(obj.primitives, obj.primitive_poses)):
            valid, msg = self._validate_primitive(prim, i)
            if not valid:
                return False, msg
            
            valid, msg = self._validate_pose(pose, i)
            if not valid:
                return False, msg
        
        return True, "物体有效"
    
    def _validate_primitive(self, primitive, index: int) -> Tuple[bool, str]:
        """验证基本形状"""
        # 检查类型
        if not hasattr(primitive, 'type'):
            return False, f"形状 {index+1}: 缺少 type 字段"
        
        # 检查尺寸
        if not hasattr(primitive, 'dimensions'):
            return False, f"形状 {index+1}: 缺少 dimensions 字段"
        
        dims = primitive.dimensions
        if not dims:
            return False, f"形状 {index+1}: dimensions 为空"        
        # 根据类型检查尺寸数量
        type_dims_required = {
            1: 3,  # BOX: [length, width, height]
            2: 1,  # SPHERE: [radius]s
            3: 2,  # CYLINDER: [radius, height]
            4: 2   # CONE: [radius, height]
        }
        
        required = type_dims_required.get(primitive.type, 0)
        if len(dims) != required:
            return False, f"形状 {index+1}: 需要 {required} 个尺寸值，实际有 {len(dims)} 个"
        
        # 检查尺寸值
        for j, dim in enumerate(dims):
            if not isinstance(dim, (int, float)):
                return False, f"形状 {index+1} 尺寸 {j+1}: 必须是数字"
            
            if dim <= 0:
                return False, f"形状 {index+1} 尺寸 {j+1}: 必须大于0"
            
            if dim < self.min_size:
                return False, f"形状 {index+1} 尺寸 {j+1}: 太小 (<{self.min_size}m)"
            
            if dim > self.max_size:
                return False, f"形状 {index+1} 尺寸 {j+1}: 太大 (>{self.max_size}m)"
        
        return True, "形状有效"
    
    def _validate_pose(self, pose, index: int) -> Tuple[bool, str]:
        """验证位姿"""
        # 检查位置
        if not hasattr(pose, 'position'):
            return False, f"位姿 {index+1}: 缺少 position 字段"
        
        pos = pose.position
        for coord, name in [(pos.x, 'x'), (pos.y, 'y'), (pos.z, 'z')]:
            if not isinstance(coord, (int, float)):
                return False, f"位姿 {index+1} {name}: 必须是数字"
            
            if abs(coord) > 100:  # 限制在±100米内
                return False, f"位姿 {index+1} {name}: 超出范围 (±100m)"
        
        # 检查姿态
        if not hasattr(pose, 'orientation'):
            return False, f"位姿 {index+1}: 缺少 orientation 字段"
        
        q = pose.orientation
        norm = math.sqrt(q.x**2 + q.y**2 + q.z**2 + q.w**2)
        
        if abs(norm - 1.0) > 0.01:  # 允许小的数值误差
            return False, f"位姿 {index+1}: 姿态四元数不是单位四元数 (norm={norm:.4f})"
        
        return True, "位姿有效"
    
    def validate_position(self, position: List[float]) -> Tuple[bool, str]:
        """
        验证位置是否合理
        
        Args:
            position: [x, y, z] 位置
            
        Returns:
            Tuple[bool, str]: (是否合理, 错误信息)
        """
        if len(position) != 3:
            return False, f"位置需要3个值，实际有 {len(position)} 个"
        
        for i, coord in enumerate(position):
            if not isinstance(coord, (int, float)):
                return False, f"位置坐标 {i} 必须是数字"
            
            if abs(coord) > 100:
                return False, f"位置坐标 {i} 超出范围 (±100m)"
        
        # 检查是否在地面以上（z >= 0）
        if position[2] < -0.5:  # 允许稍微低于地面
            return False, f"位置太低 (z={position[2]:.2f}m)"
        
        return True, "位置合理"
    
    def validate_size(self, size: List[float], shape_type: str = "box") -> Tuple[bool, str]:
        """
        验证尺寸是否合理
        
        Args:
            size: 尺寸列表
            shape_type: 形状类型
            
        Returns:
            Tuple[bool, str]: (是否合理, 错误信息)
        """
        if not size:
            return False, "尺寸不能为空"
        
        for i, dim in enumerate(size):
            if not isinstance(dim, (int, float)):
                return False, f"尺寸 {i} 必须是数字"
            
            if dim <= 0:
                return False, f"尺寸 {i} 必须大于0"
            
            if dim < self.min_size:
                return False, f"尺寸 {i} 太小 (<{self.min_size}m)"
            
            if dim > self.max_size:
                return False, f"尺寸 {i} 太大 (>{self.max_size}m)"
        
        # 根据形状类型检查尺寸数量
        type_required = {
            "box": 3,
            "sphere": 1,
            "cylinder": 2,
            "cone": 2
        }
        
        required = type_required.get(shape_type.lower(), 0)
        if required == 0:
            return False, f"未知形状类型: {shape_type}"
        
        if len(size) != required:
            return False, f"{shape_type} 需要 {required} 个尺寸值，实际有 {len(size)} 个"
        
        return True, "尺寸合理"
    
    def check_collision_simple(self, obj: CollisionObject, existing_objects: List[str]) -> Tuple[bool, str]:
        """
        简单碰撞检查（基于名称）
        
        Args:
            obj: 要添加的物体
            existing_objects: 现有物体ID列表
            
        Returns:
            Tuple[bool, str]: (是否冲突, 冲突信息)
        """        
        # 检查名称是否已存在
        if obj.id in existing_objects:
            return True, f"物体名称 '{obj.id}' 已存在"
        
        return False, "名称可用"
    
    def check_robot_proximity(self, position: List[float], safe_distance: float = 0.2) -> Tuple[bool, str]:
        """
        检查与机器人的距离（简化版本）
        
        Args:
            position: [x, y, z] 位置
            safe_distance: 安全距离
            
        Returns:
            Tuple[bool, str]: (是否安全, 警告信息)
        """
        # 简化：假设机器人基座在 [0, 0, 0]
        robot_base = [0, 0, 0]
        
        distance = math.sqrt(
            (position[0] - robot_base[0])**2 +
            (position[1] - robot_base[1])**2 +
            (position[2] - robot_base[2])**2
        )
        
        if distance < safe_distance:
            return False, f"物体距离机器人太近 ({distance:.2f}m < {safe_distance}m)"
        
        return True, f"距离机器人安全 ({distance:.2f}m)"
    
    def validate_scene_addition(self, obj: CollisionObject) -> Dict[str, Any]:
        """
        综合验证场景添加
        
        Args:
            obj: 要添加的物体
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 1. 基本验证
        valid, msg = self.validate_object(obj)
        if not valid:
            result['errors'].append(msg)
            return result
        
        # 2. 如果有客户端，检查现有物体
        if self.client:
            try:
                existing = self.client.get_collision_objects()
                collision, msg = self.check_collision_simple(obj, existing)
                if collision:
                    result['warnings'].append(msg)
            except:
                pass  # 忽略获取现有物体失败
        
        # 3. 检查与机器人的距离
        if obj.primitive_poses:
            pos = obj.primitive_poses[0].position
            position = [pos.x, pos.y, pos.z]
            safe, msg = self.check_robot_proximity(position)
            if not safe:
                result['warnings'].append(msg)
        
        # 4. 添加建议
        if obj.id.startswith('obstacle_'):
            result['suggestions'].append("考虑使用更具描述性的名称")
        
        if len(obj.primitives) > 1:
            result['suggestions'].append("复合物体可以考虑拆分为多个简单物体")
        
        result['valid'] = len(result['errors']) == 0
        return result
    
    def get_validation_report(self, obj: CollisionObject) -> str:
        """
        生成验证报告
        
        Args:
            obj: CollisionObject 实例
            
        Returns:
            str: 验证报告
        """
        result = self.validate_scene_addition(obj)
        
        report = []
        report.append(f"物体验证报告: {obj.id}")
        report.append("=" * 40)
        
        if result['valid']:
            report.append("✅ 物体基本有效")
        else:
            report.append("❌ 物体无效")
        
        if result['errors']:
            report.append("\n错误:")
            for error in result['errors']:
                report.append(f"  ❌ {error}")
        
        if result['warnings']:
            report.append("\n警告:")
            for warning in result['warnings']:
                report.append(f"  ⚠️  {warning}")
        
        if result['suggestions']:
            report.append("\n建议:")
            for suggestion in result['suggestions']:
                report.append(f"  💡 {suggestion}")
        
        if not result['errors'] and not result['warnings']:
            report.append("\n✅ 所有检查通过，物体可以安全添加")
        
        return "\n".join(report)