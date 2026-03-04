# 缓存查询引擎 - CacheQueryEngine
# moveit_core/cache_manager/src/ps_cache/query_engine.py
#!/usr/bin/env python3
"""
缓存查询引擎
提供跨模块的缓存查询功能
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json


# 导入所有专用缓存管理器
from .cache_manager import CachePathTools
from .kinematics_cache import KinematicsCache
from .grasp_cache import GraspCache
from .object_cache import ObjectCache
from .planning_cache import PlanningCache


class CacheQueryEngine:
    """缓存查询引擎"""
    
    def __init__(self):
        """初始化查询引擎"""
        self.kinematics_cache = KinematicsCache()
        self.grasp_cache = GraspCache()
        self.object_cache = ObjectCache()
        self.planning_cache = PlanningCache()
        
        print("[CacheQueryEngine] 缓存查询引擎初始化完成")
    
    # ========== 跨模块查询 ==========
    
    def query_by_object(self, object_id: str) -> Dict:
        """
        查询与物体相关的所有缓存
        
        Args:
            object_id: 物体ID
        
        Returns:
            所有相关缓存信息
        """
        results = {
            'object_id': object_id,
            'object_info': None,
            'grasp_poses': [],
            'ik_solutions': [],
            'trajectories': []
        }
        
        # 查询物体信息
        obj_info = self.object_cache.load_object_info(object_id)
        if obj_info:
            results['object_info'] = obj_info
        
        # 查询抓取位姿（需要遍历抓取缓存）
        # 简化的查询逻辑
        
        return results
    
    def query_by_robot_pose(self,
                           target_pose: List[float],
                           robot_model: str) -> Dict:
        """
        查询与机器人位姿相关的缓存
        
        Args:
            target_pose: 目标位姿
            robot_model: 机器人模型
        
        Returns:
            相关缓存信息
        """
        results = {
            'target_pose': target_pose,
            'robot_model': robot_model,
            'ik_solutions': [],
            'trajectories': []
        }
        
        # 查询IK解
        ik_solution = self.kinematics_cache.load_ik_solution(target_pose, robot_model)
        if ik_solution:
            results['ik_solutions'].append(ik_solution)
        
        return results
    
    # ========== 统计查询 ==========
    
    def get_cache_statistics(self) -> Dict:
        """获取所有缓存统计"""
        stats = {
            'total_size_mb': 0,
            'file_counts': {},
            'module_stats': {}
        }
        
        # 这里可以添加具体的统计逻辑        # 遍历所有缓存目录，计算文件数量和大小
        
        return stats
    
    # ========== 高级查询 ==========
    
    def find_similar_solutions(self,
                              query_data: Dict,
                              similarity_threshold: float = 0.1) -> List[Dict]:
        """
        查找相似的缓存解决方案
        
        Args:
            query_data: 查询数据
            similarity_threshold: 相似度阈值
        
        Returns:
            相似解决方案列表
        """
        # 这里可以实现基于内容的相似性搜索
        # 例如：查找相似的位姿、相似的物体等
        
        return []
    
    def export_cache_report(self, output_path: str) -> bool:
        """
        导出缓存报告
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            是否成功
        """
        try:
            report = {
                'generated_at': CachePathTools._get_timestamp(),
                'statistics': self.get_cache_statistics(),
                'cache_structure': self._get_cache_structure()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"[CacheQueryEngine] 缓存报告已导出: {output_path}")
            return True
            
        except Exception as e:
            print(f"[CacheQueryEngine] 导出报告失败: {e}")
            return False
    
    def _get_cache_structure(self) -> Dict:
        """获取缓存目录结构"""
        import os
        from .cache_manager import CachePathTools
        
        cache_root = CachePathTools.get_cache_root()
        structure = {}
        
        for category in ['core', 'kinematics', 'grasping', 'planning']:
            category_path = cache_root / category
            if category_path.exists():
                structure[category] = []
                for item in category_path.iterdir():
                    if item.is_dir():
                        structure[category].append({
                            'name': item.name,
                            'file_count': len(list(item.glob('*'))),
                            'size_mb': self._get_dir_size_mb(item)
                        })
        
        return structure
    
    def _get_dir_size_mb(self, directory: Path) -> float:
        """获取目录大小（MB）"""
        total_size = 0
        for file in directory.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size / (1024 * 1024)