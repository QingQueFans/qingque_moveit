#!/usr/bin/env python3
"""
碰撞检查演示 - 展示碰撞检测的各种用法
"""
import sys
import os
import time
import json

# ========== 设置路径 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # examples/
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)                # collision_detection/
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)              # planning_scene/

# 添加 core_functions 的 src 到路径
CORE_SRC = os.path.join(PROJECT_ROOT, 'core_functions', 'src')
sys.path.insert(0, CORE_SRC)

# 添加 collision_detection 的 src 到路径
DETECTION_SRC = os.path.join(MODULE_ROOT, 'src')
sys.path.insert(0, DETECTION_SRC)

# 添加 collision_objects 的 src 到路径（依赖）
OBJ_MODULE_ROOT = os.path.join(PROJECT_ROOT, 'collision_objects')
OBJ_SRC = os.path.join(OBJ_MODULE_ROOT, 'src')
sys.path.insert(0, OBJ_SRC)

# 现在可以正常导入
from ps_core.scene_client import PlanningSceneClient
from ps_collision.collision_checker import CollisionChecker
from ps_collision.distance_calculator import DistanceCalculator
from ps_collision.contact_analyzer import ContactAnalyzer
from ps_objects.object_manager import ObjectManager
from ps_objects.shape_generator import ShapeGenerator

def ensure_float(data):
    """确保数据是float类型"""
    if isinstance(data, (list, tuple)):
        return [float(x) for x in data]
    return float(data)

def setup_test_scene():
    """设置测试场景"""
    print("1. 设置测试场景")
    print("-" * 40)
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    generator = ShapeGenerator()
    
    # 清空场景
    print("清空场景...")
    manager.clear_all_objects()
    time.sleep(1)    # 创建测试物体
    test_objects = [
        {
            "name": "demo_box1",
            "type": "box",
            "position": [0.2, 0.0, 0.25],
            "size": [0.1, 0.1, 0.1]
        },
        {
            "name": "demo_box2", 
            "type": "box",
            "position": [0.5, 0.0, 0.25],
            "size": [0.1, 0.1, 0.1]
        },
        {
            "name": "demo_sphere",
            "type": "sphere",
            "position": [0.8, 0.0, 0.15],
            "radius": 0.08
        },
        {
            "name": "demo_cylinder",
            "type": "cylinder",
            "position": [0.2, 0.3, 0.2],
            "radius": 0.05,
            "height": 0.3
        },
        {
            "name": "close_box",
            "type": "box",
            "position": [0.25, 0.0, 0.25],  # 靠近box1，会碰撞
            "size": [0.1, 0.1, 0.1]
        }
    ]
    
    print(f"创建 {len(test_objects)} 个测试物体...")
    
    for obj_def in test_objects:
        obj_type = obj_def["type"]
        name = obj_def["name"]
        position = ensure_float(obj_def["position"])
        
        if obj_type == "box":
            size = ensure_float(obj_def["size"])
            obj = generator.create_box(
                name=name,
                position=position,
                size=size,
                orientation=[0.0, 0.0, 0.0, 1.0]
            )
        elif obj_type == "sphere":
            radius = ensure_float(obj_def["radius"])
            obj = generator.create_sphere(
                name=name,
                position=position,
                radius=radius,
                orientation=[0.0, 0.0, 0.0, 1.0]
            )
        elif obj_type == "cylinder":
            radius = ensure_float(obj_def["radius"])
            height = ensure_float(obj_def["height"])
            obj = generator.create_cylinder(
                name=name,
                position=position,
                radius=radius,
                height=height,
                orientation=[0.0, 0.0, 0.0, 1.0]
            )
        
        success = manager.add_object_simple(obj)
        print(f"  {name}: {'✅' if success else '❌'}")
        time.sleep(0.1)
    
    print("测试场景设置完成")
    return client, manager, generator



def demo_contact_analysis():
    """演示接触分析"""
    print("\n6. 接触分析演示")
    print("-" * 40)
    
    client = PlanningSceneClient()
    analyzer = ContactAnalyzer(client)
    
    # 分析碰撞物体的接触
    print("分析碰撞物体的接触:")
    contact_info = analyzer.analyze_contacts("demo_box1", "close_box")
    
    if "error" not in contact_info:
        if contact_info["contact"]:
            print(f"  ✅ 物体接触")
            print(f"    接触类型: {contact_info['contact_type']}")
            print(f"    接触面积: {contact_info['estimated_contact_area']:.6f} m²")
            print(f"    分析: {contact_info.get('analysis', '')}")
        else:
            print(f"  ⚠️  物体未接触")
    
    # 分析抓取接触
    print("\n分析抓取接触（模拟）:")
    
    # 创建一个"夹爪"物体
    from ps_objects.object_manager import ObjectManager
    from ps_objects.shape_generator import ShapeGenerator
    
    manager = ObjectManager(client)
    generator = ShapeGenerator()
    
    # 简单夹爪（两个相对的盒子）
    gripper_left = generator.create_box(
        name="demo_gripper_left",
        position=[0.4, 0.05, 0.25],
        size=[0.05, 0.02, 0.1],
        orientation=[0.0, 0.0, 0.0, 1.0]
    )
    
    gripper_right = generator.create_box(
        name="demo_gripper_right",
        position=[0.4, -0.05, 0.25],
        size=[0.05, 0.02, 0.1],
        orientation=[0.0, 0.0, 0.0, 1.0]
    )
    
    manager.add_object_simple(gripper_left)
    manager.add_object_simple(gripper_right)
    time.sleep(0.5)  # 分析抓取接触（假设要抓取 demo_sphere）
    print("  分析夹爪抓取球体的接触...")
    
    # 这里简化，实际应该分析两个夹爪与目标物体的接触
    grasp_info = analyzer.analyze_grasp_contacts("demo_gripper_left", "demo_sphere")
    
    if "error" not in grasp_info:
        print(f"    接触状态: {'✅ 接触' if grasp_info['contact'] else '⚠️  未接触'}")
        if grasp_info['contact']:
            print(f"    抓取质量: {grasp_info['grasp_quality']:.1%}")
            print(f"    稳定性: {'✅ 稳定' if grasp_info['grasp_stable'] else '❌ 不稳定'}")
            print(f"    建议: {grasp_info['recommendation']}")
    
    return analyzer

def demo_error_handling():
    """演示错误处理"""
    print("\n7. 错误处理演示")
    print("-" * 40)
    
    client = PlanningSceneClient()
    checker = CollisionChecker(client)
    calculator = DistanceCalculator(client)
    
    print("测试不存在的物体:")
    
    # 检查不存在的物体
    collision, info = checker.check_collision("non_existent_1", "non_existent_2")
    if "error" in info:
        print(f"  ❌ 错误: {info['error']}")
    
    # 计算不存在的物体的距离
    print("\n计算不存在的物体的距离:")
    result = calculator.compute_distance("non_existent", "demo_box1")
    if "error" in result:
        print(f"  ❌ 错误: {result['error']}")
    
    print("\n✅ 错误处理演示完成")

def cleanup_demo():
    """清理演示物体"""
    print("\n8. 清理演示")
    print("-" * 40)
    
    client = PlanningSceneClient()
    manager = ObjectManager(client)
    
    # 列出所有演示物体
    all_objects = manager.list_objects()
    demo_objects = [obj for obj in all_objects if obj.startswith("demo_")]
    
    if demo_objects:
        print(f"清理 {len(demo_objects)} 个演示物体...")
        for obj in demo_objects:
            print(f"  移除: {obj}")
            manager.remove_object_simple(obj)
            time.sleep(0.1)
        
        remaining = manager.list_objects()
        print(f"清理后剩余物体: {len(remaining)}")
    else:
        print("没有演示物体需要清理")
    
    print("✅ 清理完成")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("碰撞检查演示程序")
    print("展示碰撞检测、距离计算和接触分析的各种功能")
    print("=" * 60)
    
    try:
        # 设置测试场景
        client, manager, generator = setup_test_scene()
        time.sleep(1)
        
        # 演示1：成对碰撞检查
        checker = demo_pairwise_collision()
        time.sleep(0.5)
        
        # 演示2：多物体碰撞检查
        demo_multiple_collisions()
        time.sleep(0.5)
        
        # 演示3：自碰撞检查
        demo_self_collision()
        time.sleep(0.5)
        
        # 演示4：距离计算
        calculator = demo_distance_calculation()
        time.sleep(0.5)
        
        # 演示5：接触分析
        analyzer = demo_contact_analysis()
        time.sleep(0.5)
        
        # 演示6：错误处理
        demo_error_handling()
        time.sleep(0.5)
        
        # 清理
        cleanup_demo()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n学习了以下碰撞检测功能:")
        print("1. ✅ 成对物体碰撞检查")
        print("2. ✅ 多物体碰撞检查")
        print("3. ✅ 复合物体自碰撞检查")
        print("4. ✅ 距离计算和最近物体查找")
        print("5. ✅ 接触类型和抓取质量分析")
        print("6. ✅ 错误处理和异常情况")
        print("7. ✅ 场景清理和管理")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        # 尝试清理
        try:
            cleanup_demo()
        except:
            pass
        return 130
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试清理
        try:
            cleanup_demo()
        except:
            pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main())