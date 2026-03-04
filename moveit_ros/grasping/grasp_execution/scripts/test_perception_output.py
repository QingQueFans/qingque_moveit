#!/usr/bin/env python3
"""
测试感知模块返回的数据结构
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
moveit_root = os.path.dirname(project_root)

perception_src = os.path.join(moveit_root, 'perception', 'object_detection', 'src')
sys.path.insert(0, perception_src)

from object_detection.object_detector import PureObjectDetector

print("=== 测试感知模块输出 ===")

# 创建检测器
detector = PureObjectDetector(None, None)
detector.set_mode("hybrid")

# 获取物体信息
result = detector.get_object("box")

print("返回结果:")
import json
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n=== 分析 ===")
print(f"success: {result.get('success')}")
print(f"error: {result.get('error', '无')}")
print(f"source: {result.get('source', '未知')}")

# 检查object字段
object_data = result.get("object", {})
print(f"\nobject字段内容:")
print(f"  类型: {object_data.get('type', '未找到')}")
print(f"  尺寸: {object_data.get('dimensions', '未找到')}")
print(f"  位置: {object_data.get('position', '未找到')}")
print(f"  ID: {object_data.get('id', '未找到')}")

# 如果是字典，显示所有键
if isinstance(object_data, dict):
    print(f"\nobject的所有键: {list(object_data.keys())}")
