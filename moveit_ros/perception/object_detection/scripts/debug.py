#!/usr/bin/env python3
"""
修复后的缓存调试脚本
"""

import os
import json

def debug_cache_system():
    """调试缓存系统"""
    cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
    objects_dir = os.path.join(cache_root, "core", "objects")
    
    print("=== 缓存系统调试 ===")
    print(f"缓存根目录: {cache_root}")
    print(f"物体目录: {objects_dir}")
    print(f"目录是否存在: {os.path.exists(objects_dir)}")
    
    if os.path.exists(objects_dir):
        # 列出所有文件
        files = os.listdir(objects_dir)
        print(f"\n目录内容 ({len(files)} 个文件):")
        for f in files:
            print(f"  - {f}")
        
        # 检查所有JSON文件
        json_files = [f for f in files if f.endswith('.json')]
        print(f"\nJSON文件数量: {len(json_files)}")
        
        # 详细检查每个文件
        for filename in json_files:
            filepath = os.path.join(objects_dir, filename)
            print(f"\n{'='*50}")
            print(f"检查文件: {filename}")
            print(f"完整路径: {filepath}")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"文件结构:")
                _print_dict_structure(data, indent=2)
                
                # 正确提取物体数据
                object_data = _extract_object_data_fixed(data)
                if object_data:
                    print(f"\n✓ 找到物体数据:")
                    print(f"  ID: {object_data.get('id', 'N/A')}")
                    print(f"  类型: {object_data.get('type', 'N/A')}")
                    print(f"  位置: {object_data.get('position', 'N/A')}")
                    print(f"  尺寸: {object_data.get('dimensions', 'N/A')}")
                    print(f"  操作: {object_data.get('operation', 'N/A')}")
                else:
                    print("\n✗ 未找到物体数据")
                    
            except Exception as e:
                print(f"\n✗ 读取文件失败: {e}")
    
    else:
        print(f"\n错误: 目录 {objects_dir} 不存在！")

def _print_dict_structure(data, indent=0, prefix=""):
    """打印字典结构"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{' ' * indent}{prefix}{key}: {type(value).__name__}")
                if isinstance(value, dict) and len(value) <= 5:
                    _print_dict_structure(value, indent + 2, "")
                elif isinstance(value, list) and len(value) <= 5:
                    print(f"{' ' * (indent + 2)}[{len(value)} items]")
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f"{' ' * indent}{prefix}{key}: {type(value).__name__}({value_str})")
    elif isinstance(data, list):
        print(f"{' ' * indent}{prefix}List[{len(data)} items]")

def _extract_object_data_fixed(data):
    """从数据结构中提取物体数据 - 修复版本"""
    # 根据你的数据结构：data -> data -> data
    if isinstance(data, dict):        # 第一层：data
        layer1 = data.get("data")
        if isinstance(layer1, dict):
            # 第二层：data 里面的 data
            layer2 = layer1.get("data")
            if isinstance(layer2, dict):
                # 第三层：这才是真正的物体数据
                if "id" in layer2 or "object_id" in layer2:
                    return layer2
            
            # 如果第二层就是物体数据
            if "id" in layer1 or "object_id" in layer1:
                return layer1
    
    return None

def test_extraction():
    """测试提取函数"""
    print("\n\n=== 测试数据提取 ===")
    
    # 模拟你的数据结构
    test_data = {
        "data": {
            "object_id": "test_cube",
            "object_type": "box", 
            "data": {
                "id": "test_cube",
                "operation": "ADD",
                "frame_id": "world",
                "cached_at": "2026-01-29 16:50:13",
                "primitive_type": 1,
                "dimensions": [0.05, 0.05, 0.05],
                "type": "box",
                "position": [0.7, 0.0, 0.2],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            },
            "saved_at": "2026-01-29 16:50:13",
            "version": "1.0"
        },
        "metadata": {},
        "saved_at": "2026-01-29 16:50:13",
        "filepath": "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects/object_box_1a7ce576.json"
    }
    
    result = _extract_object_data_fixed(test_data)
    if result:
        print("✓ 测试成功！提取的物体数据：")
        print(f"  ID: {result.get('id')}")
        print(f"  类型: {result.get('type')}")
        print(f"  位置: {result.get('position')}")
    else:
        print("✗ 测试失败！")

if __name__ == "__main__":
    debug_cache_system()
    test_extraction()