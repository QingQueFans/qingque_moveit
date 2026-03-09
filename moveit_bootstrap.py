#!/usr/bin/env python3
"""
MoveIt暴力导入启动器 - 修正路径（带所有模块）
"""

import sys
import os

# ========== 暴力设置所有路径 ==========
print("🚀 MoveIt暴力启动中...")

MOVEIT_ROOT = "/home/diyuanqiongyu/qingfu_moveit"

# 所有可能的路径（基于实际诊断结果）
ALL_PATHS = [
    # ========== moveit_core 模块 ==========
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/core_functions/src",
    f"{MOVEIT_ROOT}/moveit_core/cache_manager/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_objects/src",
    f"{MOVEIT_ROOT}/moveit_core/kinematics/inverse_kinematics/src",
    f"{MOVEIT_ROOT}/moveit_core/kinematics/forward_kinematics/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_detection/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/unified_tools/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/state_validation/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/acm_management/src",
    f"{MOVEIT_ROOT}/moveit_core/planning_scene/visualization/src",
    
    # ========== moveit_plugins 模块 ==========
    f"{MOVEIT_ROOT}/moveit_plugins/moveit_controller_manager/src",
    f"{MOVEIT_ROOT}/moveit_plugins/kinematics_plugins/ml_seed_predictor/src",
    
    # ========== moveit_ros 模块 ==========
    f"{MOVEIT_ROOT}/moveit_ros/move_group/trajectory_execution/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/capability_servers/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/capability_servers_core/src",
    f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src",
    f"{MOVEIT_ROOT}/moveit_ros/perception/object_detection/src",
    
    # ========== moveit_planners 模块 ==========
    f"{MOVEIT_ROOT}/moveit_planners/src",
    
    # ========== 添加 pymoveit2 路径 ==========
    f"{MOVEIT_ROOT}/install/pymoveit2/local/lib/python3.10/dist-packages",
]

# 智能添加
added_paths = []
for path in ALL_PATHS:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        added_paths.append(path)

print(f"✅ 已添加 {len(added_paths)} 个路径")

# ========== 检查是否已经初始化 ==========
_MOVEIT_BOOTSTRAP_INITIALIZED = False

def init_moveit_paths(force=False):
    """
    初始化MoveIt路径
    
    Args:
        force: 是否强制重新初始化
    """
    global _MOVEIT_BOOTSTRAP_INITIALIZED
    
    if _MOVEIT_BOOTSTRAP_INITIALIZED and not force:
        return False
    
    print("🚀 MoveIt暴力启动中...")
    
    MOVEIT_ROOT = "/home/diyuanqiongyu/qingfu_moveit"
    
    ALL_PATHS = [
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/core_functions/src",
        f"{MOVEIT_ROOT}/moveit_core/cache_manager/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_objects/src",
        f"{MOVEIT_ROOT}/moveit_core/kinematics/inverse_kinematics/src",
        f"{MOVEIT_ROOT}/moveit_core/kinematics/forward_kinematics/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/collision_detection/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/unified_tools/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/state_validation/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/acm_management/src",
        f"{MOVEIT_ROOT}/moveit_core/planning_scene/visualization/src",
        f"{MOVEIT_ROOT}/moveit_plugins/moveit_controller_manager/src",
        f"{MOVEIT_ROOT}/moveit_plugins/kinematics_plugins/ml_seed_predictor/src",
        f"{MOVEIT_ROOT}/moveit_ros/move_group/trajectory_execution/src",
        f"{MOVEIT_ROOT}/moveit_ros/grasping/capability_servers/src",
        f"{MOVEIT_ROOT}/moveit_ros/grasping/capability_servers_core/src",
        f"{MOVEIT_ROOT}/moveit_ros/grasping/grasp_execution/src",
        f"{MOVEIT_ROOT}/moveit_ros/perception/object_detection/src",
        f"{MOVEIT_ROOT}/moveit_planners/src",
        f"{MOVEIT_ROOT}/install/pymoveit2/local/lib/python3.10/dist-packages",
    ]
    
    added_paths = []
    for path in ALL_PATHS:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            added_paths.append(path)
    
    print(f"✅ 已添加 {len(added_paths)} 个路径")
    
    _MOVEIT_BOOTSTRAP_INITIALIZED = True
    return True

# ========== 验证关键模块 ==========
def check_imports():
    """快速检查关键模块"""
    print("\n🔍 检查关键模块...")
    
    modules = [
        ("ps_core.scene_client", "PlanningSceneClient"),
        ("ps_cache.object_cache", "ObjectCache"),
        ("ps_objects.object_manager", "ObjectManager"),
        ("kin_ik.ik_solver", "IKSolver"),
        ("kin_fk.fk_solver", "FKSolver"),
        ("kin_fk.pose_computer", "PoseComputer"),
        ("ml_seed_predictor", "MLSeedPredictor"),
        ("pymoveit2", "MoveIt2"),
        ("gripper_controller_manager", "GripperControllerManager"),
        ("trajectory_execution", "TrajectoryExecutionManager"),
        ("capability_servers_core.pick_action_server", "PickActionServer"),
    ]
    
    for module, item in modules:
        try:
            exec(f"from {module} import {item}")
            print(f"  ✅ {module}.{item}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")

# 自动执行检查
check_imports()

print("🚀 MoveIt环境就绪！")