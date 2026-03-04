cd ~/qingfu_moveit/moveit_ros/planning_interface/move_group_interface/scripts/
./train_lma_from_explore.sh
./explore_high_quality.sh

🤖 ML种子预测器 - 简介
基本信息
模型类型: KNeighborsRegressor（K近邻回归）

K值: 3（默认，可配置）

训练样本: 当前9个（还在增长）

作用: 根据目标位姿预测好的IK种子

什么是K近邻（KNN）？
想象你在找餐厅：

你问朋友"附近有什么好吃的？"

朋友会推荐离你最近的3家餐厅（K=3）

然后综合这3家的评分给出建议

KNN就是这样：

给定一个新的目标位姿

找到历史数据中最相似的K个样本

综合这K个样本的种子，给出预测

工作原理
text
目标位姿 [0.55, -0.1, 0.55]
    ↓ 找最近的3个历史样本
样本1: [0.6, 0.0, 0.5] → 种子A
样本2: [0.5, 0.0, 0.5] → 种子B  
样本3: [0.5, -0.1, 0.5] → 种子C
    ↓ 加权平均
预测种子 [种子A*0.4 + 种子B*0.3 + 种子C*0.3]
优势
✅ 简单直观，容易理解

✅ 数据越多越准

✅ 自动适应工作空间

现在状态
已经训练好第一个模型

会随着新数据自动优化

很快就能看到预测效果！

cd ~/qingfu_moveit/moveit_core/planning_scene/collision_objects/scripts/

# 添加 train_1 (安全位置)
python3 ps-add-object --box --name "train_1" --position "0.4,0.0,0.4" --orientation "0,0,0,1" --yes

# 添加 train_4 (安全位置)  
python3 ps-add-object --box --name "train_4" --position "0.55,-0.1,0.55" --orientation "0,0,0,1" --yes

# 添加 train_pos3 (黄金样本位置)
python3 ps-add-object --box --name "train_pos3" --position "0.6,0.0,0.5" --orientation "0,0,0,1" --yes

# 添加5个不同位置的安全物体
python3 ps-add-object --box --name "safe_1" --position "0.4,0.1,0.35" --orientation "0,0,0,1" --yes
python3 ps-add-object --box --name "safe_2" --position "0.45,-0.1,0.4" --orientation "0,0,0,1" --yes
python3 ps-add-object --box --name "safe_3" --position "0.5,0.0,0.45" --orientation "0,0,0,1" --yes
python3 ps-add-object --box --name "safe_4" --position "0.55,0.1,0.4" --orientation "0,0,0,1" --yes
python3 ps-add-object --box --name "safe_5" --position "0.6,0.0,0.5" --orientation "0,0,0,1" --yes
# 确认添加成功
python3 ps-list-objects

聚类
python3 -c "
import sys
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')
from moveit_bootstrap import init_moveit_paths
init_moveit_paths()
from kin_ik.ik_solver import IKSolver
ik = IKSolver()
# 触发聚类分析
if hasattr(ik.ml_predictor, 'clusterer'):
    ik.ml_predictor.clusterer.analyze_all_regions()
    stats = ik.ml_predictor.get_enhanced_stats()
    print('解族情况:', stats)
else:
    print('基础统计:', ik.ml_predictor.get_stats())
"
# 快速版得出解
./explore_high_quality.sh

有关官方ik使用
因為官方默認讀取的是系統目錄的文件！
目前的情況
text
官方demo.launch.py 讀取的是：
/opt/ros/humble/share/moveit_resources_panda_moveit_config/config/kinematics.yaml
    └── kinematics_solver_timeout: 0.005 (太短！)

您修改的文件在：
/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/moveit_ik/config/kinematics.yaml
    └── kinematics_solver_timeout: 0.1 (您改好的)
官方demo不會自動找到您的文件！
它只會去系統目錄找，不會去您的家目錄找。

解決方案有兩個
方案A：覆蓋系統文件（簡單）
bash
sudo cp /home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/moveit_ik/config/kinematics.yaml \
      /opt/ros/humble/share/moveit_resources_panda_moveit_config/config/kinematics.yaml

      panda_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.1  # 應該是 0.1
  kinematics_solver_attempts: 5    # 應該是 5
  # 监控LMA数据增长

cd ~/qingfu_moveit/moveit_ros/planning_interface/move_group_interface/scripts/
./train_lma_from_explore.sh
./explore_high_quality.sh
watch -n 2 'python3 -c "
import json
f = open(\"/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data/lma_training_data.json\")
data = json.load(f)
samples = data.get(\"samples\", [])
if samples:
    errors = [s.get(\"error_mm\", 0) for s in samples]
    print(f\"LMA样本数: {len(samples)}\")
    print(f\"平均误差: {sum(errors)/len(errors):.1f}mm\")
    print(f\"最小误差: {min(errors):.1f}mm\")
else:
    print(\"LMA样本数: 0\")
"'