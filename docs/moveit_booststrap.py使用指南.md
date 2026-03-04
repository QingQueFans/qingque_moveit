#!/usr/bin/env python3
"""其他脚本 - 只需要导入一次"""

# 一行搞定所有路径设置！
import sys
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap  # 🎯 这一行就完成了所有暴力导入

# 现在可以直接使用任何模块
from ps_objects.object_manager import create_box, remove_object
from grasping.ik_solver import solve_for_object

# 使用
result = create_box("test", 0.5, 0.3, 0.4)
ik_result = solve_for_object("test")


# moveit_tools.py
import moveit_bootstrap  # 先导入启动器

from ps_objects.object_manager import (
    create_box as _create_box,
    remove_object as _remove_object,
    list_objects as _list_objects
)

from grasping.ik_solver import (
    solve_for_object as _solve_for_object,
    solve_ik as _solve_ik
)

# 包装成更友好的接口
def add_box(object_id, x, y, z, **kwargs):
    """一行调用：添加盒子"""
    return _create_box(object_id, x, y, z, **kwargs)

def solve_object_ik(object_id, **kwargs):
    """一行调用：求解物体IK"""
    return _solve_for_object(object_id, **kwargs)

# 其他包装函数...