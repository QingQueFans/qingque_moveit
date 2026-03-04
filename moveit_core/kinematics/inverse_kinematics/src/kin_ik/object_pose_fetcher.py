#!/usr/bin/env python3
"""
物体位姿获取器 - 从物体缓存系统获取物体信息
基于ObjectCache实现，专为IK求解服务
"""
import sys
import os
import argparse
import json
import time
import math
import numpy as np
from typing import List, Optional,Dict,Union,Tuple,Any
from pathlib import Path
# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)

# 1. 先设置 IK 模块路径（肯定正确）
IK_SRC = os.path.join(MODULE_ROOT, 'src')
sys.path.insert(0, IK_SRC)

# 2. 查找 moveit_core 根目录
# scripts -> inverse_kinematics -> kinematics -> moveit_core
MOVEIT_CORE_ROOT = os.path.join(SCRIPT_DIR, '..', '..', '..')
MOVEIT_CORE_ROOT = os.path.abspath(MOVEIT_CORE_ROOT)

# 3. 规划场景路径（保持原逻辑）
PLANNING_SCENE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
sys.path.insert(0, PLANNING_SCENE_SRC)

# 4. 缓存管理器路径
CACHE_MANAGER_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')
sys.path.insert(0, CACHE_MANAGER_SRC)

print(f"MOVEIT_CORE_ROOT: {MOVEIT_CORE_ROOT}")

try:
    # 先导入规划场景（正确的）
    from ps_core.scene_client import PlanningSceneClient
    
    
    # 尝试导入缓存管理器
    try:
        from ps_cache import CachePathTools
        
    except ImportError as e:
        HAS_CACHE = False
        print(f"[警告] 缓存管理器导入失败: {e}")
    
    HAS_DEPENDENCIES = True
    print("✓ 成功导入所有依赖")
    
except ImportError as e:
    print(f"[警告] 导入依赖失败: {e}")
    import traceback
    traceback.print_exc()
    HAS_DEPENDENCIES = False
    HAS_CACHE = False

class ObjectPoseFetcher:
    """物体位姿获取器 - 使用ObjectCache"""
    
    def __init__(self, cache_root=None):
        """初始化获取器"""
        self._setup_fallback()
        try:
            from ps_cache.object_cache import ObjectCache
            self.object_cache = ObjectCache()
            print("[ObjectPoseFetcher] 使用ObjectCache初始化完成")
        except ImportError as e:
            print(f"[ObjectPoseFetcher] 无法导入ObjectCache: {e}")
            self.object_cache = None
            
    
    def _setup_fallback(self):
        """备用方案：直接文件系统访问"""
        self.cache_dir = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects")
        print(f"[ObjectPoseFetcher] 使用备用文件系统访问: {self.cache_dir}")
    
    def get_object_info(self, object_id: str) -> Optional[Dict]:
        """获取完整物体信息"""
        print(f"[ObjectPoseFetcher] 获取物体: {object_id}")
        
       
        
        # 总是使用文件系统作为后备
        print(f"[ObjectPoseFetcher] 使用文件系统搜索...")
        result = self._load_object_from_files(object_id)
        
        if result:
            print(f"[ObjectPoseFetcher] ✅ 文件系统找到物体")
        else:
            print(f"[ObjectPoseFetcher] ❌ 文件系统也未找到")
        
        return result
    
    def _load_object_from_files(self, object_id: str) -> Optional[Dict]:
        """直接从缓存文件加载物体信息"""
        if not self.cache_dir.exists():
            print(f"[ObjectPoseFetcher] 缓存目录不存在: {self.cache_dir}")
            return None
        
        print(f"[ObjectPoseFetcher] 在目录中搜索物体 '{object_id}': {self.cache_dir}")
        
        # 搜索所有JSON文件，不仅仅是 object_*.json
        for cache_file in self.cache_dir.glob("*.json"):
            print(f"  检查文件: {cache_file.name}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查多层结构中的object_id
                file_object_id = data.get('data', {}).get('object_id')
                inner_object_id = data.get('data', {}).get('data', {}).get('id')
                
                print(f"    找到ID: file={file_object_id}, inner={inner_object_id}")
                
                if file_object_id == object_id or inner_object_id == object_id:
                    print(f"[ObjectPoseFetcher] ✅ 找到物体: {cache_file.name}")
                    return data
                    
            except Exception as e:
                print(f"[ObjectPoseFetcher] 读取错误 {cache_file}: {e}")
                continue
        
        print(f"[ObjectPoseFetcher] ❌ 未找到物体: {object_id}")
        return None
    
    def get_object_pose(self, object_id: str, format="dict") -> Optional[Any]:
        """
        获取物体位姿
        
        Args:
            object_id: 物体ID
            format: 返回格式 ("dict", "list", "both")
        
        Returns:
            位姿数据
        """
        object_info = self.get_object_info(object_id)
        if not object_info:
            print(f"[ObjectPoseFetcher] 无法获取物体 {object_id} 的信息")
            return None
        
        try:
            # 从你提供的缓存结构中提取
            # 结构: data -> data -> position/orientation
            position = object_info['data']['data']['position']  # [x, y, z]
            orientation = object_info['data']['data']['orientation']  # [qx, qy, qz, qw]
            
            print(f"[ObjectPoseFetcher] 提取位姿: {position} + {orientation}")            # 返回指定格式
            if format == "list":
                return position + orientation  # [x, y, z, qx, qy, qz, qw]
            elif format == "dict":
                return {
                    "position": position,
                    "orientation": orientation,
                    "full": position + orientation
                }
            elif format == "both":
                return {
                    "list": position + orientation,
                    "dict": {
                        "position": position,
                        "orientation": orientation
                    }
                }
            else:
                return position + orientation
                
        except KeyError as e:
            print(f"[ObjectPoseFetcher] 数据格式错误，缺少键: {e}")
            print(f"  可用键: {list(object_info.keys())}")
            if 'data' in object_info:
                print(f"  data键: {list(object_info['data'].keys())}")
            return None
    
    def get_object_dimensions(self, object_id: str) -> Optional[List[float]]:
        """获取物体尺寸"""
        object_info = self.get_object_info(object_id)
        if not object_info:
            return None
        
        try:
            dimensions = object_info['data']['data']['dimensions']  # [长, 宽, 高]
            print(f"[ObjectPoseFetcher] 物体尺寸: {dimensions}")
            return dimensions
        except KeyError:
            print(f"[ObjectPoseFetcher] 物体没有尺寸信息")
            return [0.1, 0.1, 0.1]  # 默认尺寸
    
    def get_object_type(self, object_id: str) -> str:
        """获取物体类型"""
        object_info = self.get_object_info(object_id)
        if not object_info:
            return "unknown"
        
        try:
            obj_type = object_info['data']['data']['type']
            return obj_type
        except KeyError:
            return "unknown"
    
    def get_all_cached_objects(self) -> List[Dict]:
        """获取所有缓存的物体"""
        if self.object_cache:
            return self.object_cache.load_all_cached_objects()
        else:
            # 备用实现
            objects = []
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("object_*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        objects.append(data)
                    except:
                        continue
            return objects


# ========== 便捷函数 ==========

def fetch_object_pose(object_id: str, format="dict"):
    """便捷函数：获取物体位姿"""
    fetcher = ObjectPoseFetcher()
    return fetcher.get_object_pose(object_id, format)


def get_pose_string_for_ik(object_id: str) -> str:
    """获取可以直接用于kin-ik命令的位姿字符串"""
    fetcher = ObjectPoseFetcher()
    pose = fetcher.get_object_pose(object_id, format="list")
    
    if pose and len(pose) == 7:
        return " ".join([f"{x:.6f}" for x in pose])
    else:
        return "0 0 0 0 0 0 1"  # 默认位姿