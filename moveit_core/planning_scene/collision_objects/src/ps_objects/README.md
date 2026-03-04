您说得对！我之前写的那个指南确实需要重写。让我基于实际验证过的使用方式重新写一个简洁实用的指南。

📚 物体管理器一行调用接口使用指南

一、快速开始

```python
# 在任何文件中，设置路径后导入：
import sys
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/collision_objects/src')

from ps_objects.object_manager import (
    create_box,           # 创建盒子
    add_object,           # 通用添加物体
    remove_object,        # 移除物体
    list_objects,         # 列出物体
    clear_all_objects,    # 清空所有物体
    get_object_info,      # 获取物体信息
    show_cache_info       # 显示缓存信息
)

# 一行调用！
result = create_box("my_box", 0.5, 0.3, 0.4)
```

二、核心函数

1. 创建盒子

```python
result = create_box(
    object_id="box_01",    # 物体ID
    x=0.5, y=0.3, z=0.4,   # 位置
    width=0.1,             # 宽度 (默认0.1)
    height=0.1,            # 高度 (默认0.1) 
    depth=0.1              # 深度 (默认0.1)
)
```

2. 通用添加物体

```python
# 方式1：字典格式
result = add_object({
    "id": "custom_box",
    "position": [0.5, 0.3, 0.4],
    "dimensions": [0.1, 0.1, 0.1],
    "orientation": [0.0, 0.0, 0.0, 1.0]  # 四元数 [x,y,z,w]
})

# 方式2：位置列表
result = add_object([0.5, 0.3, 0.4], 
                   object_id="simple_box",
                   dimensions=[0.1, 0.1, 0.1])
```

3. 管理物体

```python
# 移除物体
result = remove_object("box_01")

# 列出所有物体
objects_info = list_objects()
print(f"场景物体: {objects_info['scene_objects']}")
print(f"缓存物体: {objects_info['cached_objects']}")

# 清空所有
result = clear_all_objects()

# 获取物体信息
info = get_object_info("box_01")
```

三、完整示例

```python
#!/usr/bin/env python3
"""完整使用示例"""

import sys
import os

# 1. 设置路径
MOVEIT_CORE_ROOT = "/home/diyuanqiongyu/qingfu_moveit/moveit_core"
sys.path.insert(0, os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src'))
sys.path.insert(0, os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src'))
sys.path.insert(0, os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'collision_objects', 'src'))

# 2. 导入
from ps_objects.object_manager import (
    create_box, remove_object, list_objects, clear_all_objects
)

def demo_scene_management():
    """演示场景管理"""
    
    # 清理场景
    print("1. 清理场景...")
    clear_all_objects()
    
    # 创建几个物体
    print("\n2. 创建物体...")
    boxes = [
        ("red_box", 0.5, 0.0, 0.3),
        ("blue_box", 0.6, 0.1, 0.3),
        ("green_box", 0.4, -0.1, 0.3)
    ]
    
    for name, x, y, z in boxes:
        result = create_box(name, x, y, z)
        print(f"   {name}: {'✅' if result['success'] else '❌'}")
    
    # 列出
    print("\n3. 列出物体...")
    info = list_objects()
    print(f"   当前物体: {info['scene_objects']}")
    
    # 清理
    print("\n4. 清理...")
    for name, _, _, _ in boxes:
        remove_object(name)
    
    print("\n✅ 演示完成")

if __name__ == "__main__":
    demo_scene_management()
```

四、与IK求解器结合使用

```python
"""结合IK求解器的完整抓取流程"""

from grasping.ik_solver import solve_for_object
from ps_objects.object_manager import create_box, remove_object

def complete_grasp_task(object_id, x, y, z):
    """完整抓取任务"""
    
    # 1. 添加物体到场景
    print(f"1. 添加物体 {object_id}...")
    add_result = create_box(object_id, x, y, z)
    if not add_result['success']:
        print(f"❌ 添加物体失败")
        return False
    
    # 2. 求解IK
    print(f"2. 求解IK...")
    ik_result = solve_for_object(object_id, grasp_strategy="top")
    if not ik_result['success']:
        print(f"❌ IK求解失败")
        remove_object(object_id)  # 清理
        return False
    
    # 3. 执行抓取（这里只是示例）
    print(f"3. 抓取物体...")
    print(f"   关节解: {ik_result['joint_positions']}")    # 4. 清理
    print(f"4. 清理...")
    remove_object(object_id)
    
    return True

# 使用
complete_grasp_task("target_box", 0.5, 0.0, 0.3)
```

五、路径设置模板

```python
# path_setup.py - 路径设置模板
import sys
import os

def setup_object_manager_paths():
    """设置物体管理器的导入路径"""
    
    # 方法1：使用绝对路径（推荐）
    MOVEIT_CORE_ROOT = "/home/diyuanqiongyu/qingfu_moveit/moveit_core"
    
    # 方法2：动态计算（如果从不同位置调用）
    # current_file = os.path.abspath(__file__)
    # 根据实际情况计算 MOVEIT_CORE_ROOT
    
    paths = [
        os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src'),
        os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src'),
        os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'collision_objects', 'src'),
    ]
    
    for path in paths:
        if os.path.exists(path):
            sys.path.insert(0, path)
    
    return paths

# 使用
paths = setup_object_manager_paths()
print(f"已添加路径: {paths}")
```

六、注意事项

1. 首次调用有初始化延迟：第一次调用会初始化ROS2客户端
2. 缓存自动管理：物体会自动保存到统一缓存系统
3. 错误处理：所有函数返回标准格式的结果字典
4. 线程安全：建议不要在多个线程中同时调用

七、返回结果格式

```python
{
    "success": True/False,      # 是否成功
    "object_id": "box_01",      # 物体ID
    "timestamp": "2026-02-03 01:09:07",  # 时间戳
    "error": "错误信息",         # 失败时的错误信息
    # 其他函数可能有额外字段...
}
```

八、调试技巧

```python
# 显示缓存信息
show_cache_info()

# 检查导入
import ps_objects.object_manager as om
print(f"可用函数: {[x for x in dir(om) if not x.startswith('_')]}")
```

这个指南基于实际验证过的代码，可以直接使用。比之前的理论指南更实用！