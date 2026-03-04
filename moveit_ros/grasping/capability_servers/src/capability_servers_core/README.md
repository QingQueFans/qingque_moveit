抓取服务器使用指南

📋 核心功能概述

抓取服务器提供物体抓取与释放的一站式解决方案，支持手动指定宽度和智能自动计算。

---

🚀 快速开始

1. 基本导入

```python
from grasping.pick_action_server import (
    quick_grab,      # 快速抓取（毫米单位）
    smart_grab,      # 智能抓取（自动计算）
    release_object,  # 释放物体
    get_grasp_status # 获取状态
)
```

2. 一行抓取

```python
# 最简方式 - 智能抓取
result = smart_grab("qingque")

# 指定宽度 - 快速抓取
result = quick_grab("qingque", 50)  # 50mm宽度
```

3. 查看状态

```python
status = get_grasp_status()
print(f"夹爪就绪: {status['gripper_ready']}")
print(f"连接物体: {status['attached_object']}")
```

---

🎯 三种抓取模式

模式A：智能抓取（推荐）

```python
# 自动根据物体信息计算最佳宽度
result = smart_grab("qingque")                     # 自动策略
result = smart_grab("test_cube", "side_grasp")     # 侧向抓取
result = smart_grab("cylinder", "top_grasp")       # 顶部抓取
```

特点：

· ✅ 自动计算最佳夹爪宽度
· ✅ 支持多种抓取策略
· ✅ 考虑物体类型和尺寸
· ✅ 应用物理安全限制

模式B：快速抓取（毫米单位）

```python
# 使用毫米单位，更直观
result = quick_grab("qingque", 50)     # 50mm宽度
result = quick_grab("test_cube")       # 默认60mm
result = quick_grab("small_box", 40)   # 40mm宽度
```

特点：

· ✅ 毫米单位，直观易懂
· ✅ 简单快速，无需计算
· ✅ 适合已知物体尺寸的场景

模式C：完整控制（米制单位）

```python
# 使用米制单位，更精确
result = grab_object("qingque", width=0.05)    # 0.05m = 50mm
result = grab_object("test_cube", effort=25.0) # 指定夹紧力
```

特点：

· ✅ 米制单位，精确控制
· ✅ 可指定夹紧力
· ✅ 完整参数控制

---

🔄 释放物体

释放方式

```python
# 释放指定物体
result = release_object("qingque")

# 释放当前连接物体
result = release_object()

# 释放后张开到指定宽度
result = release_object("qingque", width_mm=100)  # 100mm
```

释放参数

参数 说明 默认值
object_id 物体ID 当前连接物体
width_mm 释放后夹爪宽度 80mm

---

📊 状态查询

获取完整状态

```python
status = get_grasp_status()

# 关键信息
print(f"服务器: {status['server']}")                # pick_action_server
print(f"活动状态: {status['active']}")              # True/False
print(f"夹爪就绪: {status['gripper_ready']}")       # True/False
print(f"连接物体: {status['attached_object']}")     # 物体ID或None
print(f"时间戳: {status['timestamp']}")             # 2026-02-08 18:19:25
```

---

🛠️ 高级用法

1. 使用完整类接口

```python
from grasping.pick_action_server import GraspAction

# 完整控制
result = GraspAction.grab("qingque", auto_calculate=True)
result = GraspAction.release("qingque", width_after=0.08)
status = GraspAction.status()
```

2. 错误处理

```python
result = smart_grab("nonexistent_object")

if result["success"]:
    # 成功处理
    width_mm = result["grasp_width"] * 1000
    print(f"抓取成功！宽度: {width_mm:.1f}mm")
    print(f"来源: {result.get('width_source', 'unknown')}")
else:
    # 错误处理
    print(f"失败: {result['error']}")
    print(f"操作: {result['operation']}")
    print(f"时间: {result['timestamp']}")
```

3. 结果字典结构

```python
{
    "success": True,                     # 是否成功
    "operation": "grab",                 # 操作类型
    "object_id": "qingque",              # 物体ID
    "grasp_width": 0.05,                 # 夹爪宽度（米）
    "grasp_effort": 30.0,                # 夹紧力（N）
    "execution_time": 0.5,               # 执行时间（秒）
    "timestamp": "2026-02-08 18:19:25",  # 时间戳
    "message": "成功抓取物体 qingque",    # 描述信息
    "width_source": "calculated"         # 宽度来源（calculated/specified）
}
```

---

⚙️ 命令行工具

安装使用

```bash
# 智能抓取
python3 ps-grab.py grab qingque --auto

# 手动抓取
python3 ps-grab.py grab qingque --width 50

# 释放物体
python3 ps-grab.py release qingque

# 查看状态
python3 ps-grab.py status

# 详细输出
python3 ps-grab.py grab qingque --auto --verbose
```

命令行参数

命令 参数 说明
grab object_id 物体ID
 --width N 夹爪宽度（mm）
 --auto 自动计算宽度
 --strategy 抓取策略
release object_id 物体ID（可选）
 --width N 释放后宽度（mm）
status --verbose 详细输出

---

🎪 使用前提与流程

必要条件

```python
# 必须确保：
# 1. ✅ 物体已在规划场景中添加
# 2. ✅ 夹爪控制器已就绪
# 3. ✅ 机械臂已移动到合适位置
```

典型工作流程

```python
# 完整抓取-放置流程
# 1. 移动机械臂到抓取位置
trajectory_executor.move_to_grasp_pose("qingque")

# 2. 智能抓取
grab_result = smart_grab("qingque")

# 3. 移动机械臂到放置位置
trajectory_executor.move_to_place_position()

# 4. 释放物体
release_result = release_object("qingque", width_mm=100)

# 5. 检查结果
if grab_result["success"] and release_result["success"]:
    print("✅ 抓取-放置任务完成！")
```

---

📈 智能计算原理

计算过程

```
输入物体信息 → 计算最佳宽度 → 应用安全限制 → 执行抓取
     ↓              ↓              ↓            ↓
物体ID/尺寸      GripperCalculator 物理限制     硬件控制
```

支持的物体类型

· 📦 盒子（Box）
· 🫙 圆柱体（Cylinder）
· ⚽ 球体（Sphere）

抓取策略

· 🤲 侧向抓取（side_grasp）
· 👆 顶部抓取（top_grasp）
· 🫴 包裹式抓取（encompassing_grasp）
· 🤏 捏取（pinch_grasp）

---

🚨 常见问题

Q1: 为什么抓取失败？

· ❌ 物体不在规划场景中
· ❌ 夹爪控制器未就绪
· ❌ 机械臂未在合适位置
· ❌ 夹爪宽度超出限制

Q2: 如何调试？

```python
# 1. 检查状态
status = get_grasp_status()
print(f"状态: {status}")

# 2. 测试简单抓取
result = quick_grab("test_cube", 60)
print(f"测试结果: {result}")

# 3. 检查错误信息
if not result["success"]:
    print(f"错误详情: {result['error']}")
```

Q3: 智能计算不准确？

· 检查物体信息是否正确
· 尝试不同的抓取策略
· 手动指定宽度作为备选

---

📝 最佳实践

1. 生产环境

```python
# 使用智能抓取 + 错误处理
try:
    result = smart_grab(object_id, strategy="side_grasp")
    if result["success"]:
        log_success(result)
    else:
        fallback_to_manual(object_id)
except Exception as e:
    handle_exception(e)
```

2. 测试环境

```python
# 测试不同参数
test_cases = [
    ("cube_1", 50, "side_grasp"),
    ("cylinder_1", None, "auto"),  # 智能计算
    ("small_box", 40, "top_grasp")
]

for obj_id, width, strategy in test_cases:
    test_grasp(obj_id, width, strategy)
```

3. 监控与日志

```python
# 记录抓取操作
def log_grasp_operation(result):
    log_data = {
        "timestamp": result["timestamp"],
        "object_id": result["object_id"],
        "width_mm": result["grasp_width"] * 1000,
        "success": result["success"],
        "execution_time": result["execution_time"],
        "width_source": result.get("width_source", "unknown")
    }
    save_to_database(log_data)
```

---

🔗 相关模块

依赖模块

· PlanningSceneClient - 规划场景管理
· GripperCalculator - 夹爪参数计算
· TrajectoryExecutor - 轨迹执行

配合使用

```python
# 完整机器人操作链
场景管理 → 轨迹规划 → 抓取执行 → 状态监控
   ↓          ↓          ↓          ↓
Planning   Trajectory   Grasping   Monitoring
```

---

🆘 故障排除

症状 可能原因 解决方案
夹爪不动 控制器未初始化 检查 gripper_ready 状态
物体不连接 场景客户端错误 检查 attach_object 方法
宽度计算错误 物体信息缺失 检查物体是否在场景中
释放失败 没有连接物体 检查 attached_object

---

🎯 提示： 智能抓取是推荐的使用方式，它自动处理了复杂的参数计算，让抓取操作更简单可靠！