📋 ros-move-group-grasp 命令行速查表
1. grasp - 抓取物体
bash
# 抓取场景中已存在的物体
ros-move-group-grasp grasp --object qingque
ros-move-group-grasp grasp --object test_cube --strategy side_grasp
ros-move-group-grasp grasp --object box --width 45

# 抓取指定位姿
ros-move-group-grasp grasp --pose 0.5 0.0 0.3 0 0 0 1
ros-move-group-grasp grasp --pose 0.6 0.1 0.2 0 0 0 1 --strategy side_grasp --width 50
2. move - 移动机械臂
bash
# 移动到指定位姿
ros-move-group-grasp move --pose 0.5 0.0 0.3 0 0 0 1
ros-move-group-grasp move --pose 0.6 0.2 0.4 0 0 0 1 --timeout 10.0

# 移动到指定关节位置
ros-move-group-grasp move --joints 0 -0.5 0 -1.5 0 1.5 0

# 移动到物体位置
ros-move-group-grasp move --object qingque
ros-move-group-grasp move --object test_cube --no-cache
3. batch - 批量抓取
bash
# 批量抓取多个物体
ros-move-group-grasp batch --objects part1 part2 part3
ros-move-group-grasp batch --objects box1 box2 box3 --strategy side_grasp
4. status - 查看任务状态
bash
# 查看当前抓取任务状态
ros-move-group-grasp status
ros-move-group-grasp status --verbose
5. cache - 缓存管理
bash
# 查看缓存统计
ros-move-group-grasp cache --stats

# 清空缓存
ros-move-group-grasp cache --clear
6. release - 释放物体
bash
# 释放当前抓取的物体
ros-move-group-grasp release

# 释放指定物体，并设置释放后宽度
ros-move-group-grasp release --object qingque --width 100
7. JSON 输出模式
bash
# 所有命令都支持 --json 参数
ros-move-group-grasp grasp --object qingque --json
ros-move-group-grasp status --json
ros-move-group-grasp cache --stats --json
🚀 快速参考卡
命令	功能	示例
grasp	抓取物体	grasp --object qingque
move	移动机械臂	move --pose 0.5 0 0.3 ...
batch	批量抓取	batch --objects a b c
status	查看状态	status
cache	缓存管理	cache --stats
release	释放物体	release --object qingque
