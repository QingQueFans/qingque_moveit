#!/bin/bash
# 探索脚本 - 高质量收集模式（阈值80mm）

echo "🧹 清理旧IK缓存..."
rm ~/qingfu_moveit/moveit_core/cache_manager/data/kinematics/ik_solutions/ik_*.json 2>/dev/null
rm ~/qingfu_moveit/moveit_core/cache_manager/data/kinematics/ik_solutions/object_links/*.json 2>/dev/null
echo "✅ 缓存清理完成"

echo "🚀 开始高质量探索（阈值80mm）..."

# ===== 定义探索点位（扩展版）=====
declare -a TARGETS=(
    # 原有高质量区域
    "0.55 -0.1 0.6"   # 出现过23mm的解
    "0.4 0.0 0.5"     # 出现过17mm的解
    "0.4 0.0 0.48"    # 出现过42mm的解
    "0.55 -0.1 0.65"  # 出现过48mm的解
    
    # ===== 新增：围绕好解扩展 =====
    "0.38 0.0 0.48"
    "0.38 0.0 0.52"
    "0.42 0.0 0.48"
    "0.42 0.0 0.52"
    "0.4 0.03 0.5"
    "0.4 -0.03 0.5"
    
    # ===== 新增：y方向探索 =====
    "0.5 0.05 0.55"
    "0.5 -0.05 0.55"
    "0.55 0.05 0.6"
    "0.55 -0.15 0.6"
    
    # ===== 新增：新区域 =====
    "0.3 0.0 0.3"
    "0.3 0.0 0.35"
    "0.35 0.0 0.3"
    "0.45 0.05 0.45"
    "0.45 -0.05 0.45"
    
    # ===== 新增：插值点连接好坏区域 =====
    "0.42 0.0 0.51"
    "0.44 0.0 0.52"
    "0.46 0.0 0.53"
    "0.48 0.0 0.54"
    
    # 原有点位
    "0.4 0.0 0.38"
    "0.4 0.0 0.4"
    "0.4 0.0 0.42"
    "0.4 0.0 0.45"
    "0.5 0.0 0.5"
    "0.5 0.0 0.52"
    "0.5 0.0 0.55"
    "0.45 -0.1 0.5"
    "0.45 -0.1 0.45"
)

# 外层循环 - 重复探索多轮
for round in {1..20}; do
    echo ""
    echo "===== 第 $round 轮探索 ====="
    
    # 每5轮动态调整（只在这个脚本内生效）
    if [ $((round % 5)) -eq 0 ] && [ $round -lt 20 ]; then
        echo ""
        echo "🔄 第 $round 轮结束，动态分析..."
        
        # 分析当前数据，找出好点周围的新点
        NEW_POINTS=$(python3 -c "
import json
import numpy as np
from collections import defaultdict

try:
    f=open('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/src/data/training_data.json')
    data=json.load(f)
    samples = data['samples']
    
    # 按点位分组
    points = defaultdict(list)
    for s in samples:
        pose = tuple(s['target_pose'][:3])
        points[pose].append(s['error'])
    
    # 找出表现好的点位（平均误差<55mm且样本>3）
    good_points = []
    for pose, errors in points.items():
        if np.mean(errors) < 55 and len(errors) > 3:
            good_points.append(pose)
    
    # 生成新点
    new_points = []
    for x, y, z in good_points[:3]:  # 只取前3个好点
        for dx in [-0.02, 0.02]:
            for dz in [-0.02, 0.02]:
                nx = round(x + dx, 2)
                nz = round(z + dz, 2)
                if 0.2 <= nx <= 0.8 and 0.2 <= nz <= 0.8:  # 工作空间内
                    new_points.append(f'{nx} {y} {nz}')
    
    # 输出去重后的新点
    for p in set(new_points):
        print(p)
except:
    pass
")
        
        # 添加新点到TARGETS
        if [ -n "$NEW_POINTS" ]; then
            while IFS= read -r new_point; do
                if [[ ! " ${TARGETS[@]} " =~ " ${new_point} " ]]; then
                    TARGETS+=("$new_point")
                    echo "  ➕ 动态添加新探索点: $new_point"
                fi
            done <<< "$NEW_POINTS"
        fi
    fi
    
    # 内层循环 - 遍历所有目标位姿
    for target in "${TARGETS[@]}"; do
        # 解析坐标
        read -r x y z <<< "$target"
        
        echo ""
        echo "🎯 探索位姿: [$x, $y, $z]"
        
        # ===== 根据点位动态调整尝试次数 =====
        if [ "$x" = "0.5" ] && [ "$z" = "0.55" ]; then
            max_attempts=25  # 难点区域多尝试
            echo "  🔥 难点区域，增加尝试次数到 $max_attempts"
        elif [ "$x" = "0.4" ] && [ "$z" = "0.5" ]; then
            max_attempts=10  # 好点区域少尝试
            echo "  ⭐ 优质区域，适度尝试 $max_attempts 次"
        else
            max_attempts=15
        fi
        
        # 调用Python脚本直接求解IK
        python3 -c "
import sys
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')
from moveit_bootstrap import init_moveit_paths
init_moveit_paths()
from kin_ik.ik_solver import IKSolver
import time
import numpy as np
from collections import defaultdict

ik = IKSolver()
x, y, z = $x, $y, $z
target_pose = [x, y, z, 0.0, 0.0, 0.0, 1.0]
max_attempts = $max_attempts

# ===== 简单的陷阱记录（存在ik对象里，只在这个脚本运行时有效）=====
if not hasattr(ik, 'trap_seeds'):
    ik.trap_seeds = defaultdict(dict)

pose_key = f'{x:.2f}_{y:.2f}_{z:.2f}'

best_error = 1000
best_result = None

for attempt in range(max_attempts):
    # ===== 跳过已知陷阱种子 =====
    current_seed = None
    if attempt == 0 and hasattr(ik, '_last_seed'):
        current_seed = ik._last_seed
    
    # 检查是否是陷阱
    if current_seed is not None:
        seed_sig = tuple(round(s, 1) for s in current_seed[:2])
        if seed_sig in ik.trap_seeds.get(pose_key, {}):
            print(f'  ⛔ 跳过陷阱种子 (已出现{ik.trap_seeds[pose_key][seed_sig]}次)')
            continue
    
    result = ik.solve(
        target_pose=target_pose,
        optimize=True,
        max_attempts=10,
        check_collision=False
    )
    
    if result.get('success', False):
        error = result.get('verification', {}).get('error_mm', 1000)
        print(f'  尝试{attempt+1}: {error:.1f}mm')
        
        if error < best_error:
            best_error = error
            best_result = result
            ik._last_seed = result['solution']
            
        if error < 80:
            break
    else:
        print(f'  尝试{attempt+1}: 失败')
    
    time.sleep(0.5)

# ===== 记录陷阱种子 =====
if best_result and best_error > 80 and attempt == max_attempts - 1:
    seed_sig = tuple(round(s, 1) for s in best_result['solution'][:2])
    if seed_sig not in ik.trap_seeds[pose_key]:
        ik.trap_seeds[pose_key][seed_sig] = 1
    else:
        ik.trap_seeds[pose_key][seed_sig] += 1
    
    if ik.trap_seeds[pose_key][seed_sig] >= 3:
        print(f'  🪤 发现陷阱种子! (已出现{ik.trap_seeds[pose_key][seed_sig]}次)')

# 打破局部最优的探索
if best_result and best_error < 120 and best_error >= 80:
    print(f'  🔍 尝试打破局部最优 (当前最佳: {best_error:.1f}mm)')
    
    for i in range(3):
        noise = np.random.normal(0, 0.2, 7)
        noisy_seed = np.array(best_result['solution']) + noise
        result2 = ik.solve(target_pose, seed=noisy_seed.tolist(), optimize=True, max_attempts=5)
        
        if result2.get('success', False):
            error2 = result2.get('verification', {}).get('error_mm', 1000)
            print(f'    扰动{i+1}: {error2:.1f}mm')
            
            if error2 < best_error and error2 < 80:
                best_error = error2
                best_result = result2
                print(f'    ✅ 找到更好的解!')
                break
    
    if abs(x - 0.55) < 0.01 and abs(y + 0.1) < 0.01 and abs(z - 0.6) < 0.01:
        print(f'  🔍 尝试已知的23mm解...')
        known_good_seed = [-0.5543052929701929, 1.8326, 2.0222360294540986, 
                          -1.5096410345607731, -2.9671, 2.110374438112213, 1.3923898911713568]
        result3 = ik.solve(target_pose, seed=known_good_seed, optimize=True, max_attempts=5)
        
        if result3.get('success', False):
            error3 = result3.get('verification', {}).get('error_mm', 1000)
            print(f'    已知解: {error3:.1f}mm')
            
            if error3 < best_error and error3 < 80:
                best_error = error3
                best_result = result3
                print(f'    ✅ 找到更好的解!')

# 处理严重偏离的解
if best_result and best_error > 120:
    print(f'  ⚠️ 发现严重偏离的解: {best_error:.1f}mm')
    
    for i in range(5):
        random_seed = np.random.uniform(-2, 2, 7)
        result = ik.solve(target_pose, seed=random_seed.tolist())
        if result.get('success', False):
            error = result.get('verification', {}).get('error_mm', 1000)
            if error < 100:
                best_error = error
                best_result = result
                print(f'    ✅ 随机搜索找到: {error:.1f}mm')
                break

# 添加高质量解
if best_result and best_error < 80:
    print(f'  ✅ 找到高质量解! 误差: {best_error:.1f}mm')
    
    ik.ml_predictor.add_sample(
        target_pose=target_pose,
        successful_seed=best_result['solution'],
        error_mm=best_error,
        object_id='high_quality'
    )
    
    stats = ik.ml_predictor.get_stats()
    print(f'  📚 已添加到训练集! 当前样本数: {stats[\"samples\"]}')
    
    if best_error < 50:
        print(f'  ✨ 超高质量解! 添加两个增强样本')
        for i in range(2):
            noise = np.random.normal(0, 0.03, 7)
            varied_seed = np.array(best_result['solution']) + noise
            ik.ml_predictor.add_sample(
                target_pose=target_pose,
                successful_seed=varied_seed.tolist(),
                error_mm=best_error * 1.05,
                object_id='high_quality_aug'
            )
            print(f'    增强样本{i+1}已添加')
else:
    print(f'  ❌ 未找到高质量解 (最佳: {best_error:.1f}mm)')
"
        
        sleep 2
    done
    
    # 每轮结束后显示当前样本数
    echo ""
    echo "📊 第 $round 轮结束，当前样本数:"
    python3 -c "
import json
f=open('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/src/data/training_data.json')
data=json.load(f)
print(f'总样本: {len(data[\"samples\"])}')
"
    
    sleep 5
done

echo ""
echo "✅ 探索完成！"