轨迹执行系统用户接口使用指南

📁 文件结构概览

```
moveit_ros/move_group/trajectory_execution/
├── src/
│   ├── trajectory_execution/
│   │   ├── trajectory_execution_manager.py    # 核心执行管理器
│   │   ├── trajectory_executor.py            # 一行调用接口（你刚完成的）
│   │   └── __init__.py
│   └── __init__.py
├── scripts/
│   └── ros-start-execution                  # 可执行脚本
└── test/                                    # 测试目录
```

🚀 快速开始

方式一：一行调用（推荐）

```python
# 最简单的使用方式
from moveit_ros.move_group.trajectory_execution.src import execute_trajectory

# 示例1：通过物体ID执行
result = execute_trajectory("coke_can_01", use_cache=True)

# 示例2：通过位姿执行
result = execute_trajectory([0.6, 0.1, 0.2, 0, 0, 0, 1])

# 示例3：通过关节角度执行
result = execute_trajectory({"joints": [0, -0.5, 0, -1.5, 0, 1.5, 0]})
```

方式二：使用便捷函数

```python
from moveit_ros.move_group.trajectory_execution.src.trajectory_execution import (
    move_to_pose,
    move_to_joints,
    get_execution_stats
)

# 快速移动到指定位置
result = move_to_pose(0.6, 0.1, 0.2, use_cache=True)

# 快速移动到关节位置
result = move_to_joints([0, -0.5, 0, -1.5, 0, 1.5, 0])

# 获取执行统计
stats = get_execution_stats()
```

方式三：使用类接口（更灵活）

```python
from moveit_ros.move_group.trajectory_execution.src.trajectory_execution import TrajectoryExecutor

# 使用单例模式
result1 = TrajectoryExecutor.execute("coke_can_01", timeout=10.0)
result2 = TrajectoryExecutor.execute([0.5, 0.0, 0.3, 0, 0, 0, 1])
```

⚙️ 核心功能说明

1. 智能缓存系统

· 自动缓存IK求解结果
· 通过物体ID快速查找
· 减少重复规划时间

2. 多种输入格式支持

```python
# 所有支持的输入格式：
# 1. 字符串（物体ID）
execute_trajectory("coke_can_01")

# 2. 列表（位姿：x,y,z,qx,qy,qz,qw）
execute_trajectory([0.6, 0.1, 0.2, 0, 0, 0, 1])

# 3. 字典（位姿）
execute_trajectory({"pose": [0.6, 0.1, 0.2, 0, 0, 0, 1]})

# 4. 字典（关节）
execute_trajectory({"joints": [0, -0.5, 0, -1.5, 0, 1.5, 0]})

# 5. 字典（物体ID）
execute_trajectory({"object_id": "coke_can_01"})
```

3. 高级参数配置

```python
result = execute_trajectory(
    "coke_can_01",
    use_cache=True,           # 是否使用缓存（默认True）
    timeout=5.0,             # 规划超时时间（秒）
    strategy="rrt_connect",  # 规划算法：rrt_connect/rrt_star/prm
    wait=True,               # 是否等待执行完成
    start={"joints": [...]}  # 指定起始状态（可选）
)
```

📊 返回结果格式

所有方法都返回统一格式的字典：

```python
{
    "success": True/False,
    "execution_time": 2.056,      # 执行时间（秒）
    "timestamp": "2026-02-01 13:58:36",
    "object_id": "coke_can_01",   # 如果有物体ID
    "target_pose": [0.6, 0.1, 0.2],  # 目标位置
    "cache_stats": {              # 缓存统计（如果启用缓存）
        "cache_enabled": True,
        "stats": {"hits": 1, "misses": 0, "saves": 1},
        "hit_rate_percent": 100.0
    },
    "error": "错误信息"           # 如果success=False
}
```

🔧 系统管理功能

```python
from moveit_ros.move_group.trajectory_execution.src.trajectory_execution import (
    get_execution_stats,
    clear_trajectory_cache
)

# 查看缓存统计
stats = get_execution_stats()
print(f"缓存命中率: {stats.get('hit_rate_percent', 0):.1f}%")

# 清空缓存
clear_trajectory_cache()
```
💡 最佳实践建议

1. 生产环境使用

```python
# 建议设置合理的超时时间和算法
result = execute_trajectory(
    "target_object",
    use_cache=True,
    timeout=10.0,
    strategy="rrt_connect"
)

if result["success"]:
    print(f"执行成功，耗时: {result['execution_time']}秒")
    if result.get("cache_info", {}).get("hit"):
        print("✅ 缓存命中，加速执行")
else:
    print(f"执行失败: {result['error']}")
```

2. 预加载常用物体

```python
# 程序启动时预加载常用物体的缓存
preload_objects = ["coke_can_01", "blue_box", "red_cube"]
for obj_id in preload_objects:
    execute_trajectory(obj_id, use_cache=True)
```

3. 错误处理

```python
try:
    result = execute_trajectory("unknown_object", use_cache=True)
    if not result["success"]:
        # 缓存未命中，尝试其他方法
        result = execute_trajectory([0.5, 0.0, 0.3, 0, 0, 0, 1])
except Exception as e:
    print(f"系统异常: {e}")
```

🎯 使用场景示例

场景1：简单抓取任务

```python
def pick_and_place(object_id, target_position):
    # 1. 移动到物体位置（使用缓存）
    pick_result = execute_trajectory(object_id, use_cache=True)
    
    if pick_result["success"]:
        # 2. 执行抓取动作
        grasp()
        
        # 3. 移动到目标位置
        place_result = execute_trajectory(target_position)
        
        # 4. 执行放置动作
        release()
```

场景2：批量处理

```python
def process_objects(object_list):
    for obj in object_list:
        print(f"处理物体: {obj['id']}")
        
        result = execute_trajectory(
            obj["id"],
            use_cache=True,
            timeout=obj.get("timeout", 5.0)
        )
        
        if result["success"]:
            log_success(obj, result)
        else:
            log_error(obj, result)
```

⚠️ 注意事项

1. 首次使用：新物体的第一次执行会较慢（需要规划并缓存）
2. 缓存目录：缓存文件保存在 ~/.planning_scene_cache/ 和 moveit_core/cache_manager/data/
3. 线程安全：系统使用单例模式，多线程调用时注意资源竞争
4. 资源清理：长时间运行后可使用 clear_trajectory_cache() 清理缓存

这个指南涵盖了所有使用场景，你可以直接分享给其他开发者使用你的轨迹执行系统。

 cd ~/qingfu_moveit/moveit_core/kinematics/inverse_kinematics/scripts/