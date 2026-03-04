#!/usr/bin/env python3
"""
测试感知检测器模式设置
"""

import sys
import os

# 设置路径（按照你项目的工作方式）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
moveit_root = os.path.dirname(project_root)

print(f"当前目录: {current_dir}")
print(f"项目根目录: {project_root}")
print(f"MoveIt根目录: {moveit_root}")

# 添加感知模块路径（这是关键！）
perception_src = os.path.join(moveit_root, 'perception', 'object_detection', 'src')
print(f"感知源码路径: {perception_src}")
print(f"路径存在: {os.path.exists(perception_src)}")

if os.path.exists(perception_src):
    sys.path.insert(0, perception_src)
    
    # 列出目录内容
    print(f"\n目录内容:")
    for item in os.listdir(perception_src):
        print(f"  - {item}")
        
        # 如果是目录，显示子内容
        if os.path.isdir(os.path.join(perception_src, item)):
            sub_path = os.path.join(perception_src, item)
            for subitem in os.listdir(sub_path):
                print(f"    * {subitem}")
    
    # 尝试导入
    try:
        print(f"\n尝试导入...")
        from object_detection.object_detector import PureObjectDetector
        print("✓ 导入成功！")
        
        # 测试
        print("\n=== 测试模式设置 ===")
        detector = PureObjectDetector(None, None)
        print(f"初始模式: {getattr(detector, 'mode', '未知')}")
        
        # 尝试设置模式
        if hasattr(detector, 'set_mode'):
            detector.set_mode("cache_only")
            print(f"设置cache_only后模式: {getattr(detector, 'mode', '未知')}")
        
        # 显示所有属性
        print(f"\n检测器属性:")
        for attr in dir(detector):
            if not attr.startswith('_'):
                print(f"  - {attr}")
                
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("✗ 感知源码目录不存在！")
