IK求解器一行调用接口指南

一、概述

在 ik_solver.py 文件末尾添加的IK求解器简化接口，提供与轨迹执行器相同的一行调用体验。

二、安装位置

接口已添加到 ik_solver.py 文件末尾，无需额外安装。

三、使用方式

1. 一行调用（推荐）

```python
# 在任何文件中
from kin_ik.ik_solver import solve_ik

# 通过物体ID调用
result = solve_ik("box")
result = solve_ik("coke_can_01")

# 通过位姿调用
result = solve_ik([0.5, 0.0, 0.3, 0, 0, 0, 1])

# 通过字典调用
result = solve_ik({"pose": [0.6, 0.1, 0.2, 0, 0, 0, 1], "object_id": "test_cube"})
```

2. 快速求解函数

```python
from kin_ik.ik_solver import solve_for_object, solve_pose

# 快速求解物体
result = solve_for_object("box")
result = solve_for_object("coke_can_01", grasp_strategy="side", offset=0.03)

# 快速求解位姿
result = solve_pose(0.5, 0.0, 0.3)  # 使用默认姿态
result = solve_pose(0.6, 0.1, 0.2, 0, 0, 0, 1, object_id="test")  # 指定完整姿态
```

3. 批量求解

```python
from kin_ik.ik_solver import batch_solve_ik

# 批量求解多个物体
results = batch_solve_ik(["box", "coke_can_01", "test_cube"])

# 批量求解带不同参数
results = batch_solve_ik([
    {"object_id": "box", "grasp_strategy": "top"},
    {"object_id": "coke_can_01", "grasp_strategy": "side", "offset": 0.02}
])
```

4. 管理功能

```python
from kin_ik.ik_solver import get_ik_solver_stats, clear_ik_cache

# 获取统计信息
stats = get_ik_solver_stats()
print(f"缓存命中率: {stats.get('hit_rate', 0)*100:.1f}%")

# 清空缓存
clear_ik_cache()
```

5. 类方式调用

```python
from kin_ik.ik_solver import IKSolverFacade

# 使用外观类
result = IKSolverFacade.solve("box", grasp_strategy="top")
```

四、参数说明

主要参数

```python
solve_ik(target, **kwargs)
# target: 可以是字符串（物体ID）、列表（位姿）、字典
# kwargs可选参数:
#   - grasp_strategy: 抓取策略 ("top", "side", "front")，默认"top"
#   - seed: 初始关节种子
#   - use_cache: 是否使用缓存，默认True
#   - check_collision: 检查碰撞，默认False
#   - save_to_cache: 保存到缓存，默认True
#   - offset: 抓取偏移距离，默认0.05
```

返回值格式

```python
{
    "success": True/False,           # 是否成功
    "joint_positions": [0.1, 0.2,...], # 关节位置（成功时）
    "pose": [x,y,z,qx,qy,qz,qw],    # 目标位姿
    "object_id": "box",             # 物体ID（如果提供）
    "strategy": "top",              # 使用的抓取策略
    "timestamp": "2024-01-01 12:00:00", # 时间戳
    "cache_hit": True/False,        # 是否缓存命中
    "error": "错误信息"              # 错误信息（失败时）
}
```

五、高级用法

1. 禁用缓存

```python
result = solve_ik("box", use_cache=False, save_to_cache=False)
```

2. 自定义种子

```python
custom_seed = [0.0, -1.57, 0.0, -1.57, 0.0, 1.57, 0.0]
result = solve_ik("box", seed=custom_seed)
```

3. 碰撞检查

```python
result = solve_ik("box", check_collision=True)
```

4. 只求解不保存

```python
result = solve_ik([0.5, 0.0, 0.3, 0,0,0,1], save_to_cache=False)
```

六、测试代码

```python
# ========== IK求解器简化接口测试 ==========
if __name__ == "__main__":
    print("=== IK求解器简化接口测试 ===")
    
    # 测试1: 物体ID模式
    print("\n测试1: 物体ID模式")
    result1 = solve_ik("box")
    print(f"  成功: {result1['success']}")
    if result1['success']:
        print(f"  关节数: {len(result1.get('joint_positions', []))}")
        print(f"  缓存命中: {result1.get('cache_hit', False)}")
    
    # 测试2: 位姿模式
    print("\n测试2: 位姿模式")
    result2 = solve_ik([0.5, 0.0, 0.3, 0, 0, 0, 1])
    print(f"  成功: {result2['success']}")
    
    # 测试3: 快速函数
    print("\n测试3: 快速函数")
    result3 = solve_for_object("coke_can_01", grasp_strategy="side")
    print(f"  成功: {result3['success']}, 策略: {result3.get('strategy', 'N/A')}")
    
    # 测试4: 批量求解
    print("\n测试4: 批量求解")
    results = batch_solve_ik(["box", "test_cube"])
    print(f"  总数: {results['total']}, 成功: {results['successful']}")
    
    # 测试5: 获取统计信息
    print("\n测试5: 统计信息")
    stats = get_ik_solver_stats()
    print(f"  缓存信息: {stats}")
    
    print("\n=== 测试完成 ===")
```

七、优势特性

1. 简单易用：一行代码完成IK求解
2. 多种输入格式：支持物体ID、位姿列表、完整字典
3. 智能解析：自动判断输入类型并处理
4. 缓存优化：内置缓存机制提升性能
5. 错误处理：内置异常捕获和标准化错误输出
6. 向后兼容：不破坏现有代码结构
7. 统计功能：提供缓存命中率等性能指标

八、注意事项

1. 首次调用会有初始化延迟
2. 缓存默认开启，适合重复求解相同目标
3. 返回结果已标准化，包含success字段
4. 所有时间相关值使用国际单位制（米、弧度）
5. 建议为每个物体ID指定合适的抓取策略