#!/usr/bin/env python3
"""
物体检测包
"""

from .object_detector import PureObjectDetector
# 如果你还有其他模块，比如：
# from .shape_detector import ShapeDetector

__all__ = [
    'PureObjectDetector',
    # 'ShapeDetector',
]