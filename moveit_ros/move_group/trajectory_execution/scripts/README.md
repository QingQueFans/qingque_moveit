运行这些脚本需要先打开控制管理器
# 终端2
cd ~/qingfu_moveit/moveit_plugins/moveit_controller_manager/scripts
python3 ros-start-controller

# 等待看到：✓ 找到可用控制器: /panda_arm_controller/follow_joint_trajectory

明白了！你只想要 ros-start-execution 脚本的纯命令行使用指南。这是最精简的版本：

🎯 ros-start-execution 脚本纯命令行指南

📌 基本命令格式

```bash
cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution/scripts
python3 ros-start-execution [参数]
```

---

🚀 1. 基础执行命令

零位置测试（最安全）

```bash
python3 ros-start-execution --zero
```

默认轨迹（3个点）

```bash
python3 ros-start-execution
```

指定点数

```bash
python3 ros-start-execution --points 5
```

---

⚙️ 2. 参数调整命令

速度控制

```bash
# 半速执行
python3 ros-start-execution --velocity 0.5

# 慢速执行
python3 ros-start-execution --velocity 0.3

# 全速执行（默认）
python3 ros-start-execution --velocity 1.0
```

加速度控制

```bash
python3 ros-start-execution --acceleration 0.5
```

关节数指定

```bash
# Panda机械臂（7关节）
python3 ros-start-execution --joints 7

# 其他机械臂
python3 ros-start-execution --joints 6
```

---

📊 3. 信息查询命令

查看执行状态

```bash
python3 ros-start-execution --status
```

查看配置

```bash
python3 ros-start-execution --config
```

查看历史记录

```bash
# 查看最近5条记录
python3 ros-start-execution --history 5

# 查看最近10条记录
python3 ros-start-execution --history 10
```

停止当前执行

```bash
python3 ros-start-execution --stop
```

---

💾 4. 输出控制命令

JSON格式输出

```bash
python3 ros-start-execution --json
```

详细输出

```bash
# 一级详细
python3 ros-start-execution --verbose

# 二级详细
python3 ros-start-execution -vv

# 三级详细
python3 ros-start-execution -vvv
```

保存到文件

```bash
python3 ros-start-execution --output result.json
```

---

🔧 5. 运行模式命令

模拟模式（不连接ROS）

```bash
python3 ros-start-execution --no-ros
```

强制同步模式

```bash
python3 ros-start-execution --sync
```

异步执行（不等待完成）

```bash
python3 ros-start-execution --async
```

---

🎯 6. 常用组合命令

安全测试组合

```bash
python3 ros-start-execution --zero --velocity 0.3 --verbose
```

调试组合

```bash
python3 ros-start-execution --points 2 --json --verbose
```

性能测试组合

```bash
python3 ros-start-execution --points 10 --velocity 1.0 --acceleration 1.0
```

快速验证组合

```bash
python3 ros-start-execution --zero --json --output test_result.json
```

---

📝 7. 帮助命令

查看完整帮助

```bash
python3 ros-start-execution --help
```

查看示例

```bash
python3 ros-start-execution -h | grep -A 10 "示例"
```

---

🚨 8. 故障排除命令

检查依赖

```bash
cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution
python3 -c "from ps_core.scene_client import PlanningSceneClient; print('依赖正常')"
```

简单测试

```bash
# 最小测试
python3 ros-start-execution --points 1 --no-ros
```

---

🎪 9. 实际应用示例

示例1：完整的执行流程

```bash
# 1. 检查状态
python3 ros-start-execution --status

# 2. 零位置测试
python3 ros-start-execution --zero --verbose

# 3. 执行轨迹
python3 ros-start-execution --points 3 --velocity 0.7

# 4. 查看结果
python3 ros-start-execution --history 3
```

示例2：批量测试

```bash
# 测试不同速度
for speed in 0.3 0.5 0.8 1.0; do
    echo "测试速度: $speed"
    python3 ros-start-execution --points 2 --velocity $speed --output speed_${speed}.json
done
```

这就是纯命令行使用指南，直接复制粘贴到终端即可使用！
📋 全部可执行脚本命令（完整版）

🔧 1. 轨迹执行模块脚本

```bash
# 主要执行脚本
cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution

# 轨迹执行
python3 ros-start-execution
python3 ros-start-execution --zero
python3 ros-start-execution --points 5
python3 ros-start-execution --velocity 0.5 --acceleration 0.3

# 状态查询
python3 ros-start-execution --status
python3 ros-start-execution --config
python3 ros-start-execution --history 10

# 输出控制
python3 ros-start-execution --json
python3 ros-start-execution --verbose
python3 ros-start-execution --output result.json

# 运行模式
python3 ros-start-execution --no-ros
python3 ros-start-execution --sync
```

🛑 2. 停止执行脚本

```bash
python3 ros-stop-execution
```

📊 3. 轨迹监控脚本

```bash
# 实时监控
python3 ros-monitor-trajectory
python3 ros-monitor-trajectory --interval 0.5

# 状态检查
python3 ros-monitor-trajectory --status

# 历史查看
python3 ros-monitor-trajectory --history 8
```

🔍 4. 控制器状态脚本

```bash
python3 ros-controller-status
```

🎨 5. 可视化脚本（暂缓）

```bash
python3 ros-execution-visualize
```

🚀 6. 控制器管理器脚本

```bash
# 重要：必须先运行这个！
cd ~/qingfu_moveit/moveit_plugins/moveit_controller_manager/scripts
python3 ros-start-controller
```

🔄 7. 能力服务器脚本（move_group下）

```bash
cd ~/qingfu_moveit/moveit_ros/move_group/capability_servers/scripts

# 移动服务器
python3 ros-start-move-server

# 规划服务器
python3 ros-start-plan-server

# 执行服务器
python3 ros-start-execute-server

# 查询服务器
python3 ros-start-query-server

# 状态检查
python3 ros-capability-status
```

🗺️ 8. 规划流水线脚本

```bash
cd ~/qingfu_moveit/moveit_ros/move_group/planning_pipeline/scripts

# 设置流水线
python3 ros-setup-pipeline

# 配置规划器
python3 ros-configure-planner

# 运行规划
python3 ros-run-pipeline

# 流水线状态
python3 ros-pipeline-status
```

🦾 9. 运动学管理脚本

```bash
cd ~/qingfu_moveit/moveit_ros/move_group/kinematics_management/scripts

# 配置运动学
python3 ros-configure-kinematics

# IK求解器选择
python3 ros-select-ik-solver

# FK求解器选择
python3 ros-select-fk-solver

# 运动学状态
python3 ros-kinematics-status
```

✅ 验证脚本

```bash
# 快速测试所有脚本
cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution/scripts
chmod +x ros-*  # 确保有执行权限

# 测试核心功能
python3 ros-start-execution --zero --verbose
python3 ros-controller-status
python3 ros-monitor-trajectory --status
```

好的！我把所有命令行参数分类整理如下：

📋 命令行参数分类列表

🎯 一、规划相关参数（核心功能）

参数 简写 类型 默认值 说明
--plan -P 布尔 False 启用规划模式（使用OMPL生成轨迹）
--plan-only  布尔 False 只规划不执行（生成轨迹但不执行）
--goal-joints  字符串 无 目标关节角度，逗号分隔 "0,0.5,0,-1,0,1,0"
--goal-pose  字符串 无 目标末端位姿，格式： "x,y,z,roll,pitch,yaw" 或 "x,y,z,qx,qy,qz,qw"
--algorithm -a 字符串 rrt_connect 规划算法选择： rrt_connect, rrt_star, prm
--planning-time  浮点 5.0 规划超时时间（秒）

---

🛠️ 二、轨迹参数（传统模式）

参数 简写 类型 默认值 说明
--points -p 整数 3 预设轨迹的点数（1-10）
--zero -z 布尔 False 使用零位置轨迹（最安全）
--velocity  浮点 1.0 速度缩放因子（0.1-2.0）
--acceleration  浮点 1.0 加速度缩放因子（0.1-2.0）

---

⚙️ 三、控制命令（管理功能）

参数 简写 类型 说明
--stop  布尔 停止当前执行中的轨迹
--status -s 布尔 查看执行状态和进度
--config  布尔 查看当前执行配置
--history  整数 查看最近N条执行历史

---

📊 四、输出选项（结果展示）

参数 简写 类型 说明
--output -o 字符串 保存结果到指定JSON文件
--json -j 布尔 以JSON格式输出结果
--verbose -v 计数 详细输出模式（可重复：-v, -vv, -vvv）

---

🔧 五、运行模式（环境配置）

参数 简写 类型 说明
--no-ros  布尔 模拟模式（不连接ROS，用于测试）
--sync  布尔 强制使用同步模式（默认已启用）

---

🎯 典型使用场景分类

场景1：规划与执行

```bash
# 规划并执行到指定关节位置
ros-start-execution --plan --goal-joints "0,0.5,0,-1,0,1,0"

# 规划并执行到末端位姿
ros-start-execution --plan --goal-pose "0.42,0.0,0.52,0,0,0,1"

# 只规划不执行（用于调试）
ros-start-execution --plan-only --algorithm rrt_star --planning-time 10.0
```

场景2：预设轨迹执行

```bash
# 执行3点预设轨迹
ros-start-execution

# 执行零位置轨迹（回零）
ros-start-execution --zero

# 慢速执行
ros-start-execution --velocity 0.5 --acceleration 0.3

# 执行单点轨迹
ros-start-execution --points 1
```

场景3：系统管理

```bash
# 查看当前状态
ros-start-execution --status

# 停止当前执行
ros-start-execution --stop

# 查看配置
ros-start-execution --config

# 查看最近5条执行历史
ros-start-execution --history 5
```

场景4：数据导出与调试

```bash
# JSON格式输出
ros-start-execution --plan --json

# 详细输出
ros-start-execution --plan -vv

# 保存结果到文件
ros-start-execution --plan --output result.json

# 模拟模式测试
ros-start-execution --no-ros --plan
```

---

🔄 模式选择流程图

```
用户输入 → 判断模式:
├── 如果包含 --plan 参数 → 规划模式
│   ├── 如果包含 --plan-only → 只规划不执行
│   └── 否则 → 规划并执行
│
├── 如果包含控制命令 → 管理功能
│   ├── --stop → 停止执行
│   ├── --status → 查看状态
│   ├── --config → 查看配置
│   └── --history → 查看历史
│
└── 否则 → 预设轨迹模式
    ├── 如果包含 --zero → 零位置轨迹
    └── 否则 → 随机轨迹（点数由 --points 决定）
```

---

⚠️ 参数互斥关系

1. --plan 与 --points/--zero：互斥，不能同时使用
2. --plan-only 必须与 --plan 一起使用
3. --goal-joints 与 --goal-pose：互斥，只能选一个
4. 控制命令（--stop/--status等）：互斥，一次只能执行一个

---

📈 参数使用频率统计

使用频率 参数 主要用户
高 --plan, --goal-joints 日常操作
中 --velocity, --zero 安全操作
低 --plan-only, --algorithm 调试/开发
管理 --stop, --status 系统维护

这样分类整理后，你可以清楚地看到所有参数的功能和使用场景。
# 1. 正常执行（会自动记录状态）
ros-start-execution --plan --goal-joints "0,0.5,0,-1,0,1,0"

# 2. 如果不满意，回退到执行前
ros-start-execution --rollback

# 3. 交互式回退（需要确认）
ros-start-execution --rollback --rollback-confirm

# 4. 查看回退信息
ros-start-execution --rollback-info

# 5. 清除所有回退记录
ros-start-execution --clear-rollback