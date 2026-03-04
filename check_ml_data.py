#!/usr/bin/env python3
import json
from pathlib import Path

data_file = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/src/data/training_data.json")

if data_file.exists():
    with open(data_file, 'r') as f:
        data = json.load(f)
    samples = data.get("samples", [])
    print(f"✅ 数据文件存在，共 {len(samples)} 个样本")
    for i, s in enumerate(samples):
        print(f"  样本{i+1}: 目标 {s['target_pose'][:3]}, 误差 {s['error']:.1f}mm, 物体 {s.get('object_id', 'unknown')}")
else:
    print("❌ 还没有样本数据")
    print(f"   查找路径: {data_file}")
