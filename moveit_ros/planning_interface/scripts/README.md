✅ plan-grasp 运行命令大全
1. 基础抓取
bash
cd ~/qingfu_moveit
./moveit_ros/planning_interface/scripts/plan-grasp train_1
2. 指定夹爪宽度
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --width 40
3. 指定抓取策略
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --strategy top_grasp
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --strategy side_grasp
4. 调整接近距离
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --approach 0.15
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --approach 0.05
5. 设置规划超时
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --timeout 10.0
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --timeout 3.0
6. 详细输出
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --verbose
7. JSON 格式输出
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --json
8. 组合参数
bash
./moveit_ros/planning_interface/scripts/plan-grasp train_1 --width 40 --strategy top_grasp --approach 0.1 --timeout 8.0 --verbose
9. 用 python3 运行（如果没权限）
bash
cd ~/qingfu_moveit
python3 moveit_ros/planning_interface/scripts/plan-grasp train_1
10. 添加到 PATH 后直接运行
bash
export PATH=$PATH:~/qingfu_moveit/moveit_ros/planning_interface/scripts
plan-grasp train_1
最常用的是第1条和第6条！

