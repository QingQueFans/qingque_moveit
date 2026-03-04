#!/usr/bin/env python3
"""
基础场景操作示例
"""
import sys
import os

# 添加路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from ps_core.scene_client import PlanningSceneClient
from ps_core.scene_manager import PlanningSceneManager
from ps_core.utils import create_pose, print_pose

def demo_basic_operations():
    """演示基本场景操作"""
    print("=" * 60)
    print("基础场景操作演示")
    print("=" * 60)
    
    # 1. 创建客户端
    print("\n1. 创建 PlanningScene 客户端...")
    client = PlanningSceneClient()
    manager = PlanningSceneManager(client)
    
    # 2. 显示当前场景
    print("\n2. 当前场景信息:")
    client.print_scene_info()
    
    # 3. 列出所有物体
    print("\n3. 列出碰撞物体:")
    objects = client.get_collision_objects()
    if objects:
        for obj in objects:
            print(f"  - {obj}")
    else:
        print("  场景中没有碰撞物体")
    
    # 4. 添加物体示例
    print("\n4. 添加碰撞物体...")
    
    # 添加一个桌子
    print("  添加桌子 (1.0x1.0x0.1m)...")
    success = manager.add_box(
        "table",
        position=[0.5, 0.0, 0.05],  # 位置 (z=高度的一半)
        size=[1.0, 1.0, 0.1]        # 尺寸 (长,宽,高)
    )
    print(f"  结果: {'成功' if success else '失败'}")
    
    # 添加一个障碍物
    print("  添加障碍物 (0.2x0.2x0.4m)...")
    success = manager.add_box(
        "obstacle",
        position=[0.3, 0.3, 0.2],
        size=[0.2, 0.2, 0.4]
    )
    print(f"  结果: {'成功' if success else '失败'}")
    
    # 5. 验证添加结果
    print("\n5. 验证添加结果:")
    objects = client.get_collision_objects()
    print(f"  当前有 {len(objects)} 个碰撞物体:")
    for obj in objects:
        print(f"    - {obj}")
    
    # 6. 移除物体
    print("\n6. 移除桌子...")
    success = manager.remove_object("table")
    success = manager.remove_object("obstacle")
    print(f"  结果: {'成功' if success else '失败'}")
    
    # 7. 最终状态
    print("\n7. 最终场景状态:")
    client.print_scene_info()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)

def demo_pose_utilities():
    """演示位姿工具函数"""
    print("\n" + "=" * 60)
    print("位姿工具函数演示")
    print("=" * 60)
    
    # 创建位姿
    pose1 = create_pose(x=0.5, y=0.2, z=0.8)
    print("\n1. 使用 create_pose 创建位姿:")
    print_pose(pose1, "示例位姿")
    
    # 带旋转的位姿
    pose2 = create_pose(x=1.0, y=0.5, z=0.3, 
                       qx=0.0, qy=0.707, qz=0.0, qw=0.707)
    print("\n2. 带旋转的位姿:")
    print_pose(pose2, "旋转位姿")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        demo_basic_operations()
        demo_pose_utilities()
    except KeyboardInterrupt:
        print("\n\n演示被中断")
    except Exception as e:
        print(f"\n错误: {e}")