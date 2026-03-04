#!/bin/bash
# LMA专用训练脚本 - 利用探索结果训练LMA模型（增强版）

echo "========================================="
echo "🎯 LMA专用ML系统训练工具 (增强版)"
echo "========================================="
echo ""

# 设置LMA数据目录
LMA_DATA_DIR="/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data"
LMA_MODELS_DIR="$LMA_DATA_DIR/models"
LMA_CLUSTERS_DIR="$LMA_DATA_DIR/clusters"
LMA_LOCAL_MODELS_DIR="$LMA_DATA_DIR/local_models"
LMA_STATS_DIR="$LMA_DATA_DIR/stats"

# 创建目录
mkdir -p "$LMA_MODELS_DIR"
mkdir -p "$LMA_CLUSTERS_DIR"
mkdir -p "$LMA_LOCAL_MODELS_DIR"
mkdir -p "$LMA_STATS_DIR"

# 显示当前LMA数据状态（增强版）
echo "📊 当前LMA系统状态:"
python3 -c "
import json
import os
from pathlib import Path

lma_file = '$LMA_DATA_DIR/lma_training_data.json'
cluster_file = '$LMA_CLUSTERS_DIR/lma_clusters.json'
stats_file = '$LMA_STATS_DIR/lma_stats.json'

# 显示样本统计
if os.path.exists(lma_file):
    with open(lma_file) as f:
        data = json.load(f)
    samples = data.get('samples', [])
    print(f'  📁 LMA样本总数: {len(samples)}')
    
    if samples:
        errors = [s.get('error_mm', 0) for s in samples]
        print(f'  📊 误差统计:')
        print(f'    平均: {sum(errors)/len(errors):.1f}mm')
        print(f'    最小: {min(errors):.1f}mm')
        print(f'    最大: {max(errors):.1f}mm')
        
        # 显示最近3个样本
        print(f'\n  🔍 最近样本:')
        for s in samples[-3:]:
            t = s.get('target_pose', [0,0,0])
            e = s.get('error_mm', 0)
            print(f'    pose [{t[0]:.2f}, {t[1]:.2f}, {t[2]:.2f}] -> {e:.1f}mm')
else:
    print('  📁 LMA样本数: 0 (尚未收集)')

# 显示聚类统计
if os.path.exists(cluster_file):
    with open(cluster_file) as f:
        clusters = json.load(f)
    total_clusters = sum(len(v.get('clusters', {})) for v in clusters.values())
    print(f'\n  🎯 LMA解族总数: {total_clusters}')
    
    # 显示每个区域的解族数
    if clusters:
        print(f'  区域分布:')
        for region, info in clusters.items():
            c_count = len(info.get('clusters', {}))
            if c_count > 0:
                print(f'    {region}: {c_count}个解族')
else:
    print(f'\n  🎯 LMA解族数: 0 (尚未聚类)')

# 显示模型状态
model_file = '$LMA_MODELS_DIR/latest.pkl'
if os.path.exists(model_file):
    try:
        import joblib
        model = joblib.load(model_file)
        model_type = type(model).__name__
        print(f'\n  🤖 全局模型: {model_type}')
    except:
        print(f'\n  🤖 全局模型: 存在但无法加载')
else:
    print(f'\n  🤖 全局模型: 未训练')

# 显示局部模型数量
local_models = list(Path('$LMA_LOCAL_MODELS_DIR').glob('*.pkl'))
print(f'  🧩 局部模型: {len(local_models)}个')

# 显示验证统计
if os.path.exists('$LMA_STATS_DIR/validation_log.json'):
    with open('$LMA_STATS_DIR/validation_log.json') as f:
        val_data = json.load(f)
    val_count = len(val_data.get('history', []))
    print(f'  ✅ 验证记录: {val_count}条')
"
echo ""

# 检查是否需要收集更多LMA数据
read -p "是否要先运行探索脚本来收集LMA数据? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 启动LMA探索模式..."
    
    # 增强版探索脚本
    cat > /tmp/lma_explore.py << 'PYTHONEOF'
#!/usr/bin/env python3
"""
LMA探索脚本 - 增强版，支持聚类和空间分区
"""
import sys
import os
import time
import numpy as np

sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')
from moveit_bootstrap import init_moveit_paths
init_moveit_paths()
from kin_ik.ik_solver import IKSolver

def explore_lma():
    """使用LMA求解器探索并收集数据"""
    ik = IKSolver()
    
    # 确保LMA组件已初始化
    if not hasattr(ik, 'lma_data_collector') or ik.lma_data_collector is None:
        print("❌ LMA数据收集器未初始化")
        return
    
    # 定义探索点位（按区域分组）
    targets_by_region = {
        "近处区域": [
            [0.4, 0.0, 0.4],
            [0.4, 0.0, 0.5],
            [0.4, 0.0, 0.6],
            [0.35, 0.0, 0.45],
        ],
        "中等区域": [
            [0.55, -0.1, 0.6],
            [0.5, 0.0, 0.5],
            [0.5, 0.0, 0.55],
            [0.45, -0.1, 0.5],
        ],
        "远处区域": [
            [0.65, 0.0, 0.65],
            [0.6, 0.0, 0.6],
            [0.7, 0.0, 0.7],
        ],
        "侧向区域": [
            [0.5, 0.15, 0.5],
            [0.5, -0.15, 0.5],
            [0.6, 0.2, 0.6],
        ]
    }
    
    print(f"\n🎯 LMA探索开始")
    print("=" * 50)
    
    total_success = 0
    total_attempts = 0
    before_count = ik.lma_data_collector.get_stats()['count']
    
    # 按区域探索
    for region_name, targets in targets_by_region.items():
        print(f"\n📌 探索 {region_name} ({len(targets)}个点位)")
        
        for i, pose in enumerate(targets):
            target_pose = pose + [0.0, 0.0, 0.0, 1.0]
            print(f"\n  [{i+1}/{len(targets)}] [{pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f}]")
            
            # 多次尝试
            best_error = 1000
            best_solution = None
            ml_source = None
            
            for attempt in range(10):
                result = ik.solve_with_moveit_simple(target_pose)
                total_attempts += 1
                
                if result.get('success', False):
                    error = result.get('error_mm', 1000)
                    source = result.get('ml_source', 'unknown')
                    print(f"    尝试{attempt+1}: {error:.1f}mm (ML: {source})")
                    
                    if error < best_error:
                        best_error = error
                        best_solution = result.get('solution')
                        ml_source = source
                        
                    if error < 30:  # 高质量解
                        break
                else:
                    print(f"    尝试{attempt+1}: 失败")
                
                time.sleep(0.3)
            
            if best_solution is not None and best_error < 100:
                total_success += 1
                print(f"    ✅ 成功! 误差: {best_error:.1f}mm")
            else:
                print(f"    ❌ 失败")
            
            time.sleep(0.5)
    
    after_count = ik.lma_data_collector.get_stats()['count']
    new_samples = after_count - before_count
    
    print("\n" + "=" * 50)
    print("LMA探索完成!")
    print(f"  新增LMA样本: {new_samples}")
    print(f"  总LMA样本: {after_count}")
    print(f"  成功率: {total_success}/{total_attempts} = {total_success/total_attempts*100:.1f}%")

if __name__ == "__main__":
    explore_lma()
PYTHONEOF

    # 运行LMA探索
    python3 /tmp/lma_explore.py
    rm /tmp/lma_explore.py
    
    echo ""
    echo "LMA探索完成！"
fi

echo ""
echo "========================================="
echo "开始训练LMA模型（包含聚类和局部模型）..."
echo "========================================="

# 训练LMA模型（增强版）
python3 -c "
import sys
import os
import time
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')

from moveit_plugins.kinematics_plugins.ml_seed_predictor.src.lma_predictor.lma_predictor import LMAPredictor

# 配置文件路径
config_path = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/config/lma_config.yaml'

# 初始化预测器
predictor = LMAPredictor(config_path)

# 获取当前状态
stats = predictor.get_stats()
print(f'\n📊 训练前状态:')
print(f'  📁 样本数: {stats[\"data\"][\"count\"]}')
# ===== 【新增】训练前先清理低质量样本 =====
if stats['data']['count'] > 200:
    print('\n🧹 清理低质量样本...')
    if hasattr(predictor.data_collector, 'prune_low_quality'):
        predictor.data_collector.prune_low_quality(200)
    else:
        # 如果没有prune方法，手动清理
        samples = predictor.data_collector.data
        samples.sort(key=lambda x: x['error_mm'])
        predictor.data_collector.data = samples[:200]
        predictor.data_collector._save_data()
        print(f'  ✂️ 已清理到200个最佳样本')
        # 更新stats
        stats = predictor.get_stats()
        print(f'  📁 清理后样本数: {stats[\"data\"][\"count\"]}')

print(f'  🎯 解族数: {stats[\"clusters\"][\"total\"]}')
print(f'  🧩 局部模型: {stats[\"models\"][\"local\"][\"count\"]}')
print(f'  🤖 全局模型已训练: {stats[\"models\"][\"global\"][\"trained\"]}')

if stats['data']['count'] < 5:
    print('\n❌ 样本不足5个，无法训练')
    sys.exit(1)

# 训练模型（同时训练全局和局部）
print('\n🏋️ 开始训练...')
start_time = time.time()

# 1. 强制重新聚类（可选）
if stats['data']['count'] > 10:
    print('  正在重新聚类...')
    predictor.force_recluster()

# 2. 训练所有模型
success = predictor.train(train_global=True, train_local=True)
elapsed = time.time() - start_time

if success:
    print(f'✅ 训练成功! 耗时: {elapsed:.2f}秒')
    
    # 获取新状态
    new_stats = predictor.get_stats()
    print(f'\n📊 训练后状态:')
    print(f'  🎯 解族数: {new_stats[\"clusters\"][\"total\"]}')
    print(f'  🧩 局部模型: {new_stats[\"models\"][\"local\"][\"count\"]}')
    print(f'  🤖 全局模型类型: {new_stats[\"models\"][\"global\"][\"type\"]}')
    
    # 测试几个点（使用增强预测）
    print(f'\n🧪 测试预测 (使用聚类增强):')
    test_points = [
        [0.55, -0.1, 0.6],
        [0.4, 0.0, 0.5],
        [0.5, 0.0, 0.5],
        [0.45, -0.1, 0.45],
    ]
    
    for point in test_points:
        # 使用带聚类的预测
        pred, conf, cluster_id = predictor.predict_with_clustering(point)
        if pred is not None:
            if cluster_id:
                print(f'  {point} -> [{pred[0]:.3f}, {pred[1]:.3f}, {pred[2]:.3f}...] (解族:{cluster_id}, 置信度:{conf:.2f})')
            else:
                pred2, unc = predictor.predict(point)
                print(f'  {point} -> [{pred[0]:.3f}, {pred[1]:.3f}, {pred[2]:.3f}...] (全局, 不确定度:{unc:.3f})')
        else:
            print(f'  {point} -> 预测失败')
else:
    print('❌ 训练失败')
"

echo ""
echo "========================================="
echo "LMA模型训练完成！"
echo "========================================="

# 显示最终统计（增强版）
echo ""
echo "📊 最终LMA系统状态:"
python3 -c "
import json
import os
from pathlib import Path

lma_file = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/lma_training_data.json'
cluster_file = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/clusters/lma_clusters.json'
model_file = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/models/latest.pkl'
local_models_dir = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/local_models'

# 样本统计
if os.path.exists(lma_file):
    with open(lma_file) as f:
        data = json.load(f)
    samples = data.get('samples', [])
    print(f'  📁 LMA样本总数: {len(samples)}')

# 聚类统计
if os.path.exists(cluster_file):
    with open(cluster_file) as f:
        clusters = json.load(f)
    total_clusters = sum(len(v.get('clusters', {})) for v in clusters.values())
    print(f'  🎯 LMA解族总数: {total_clusters}')

# 局部模型统计
local_models = list(Path(local_models_dir).glob('*.pkl'))
print(f'  🧩 局部模型数量: {len(local_models)}')

# 全局模型统计
if os.path.exists(model_file):
    import joblib
    try:
        model = joblib.load(model_file)
        model_type = type(model).__name__
        print(f'  🤖 全局模型类型: {model_type}')
    except:
        print(f'  🤖 全局模型: 存在但无法加载')
else:
    print(f'  🤖 全局模型: 未训练')

# 验证统计
val_file = '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/stats/validation_log.json'
if os.path.exists(val_file):
    with open(val_file) as f:
        val_data = json.load(f)
    val_count = len(val_data.get('history', []))
    if val_count > 0:
        errors = [h['error_mm'] for h in val_data['history'][-100:]]
        print(f'  ✅ 最近100次平均误差: {sum(errors)/len(errors):.1f}mm')
"

echo ""
echo "✅ LMA训练脚本执行完毕"
echo ""
echo "可用命令:"
echo "  ./test_lma              # 测试LMA预测器"
echo "  ./compare_ml             # 对比原ML和LMA"
echo "  ls -la $LMA_DATA_DIR     # 查看LMA数据文件"
