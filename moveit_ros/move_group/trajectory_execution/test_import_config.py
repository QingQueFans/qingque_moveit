#!/usr/bin/env python3
"""
测试导入配置是否生效
"""
import sys
import os

print("=" * 60)
print("导入配置测试")
print("=" * 60)

# 显示当前Python版本
print(f"Python版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")
print()

# 显示sys.path中的路径
print("当前sys.path路径:")
for i, path in enumerate(sys.path, 1):
    print(f"  {i:2d}. {path}")
print()

# 测试导入的路径
test_paths = [
    ("控制器管理器", "/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/moveit_controller_manager/src"),
    ("规划场景", "/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/core_functions/src"),
    ("轨迹执行", "/home/diyuanqiongyu/qingfu_moveit/moveit_ros/move_group/trajectory_execution/src")
]

print("📁 检查关键路径:")
for name, path in test_paths:
    if os.path.exists(path):
        print(f"  ✅ {name}: {path}")
        # 检查是否有Python模块
        if os.path.exists(os.path.join(path, "__init__.py")):
            print(f"     包含__init__.py (Python包)")
    else:
        print(f"  ❌ {name}路径不存在: {path}")
print()

# 测试导入
print("🔄 测试导入关键模块:")
try:
    from ps_core.scene_client import PlanningSceneClient
    print("  ✅ PlanningSceneClient - 导入成功")
except ImportError as e:
    print(f"  ❌ PlanningSceneClient - 导入失败: {e}")

try:
    from moveit_controller_manager import MoveItControllerManager
    print("  ✅ MoveItControllerManager - 导入成功")
except ImportError as e:
    print(f"  ❌ MoveItControllerManager - 导入失败: {e}")

try:
    from trajectory_execution import TrajectoryExecutionManager
    print("  ✅ TrajectoryExecutionManager - 导入成功")
except ImportError as e:
    print(f"  ❌ TrajectoryExecutionManager - 导入失败: {e}")

print()
print("📊 导入测试完成")
print("=" * 60)
