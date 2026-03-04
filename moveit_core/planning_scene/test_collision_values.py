#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.expanduser('~/qingfu_moveit/moveit_core/planning_scene/core_functions/src'))
sys.path.append(os.path.expanduser('~/qingfu_moveit/moveit_core/planning_scene/collision_detection/src'))

from ps_core.scene_client import PlanningSceneClient
from ps_collision.collision_checker import CollisionChecker

# 初始化
client = PlanningSceneClient()
checker = CollisionChecker(client)

print("=== 直接测试碰撞检测 ===")

# 测试 debug1 和 debug2
print("\n1. 测试 debug1 ↔ debug2 (完全相同位置):")
collision1, info1 = checker.check_collision("debug1", "debug2")
print(f"   碰撞结果: {collision1}")
print(f"   详细信息: {info1}")

# 测试 box1 和 box2
print("\n2. 测试 box1 ↔ box2 (部分重叠):")
collision2, info2 = checker.check_collision("box1", "box2")
print(f"   碰撞结果: {collision2}")
print(f"   详细信息: {info2}")

# 手动计算验证
print("\n3. 手动计算验证:")
print("   debug1 和 debug2:")
print("   位置相同，尺寸相同，应该完全碰撞")

print("\n   box1 和 box2:")
print("   box1: 位置 (0.5,0.2,0.4), 尺寸 (0.2,0.1,0.15)")
print("   box2: 位置 (0.4,0.2,0.4), 尺寸 (0.1,0.1,0.15)")
print("   X轴: |0.5-0.4| = 0.1 < (0.1+0.05) = 0.15? ✓ 应该碰撞")
print("   Y轴: |0.2-0.2| = 0.0 < (0.05+0.05) = 0.1? ✓ 应该碰撞")
print("   Z轴: |0.4-0.4| = 0.0 < (0.075+0.075) = 0.15? ✓ 应该碰撞")
print("   结论: 应该检测为碰撞！")
