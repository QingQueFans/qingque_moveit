# 终端2：进入脚本目录
cd ~/qingfu_moveit/moveit_ros/grasping/capability_servers/scripts/

# 测试夹爪闭合（抓取动作）
python3 ros-start-pick-server --test --object test_cube --verbose

# 你应该在终端看到：
# [抓取序列] 闭合夹爪
# [夹爪控制器] 夹爪闭合: width=0.0m, effort=30.0N

# 在RViz中应该看到：
# 夹爪从张开状态 → 完全闭合状态


# 手动张开到40mm
ros2 action send_goal /panda_hand_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.04, max_effort: 10.0}}"

cd ~/qingfu_moveit/moveit_ros/grasping/capability_servers/scripts
python3 ros-start-pick-server --test --object test_cube --verbose

# 测试放置（会调用 release_sync）
python3 ros-start-place-server --test --object test_cube --verbose

# 即使 detach_object 失败，夹爪张开应该还是会执行

# 显示横幅和帮助
python3  ps-grab

# 快速抓取（手动指定宽度）
python3  ps-grab grab qingque
python3  ps-grab grab qingque --width 50
python3  ps-grab grab qingque --width 0
python3  ps-grab grab qingque --width 50 --verbose

# 智能抓取（自动计算）
python3  ps-grab grab qingque --auto
python3  ps-grab grab qingque --auto --strategy side_grasp
python3  ps-grab grab qingque --auto --strategy top_grasp --verbose

# 释放物体
python3  ps-grab release qingque
python3  ps-grab release --width 100
python3  ps-grab release --width 100 --verbose

# 状态查询
python3  ps-grab status
python3  ps-grab status --verbose

# JSON格式输出（适合脚本调用）
python3  ps-grab grab qingque --auto --json
python3  ps-grab status --json