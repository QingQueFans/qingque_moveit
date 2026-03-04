# 统一缓存管理器主类 - UnifiedCacheManager
# moveit_core/cache_manager/src/ps_cache/path_tools.py
#!/usr/bin/env python3
"""
缓存路径工具模块
提供统一的路径处理函数，供其他模块导入使用
"""
import os
import json
from pathlib import Path
from typing import Optional, Union, Dict, List
import hashlib

class CachePathTools:
    """缓存路径工具类"""
    
    # 类变量，存储缓存根目录（可以在初始化时设置）
    _cache_root = None
    _initialized = False
    
    @classmethod
    def initialize(cls, cache_root: Optional[str] = None):
        """初始化路径工具（只需调用一次）"""
        if cls._initialized:
            return
        
       
        if cache_root is None:
            # 使用模块内的 data 目录
            current_file = Path(__file__).resolve()
            # 计算：src/ps_cache/path_tools.py → src/ps_cache → src → cache_manager → data
            module_dir = current_file.parent.parent.parent  # cache_manager目录
            cache_root = str(module_dir / 'data')
        cls._cache_root = Path(cache_root)
        cls._ensure_directories()
        cls._initialized = True
        
        print(f"[CachePathTools] 初始化完成，缓存根目录: {cls._cache_root}")
    
    @classmethod
    def _ensure_directories(cls):
        """确保必要的目录存在"""
        required_dirs = [
            'core/objects',
            'kinematics/ik_solutions',
            'kinematics/fk_results',
            'grasping/grasp_poses',
            'planning/trajectories'
        ]
        
        for dir_path in required_dirs:
            full_path = cls._cache_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    # ========== 通用路径函数 ==========
    
    @classmethod
    def get_cache_file(cls, 
                      category: str, 
                      subcategory: str,
                      filename: str,
                      ensure_exists: bool = True) -> Path:
        """
        获取缓存文件路径（主要函数）
        
        Args:
            category: 类别 ('kinematics', 'grasping', 'planning', 'core')
            subcategory: 子类别 ('ik_solutions', 'grasp_poses', etc.)
            filename: 文件名（可带扩展名）
            ensure_exists: 是否确保目录存在
        
        Returns:
            完整路径
        """
        cls._check_initialized()
        
        # 构建路径
        if subcategory:
            file_path = cls._cache_root / category / subcategory / filename
            if ensure_exists:
                file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_path = cls._cache_root / category / filename
            if ensure_exists:
                file_path.parent.mkdir(parents=True, exist_ok=True)
        
        return file_path
    
    @classmethod
    def generate_cache_filename(cls, 
                               prefix: str,
                               data_hash: Optional[str] = None,
                               extension: str = 'json') -> str:
        """
        生成缓存文件名
        
        Args:
            prefix: 文件前缀
            data_hash: 数据哈希（可选）
            extension: 文件扩展名
        
        Returns:
            格式化的文件名
        """
        import time
        
        timestamp = int(time.time())
        
        if data_hash:
            # 如果有数据哈希，使用哈希
            if len(data_hash) > 8:
                data_hash = data_hash[:8]
            filename = f"{prefix}_{data_hash}_{timestamp}.{extension}"
        else:
            # 否则使用随机字符串
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            filename = f"{prefix}_{random_str}_{timestamp}.{extension}"
        
        return filename
    
    @classmethod
    def compute_data_hash(cls, data: Union[Dict, List, str]) -> str:
        """计算数据的哈希值"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    
    
    # ========== 文件操作辅助函数 ==========
    
    @classmethod
    def save_to_cache(cls,
                     filepath: Path,
                     data: Dict,
                     metadata: Optional[Dict] = None) -> bool:
        """保存数据到缓存文件"""
        try:
            cache_entry = {
                'data': data,
                'metadata': metadata or {},
                'saved_at': cls._get_timestamp(),
                'filepath': str(filepath)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2)
            
            print(f"[CachePathTools] 保存到: {filepath}")
            return True
            
        except Exception as e:
            print(f"[CachePathTools] 保存失败 {filepath}: {e}")
            return False
    
    @classmethod
    def load_from_cache(cls, filepath: Path) -> Optional[Dict]:
        """从缓存文件加载数据"""
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[CachePathTools] 加载失败 {filepath}: {e}")
            return None
    
    @classmethod
    def find_in_cache(cls,
                     category: str,
                     subcategory: str,
                     search_pattern: str = "*.json") -> List[Path]:
        """在缓存目录中查找文件"""
        search_dir = cls._cache_root / category / subcategory
        
        if not search_dir.exists():
            return []
        
        return list(search_dir.glob(search_pattern))
    
    # ========== 在运动学模块中的使用示例 ==========
    
    @classmethod
    def ik_solution_to_cache(cls,
                            target_pose: List[float],
                            joint_solution: List[float],
                            robot_model: str,
                            metadata: Optional[Dict] = None) -> str:
        """
        IK解保存到缓存（完整流程示例）
        
        Returns:
            缓存文件路径（字符串）
        """
        # 1. 获取路径
        pose_data = {'position': target_pose[:3], 'orientation': target_pose[3:]}
        filepath = cls.get_ik_solution_path(pose_data, robot_model)
        
        # 2. 准备数据
        ik_data = {
            'target_pose': target_pose,
            'joint_solution': joint_solution,
            'robot_model': robot_model,
            'metadata': metadata or {}
        }
        
        # 3. 保存
        if cls.save_to_cache(filepath, ik_data):
            return str(filepath)
        else:
            return ""
    
    # ========== 工具函数 ==========
    
    @classmethod
    def _check_initialized(cls):
        """检查是否已初始化"""
        if not cls._initialized:
            cls.initialize()
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def get_cache_root(cls) -> Path:
        """获取缓存根目录"""
        cls._check_initialized()
        return cls._cache_root