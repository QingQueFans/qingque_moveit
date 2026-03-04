# test_cached_executor.py
#!/usr/bin/env python3
"""
缓存包装器功能测试
"""

import sys
import os

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, 'src')
sys.path.insert(0, SRC_DIR)

from trajectory_execution.trajectory_execution_manager import TrajectoryExecutionManager
from trajectory_execution.cache_executor import CachedTrajectoryExecutor

print("=" * 60)
print("缓存包装器功能测试")
print("=" * 60)

# 1. 创建执行器
print("1. 创建执行器实例...")
original = TrajectoryExecutionManager()
cached = CachedTrajectoryExecutor(original)

print("\n2. 查看初始统计...")
stats = cached.get_stats()
print(f"   总请求数: {stats['statistics']['total_requests']}")
print(f"   缓存命中: {stats['statistics']['cache_hits']}")
print(f"   缓存未命中: {stats['statistics']['cache_misses']}")

print("\n3. 测试第一次规划执行（应该缓存未命中）...")
test_start = {
    "joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
}
test_goal = {
    "pose": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0]
}

result1 = cached.plan_and_execute_cached(test_start, test_goal)
print(f"   成功: {result1.get('success', False)}")
print(f"   缓存命中: {result1.get('cache_info', {}).get('hit', False)}")
print(f"   缓存保存: {result1.get('cache_info', {}).get('saved', False)}")
print(f"   执行时间: {result1.get('execution_time', 0):.2f}秒")

print("\n4. 查看第一次后的统计...")
stats = cached.get_stats()
print(f"   总请求数: {stats['statistics']['total_requests']}")
print(f"   缓存命中: {stats['statistics']['cache_hits']}")
print(f"   缓存未命中: {stats['statistics']['cache_misses']}")
print(f"   缓存保存: {stats['statistics']['cache_saves']}")

print("\n5. 测试第二次规划执行（应该缓存命中）...")
result2 = cached.plan_and_execute_cached(test_start, test_goal)
print(f"   成功: {result2.get('success', False)}")
print(f"   缓存命中: {result2.get('cache_info', {}).get('hit', False)}")
print(f"   执行时间: {result2.get('execution_time', 0):.2f}秒")

print("\n6. 最终统计...")
stats = cached.get_stats()
print(f"   总请求数: {stats['statistics']['total_requests']}")
print(f"   缓存命中: {stats['statistics']['cache_hits']}")
print(f"   缓存未命中: {stats['statistics']['cache_misses']}")
print(f"   缓存保存: {stats['statistics']['cache_saves']}")
print(f"   命中率: {stats['performance']['hit_rate']}")

print("\n7. 检查缓存文件...")
import glob
cache_dir = "/home/diyuanqiongyu/.planning_scene_cache/kinematics/ik_solutions"
cache_files = glob.glob(f"{cache_dir}/ik_*.json")
print(f"   缓存文件数量: {len(cache_files)}")

if cache_files:
    print(f"   最新缓存文件:")
    import os
    for file in sorted(cache_files, key=os.path.getmtime, reverse=True)[:3]:
        print(f"     - {os.path.basename(file)}")
        
    # 查看缓存文件内容
    print(f"\n   查看第一个缓存文件内容:")
    try:
        with open(cache_files[0], 'r') as f:
            import json
            data = json.load(f)
            print(f"     目标位姿: {data.get('data', {}).get('target_pose', [])[:3]}")
            joint_solution = data.get('data', {}).get('joint_solution', [])
            print(f"     关节解长度: {len(joint_solution)}")
    except Exception as e:
        print(f"     读取错误: {e}")

print("\n" + "=" * 60)
if stats['statistics']['cache_hits'] > 0:
    print("✅ 缓存功能测试成功！")
else:
    print("⚠️  缓存命中为0，检查缓存保存逻辑")
    
    # 额外调试信息
    print(f"\n调试信息:")
    print(f"  执行结果1 success: {result1.get('success')}")
    print(f"  执行结果2 success: {result2.get('success')}")
    print(f"  是否启用缓存: {cached.use_cache}")
    
    # 检查缓存目录权限
    if os.path.exists(cache_dir):
        print(f"  缓存目录可写: {os.access(cache_dir, os.W_OK)}")
    else:
        print(f"  缓存目录不存在: {cache_dir}")
        
print("=" * 60)