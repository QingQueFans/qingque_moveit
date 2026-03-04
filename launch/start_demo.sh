#!/bin/bash
echo "🚀 启动 Panda MoveIt 2 演示"
echo "=========================="

# 检查并设置ROS环境
if [ -z "$ROS_DISTRO" ]; then
    echo "设置ROS 2 Humble环境..."
    source /opt/ros/humble/setup.bash
fi

echo "当前ROS版本: $ROS_DISTRO"
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 检查是否已安装必要包
echo "检查安装包..."
if ! ros2 pkg list | grep -q "moveit_resources_panda_moveit_config"; then
    echo "⚠️  未找到panda_moveit_config包"
    read -p "是否安装? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt install ros-humble-moveit-resources-panda-moveit-config
    else
        echo "❌ 未安装必要包，退出"
        exit 1
    fi
fi

# 启动演示
echo "启动MoveIt 2演示..."
echo "按 Ctrl+C 停止演示"
echo "--------------------------"

ros2 launch moveit_resources_panda_moveit_config demo.launch.py

echo "演示已停止"
echo "--------------------------"
