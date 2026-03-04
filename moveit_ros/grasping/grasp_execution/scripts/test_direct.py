#!/usr/bin/env python3
"""
测试直接模式
"""

import sys
import os

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
module_root = os.path.dirname(current_dir)
src_path = os.path.join(module_root, 'src')
sys.path.insert(0, src_path)

print(f"当前目录: {current_dir}")
print(f"模块根目录: {module_root}")
print(f"源码路径: {src_path}")

try:
    from grasping.gripper_controller import GripperController
    print("✓ GripperController 导入成功")
    
    # 创建控制器
    controller = GripperController()
    
    # 测试数据
    object_info = {
        "type": "box",
        "dimensions": [0.05, 0.05, 0.05],
        "position": [0.7, 0.0, 0.2],
        "orientation": [0, 0, 0, 1]
    }
    
    print(f"\n=== 测试抓取计算 ===")
    print(f"物体信息: {object_info}")
    
    result = controller.calculate_grasp_parameters(object_info, "auto")
    
    print(f"\n计算结果:")
    print(f"成功: {result.get('success', False)}")
    
    if result.get("success"):
        print(f"抓取策略: {result.get('grasp_strategy')}")
        print(f"夹爪宽度: {result.get('gripper_width', 0)*1000:.1f} mm")
        print(f"夹紧力: {result.get('gripper_force', 0):.1f} N")
        print(f"置信度: {result.get('confidence', 0):.2f}")
    else:
        print(f"错误: {result.get('error', '未知')}")
        
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
