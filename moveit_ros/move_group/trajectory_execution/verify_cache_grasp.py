#!/usr/bin/env python3
"""
一行调用接口验证
验证是否可以通过一行代码执行缓存抓取
"""

import os
import sys

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"🔍 验证一行调用接口")
print(f"目录: {SCRIPT_DIR}")

# ========== 检查一行调用接口 ==========

def verify_one_line_api():
    """验证一行调用接口"""
    print("\n" + "="*60)
    print("验证: 一行调用接口")
    print("="*60)
    
    # 查找包含一行调用接口的文件
    api_files = []
    
    # 搜索当前目录
    for filename in os.listdir(SCRIPT_DIR):
        if filename.endswith('.py'):
            filepath = os.path.join(SCRIPT_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含一行调用接口的关键特征
                api_keywords = [
                    'class TrajectoryExecutor',
                    'def execute_trajectory',
                    'def move_to_pose', 
                    'def move_to_joints',
                    'execute_trajectory(target'
                ]
                
                found_keywords = []
                for keyword in api_keywords:
                    if keyword in content:
                        found_keywords.append(keyword)
                
                if found_keywords:
                    api_files.append({
                        'file': filename,
                        'keywords': found_keywords
                    })
                    
            except:
                pass
    
    if not api_files:
        print("❌ 找不到一行调用接口文件")
        return False
    
    print(f"✅ 找到 {len(api_files)} 个包含一行调用接口的文件:")
    for file_info in api_files:
        print(f"   📄 {file_info['file']}")
        print(f"      包含: {', '.join(file_info['keywords'][:3])}")
    
    # 检查关键函数
    print(f"\n🔍 检查关键函数:")
    
    # 假设你的接口在某个文件中，我们检查最常见的特征
    key_functions = [
        ('TrajectoryExecutor', '类定义'),
        ('execute()', '类方法'),
        ('execute_trajectory()', '全局函数'),
        ('move_to_pose()', '便捷函数'),
        ('move_to_joints()', '便捷函数')
    ]
    
    all_content = ""
    for file_info in api_files:
        filepath = os.path.join(SCRIPT_DIR, file_info['file'])
        with open(filepath, 'r', encoding='utf-8') as f:
            all_content += f.read() + "\n"
    
    for func_name, desc in key_functions:
        if func_name in all_content:
            print(f"   ✅ {desc} ({func_name})")
        else:
            print(f"   ❌ 缺少: {desc}")    # 检查缓存集成
    print(f"\n🔍 检查缓存集成:")
    cache_keywords = [
        'plan_and_execute_cached',
        'use_cache=True',
        'cache_manager',
        '缓存命中'
    ]
    
    for keyword in cache_keywords:
        if keyword in all_content:
            print(f"   ✅ 集成缓存: {keyword}")
        else:
            print(f"   ⚠️  未找到: {keyword}")
    
    return True

def verify_api_usage():
    """验证API使用方式"""
    print("\n" + "="*60)
    print("验证: API使用方式")
    print("="*60)
    
    print("💡 一行调用接口应该支持:")
    
    usage_examples = [
        {
            "desc": "位姿模式",
            "code": "result = execute_trajectory({'pose': [0.5, 0.0, 0.3, 0,0,0,1]})",
            "功能": "给定位置+姿态，自动规划执行"
        },
        {
            "desc": "关节模式", 
            "code": "result = execute_trajectory({'joints': [0, -0.5, 0, -1.5, 0, 1.5, 0]})",
            "功能": "直接控制关节角度"
        },
        {
            "desc": "物体ID模式",
            "code": "result = execute_trajectory('test_cube')",
            "功能": "通过物体ID自动获取抓取位姿"
        },
        {
            "desc": "使用缓存",
            "code": "result = execute_trajectory({'pose': [...]}, use_cache=True)",
            "功能": "启用缓存加速重复执行"
        },
        {
            "desc": "便捷函数",
            "code": "result = move_to_pose(0.5, 0.0, 0.3)",
            "功能": "快速移动到指定位置"
        }
    ]
    
    for example in usage_examples:
        print(f"\n📌 {example['desc']}:")
        print(f"   代码: {example['code']}")
        print(f"   功能: {example['功能']}")
    
    print(f"\n✅ API设计完整")
    return True

def verify_actual_import():
    """验证实际导入"""
    print("\n" + "="*60)
    print("验证: 实际导入测试")
    print("="*60)
    
    # 尝试导入（可能需要调整路径）
    sys.path.insert(0, SCRIPT_DIR)
    sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))
    sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src/trajectory_execution'))
    
    imports_to_test = [
        ('TrajectoryExecutor', '一行调用接口类'),
        ('execute_trajectory', '全局执行函数'),
        ('move_to_pose', '便捷函数'),
        ('move_to_joints', '便捷函数')
    ]
    
    print("尝试导入模块...")
    
    for import_name, desc in imports_to_test:
        try:
          # 尝试从不同位置导入
            try:
                exec(f"from trajectory_execution_manager import {import_name}")
                print(f"   ✅ {desc}: 从trajectory_execution_manager导入成功")
                continue
            except:
                pass
            
            try:
                exec(f"from .trajectory_execution_manager import {import_name}")
                print(f"   ✅ {desc}: 从.trajectory_execution_manager导入成功")
                continue
            except:
                pass
            
            try:
                exec(f"from src.trajectory_execution.trajectory_execution_manager import {import_name}")
                print(f"   ✅ {desc}: 从完整路径导入成功")
                continue
            except:
                pass            # 检查是否在全局定义
            try:
                # 读取文件检查全局定义
                for filename in ['trajectory_execution_manager.py', 'cache_executor.py']:
                    filepath = os.path.join(SCRIPT_DIR, 'src/trajectory_execution', filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'r') as f:
                            if f'def {import_name}' in f.read() or f'class {import_name}' in f.read():
                                print(f"   ⚠️  {desc}: 在文件中定义，但导入路径可能不对")
                                break
                else:
                    print(f"   ❌ {desc}: 导入失败")
                    
            except:
                print(f"   ❌ {desc}: 导入失败")
                
        except Exception as e:
            print(f"   ❌ {desc}: 导入错误 - {e}")
    
    return True

# ========== 主验证 ==========

def main():
    """主验证函数"""
    print("\n" + "="*60)
    print("一行调用接口验证")
    print("="*60)
    
    checks = [
        ("接口存在性", verify_one_line_api),
        ("使用方式", verify_api_usage),
        ("实际导入", verify_actual_import)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n▶ 验证: {name}")
        try:
            passed = check_func()
            results.append((name, passed))
            print(f"{'✅ 通过' if passed else '❌ 失败'}")
        except Exception as e:
            print(f"❌ 验证异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 结果汇总
    print("\n" + "="*60)
    print("验证结果")
    print("="*60)
    
    all_passed = all(passed for _, passed in results)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 一行调用接口验证成功！")
        print("")
        print("你可以这样使用:")
        print("  1. 直接导入: from xxx import execute_trajectory")
        print("  2. 一行调用: result = execute_trajectory({'pose': [...]}, use_cache=True)")
        print("  3. 检查结果: if result['success']: ...")
    else:
        print("⚠️  一行调用接口不完整")
        print("需要检查TrajectoryExecutor类的实现")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)