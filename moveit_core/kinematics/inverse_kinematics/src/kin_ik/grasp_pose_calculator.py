#!/usr/bin/env python3
"""
抓取位姿计算器 - 基于物体信息计算抓取位姿
专为逆运动学求解设计
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
from .object_pose_fetcher import ObjectPoseFetcher

class GraspPoseCalculator:
    """抓取位姿计算器"""
    
    def __init__(self):
        """初始化计算器"""
        self.pose_fetcher = ObjectPoseFetcher()
        print("[GraspPoseCalculator] 初始化完成")
    
    def calculate_grasp_pose(self,
                           object_id: str,
                           grasp_strategy: str = "top",
                           offset_distance: float = 0.05,
                           approach_angle: float = 0.0) -> Optional[List[float]]:
        """
        计算抓取位姿
        
        Args:
            object_id: 物体ID
            grasp_strategy: 抓取策略 ("top", "side", "front", "back")
            offset_distance: 抓取偏移距离（米）
            approach_angle: 接近角度（弧度）
        
        Returns:
            7元素抓取位姿 [x, y, z, qx, qy, qz, qw]
        """
        print(f"[GraspPoseCalculator] 为物体 {object_id} 计算抓取位姿")
        print(f"  策略: {grasp_strategy}, 偏移: {offset_distance}m")
        
        # 1. 获取物体基础信息
        object_pose = self.pose_fetcher.get_object_pose(object_id, format="dict")
        if not object_pose:
            print(f"[GraspPoseCalculator] ❌ 无法获取物体位姿")
            return None
        
        dimensions = self.pose_fetcher.get_object_dimensions(object_id)
        object_type = self.pose_fetcher.get_object_type(object_id)
        
        print(f"[GraspPoseCalculator] 物体类型: {object_type}, 尺寸: {dimensions}")
        
        # 2. 提取基础位姿
        base_position = object_pose["position"]  # [x, y, z]
        base_orientation = object_pose["orientation"]  # [qx, qy, qz, qw]
        
        # 3. 根据策略计算抓取偏移
        offset_vector = self._calculate_grasp_offset(
            grasp_strategy=grasp_strategy,
            dimensions=dimensions,
            offset_distance=offset_distance
        )
        
        # 4. 计算抓取位姿
        grasp_position = [
            base_position[0] + offset_vector[0],
            base_position[1] + offset_vector[1],
            base_position[2] + offset_vector[2]
        ]
        
        # 5. 计算抓取方向（基于策略）
        grasp_orientation = self._calculate_grasp_orientation(
            grasp_strategy=grasp_strategy,
            base_orientation=base_orientation,
            approach_angle=approach_angle
        )
        
        # 6. 合并结果
        grasp_pose = grasp_position + grasp_orientation
        
        print(f"[GraspPoseCalculator] ✅ 计算完成")
        print(f"  基础位姿: {base_position}")
        print(f"  抓取位姿: {grasp_position}")
        print(f"  抓取方向: {grasp_orientation}")
        
        return grasp_pose
    
    def _calculate_grasp_offset(self,
                            grasp_strategy: str,
                            dimensions: List[float],
                            offset_distance: float) -> List[float]:
        """计算抓取偏移向量 - 临时禁用偏移"""
        length, width, height = dimensions
        
        if grasp_strategy == "top":
            # 在物体正上方 - 不加偏移
            return [0, 0, height/2]  # ← 删掉 + offset_distance
        
        elif grasp_strategy == "side":
            # 在物体侧面（长边）- 不加偏移
            return [length/2, 0, 0]  # ← 删掉 + offset_distance
        
        elif grasp_strategy == "front":
            # 在物体正面（宽边）- 不加偏移
            return [0, width/2, 0]  # ← 删掉 + offset_distance
        
        elif grasp_strategy == "back":
            # 在物体背面 - 不加偏移
            return [0, -width/2, 0]  # ← 删掉 - offset_distance
        
        elif grasp_strategy == "bottom":
            # 在物体下方 - 不加偏移
            return [0, 0, -height/2]  # ← 删掉 - offset_distance
        
        else:
            # 默认：在物体正上方 - 不加偏移
            return [0, 0, height/2]  # ← 删掉 + offset_distance
    
    def _calculate_grasp_orientation(self,
                                   grasp_strategy: str,
                                   base_orientation: List[float],
                                   approach_angle: float) -> List[float]:
        """计算抓取方向"""        # 简化为保持物体方向，可根据策略调整
        return base_orientation
    
    def calculate_multiple_grasps(self,
                                object_id: str,
                                grasp_strategies: List[str] = None) -> Dict[str, List[float]]:
        """计算多个抓取位姿"""
        if grasp_strategies is None:
            grasp_strategies = ["top", "side", "front"]
        
        results = {}
        for strategy in grasp_strategies:
            grasp_pose = self.calculate_grasp_pose(object_id, strategy)
            if grasp_pose:
                results[strategy] = grasp_pose
        
        return results
    
    def validate_grasp_pose(self,
                          object_id: str,
                          grasp_pose: List[float],
                          tolerance: float = 0.01) -> bool:
        """验证抓取位姿是否合理"""
        # 1. 获取物体位姿
        object_pose = self.pose_fetcher.get_object_pose(object_id, format="list")
        if not object_pose:
            return False
        
        # 2. 检查抓取点是否在物体附近
        object_pos = object_pose[:3]
        grasp_pos = grasp_pose[:3]
        
        distance = np.linalg.norm(np.array(grasp_pos) - np.array(object_pos))
        
        # 3. 获取物体尺寸
        dimensions = self.pose_fetcher.get_object_dimensions(object_id)
        max_dimension = max(dimensions) if dimensions else 0.2
        
        # 抓取点应该在物体附近（1.5倍最大尺寸内）
        is_valid = distance <= max_dimension * 1.5
        
        print(f"[GraspPoseCalculator] 验证结果: {'有效' if is_valid else '无效'}")
        print(f"  距离物体: {distance:.3f}m, 最大尺寸: {max_dimension:.3f}m")
        
        return is_valid


# ========== IK专用函数 ==========

def get_grasp_pose_for_ik(object_id: str, **kwargs) -> Optional[List[float]]:
    """为IK求解获取抓取位姿"""
    calculator = GraspPoseCalculator()
    return calculator.calculate_grasp_pose(object_id, **kwargs)


def get_grasp_command_string(object_id: str, grasp_strategy="top") -> str:
    """生成可以直接执行的命令字符串"""
    calculator = GraspPoseCalculator()
    grasp_pose = calculator.calculate_grasp_pose(object_id, grasp_strategy)
    
    if grasp_pose and len(grasp_pose) == 7:
        pose_str = " ".join([f"{x:.6f}" for x in grasp_pose])
        return f"kin-ik --pose \"{pose_str}\" --object-id \"{object_id}\""
    else:
        return "# 无法计算抓取位姿"


# ========== 命令行接口 ==========

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='抓取位姿计算器')
    parser.add_argument('--object-id', type=str, required=True, help='物体ID')
    parser.add_argument('--grasp-strategy', type=str, default='top',
                       choices=['top', 'side', 'front', 'back', 'bottom'],
                       help='抓取策略')
    parser.add_argument('--offset', type=float, default=0.05,
                       help='抓取偏移距离（米）')
    parser.add_argument('--list-strategies', action='store_true',
                       help='列出所有抓取策略')
    
    args = parser.parse_args()
    
    if args.list_strategies:
        print("可用的抓取策略:")
        print("  top    - 顶部抓取（默认）")
        print("  side   - 侧面抓取")
        print("  front  - 正面抓取")
        print("  back   - 背面抓取")
        print("  bottom - 底部抓取")
        exit(0)
    
    calculator = GraspPoseCalculator()
    grasp_pose = calculator.calculate_grasp_pose(
        args.object_id,
        args.grasp_strategy,
        args.offset
    )
    
    if grasp_pose:
        print(f"\n✅ 抓取位姿计算结果:")
        print(f"   物体ID: {args.object_id}")
        print(f"   抓取策略: {args.grasp_strategy}")
        print(f"   偏移距离: {args.offset}m")
        print(f"   抓取位姿: {grasp_pose}")
        
        # 输出可以直接用于kin-ik的格式
        print(f"\n📋 可以直接用于 kin-ik 命令:")
        pose_str = " ".join([str(x) for x in grasp_pose])
        print(f"   kin-ik --pose \"{pose_str}\" --object-id \"{args.object_id}\"")
        
        # 验证位姿
        is_valid = calculator.validate_grasp_pose(args.object_id, grasp_pose)
        print(f"\n🔍 验证结果: {'✅ 有效' if is_valid else '❌ 可能无效'}")
    else:
        print(f"❌ 无法计算抓取位姿")