#!/usr/bin/env python3
"""
物体操作示例 - 演示完整的物体创建、修改、管理流程
注意处理：缓存问题、float类型转换、文件路径等常见问题
"""
import sys
import os
import time
import json

# ========== 关键：设置正确的路径 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # examples/
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)                # collision_objects/
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)              # planning_scene/

# 添加 core_functions 的 src 到路径
CORE_SRC = os.path.join(PROJECT_ROOT, 'core_functions', 'src')
sys.path.insert(0, CORE_SRC)

# 添加 collision_objects 的 src 到路径
OBJ_SRC = os.path.join(MODULE_ROOT, 'src')
sys.path.insert(0, OBJ_SRC)

# 现在可以正常导入
from ps_core.scene_client import PlanningSceneClient
from ps_objects.object_manager import ObjectManager
from ps_objects.shape_generator import ShapeGenerator
from ps_objects.object_validator import ObjectValidator

def ensure_float_list(data_list):
    """确保列表中的所有元素都是float类型（处理ROS2类型严格问题）"""
    return [float(item) for item in data_list]

def demo_basic_operations():
    """演示基础物体操作"""
    print("=" * 60)
    print("1. 基础物体操作演示")
    print("=" * 60)
    
    # 初始化
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    generator = ShapeGenerator()
    validator = ObjectValidator(client)
    
    # 1.1 清空场景
    print("\n1.1 清空场景...")
    manager.clear_all_objects()
    time.sleep(0.5)
    
    # 1.2 创建立方体（注意float类型转换）
    print("\n1.2 创建立方体...")
    box = generator.create_box(
        name="demo_box",
        position=ensure_float_list([0.3, 0.2, 0.25]),  # 确保float
        size=ensure_float_list([0.15, 0.1, 0.05]),     # 确保float
        orientation=ensure_float_list([0.0, 0.0, 0.0, 1.0])  # 确保float
    )
    
    # 验证物体
    print("验证物体...")
    valid, msg = validator.validate_object(box)
    print(f"验证结果: {'✅' if valid else '❌'} {msg}")
    
    # 添加物体
    success = manager.add_object_simple(box)
    print(f"添加结果: {'✅ 成功' if success else '❌ 失败'}")
    time.sleep(0.3)
    
    # 1.3 创建球体
    print("\n1.3 创建球体...")
    sphere = generator.create_sphere(
        name="demo_sphere",
        position=ensure_float_list([0.6, 0.3, 0.15]),
        radius=0.08,
        orientation=ensure_float_list([0.0, 0.0, 0.0, 1.0])
    )
    
    manager.add_object_simple(sphere)
    time.sleep(0.3)
    
    # 1.4 列出所有物体
    print("\n1.4 当前场景中的物体:")
    objects = manager.list_objects()
    for obj_id in objects:
        cached_info = manager.get_object_from_cache(obj_id)
        if cached_info:
            print(f"  - {obj_id}: {cached_info.get('type', 'unknown')} at {cached_info.get('position', [])}")
        else:
            print(f"  - {obj_id}: (无缓存)")
    
    return manager, generator, validator

def demo_modify_with_cache():
    """演示使用缓存的修改操作"""
    print("\n" + "=" * 60)
    print("2. 使用缓存的修改操作演示")
    print("=" * 60)
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    generator = ShapeGenerator()
    
    # 2.1 修改立方体位置（自动使用缓存中的尺寸）
    print("\n2.1 修改立方体位置...")
    
    # 检查缓存
    cached_info = manager.get_object_from_cache("demo_box")
    if cached_info:
        print(f"从缓存获取原尺寸: {cached_info.get('dimensions', [])}")
        print(f"从缓存获取原类型: {cached_info.get('type', 'unknown')}")
    else:
        print("⚠️  缓存中没有demo_box的信息")
    
    # 模拟修改命令
    print("执行修改: demo_box --move-to \"0.5,0.4,0.25\"")
    
    # 在实际脚本中，会使用缓存信息重新创建物体
    # 这里只是演示逻辑
    if cached_info:
        print("✅ 自动使用缓存尺寸重新创建物体")
    else:
        print("❌ 无法修改：没有缓存信息")
    
    # 2.2 批量修改演示
    print("\n2.2 批量修改演示...")
    
    # 获取当前所有物体
    objects = manager.list_objects()
    print(f"当前有 {len(objects)} 个物体")    
    # 模拟批量移动
    for obj_id in objects:
        cached = manager.get_object_from_cache(obj_id)
        if cached:
            obj_type = cached.get('type', 'box')
            print(f"  - {obj_id} ({obj_type}): 可从缓存获取完整参数")
    
    return manager

def demo_file_operations():
    """演示文件操作"""
    print("\n" + "=" * 60)
    print("3. 文件操作演示")
    print("=" * 60)
    
    # 3.1 创建配置文件
    config_dir = os.path.join(MODULE_ROOT, "configs", "examples")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "demo_objects.json")
    
    # 创建示例配置文件
    config_data = {
        "name": "demo_from_file",
        "type": "composite",
        "shapes": [
            {
                "type": "box",
                "name": "file_box",
                "position": [0.0, 0.0, 0.5],
                "size": [0.2, 0.2, 0.1],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            },
            {
                "type": "cylinder",
                "name": "file_cylinder",
                "position": [0.3, 0.0, 0.25],
                "radius": 0.05,
                "height": 0.3,
                "orientation": [0.0, 0.0, 0.0, 1.0]
            }
        ]
    }
    
    # 确保所有数值都是float（解决ROS2类型问题）
    def convert_to_float(data):
        if isinstance(data, dict):
            return {k: convert_to_float(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_to_float(v) for v in data]
        elif isinstance(data, (int, float)):
            return float(data)
        else:
            return data
    
    config_data = convert_to_float(config_data)
    
    # 保存配置文件
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\n3.1 创建配置文件: {config_file}")
    print("配置文件内容:")
    print(json.dumps(config_data, indent=2))
    
    # 3.2 演示从文件加载
    print("\n3.2 从文件加载物体:")
    print("命令: ./ps-add-object --from-file configs/examples/demo_objects.json")
    print("注意：需要确保路径正确，建议使用绝对路径或相对路径")
    
    # 3.3 演示导出物体列表
    print("\n3.3 导出物体列表到文件:")
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    
    objects = manager.list_objects()
    export_data = {
        "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "object_count": len(objects),
        "objects": []
    }
    
    for obj_id in objects:
        cached = manager.get_object_from_cache(obj_id)
        if cached:
            export_data["objects"].append({
                "id": obj_id,
                "type": cached.get("type", "unknown"),
                "position": cached.get("position", []),
                "dimensions": cached.get("dimensions", [])
            })
    
    export_file = os.path.join(config_dir, "exported_objects.json")
    with open(export_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"已导出到: {export_file}")
    print(f"导出了 {len(export_data['objects'])} 个物体的信息")
    
    return config_file, export_file

def demo_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("4. 常见错误处理演示")
    print("=" * 60)
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    validator = ObjectValidator(client)    
    # 4.1 创建无效物体（验证失败）
    print("\n4.1 创建无效物体演示...")
    
    from moveit_msgs.msg import CollisionObject
    invalid_obj = CollisionObject()
    invalid_obj.id = ""
    invalid_obj.operation = b'\x00'
    
    # 验证会失败
    valid, msg = validator.validate_object(invalid_obj)
    print(f"无效物体验证: {'✅' if valid else '❌'} {msg}")
    
    # 4.2 修改不存在的物体
    print("\n4.2 修改不存在物体演示...")
    non_existent = "non_existent_object"
    cached = manager.get_object_from_cache(non_existent)
    print(f"查找不存在的物体 '{non_existent}': {'❌ 不存在' if not cached else '✅ 存在'}")
    
    # 4.3 类型转换问题
    print("\n4.3 类型转换问题演示...")
    
    # 错误示例：使用int而不是float
    print("错误示例: position=[0, 0, 0] (整数)")
    print("正确示例: position=[0.0, 0.0, 0.0] (浮点数)")
    print("解决方案: 使用 ensure_float_list() 函数")
    
    # 4.4 缓存问题
    print("\n4.4 缓存问题演示...")
    
    # 清空缓存（模拟重启后）
    print("模拟重启后缓存状态...")
    cache_info = manager.list_cached_objects()
    print(f"当前缓存物体数量: {len(cache_info)}")
    
    if len(cache_info) == 0:
        print("⚠️  缓存为空，修改物体时需要用户提供完整参数")
        print("解决方案: 重新创建物体以建立缓存")
    else:
        print("✅ 缓存正常，可自动获取物体参数")
    
    return validator

def demo_advanced_scenarios():
    """演示高级场景"""
    print("\n" + "=" * 60)
    print("5. 高级场景演示")
    print("=" * 60)
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    generator = ShapeGenerator()
    
    # 5.1 创建复合物体
    print("\n5.1 创建复合物体（桌子）...")
    
    table_shapes = [
        {
            "type": "box",
            "position": [0.0, 0.0, 0.3],
            "size": [0.8, 0.8, 0.05],
            "orientation": [0.0, 0.0, 0.0, 1.0]
        },
        {
            "type": "cylinder",
            "position": [-0.35, -0.35, 0.15],
            "radius": 0.03,
            "height": 0.3
        },
        {
            "type": "cylinder",
            "position": [0.35, -0.35, 0.15],
            "radius": 0.03,
            "height": 0.3
        }
    ]
    
    # 确保所有数值都是float
    for shape in table_shapes:
        if "position" in shape:
            shape["position"] = ensure_float_list(shape["position"])
        if "size" in shape:
            shape["size"] = ensure_float_list(shape["size"])
        if "orientation" in shape:
            shape["orientation"] = ensure_float_list(shape["orientation"])
    
    table = generator.create_composite("demo_table", table_shapes)
    
    # 验证复合物体
    from ps_objects.object_validator import ObjectValidator
    validator = ObjectValidator(client)
    valid, msg = validator.validate_object(table)
    
    if valid:
        print(f"复合物体验证: ✅ {msg}")
        print(f"包含 {len(table_shapes)} 个形状")
        
        # 添加物体
        success = manager.add_object_simple(table)
        print(f"添加复合物体: {'✅ 成功' if success else '❌ 失败'}")
    else:
        print(f"复合物体验证: ❌ {msg}")    
    # 5.2 场景状态管理
    print("\n5.2 场景状态管理...")
    
    # 保存当前场景快照
    objects = manager.list_objects()
    print(f"当前场景状态: {len(objects)} 个物体")
    
    # 演示批量操作
    if len(objects) > 0:
        print("批量操作演示:")
        print("  1. 可批量移除: ./ps-remove-object --pattern \"demo_*\"")
        print("  2. 可批量移动: ./ps-modify-object --pattern \"demo_*\" --move-to \"1.0,0,0.5\"")
        print("  3. 可导出场景: ./ps-list-objects --json --export scene_state.json")
    
    return manager

def main():
    """主函数 - 运行所有演示"""
    print("\n" + "=" * 60)
    print("物体操作示例程序")
    print("演示碰撞物体管理的完整流程")
    print("注意处理常见问题：缓存、类型转换、文件路径等")
    print("=" * 60)
    
    try:
        # 演示1：基础操作
        manager, generator, validator = demo_basic_operations()
        time.sleep(1)
        
        # 演示2：缓存修改
        demo_modify_with_cache()
        time.sleep(1)
        
        # 演示3：文件操作
        config_file, export_file = demo_file_operations()
        time.sleep(1)
        
        # 演示4：错误处理
        demo_error_handling()
        time.sleep(1)
        
        # 演示5：高级场景
        demo_advanced_scenarios()
        time.sleep(1)
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n关键要点总结:")
        print("1. ✅ 总是使用float类型（ROS2要求严格）")
        print("2. ✅ 利用缓存避免参数丢失") 
        print("3. ✅ 验证物体确保数据完整性")
        print("4. ✅ 使用配置文件简化复杂操作")
        print("5. ✅ 处理常见错误（不存在的物体、无效参数等）")
        
        # 最终清理
        print("\n清理演示物体...")
        objects = manager.list_objects()
        demo_objects = [obj for obj in objects if obj.startswith("demo_")]
        
        if demo_objects:
            print(f"移除演示物体: {', '.join(demo_objects)}")
            for obj in demo_objects:
                manager.remove_object_simple(obj)
                time.sleep(0.1)
        
        print("✅ 演示程序完成！")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())