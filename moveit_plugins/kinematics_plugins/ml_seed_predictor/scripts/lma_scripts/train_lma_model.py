#!/usr/bin/env python3
"""
训练LMA专用模型脚本
"""
import sys
import os

# 添加路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PREDICTOR_DIR)

from lma_predictor import LMAPredictor
import numpy as np

def main():
    print("=" * 60)
    print("LMA专用模型训练工具")
    print("=" * 60)
    
    # 配置文件路径
    config_path = os.path.join(PREDICTOR_DIR, 'config', 'lma_config.yaml')
    
    # 初始化预测器
    predictor = LMAPredictor(config_path)
    
    # 显示当前状态
    stats = predictor.get_stats()
    print(f"\n当前状态:")
    print(f"  LMA样本数: {stats['data']['count']}")
    print(f"  预测次数: {stats['predictions']['total_predictions']}")
    print(f"  模型已训练: {stats['model']['trained']}")
    print(f"  模型类型: {stats['model']['type']}")
    
    if stats['data']['count'] < 5:
        print("\n⚠️ 样本不足，至少需要5个")
        return
    
    # 训练模型
    print(f"\n开始训练...")
    success = predictor.train()
    
    if success:
        print(f"✅ 训练成功!")
        
        # 测试几个点
        test_points = [
            [0.55, -0.1, 0.6],
            [0.4, 0.0, 0.5],
            [0.5, 0.0, 0.5]
        ]
        
        print("\n测试预测:")
        for point in test_points:
            pred, unc = predictor.predict(point)
            if pred is not None:
                print(f"  {point} -> {[round(p,3) for p in pred[:3]]}... (不确定度:{unc:.3f})")
    else:
        print(f"❌ 训练失败")

if __name__ == "__main__":
    main()
