#!/usr/bin/env python3
"""
碰撞物体管理模块
提供专业的碰撞物体创建、管理和验证功能
"""

from .object_manager import ObjectManager
from .shape_generator import ShapeGenerator
from .object_validator import ObjectValidator

__all__ = [
    'ObjectManager',
    'ShapeGenerator', 
    'ObjectValidator'
]

__version__ = '0.1.0'