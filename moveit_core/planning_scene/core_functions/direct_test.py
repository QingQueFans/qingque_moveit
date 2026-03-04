#!/usr/bin/env python3
import sys
import os

print("=" * 60)
print("诊断导入问题")
print("=" * 60)

# 1. 打印当前目录
print(f"当前目录: {os.getcwd()}")

# 2. 添加 src 目录
src_path = os.path.join(os.getcwd(), 'src')
print(f"添加路径: {src_path}")
print(f"路径存在: {os.path.exists(src_path)}")

sys.path.insert(0, src_path)

# 3. 检查 ps_core 目录
ps_core_path = os.path.join(src_path, 'ps_core')
print(f"ps_core路径: {ps_core_path}")
print(f"ps_core存在: {os.path.exists(ps_core_path)}")

if os.path.exists(ps_core_path):
    print("ps_core目录内容:")
    for item in os.listdir(ps_core_path):
        print(f"  - {item}")

# 4. 尝试导入
print("\n尝试导入...")
try:
    import ps_core
    print("✓ 成功导入 ps_core 包")
    print(f"  包位置: {ps_core.__file__}")
except ImportError as e:
    print(f"✗ 导入 ps_core 失败: {e}")

# 5. 尝试直接导入模块
print("\n尝试直接导入模块...")
try:
    from ps_core import scene_client
    print("✓ 成功导入 scene_client 模块")
    print(f"  模块位置: {scene_client.__file__}")
    
    # 检查是否有 PlanningSceneClient 类
    if hasattr(scene_client, 'PlanningSceneClient'):
        print("✓ 找到 PlanningSceneClient 类")
    else:
        print("✗ 未找到 PlanningSceneClient 类")
        print(f"  scene_client 中的内容: {dir(scene_client)}")
except ImportError as e:
    print(f"✗ 导入 scene_client 失败: {e}")

print("=" * 60)
