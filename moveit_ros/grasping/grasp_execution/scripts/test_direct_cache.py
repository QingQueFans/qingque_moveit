#!/usr/bin/env python3
"""
直接读取缓存文件，测试数据结构
"""

import json
import os

# 你刚刚生成的缓存文件
cache_file = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects/object_box_34be958a.json"

print(f"读取缓存文件: {cache_file}")

with open(cache_file, 'r') as f:
    data = json.load(f)

print("\n=== 完整缓存结构 ===")
print(json.dumps(data, indent=2))

print("\n=== 提取物体信息 ===")
# 根据你的缓存结构
if 'data' in data:
    layer1 = data['data']
    print(f"第一层 data: {list(layer1.keys())}")
    
    if 'data' in layer1:
        object_data = layer1['data']
        print(f"\n真正的物体数据:")
        print(f"  ID: {object_data.get('id')}")
        print(f"  类型: {object_data.get('type')}")
        print(f"  尺寸: {object_data.get('dimensions')}")
        print(f"  位置: {object_data.get('position')}")
        print(f"  操作: {object_data.get('operation')}")
        
        # 这就是夹爪控制器需要的数据
        object_info_for_gripper = {
            "id": object_data.get('id'),
            "type": object_data.get('type'),
            "dimensions": object_data.get('dimensions'),
            "position": object_data.get('position'),
            "orientation": object_data.get('orientation')
        }
        
        print(f"\n夹爪控制器需要的格式:")
        print(json.dumps(object_info_for_gripper, indent=2))
    else:
        print("错误: 没有找到第二层 data 字段")
else:
    print("错误: 没有找到 data 字段")
