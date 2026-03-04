#!/usr/bin/env python3
"""
constraints.py - 约束处理核心类
"""
from typing import Dict, List, Any, Optional
import time
import os
import json
import sys

# ========== 设置路径 ==========
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(MODULE_ROOT))

PLANNING_SCENE_SRC = os.path.join(PROJECT_ROOT, 'planning_scene', 'core_functions', 'src')
sys.path.insert(0, PLANNING_SCENE_SRC)

try:
    from ps_core.scene_client import PlanningSceneClient
    HAS_SCENE_CLIENT = True
except ImportError as e:
    print(f"[Constraints警告] 导入PlanningSceneClient失败: {e}")
    HAS_SCENE_CLIENT = False


class ConstraintsHandler:
    """约束处理器"""
    
    def __init__(self, scene_client=None):
        """
        初始化约束处理器
        
        Args:
            scene_client: PlanningSceneClient实例
        """
        if scene_client is None and HAS_SCENE_CLIENT:
            self.client = PlanningSceneClient()
        else:
            self.client = scene_client
        
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        
        # 约束类型
        self.constraint_types = {
            "position": "位置约束",
            "orientation": "方向约束",
            "joint": "关节约束",
            "visibility": "可见性约束",
            "collision": "碰撞约束"
        }
        
        # 当前活动的约束
        self.active_constraints = {}
        
        print("[ConstraintsHandler] 初始化完成")
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[Constraints缓存] 缓存文件不存在: {self.cache_file}")
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[Constraints缓存] 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[Constraints缓存] 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if isinstance(value, (int, float)):
            return float(value)
        return value
    
    def create_position_constraint(self, name: str, position: List[float], 
                                  tolerance: List[float] = None, weight: float = 1.0) -> Dict:
        """创建位置约束"""
        start_time = time.time()
        
        try:
            if tolerance is None:
                tolerance = [0.01, 0.01, 0.01]
            
            constraint = {
                "type": "position",
                "name": name,
                "position": self._ensure_float(position),
                "tolerance": self._ensure_float(tolerance),
                "weight": self._ensure_float(weight),
                "created_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.active_constraints[name] = constraint
            
            return {
                "success": True,
                "result": f"位置约束 '{name}' 创建成功",
                "constraint": constraint,
                "active_constraints": len(self.active_constraints),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }