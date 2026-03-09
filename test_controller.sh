#!/bin/bash
# RobotPress 一键启动脚本
# 功能：启动 ROS 2 服务节点 + rosbridge WebSocket + 前端

# ========== 颜色定义 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ========== 检查环境 ==========
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 RobotPress 一键启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查是否在 qingfu_moveit 目录下
if [ ! -d "$HOME/qingfu_moveit" ]; then
    echo -e "${RED}❌ 错误：找不到 ~/qingfu_moveit 目录${NC}"
    exit 1
fi

cd "$HOME/qingfu_moveit"

# ========== 清理可能占用的进程 ==========
echo -e "${YELLOW}🔄 清理旧进程...${NC}"
pkill -f "rosbridge" 2>/dev/null
pkill -f "grasp_service" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sleep 1

# ========== 启动服务节点 ==========
echo -e "${GREEN}📡 [1/3] 启动 ROS 2 服务节点...${NC}"
source install/setup.bash

# 直接用完整路径运行（避免 ros2 run 找不到的问题）
/home/diyuanqiongyu/qingfu_moveit/install/robot_services/bin/grasp_service &
GRASP_PID=$!
echo -e "${GREEN}✅ 服务节点已启动 (PID: $GRASP_PID)${NC}"
sleep 2

# ========== 启动 rosbridge ==========
echo -e "${GREEN}🌉 [2/3] 启动 rosbridge WebSocket 服务器...${NC}"
source install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=8765 &
ROSBRIDGE_PID=$!
echo -e "${GREEN}✅ rosbridge 已启动 (PID: $ROSBRIDGE_PID)${NC}"
sleep 3

# ========== 启动前端 ==========
echo -e "${GREEN}🎨 [3/3] 启动前端开发服务器...${NC}"
cd "$HOME/qingfu_moveit/robotpress/frontend"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端已启动 (PID: $FRONTEND_PID)${NC}"

# ========== 显示状态 ==========
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 所有服务已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "📡 服务节点 PID: ${YELLOW}$GRASP_PID${NC}"
echo -e "🌉 rosbridge PID: ${YELLOW}$ROSBRIDGE_PID${NC}"
echo -e "🎨 前端 PID:    ${YELLOW}$FRONTEND_PID${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "📌 访问地址: ${GREEN}http://localhost:5173${NC}"
echo -e "📌 停止服务: ${YELLOW}按 Ctrl+C 或运行 ./stop_robotpress.sh${NC}"
echo -e "${BLUE}========================================${NC}"

# ========== 等待用户中断 ==========
wait