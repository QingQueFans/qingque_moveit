#!/usr/bin/env python3
"""
碰撞检测模块
提供专业的碰撞检测、距离计算和接触分析功能
"""

from .collision_checker import CollisionChecker
from .distance_calculator import DistanceCalculator
from .contact_analyzer import ContactAnalyzer

__all__ = [
    'CollisionChecker',
    'DistanceCalculator',
    'ContactAnalyzer'
]

__version__ = '0.1.0'