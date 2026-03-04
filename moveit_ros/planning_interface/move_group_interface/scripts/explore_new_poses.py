#!/usr/bin/env python3
"""
主动探索新位姿，快速收集数据
"""
import sys
import time
import numpy as np

# 设置路径
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')
from moveit_bootstrap import init_moveit_paths
init_moveit_paths()

from kin_ik.ik_solver import IKSolver

def explore_new_poses():
    """主动探索新位姿"""
    ik = IKSolver()
    
    # 1. 定义要探索的新位姿
    new_poses = [
        # train_1 的新高度
        [0.4, 0.0, 0.38],  # 稍微低一点
        [0.4, 0.0, 0.4],   # 新位置
        [0.4, 0.0, 0.42],  # 中间
        [0.4, 0.0, 0.45],  # 中间
        [0.4, 0.0, 0.48],  # 接近旧位置
        [0.4, 0.0, 0.5],   # 旧位置
        
        # safe_3 的探索
        [0.5, 0.0, 0.5],
        [0.5, 0.0, 0.52],
        [0.5, 0.0, 0.55],
    ]
    
    print(f"\n🔍 开始探索 {len(new_poses)} 个新位姿...")
    
    for i, pose in enumerate(new_poses):
        print(f"\n===== 探索 {i+1}/{len(new_poses)} =====")
        print(f"目标位姿: {pose}")
        
        # 2. 构造完整位姿（添加默认方向）
        target_pose = pose + [0.0, 0.0, 0.0, 1.0]
        
        # 3. 尝试求解（放宽参数）
        result = ik.solve(
            target_pose=target_pose,
            optimize=True,
            max_attempts=10,        # 多试几次
            check_collision=False
        )
        
        # 4. 输出结果
        if result.get("success", False):
            error = result.get("verification", {}).get("error_mm", 0)
            print(f"  ✅ 成功! 误差: {error:.1f}mm")
            # 主动添加到ML
            if error < 100:  # 放宽阈值
                ik.ml_predictor.add_sample(
                    target_pose=target_pose,
                    successful_seed=result["solution"],
                    error_mm=error
                )
                print(f"  📚 已添加到训练集 (样本数: {ik.ml_predictor.get_stats()['samples']})")            
           
        else:
            print(f"  ❌ 失败")
        
        # 5. 稍作等待
        time.sleep(1)
    
    print("\n✅ 探索完成！")

def explore_with_strategy():
    """带策略的探索（更高效）"""
    ik = IKSolver()
    
    # 先试中间点，再往两边扩散
    base_poses = [
        [0.4, 0.0, 0.45],  # 中间点
        [0.4, 0.0, 0.4],   # 往下
        [0.4, 0.0, 0.5],   # 往上
        [0.4, 0.0, 0.38],  # 更下
        [0.4, 0.0, 0.52],  # 更上
    ]
    
    for pose in base_poses:
        print(f"\n🎯 探索 {pose}")
        target = pose + [0,0,0,1]
        
        # 多参数尝试
        for attempt in range(3):
            result = ik.solve(
                target_pose=target,
                seed=None,  # 随机种子
                optimize=True,
                max_attempts=8
            )
            
            if result.get("success", False):
                error = result.get("verification", {}).get("error_mm", 0)
                print(f"  尝试{attempt+1}: {error:.1f}mm")
                
                if error < 150:
                    print(f"  ✅ 学习!")
                    break
            time.sleep(0.5)

if __name__ == "__main__":
    # 运行探索
    explore_new_poses()
    # explore_with_strategy()  # 或者用这个