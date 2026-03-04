# 抓取缓存接口 - GraspCache
# moveit_core/cache_manager/src/ps_cache/grasp_cache.py
#!/usr/bin/env python3
"""
抓取专用缓存管理器
"""
from typing import Dict, List, Optional, Union
from pathlib import Path
import json
import hashlib
import time

# 导入通用缓存管理器
from .cache_manager import CachePathTools  # ⭐️ 使用正确的类名

class GraspCache:
    """抓取专用缓存管理器"""
    
    def __init__(self):
        """初始化抓取缓存"""
        CachePathTools.initialize()
        print("[GraspCache] 抓取缓存管理器初始化完成")
    
    # ========== 抓取位姿缓存 ==========
    
    def get_grasp_pose_path(self,
                           object_id: str,
                           grasp_type: str = "top",
                           custom_name: Optional[str] = None) -> Path:
        """
        获取抓取位姿缓存路径
        
        Args:
            object_id: 物体ID
            grasp_type: 抓取类型 (top, side, pinch等)
            custom_name: 自定义文件名
        
        Returns:
            抓取位姿缓存文件路径
        """
        # 计算哈希
        data_hash = CachePathTools.compute_data_hash({
            'object': object_id,
            'type': grasp_type
        })[:12]
        
        if custom_name:
            filename = f"{custom_name}_{data_hash}.json"
        else:
            filename = f"grasp_{grasp_type}_{data_hash}.json"
        
        return CachePathTools.get_cache_file('grasping', 'grasp_poses', filename)
    
    def save_grasp_poses(self,
                        object_id: str,
                        grasp_poses: List[Dict],
                        grasp_type: str = "top",
                        metadata: Optional[Dict] = None) -> str:
        """
        保存抓取位姿到缓存
        
        Returns:
            缓存文件路径
        """
        filepath = self.get_grasp_pose_path(object_id, grasp_type)
        
        grasp_data = {
            'object_id': object_id,
            'grasp_type': grasp_type,
            'grasp_poses': grasp_poses,
            'pose_count': len(grasp_poses),
            'metadata': metadata or {}
        }
        
        if CachePathTools.save_to_cache(filepath, grasp_data):
            print(f"[GraspCache] 抓取位姿已保存: {filepath}")
            return str(filepath)
        return ""
    
    def load_grasp_poses(self,
                        object_id: str,
                        grasp_type: str = "top") -> Optional[Dict]:
        """加载抓取位姿缓存"""
        filepath = self.get_grasp_pose_path(object_id, grasp_type)
        return CachePathTools.load_from_cache(filepath)
    
    # ========== 抓取质量评分缓存 ==========
    
    def save_grasp_quality(self,
                          grasp_id: str,
                          quality_scores: Dict,
                          evaluation_method: str = "force_closure",
                          metadata: Optional[Dict] = None) -> str:
        """保存抓取质量评分"""
        # 计算哈希
        data_hash = CachePathTools.compute_data_hash({
            'grasp_id': grasp_id,
            'method': evaluation_method
        })[:12]
        
        filename = f"quality_{data_hash}.json"
        filepath = CachePathTools.get_cache_file('grasping', 'quality_scores', filename)
        
        quality_data = {
            'grasp_id': grasp_id,
            'evaluation_method': evaluation_method,
            'quality_scores': quality_scores,
            'metadata': metadata or {}
        }
        
        if CachePathTools.save_to_cache(filepath, quality_data):
            return str(filepath)
        return ""    # ========== 执行日志缓存 ==========
    
    def save_execution_log(self,
                          execution_id: str,
                          log_data: Dict,
                          log_type: str = "grasp_execution") -> str:
        """保存执行日志"""
        timestamp = int(time.time())
        filename = f"{log_type}_{execution_id}_{timestamp}.log"
        filepath = CachePathTools.get_cache_file('grasping', 'execution_logs', filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
            print(f"[GraspCache] 执行日志已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"[GraspCache] 保存日志失败: {e}")
            return ""
    
    # ========== 缓存管理 ==========
    
    def clear_grasp_cache(self, cache_type: str = "all"):
        """清理抓取缓存"""
        if cache_type in ["grasp_poses", "all"]:
            poses_dir = CachePathTools.get_cache_file('grasping', 'grasp_poses', '')
            if poses_dir.exists():
                for file in poses_dir.glob('*.json'):
                    file.unlink()
                print(f"[GraspCache] 已清理抓取位姿缓存")
        
        if cache_type in ["quality_scores", "all"]:
            quality_dir = CachePathTools.get_cache_file('grasping', 'quality_scores', '')
            if quality_dir.exists():
                for file in quality_dir.glob('*.json'):
                    file.unlink()
                print(f"[GraspCache] 已清理质量评分缓存")