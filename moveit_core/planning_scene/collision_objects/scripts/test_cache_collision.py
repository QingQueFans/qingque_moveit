#!/usr/bin/env python3
import json
import os
import numpy as np

def check_collision_from_cache(obj1_id, obj2_id):
    """直接从缓存文件检查碰撞"""
    
    # 缓存文件路径
    cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    if not os.path.exists(cache_file):
        return False, {"error": "缓存文件不存在"}
    
    # 加载缓存
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except Exception as e:
        return False, {"error": f"加载缓存失败: {e}"}
    
    print(f"缓存类型: {type(cache)}")
    print(f"缓存内容: {cache}")
    
    # 查找物体
    if isinstance(cache, dict):
        # 字典格式
        if obj1_id not in cache:
            return False, {"error": f"物体 {obj1_id} 不在缓存中"}
        if obj2_id not in cache:
            return False, {"error": f"物体 {obj2_id} 不在缓存中"}
        
        obj1 = cache[obj1_id]
        obj2 = cache[obj2_id]
        
    elif isinstance(cache, list):
        # 列表格式
        obj1 = None
        obj2 = None
        for item in cache:
            if isinstance(item, dict):
                if item.get('id') == obj1_id or item.get('name') == obj1_id:
                    obj1 = item
                if item.get('id') == obj2_id or item.get('name') == obj2_id:
                    obj2 = item
        
        if not obj1:
            return False, {"error": f"物体 {obj1_id} 不在缓存中"}
        if not obj2:
            return False, {"error": f"物体 {obj2_id} 不在缓存中"}
    else:
        return False, {"error": f"未知缓存格式: {type(cache)}"}
    
    # 提取位置和尺寸
    def get_position(obj):
        if isinstance(obj, dict):
            if 'position' in obj:
                return obj['position']
            elif 'pose' in obj and 'position' in obj['pose']:
                return obj['pose']['position']
        return [0, 0, 0]
    
    def get_size(obj):
        if isinstance(obj, dict):
            if 'dimensions' in obj:
                return obj['dimensions']
            elif 'size' in obj:
                return obj['size']
        return [0.1, 0.1, 0.1]
    
    pos1 = get_position(obj1)
    pos2 = get_position(obj2)
    size1 = get_size(obj1)
    size2 = get_size(obj2)
    
    print(f"\n物体 {obj1_id}: 位置 {pos1}, 尺寸 {size1}")
    print(f"物体 {obj2_id}: 位置 {pos2}, 尺寸 {size2}")
    
    # 碰撞检测
    collision = (
        abs(pos1[0] - pos2[0]) < (size1[0]/2 + size2[0]/2) and
        abs(pos1[1] - pos2[1]) < (size1[1]/2 + size2[1]/2) and
        abs(pos1[2] - pos2[2]) < (size1[2]/2 + size2[2]/2)
    )
    
    info = {
        "position1": pos1,
        "position2": pos2,
        "size1": size1,
        "size2": size2,
        "collision": collision
    }
    
    return collision, info

# 测试
print("直接从缓存检查碰撞:")
collision, info = check_collision_from_cache("debug1", "debug2")
print(f"debug1 ↔ debug2: {collision}")
print(f"信息: {info}")

print()

collision, info = check_collision_from_cache("box1", "box2")
print(f"box1 ↔ box2: {collision}")
print(f"信息: {info}")
