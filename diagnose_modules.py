#!/usr/bin/env python3
"""
MoveIt暴力导入启动器 - 最终修正版
添加 grasping 模块支持
"""

import sys
import os

# ========== 暴力设置所有路径 ==========
print("🚀 MoveIt暴力启动中...")

MOVEIT_ROOT = "/home/diyuanqiongyu/qingfu_moveit"

# 🔥 修正后的路径列表（基于诊断结果）
ALL_PATHS = [
    # ========== moveit_core 模块 ==========
    # 核心模块
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/core_functions/src",  # ps_core
    f"{MOVEIT_ROOT}/moveit_core/cache_manager/src",  # ps_cache
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_objects/src",  # ps_objects
    f"{MOVEIT_ROOT}/moveit_core/kinematics/inverse_kinematics/src",  # kin_ik
    
    # 其他规划场景模块
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_detection/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/unified_tools/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/state_validation/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/acm_management/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/visualization/src",
    
    # ========== moveit_ros 模块 ==========
    # 抓取相关 - 关键路径！✅
    f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src",  # grasping 模块在这里！
    f"{MOVEIT_ROOT}/moveit_ros/grasping/capability_servers/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_planning/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_visualization/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/object_perception/src",
    
    # 规划执行相关
    f"{MOVEIT_ROOT}/moveit_ros/move_group/trajectory_execution/src",
    
    # 感知相关
    f"{MOVEIT_ROOT}/moveit_ros/perception/object_detection/src",
    f"{MOVEIT_ROOT}/moveit_ros/perception/depth_image_processing/src",
    f"{MOVEIT_ROOT}/moveit_ros/perception/octomap_integration/src",
    f"{MOVEIT_ROOT}/moveit_ros/perception/sensor_integration/src",
    f"{MOVEIT_ROOT}/moveit_ros/perception/point_cloud_processing/src",
    
    # ========== moveit_plugins 模块 ==========
    f"{MOVEIT_ROOT}/moveit_plugins/moveit_controller_manager/src",
    f"{MOVEIT_ROOT}/moveit_plugins/controller_manager/src",
    
    # ========== 其他 ==========
    f"{MOVEIT_ROOT}/moveit_planners/src",
    f"{MOVEIT_ROOT}/moveit_ros/planning_interface/move_group_interface/src",
]

# 智能添加
added_paths = []
for path in ALL_PATHS:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        added_paths.append(path)

print(f"✅ 已添加 {len(added_paths)} 个路径")

# ========== 验证关键模块 ==========
def check_imports():
    """快速检查关键模块"""
    print("\n🔍 检查关键模块...")
    
    # 原有的模块
    core_modules = [
        ("ps_core.scene_client", "PlanningSceneClient"),
        ("ps_cache.object_cache", "ObjectCache"),
        ("ps_objects.object_manager", "ObjectManager"),
        ("kin_ik.ik_solver", "IKSolver"),
    ]
    
    for module, item in core_modules:
        try:
            exec(f"from {module} import {item}")
            print(f"  ✅ {module}.{item}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
    
    # 新增：检查 grasping 模块 ✅
    print("\n🔍 检查 grasping 模块...")
    
    grasping_modules = [
        ("grasping.gripper_controller", "GripperController"),
        ("grasping.object_detector", "ObjectDetector"),
        ("grasping", "__init__"),  # 检查包本身
    ]
    
    for module, item in grasping_modules:
        try:
            if item == "__init__":
                exec(f"import {module}")
                print(f"  ✅ {module} (包)")
            else:
                exec(f"from {module} import {item}")
                print(f"  ✅ {module}.{item}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")            # 如果是 gripper_controller，提供详细诊断
            if module == "grasping.gripper_controller":
                grasping_path = f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src"
                gripper_file = os.path.join(grasping_path, "grasping", "gripper_controller.py")
                if os.path.exists(gripper_file):
                    print(f"    文件存在: {gripper_file}")
                    print(f"    目录内容: {os.listdir(os.path.dirname(gripper_file))}")

# ========== 创建模块别名（如果需要） ==========
def create_aliases():
    """创建模块别名以兼容不同导入方式"""
    print("\n🔧 创建模块别名...")
    
    # 尝试导入实际模块并创建别名
    import importlib
    
    # 检查并创建 ps_core 别名
    try:
        ps_core_module = importlib.import_module("ps_core")
        print(f"  ✅ ps_core 直接可用: {ps_core_module.__file__}")
    except ImportError:
        print("  ⚠️  ps_core 不可直接导入")
    
    # 检查 grasping 包
    try:
        grasping_module = importlib.import_module("grasping")
        print(f"  ✅ grasping 直接可用: {grasping_module.__file__}")
    except ImportError as e:
        print(f"  ❌ grasping 导入失败: {e}")
        
        # 尝试直接导入 gripper_controller
        try:
            # 检查文件是否存在
            gripper_path = f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src/grasping/gripper_controller.py"
            if os.path.exists(gripper_path):
                print(f"  📄 gripper_controller.py 文件存在: {gripper_path}")
                
                # 尝试直接添加到模块中
                sys.path.insert(0, f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src")
                
                try:
                    import grasping.gripper_controller
                    print("  ✅ 通过直接路径导入成功")
                except:
                    # 创建 grasping 包的占位符
                    grasping_package_path = f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src/grasping"
                    if os.path.exists(os.path.join(grasping_package_path, "__init__.py")):
                        print(f"  ✅ grasping 包有 __init__.py")
                    else:
                        print(f"  ⚠️ grasping 包缺少 __init__.py")
        except Exception as ex:
            print(f"  ❌ 诊断失败: {ex}")

# 自动执行检查
check_imports()
create_aliases()

print("\n🚀 MoveIt环境就绪！")
print("💡 提示：现在可以直接导入模块，例如：")
print("  from ps_core.scene_client import PlanningSceneClient")
print("  from ps_objects.object_manager import ObjectManager")
print("  from grasping.gripper_controller import GripperController")