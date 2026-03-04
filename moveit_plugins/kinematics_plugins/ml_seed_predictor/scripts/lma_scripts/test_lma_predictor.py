#!/usr/bin/env python3
"""
测试LMA预测器
"""
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PREDICTOR_DIR)

from lma_predictor import LMAPredictor

def main():
    print("=" * 60)
    print("LMA预测器测试")
    print("=" * 60)
    
    config_path = os.path.join(PREDICTOR_DIR, 'config', 'lma_config.yaml')
    predictor = LMAPredictor(config_path)
    
    # 测试点
    test_points = [
        [0.55, -0.1, 0.6],
        [0.4, 0.0, 0.5],
        [0.45, -0.1, 0.45],
        [0.5, 0.0, 0.55],
        [0.4, 0.0, 0.4],
        [0.35, 0.0, 0.35],
        [0.6, 0.0, 0.6]
    ]
    
    print(f"\n测试 {len(test_points)} 个点:\n")
    
    total_time = 0
    successful = 0
    
    for i, point in enumerate(test_points):
        start = time.time()
        pred, unc = predictor.predict(point)
        elapsed = (time.time() - start) * 1000
        total_time += elapsed
        
        if pred is not None:
            successful += 1
            status = "✅"
            pred_str = f"[{pred[0]:.3f}, {pred[1]:.3f}, {pred[2]:.3f}, ...]"
        else:
            status = "❌"
            pred_str = "None"
        
        print(f"{status} 点 {i+1}: {point}")
        print(f"   预测: {pred_str}")
        print(f"   不确定度: {unc:.3f}")
        print(f"   耗时: {elapsed:.2f}ms\n")
    
    print("-" * 60)
    print(f"总计: {successful}/{len(test_points)} 成功")
    print(f"平均耗时: {total_time/len(test_points):.2f}ms")

if __name__ == "__main__":
    main()
