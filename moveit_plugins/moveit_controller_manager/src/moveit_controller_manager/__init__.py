#!/usr/bin/env python3
"""
MoveIt控制器管理器包
"""

from .controller_manager import MoveItControllerManager

__all__ = ['MoveItControllerManager', 'execute_trajectory_sync']