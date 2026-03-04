# moveit_core/cache_manager/src/ps_cache/planning_cache.py
#!/usr/bin/env python3
"""
规划专用缓存管理器
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import pickle  # 用于二进制序列化
import time

# 导入通用缓存管理器
from .cache_manager import CachePathTools  # ⭐️ 使用正确的类名

class PlanningCache:
    """规划专用缓存管理器"""
    
    def __init__(self):
        """初始化规划缓存"""
        CachePathTools.initialize()
        print("[PlanningCache] 规划缓存管理器初始化完成")
    
    # ========== 轨迹缓存 ==========
    
    def get_trajectory_path(self,
                           start_state: List[float],
                           goal_state: List[float],
                           planner: str = "RRT") -> Path:
        """
        获取轨迹缓存路径
        
        Args:
            start_state: 起始状态
            goal_state: 目标状态
            planner: 规划器名称
        
        Returns:
            轨迹缓存文件路径
        """
        # 计算轨迹哈希
        data_hash = CachePathTools.compute_data_hash({
            'start': start_state,
            'goal': goal_state,
            'planner': planner
        })[:12]
        
        filename = f"traj_{planner}_{data_hash}.traj"
        return CachePathTools.get_cache_file('planning', 'trajectories', filename)
    
    def save_trajectory(self,
                       trajectory_data: Dict,
                       planner: str = "RRT",
                       metadata: Optional[Dict] = None) -> str:
        """
        保存轨迹到缓存
        
        Returns:
            缓存文件路径
        """
        start_state = trajectory_data.get('start_state', [])
        goal_state = trajectory_data.get('goal_state', [])
        
        filepath = self.get_trajectory_path(start_state, goal_state, planner)
        
        # 增强轨迹数据
        traj_info = {
            'trajectory': trajectory_data,
            'planner': planner,
            'start_state': start_state,
            'goal_state': goal_state,
            'metadata': metadata or {},
            'saved_at': CachePathTools._get_timestamp()
        }
        
        try:
            # 使用pickle保存二进制数据
            with open(filepath, 'wb') as f:
                pickle.dump(traj_info, f)
            print(f"[PlanningCache] 轨迹已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"[PlanningCache] 保存轨迹失败: {e}")
            return ""
    
    def load_trajectory(self,
                       start_state: List[float],
                       goal_state: List[float],
                       planner: str = "RRT") -> Optional[Any]:
        """加载轨迹缓存"""
        filepath = self.get_trajectory_path(start_state, goal_state, planner)
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[PlanningCache] 加载轨迹失败: {e}")
            return None
    
    # ========== 碰撞检查缓存 ==========
    
    def save_collision_check(self,
                            check_id: str,
                            check_results: Dict,
                            check_type: str = "pairwise") -> str:
        """保存碰撞检查结果"""
        data_hash = CachePathTools.compute_data_hash(check_id)[:8]
        filename = f"collision_{check_type}_{data_hash}.bin"
        filepath = CachePathTools.get_cache_file('planning', 'collision_checks', filename)
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(check_results, f)
            return str(filepath)
        except Exception as e:
            print(f"[PlanningCache] 保存碰撞检查失败: {e}")
            return ""    # ========== 搜索树缓存 ==========
    
    def save_search_tree(self,
                        tree_id: str,
                        tree_data: Any,
                        algorithm: str = "RRT") -> str:
        """保存搜索树"""
        data_hash = CachePathTools.compute_data_hash(tree_id)[:8]
        filename = f"tree_{algorithm}_{data_hash}.tree"
        filepath = CachePathTools.get_cache_file('planning', 'search_trees', filename)
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(tree_data, f)
            return str(filepath)
        except Exception as e:
            print(f"[PlanningCache] 保存搜索树失败: {e}")
            return ""
    
    # ========== 规划统计缓存 ==========
    
    def save_planning_stats(self,
                           stats_id: str,
                           statistics: Dict,
                           plan_type: str = "motion") -> str:
        """保存规划统计"""
        timestamp = int(time.time())
        filename = f"stats_{plan_type}_{stats_id}_{timestamp}.json"
        filepath = CachePathTools.get_cache_file('planning', 'trajectories', filename)
        
        stats_data = {
            'stats_id': stats_id,
            'plan_type': plan_type,
            'statistics': statistics,
            'timestamp': timestamp
        }
        
        if CachePathTools.save_to_cache(filepath, stats_data):
            return str(filepath)
        return ""
    
    # ========== 缓存管理 ==========
    
    def clear_planning_cache(self, cache_type: str = "all"):
        """清理规划缓存"""
        import shutil
        
        if cache_type in ["trajectories", "all"]:
            traj_dir = CachePathTools.get_cache_file('planning', 'trajectories', '')
            if traj_dir.exists():
                shutil.rmtree(traj_dir)
                traj_dir.mkdir()
                print(f"[PlanningCache] 已清理轨迹缓存")
        
        if cache_type in ["collision_checks", "all"]:
            collision_dir = CachePathTools.get_cache_file('planning', 'collision_checks', '')
            if collision_dir.exists():
                shutil.rmtree(collision_dir)
                collision_dir.mkdir()
                print(f"[PlanningCache] 已清理碰撞检查缓存")