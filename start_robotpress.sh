#!/bin/bash
# RobotPress 简化启动脚本

echo "========================================"
echo "🚀 RobotPress 简化启动"
echo "========================================"

# 终端1: 前端
echo "📱 启动前端..."
gnome-terminal -- bash -c "cd ~/qingfu_moveit/robotpress/frontend && npm run dev; exec bash"

# 终端2: 后端桥接
echo "🌉 启动后端桥接服务器..."
gnome-terminal -- bash -c "cd ~/qingfu_moveit/robotpress/backend && source ~/qingfu_moveit/qingque_env/bin/activate && python3 bridge.py; exec bash"

# 终端3: MoveIt 仿真
echo "🤖 启动 MoveIt 仿真..."
gnome-terminal -- bash -c "source /opt/ros/humble/setup.bash && source ~/qingfu_moveit/install/setup.bash && ros2 launch moveit_resources_panda_moveit_config demo.launch.py; exec bash"

echo "========================================"
echo "✅ 所有服务已启动"
echo "📌 前端地址: http://localhost:5173"
echo "========================================"