#!/usr/bin/env python3
"""
对比原ML和LMA专用ML的性能
"""
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PREDICTOR_DIR)

try:
    from src.ml_seed_predictor.predictor import MLSeedPredictor
except ImportError:
    print("⚠️ 无法导入原ML预测器")
    MLSeedPredictor = None

from src.lma_predictor.lma_predictor import LMAPredictor

def main():
    print("=" * 60)
    print("ML预测器对比测试")
    print("=" * 60)
    
    config_path = os.path.join(PREDICTOR_DIR, 'config', 'lma_config.yaml')
    
    # 初始化两个预测器
    print("\n初始化预测器...")
    
    lma_predictor = LMAPredictor(config_path)
    
    original_predictor = None
    if MLSeedPredictor:
        try:
            original_predictor = MLSeedPredictor()
            print("✅ 原ML预测器初始化成功")
        except Exception as e:
            print(f"⚠️ 原ML预测器初始化失败: {e}")
    
    # 显示统计
    lma_stats = lma_predictor.get_stats()
    print(f"\nLMA专用ML:")
    print(f"  样本数: {lma_stats['data']['count']}")
    print(f"  模型已训练: {lma_stats['model']['trained']}")
    print(f"  模型类型: {lma_stats['model']['type']}")
    
    if original_predictor:
        orig_stats = original_predictor.get_stats()
        print(f"\n原ML:")
        print(f"  样本数: {orig_stats['samples']}")
        print(f"  模型已训练: {orig_stats['model_trained']}")
    
    # 测试点
    test_points = [
        [0.55, -0.1, 0.6],
        [0.4, 0.0, 0.5],
        [0.45, -0.1, 0.45],
        [0.5, 0.0, 0.55],
        [0.4, 0.0, 0.4]
    ]
    
    print("\n" + "=" * 60)
    print("预测对比:")
    print("=" * 60)
    
    for i, point in enumerate(test_points):
        print(f"\n测试点 {i+1}: {point}")
        
        # 原ML预测
        if original_predictor:
            start = time.time()
            try:
                orig_pred = original_predictor.predict(point)
                orig_time = (time.time() - start) * 1000
                orig_str = f"{[round(p,3) for p in orig_pred[:3]]}..." if orig_pred is not None else "None"
            except Exception as e:
                orig_str = f"错误: {e}"
                orig_time = 0
        else:
            orig_str = "不可用"
            orig_time = 0
        
        # LMA预测
        start = time.time()
        lma_pred, lma_unc = lma_predictor.predict(point)
        lma_time = (time.time() - start) * 1000
        lma_str = f"{[round(p,3) for p in lma_pred[:3]]}..." if lma_pred is not None else "None"
        
        print(f"  原ML:     {orig_str} ({orig_time:.1f}ms)")
        print(f"  LMA专用:  {lma_str}  不确定度:{lma_unc:.3f} ({lma_time:.1f}ms)")

if __name__ == "__main__":
    main()
