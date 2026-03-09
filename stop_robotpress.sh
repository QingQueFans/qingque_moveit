#!/bin/bash
# RobotPress 停止脚本

if [ -f /tmp/robotpress_pids.txt ]; then
    echo "🛑 正在停止 RobotPress 服务..."
    read MOVEIT_PID SERVICE_PID ROSBRIDGE_PID FRONTEND_PID < /tmp/robotpress_pids.txt
    
    kill -9 $MOVEIT_PID $SERVICE_PID $ROSBRIDGE_PID $FRONTEND_PID 2>/dev/null
    rm /tmp/robotpress_pids.txt
    echo "✅ 所有服务已停止"
else
    echo "❌ 找不到 PID 文件，尝试直接 kill 进程"
    pkill -f "moveit_resources_panda_moveit_config"
    pkill -f "grasp_service"
    pkill -f "rosbridge"
    pkill -f "npm run dev"
    echo "✅ 已停止所有相关进程"
fi