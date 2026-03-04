#!/bin/bash
# 训练脚本 - 先清理，再训练

echo "🧹 清理旧IK缓存..."
rm ~/qingfu_moveit/moveit_core/cache_manager/data/kinematics/ik_solutions/ik_*.json 2>/dev/null
rm ~/qingfu_moveit/moveit_core/cache_manager/data/kinematics/ik_solutions/object_links/*.json 2>/dev/null
echo "✅ 缓存清理完成"

echo "🚀 开始训练..."
for i in {1..50}; do
    echo ""
    echo "===== 第 $i 轮训练 ====="
    
    for obj in safe_1 safe_2 safe_3 safe_4 safe_5 train_1 train_4 train_pos3; do
        echo "抓取 $obj..."
        python3 ros-move-group-grasp grasp --object $obj
        
        echo "释放 $obj..."
        python3 ros-move-group-grasp release --object $obj
        
        sleep 2
    done
done

echo ""
echo "✅ 训练完成！"