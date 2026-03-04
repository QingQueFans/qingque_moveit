#!/usr/bin/env python3
"""
测试夹爪计算器的一行调用接口
"""

import sys
import os
import json
import argparse
import time

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)  # grasp_execution/
GRASPING_ROOT = os.path.dirname(MODULE_ROOT)  # grasping/
PROJECT_ROOT = os.path.dirname(GRASPING_ROOT)  # moveit_ros/
MOVEIT_ROOT = os.path.dirname(PROJECT_ROOT)  # qingfu_moveit/
MOVEIT_CORE_ROOT = os.path.join(MOVEIT_ROOT, 'moveit_core')

print(f"[路径] 脚本目录: {SCRIPT_DIR}")
print(f"[路径] 模块根目录: {MODULE_ROOT}")
print(f"[路径] 抓取根目录: {GRASPING_ROOT}")
print(f"[路径] ROS根目录: {PROJECT_ROOT}")
print(f"[路径] 项目根目录: {MOVEIT_ROOT}")

# 1. 首先添加当前模块路径
GRASPING_SRC = os.path.join(MODULE_ROOT, 'src')
sys.path.insert(0, GRASPING_SRC)

# 2. 按照感知模块的路径模式添加
# 感知模块路径应该是：moveit_ros/perception/object_detection/src
PERCEPTION_MODULE = os.path.join(PROJECT_ROOT, 'perception', 'object_detection')
PERCEPTION_SRC = os.path.join(PERCEPTION_MODULE, 'src')

print(f"[路径] 感知模块目录: {PERCEPTION_MODULE}")
print(f"[路径] 感知源码目录: {PERCEPTION_SRC}")
print(f"[路径] 目录存在: {os.path.exists(PERCEPTION_SRC)}")

if os.path.exists(PERCEPTION_SRC):
    sys.path.insert(0, PERCEPTION_SRC)
    
    # 列出目录内容调试
    print(f"[调试] {PERCEPTION_SRC} 内容:")
    for item in os.listdir(PERCEPTION_SRC):
        print(f"  - {item}")
else:
    print(f"[警告] 感知源码目录不存在: {PERCEPTION_SRC}")

# 3. 添加缓存模块路径（按照之前成功的模式）
CACHE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')
sys.path.insert(0, CACHE_SRC)

# 4. 添加规划场景相关路径（如果需要）
CORE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
OBJ_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'collision_objects', 'src')

sys.path.insert(0, CORE_SRC)
sys.path.insert(0, OBJ_SRC)

print(f"\n[导入] 开始导入依赖...")

# ========== 测试函数 ==========

def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "="*50)
    print("测试1: 基本功能导入")
    print("="*50)
    
    try:        # 测试导入
        from grasping.gripper_controller import (
            GripperCalculator, 
            calculate_gripper,
            get_gripper_width,
            get_gripper_params
        )
        
        print("✅ 所有函数导入成功")
        print(f"  - GripperCalculator: {GripperCalculator}")
        print(f"  - calculate_gripper: {calculate_gripper}")
        print(f"  - get_gripper_width: {get_gripper_width}")
        print(f"  - get_gripper_params: {get_gripper_params}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_calculate_gripper():
    """测试 calculate_gripper 函数"""
    print("\n" + "="*50)
    print("测试2: calculate_gripper 函数")
    print("="*50)
    
    try:
        from grasping.gripper_controller import calculate_gripper
        
        test_cases = [
            {
                "name": "物体ID模式",
                "input": "test_cube",
                "kwargs": {}
            },
            {
                "name": "尺寸列表-盒子",
                "input": [0.05, 0.05, 0.05],
                "kwargs": {"type": "box"}
            },
            {
                "name": "尺寸列表-圆柱",
                "input": [0.03, 0.12],
                "kwargs": {"type": "cylinder"}
            },
            {
                "name": "尺寸列表-球体",
                "input": [0.04],
                "kwargs": {"type": "sphere"}
            },
            {
                "name": "完整字典输入",
                "input": {
                    "type": "box",
                    "dimensions": [0.1, 0.05, 0.03],
                    "position": [0.6, 0.1, 0.2]
                },
                "kwargs": {}
            }
        ]
        
        all_passed = True
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. {test['name']}:")
            print(f"   输入: {test['input']}")
            
            try:
                result = calculate_gripper(test['input'], **test['kwargs'])
                
                if result["success"]:
                    width_mm = result["gripper_width"] * 1000
                    print(f"   ✅ 成功")
                    print(f"     宽度: {width_mm:.1f} mm")
                    print(f"     力: {result['gripper_force']:.1f} N")
                    print(f"     策略: {result.get('grasp_strategy', 'N/A')}")
                    print(f"     置信度: {result.get('confidence', 0):.2f}")
                else:
                    print(f"   ❌ 失败: {result.get('error', '未知错误')}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_get_gripper_width():
    """测试快速宽度获取"""
    print("\n" + "="*50)
    print("测试3: get_gripper_width 函数")
    print("="*50)
    
    try:
        from grasping.gripper_controller import get_gripper_width
        
        test_cases = [
            {"input": [0.03, 0.03, 0.03], "desc": "3cm立方体"},
            {"input": [0.1, 0.1, 0.1], "desc": "10cm立方体"},
            {"input": [0.025, 0.15], "desc": "半径2.5cm高15cm圆柱"},
            {"input": [0.035], "desc": "半径3.5cm球体"}
        ]
        
        all_passed = True
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. {test['desc']}:")
            
            if isinstance(test['input'], list) and len(test['input']) == 3:
                kwargs = {"type": "box"}
            elif isinstance(test['input'], list) and len(test['input']) == 2:
                kwargs = {"type": "cylinder"}
            elif isinstance(test['input'], list) and len(test['input']) == 1:
                kwargs = {"type": "sphere"}
            else:
                kwargs = {}
            
            width_mm = get_gripper_width(test['input'], **kwargs)
            
            if width_mm > 0:
                print(f"   ✅ 宽度: {width_mm:.1f} mm")
            else:
                print(f"   ❌ 获取失败")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_get_gripper_params():
    """测试多参数获取"""
    print("\n" + "="*50)
    print("测试4: get_gripper_params 函数")
    print("="*50)
    
    try:
        from grasping.gripper_controller import get_gripper_params        # 测试各种物体
        test_objects = [
            {
                "name": "小盒子",
                "input": [0.03, 0.03, 0.03],
                "type": "box"
            },
            {
                "name": "大盒子", 
                "input": [0.1, 0.05, 0.03],
                "type": "box"
            },
            {
                "name": "细高圆柱",
                "input": [0.025, 0.15],
                "type": "cylinder"
            },
            {
                "name": "矮粗圆柱",
                "input": [0.04, 0.06],
                "type": "cylinder"
            },
            {
                "name": "中等球体",
                "input": [0.035],
                "type": "sphere"
            }
        ]
        
        all_passed = True
        
        print("物体类型 | 宽度(mm) | 力(N) | 策略")
        print("-" * 40)
        
        for obj in test_objects:
            try:
                width_mm, force, strategy = get_gripper_params(
                    obj["input"], 
                    type=obj["type"]
                )
                
                if width_mm > 0:
                    print(f"{obj['name']:10} | {width_mm:7.1f} | {force:5.1f} | {strategy}")
                else:
                    print(f"{obj['name']:10} | 失败")
                    all_passed = False
                    
            except Exception as e:
                print(f"{obj['name']:10} | 异常: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*50)
    print("测试5: 错误处理")
    print("="*50)
    
    try:
        from grasping.gripper_controller import calculate_gripper
        
        error_cases = [
            {
                "name": "无效类型",
                "input": [0.05, 0.05, 0.05],
                "kwargs": {"type": "invalid_type"},
                "should_fail": True
            },
            {
                "name": "空输入",
                "input": [],
                "kwargs": {},
                "should_fail": True
            },
            {
                "name": "无效尺寸",
                "input": [-0.1, 0.1, 0.1],
                "kwargs": {"type": "box"},
                "should_fail": True
            },
            {
                "name": "数字输入",
                "input": 123,
                "kwargs": {},
                "should_fail": True
            }
        ]
        
        all_passed = True
        
        for test in error_cases:
            print(f"\n{test['name']}:")
            print(f"  输入: {test['input']}")
            
            try:
                result = calculate_gripper(test['input'], **test['kwargs'])
                
                if test['should_fail']:
                    if not result["success"]:
                        print(f"  ✅ 预期失败，实际失败: {result.get('error', '未知')}")
                    else:
                        print(f"  ❌ 预期失败，但成功了")
                        all_passed = False
                else:
                    if result["success"]:
                        print(f"  ✅ 预期成功，实际成功")
                    else:
                        print(f"  ❌ 预期成功，但失败: {result.get('error', '未知')}")
                        all_passed = False
                        
            except Exception as e:
                print(f"  ⚠️ 抛出异常: {e}")
                if test['should_fail']:
                    print(f"  ✅ 异常符合预期")
                else:
                    print(f"  ❌ 不应抛出异常")
                    all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
def test_performance():
    """测试性能（多次调用）"""
    print("\n" + "="*50)
    print("测试6: 性能测试")
    print("="*50)
    
    try:
        from grasping.gripper_controller import get_gripper_width
        import time
        
        # 测试多次调用
        num_calls = 10
        test_input = [0.05, 0.05, 0.05]
        
        print(f"进行 {num_calls} 次调用...")
        
        start_time = time.time()
        
        results = []
        for i in range(num_calls):
            # 稍微改变尺寸，模拟不同输入
            modified_input = [dim * (1 + i * 0.01) for dim in test_input]
            width = get_gripper_width(modified_input, type="box")
            results.append(width)
            
            if (i + 1) % 5 == 0:
                print(f"  已完成 {i + 1}/{num_calls}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 统计
        successful = sum(1 for w in results if w > 0)
        avg_time = total_time / num_calls
        
        print(f"\n结果:")
        print(f"  总时间: {total_time:.3f} 秒")
        print(f"  平均每次: {avg_time:.3f} 秒")
        print(f"  成功次数: {successful}/{num_calls}")
        
        if successful == num_calls:
            print("✅ 所有调用成功")
            return True
        else:
            print(f"❌ 部分调用失败 ({num_calls - successful} 次)")
            return False
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


# ========== 主测试函数 ==========

def run_all_tests():
    """运行所有测试"""
    print("=== 开始夹爪计算器一行调用接口测试 ===")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
       # 运行测试
    tests = [
        ("基本功能导入", test_basic_functionality),
        ("calculate_gripper", test_calculate_gripper),
        ("get_gripper_width", test_get_gripper_width),
        ("get_gripper_params", test_get_gripper_params),
        ("错误处理", test_error_handling),
        ("性能测试", test_performance)
    ]
    
    for test_name, test_func in tests:
        print(f"\n▶ 运行测试: {test_name}")
        try:
            passed = test_func()
            test_results.append((test_name, passed))
            
            if passed:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
            test_results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    total = len(test_results)
    passed = sum(1 for _, result in test_results if result)
    failed = total - passed
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！一行调用接口工作正常。")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要检查。")
        return False


# ========== 主程序 ==========

if __name__ == "__main__":
    import time
    
    try:
        success = run_all_tests()
        
        if success:            # 演示使用示例
            print("\n" + "="*60)
            print("使用示例演示")
            print("="*60)
            
            try:
                from grasping.gripper_controller import (
                    calculate_gripper,
                    get_gripper_width,
                    get_gripper_params
                )
                
                print("\n示例1: 简单宽度获取")
                width = get_gripper_width([0.05, 0.05, 0.05], type="box")
                print(f"   5cm立方体需要夹爪宽度: {width:.1f} mm")
                
                print("\n示例2: 完整参数获取")
                width, force, strategy = get_gripper_params([0.03, 0.12], type="cylinder")
                print(f"   圆柱体抓取:")
                print(f"     宽度: {width:.1f} mm")
                print(f"     力: {force:.1f} N") 
                print(f"     策略: {strategy}")
                
                print("\n示例3: 完整结果获取")
                result = calculate_gripper("test_cube")
                if result["success"]:
                    print(f"   test_cube 抓取方案:")
                    print(f"     宽度: {result['gripper_width']*1000:.1f} mm")
                    print(f"     力: {result['gripper_force']:.1f} N")
                    print(f"     策略: {result['grasp_strategy']}")
                    print(f"     置信度: {result['confidence']:.2f}")
                
                print("\n🎯 一行调用接口已准备就绪！")
                print("   在其他模块中可以直接导入使用:")
                print("   from grasping.gripper_controller import calculate_gripper")
                print("   result = calculate_gripper('物体ID或尺寸')")
                
            except Exception as e:
                print(f"演示失败: {e}")
        
        exit_code = 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        exit_code = 1
    except Exception as e:
        print(f"\n测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)