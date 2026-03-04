#!/bin/bash
# 自动激活ROS 2环境脚本

echo "激活ROS 2环境..."
source /opt/ros/humble/setup.bash

# 验证
echo "ROS_DISTRO: $ROS_DISTRO"
if command -v ros2 &> /dev/null; then
    echo "✅ ros2 命令可用"
else
    echo "❌ ros2 命令不可用"
fi

# 可选：激活工作空间（如果存在）
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
    echo "✅ 工作空间环境已激活"
fi
