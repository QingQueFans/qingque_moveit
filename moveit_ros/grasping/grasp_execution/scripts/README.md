# 为缓存中的物体计算抓取参数
python3 ros-control-gripper --object qingque
python3 ros-control-gripper --object box

# 指定抓取策略
python3 ros-control-gripper --object red_cup --strategy side_grasp

# 直接输入物体参数
python3 ros-control-gripper --direct --type box --dimensions 0.05 0.05 0.05
python3 ros-control-gripper --direct --type cylinder --dimensions 0.03 0.12
python3 ros-control-gripper --direct --type sphere --dimensions 0.04

# 查看夹爪状态
python3 ros-control-gripper --status

# 查看当前配置
python3 ros-control-gripper --config

# 测试所有预定义物体
python3 ros-control-gripper --test-all

# 详细输出
python3 ros-control-gripper --object test_cube --verbose

# JSON格式输出
python3 ros-control-gripper --object test_cube --json

# 自定义夹爪参数
python3 ros-control-gripper --object test_cube --min-width 0.01 --max-width 0.08