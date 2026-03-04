#!/usr/bin/env python3
import sys
import os

# 导入暴力启动器
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

# 测试导入
try:
    from grasping.gripper_controller import GripperController
    print("✅ 成功导入 GripperController")
    
    from ps_core.scene_client import PlanningSceneClient
    print("✅ 成功导入 PlanningSceneClient")
    
    print("\n🎉 所有导入成功！可以使用了。")
except ImportError as e:
    print(f"❌ 导入失败: {e}")