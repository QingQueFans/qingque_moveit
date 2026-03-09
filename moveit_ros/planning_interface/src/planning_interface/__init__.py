"""planning_interface 主包"""
from .core.task import Task
from .stages import Stage, MoveTo, AttachObject, ModifyScene
from .containers import SerialContainer
from .knowledge import ObjectCache

# ===== 导入快捷函数 =====
from .core.task import (
    grasp_object,
    move_to_pose,
    move_to_joints,
    add_box,
    add_sphere,
    add_cylinder,
    remove_object,
    move_object,
    get_object_pose,
    get_object_dimensions
)

__all__ = [
    'Task',
    'Stage',
    'MoveTo',
    'AttachObject',
    'ModifyScene',
    'SerialContainer',
    'ObjectCache',
    # 添加快捷函数
    'grasp_object',
    'move_to_pose',
    'move_to_joints',
    'add_box',
    'add_sphere',
    'add_cylinder',
    'remove_object',
    'move_object',
    'get_object_pose',
    'get_object_dimensions'
]