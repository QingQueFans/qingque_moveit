#!/usr/bin/env python3
"""
清理 train_4 的重复数据
"""
import json
from pathlib import Path

data_file = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/src/data/training_data.json")
backup_file = data_file.with_suffix('.backup.json')

# 备份
print(f"📦 备份到: {backup_file}")
data_file.rename(backup_file)

# 读取
with open(backup_file, 'r') as f:
    data = json.load(f)

samples = data["samples"]
print(f"总样本: {len(samples)}")

# 找出所有 train_4 样本
train4_samples = [s for s in samples if s.get("object_id") == "train_4"]
print(f"train_4 样本: {len(train4_samples)}")

# 按误差排序，保留最好的几个
train4_samples.sort(key=lambda x: x["error"])

# 保留前3个最好的，其他的删除
keep_count = 3
keep_samples = train4_samples[:keep_count]
print(f"保留 {keep_count} 个最好的 train_4 样本:")
for s in keep_samples:
    print(f"  误差: {s['error']:.1f}mm, 目标: {s['target_pose'][:3]}")

# 重新构建样本列表
other_samples = [s for s in samples if s.get("object_id") != "train_4"]
new_samples = other_samples + keep_samples

# 按时间排序
new_samples.sort(key=lambda x: x["timestamp"])

data["samples"] = new_samples
data["count"] = len(new_samples)

with open(data_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ 完成！新样本数: {len(new_samples)}")