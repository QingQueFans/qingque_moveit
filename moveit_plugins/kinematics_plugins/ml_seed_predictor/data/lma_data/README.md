LMA数据目录结构详解
text
~/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/
├── lma_training_data.json      # 核心训练数据
├── models/                      # 全局模型
│   ├── latest.pkl               # 最新模型
│   ├── scaler.pkl                # 数据标准化器
│   └── model_metadata.json       # 模型信息
├── clusters/                     # 聚类结果
│   ├── lma_clusters.json         # LMA解族信息
│   └── cluster_metadata.json     # 聚类元数据
├── local_models/                 # 局部模型（每个解族一个）
│   ├── lma_near_cluster_0.pkl
│   ├── lma_near_cluster_0_meta.json
│   └── ...
└── stats/                        # 统计信息
    ├── lma_stats.json            # 整体统计
    ├── validation_log.json       # 验证历史
    └── training_history.json     # 训练记录
各文件详细说明
1. lma_training_data.json - 核心数据
json
{
  "samples": [
    {
      "target_pose": [0.55, -0.1, 0.6],        # 目标位置
      "solution": [-0.55, 1.83, 2.02, ...],    # 求解出的关节角度
      "error_mm": 23.5,                         # 误差(mm)
      "seed_used": [-0.54, 1.82, ...],          # 使用的种子
      "timestamp": 1709123456.789,               # 时间戳
      "metadata": {                              # 元数据
        "ml_source": "LMA专用ML",
        "region": "lma_r2_z2",
        "phase": "initial_collection"
      }
    }
  ],
  "count": 42,                                   # 样本总数
  "last_updated": 1709123456.789
}
2. models/latest.pkl - 全局模型
用所有数据训练的通用模型

当没有匹配的局部模型时使用

定期重新训练更新

3. clusters/lma_clusters.json - 聚类结果
json
{
  "lma_near": {
    "sample_count": 15,
    "clusters": {
      "lma_near_cluster_0": {
        "center": [-0.55, 1.83, 2.02, ...],    # 簇中心
        "bounds": [[...], [...]],                # 边界范围
        "size": 8,                                # 样本数
        "avg_error": 28.5                         # 平均误差
      }
    }
  }
}
4. local_models/ - 局部模型
每个解族一个专用模型

精度比全局模型更高

命名规则：{region}_cluster_{id}.pkl

5. stats/lma_stats.json - 实时统计
json
{
  "count": 42,
  "avg_error": 34.2,
  "min_error": 12.5,
  "max_error": 89.3,
  "std_error": 15.7,
  "last_updated": "2024-02-28 15:30:45"
}
常用操作命令
查看数据量
bash
# 查看样本数
python3 -c "
import json
f = open('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/lma_training_data.json')
data = json.load(f)
print(f'LMA样本数: {len(data.get(\"samples\", []))}')
"
查看误差分布
bash
python3 -c "
import json
import numpy as np
f = open('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/lma_training_data.json')
data = json.load(f)
errors = [s['error_mm'] for s in data.get('samples', [])]
if errors:
    print(f'平均: {np.mean(errors):.1f}mm')
    print(f'最小: {np.min(errors):.1f}mm')
    print(f'最大: {np.max(errors):.1f}mm')
    print(f'<50mm: {sum(e<50 for e in errors)}个')
    print(f'50-100mm: {sum(50<=e<100 for e in errors)}个')
"
查看最近样本
bash
python3 -c "
import json
f = open('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/lma_training_data.json')
data = json.load(f)
for s in data.get('samples', [])[-5:]:
    print(f\"pose: {s['target_pose'][:3]}, error: {s['error_mm']:.1f}mm\")
"
备份LMA数据
bash
tar -czf ~/lma_data_backup_$(date +%Y%m%d).tar.gz -C ~/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data lma_data
数据生命周期
收集阶段：样本存入 lma_training_data.json

聚类阶段：clusters/lma_clusters.json 记录解族

训练阶段：生成 models/latest.pkl 和局部模型

验证阶段：stats/validation_log.json 记录预测效果

优化阶段：根据统计调整阈值和参数

现在你的LMA数据目录还是空的，等收集到样本后，这些文件就会自动生成！

