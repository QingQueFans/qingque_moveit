# 运动学缓存接口 - KinematicsCache
# moveit_core/cache_manager/src/ps_cache/kinematics_cache.py
#!/usr/bin/env python3
"""
运动学专用缓存管理器
使用通用路径工具，提供运动学特定功能
"""
from typing import Dict, List, Optional, Union
from pathlib import Path
import json
import numpy as np
# 导入通用路径工具
from .cache_manager import CachePathTools

class KinematicsCache:
    """运动学专用缓存管理器"""
    
    def __init__(self):
        """初始化运动学缓存"""
        # 确保路径工具已初始化
        CachePathTools.initialize()
        print("[KinematicsCache] 运动学缓存管理器初始化完成")
    
    # ========== IK解缓存方法 ==========
    
    def get_ik_solution_path(self, 
                           pose_data: Dict,
                           robot_model: str,
                           custom_name: Optional[str] = None,
                           allow_duplicates: bool = False) -> Path:
        """
        获取IK解缓存路径
        
        Args:
            pose_data: 位姿数据
            robot_model: 机器人模型名称
            custom_name: 自定义文件名（可选）
            allow_duplicates: 是否允许相同位姿多个文件
        
        Returns:
            IK解缓存文件路径
        """
        # 计算位姿哈希
        pose_hash = CachePathTools.compute_data_hash({
            'pose': pose_data,
            'robot': robot_model
        })[:12]
        
        if custom_name:
            base_filename = f"{custom_name}_{pose_hash}"
        else:
            base_filename = f"ik_{pose_hash}"
        
        # 如果允许重复，添加序号
        if allow_duplicates:
            # 查找已有文件
            pattern = f"{base_filename}_*.json"
            existing = CachePathTools.find_in_cache('kinematics', 'ik_solutions', pattern)
            
            if existing:
                # 找到最大序号
                max_seq = 0
                for file in existing:
                    # 从 ik_5c709ed597ac_001.json 提取 001
                    name = file.stem
                    parts = name.split('_')
                    if len(parts) >= 3:
                        try:
                            seq = int(parts[-1])
                            max_seq = max(max_seq, seq)
                        except:
                            pass
                
                sequence = max_seq + 1
                filename = f"{base_filename}_{sequence:03d}.json"
            else:
                filename = f"{base_filename}_001.json"
        else:
            filename = f"{base_filename}.json"
        
        return CachePathTools.get_cache_file('kinematics', 'ik_solutions', filename)
    def save_ik_solution(self,
                        target_pose: List[float],
                        joint_solution: List[float],
                        robot_model: str,
                        metadata: Optional[Dict] = None,
                        allow_duplicates: bool = False,
                        object_id: Optional[str] = None) -> str:
        """
        保存IK解到缓存
        
        Args:
            target_pose: 目标位姿
            joint_solution: 关节解
            robot_model: 机器人模型
            metadata: 元数据
            allow_duplicates: 是否允许重复
            object_id: 物体ID（新增）
        
        Returns:
            缓存文件路径
        """
        # 确保所有数据都是可序列化的Python原生类型
        serializable_target_pose = [float(x) for x in target_pose] if target_pose else []
        serializable_joint_solution = [float(x) for x in joint_solution] if joint_solution else []
        
        # 【关键】确保使用完整的7元素位姿，与load_ik_solution保持一致
        if len(serializable_target_pose) == 3:
            full_pose = serializable_target_pose + [0.0, 0.0, 0.0, 1.0]
        else:
            full_pose = serializable_target_pose[:7]
        
        # 准备位姿数据 - 用 full_pose！
        pose_data = {
            'position': full_pose[:3],
            'orientation': full_pose[3:]
        }
        
        # 【调试】打印保存时的数据
        print(f"[调试保存] full_pose = {full_pose}")
        print(f"[调试保存] pose_data = {pose_data}")
        print(f"[调试保存] 计算哈希的数据: {{'pose': {pose_data}, 'robot': '{robot_model}'}}")
        
        # 获取路径
        filepath = self.get_ik_solution_path(
            pose_data=pose_data,
            robot_model=robot_model,
            allow_duplicates=allow_duplicates
        )
        
        # 准备元数据
        if metadata is None:
            metadata = {}
        
        # 如果提供了object_id，添加到metadata
        if object_id:
            metadata['object_id'] = str(object_id)
            metadata['source'] = metadata.get('source', 'trajectory_execution')
        
        # 确保metadata中的所有值都是可序列化的
        serializable_metadata = {}
        for key, value in metadata.items():
            try:
                # 尝试转换为可序列化类型
                if isinstance(value, (int, float, str, bool, type(None))):
                    serializable_metadata[key] = value
                elif isinstance(value, list):
                    serializable_metadata[key] = [float(x) if isinstance(x, (int, float, np.integer, np.floating)) else str(x) 
                                                for x in value]
                else:
                    serializable_metadata[key] = str(value)
            except:
                serializable_metadata[key] = str(value)
        
        # 准备缓存数据 - 保存完整的 full_pose
        ik_data = {
            'target_pose': full_pose,  # 保存完整的7元素位姿
            'joint_solution': serializable_joint_solution,
            'robot_model': robot_model,
            'metadata': serializable_metadata
        }
        
        # 保存
        if CachePathTools.save_to_cache(filepath, ik_data):
            print(f"[KinematicsCache] IK解已保存: {filepath}")
            
            # 可选：如果提供了object_id，创建对应的符号链接
            if object_id:
                self._create_object_symbolic_link(object_id, filepath)
                
            return str(filepath)
        else:
            return ""
        
    def load_ik_solution(self, target_pose, robot_model, sequence=0):
        print(f"[调试加载] load_ik_solution 参数: target_pose={target_pose}")
        
        # 确保使用完整的7元素位姿
        if len(target_pose) == 3:
            full_pose = list(target_pose) + [0.0, 0.0, 0.0, 1.0]
        else:
            full_pose = list(target_pose[:7])
        
        # 【关键】用 full_pose 创建 pose_data，确保与保存时一致
        pose_data = {
            'position': full_pose[:3],
            'orientation': full_pose[3:]
        }
        
        print(f"[调试加载] full_pose = {full_pose}")
        print(f"[调试加载] pose_data = {pose_data}")
        print(f"[调试加载] 计算哈希的数据: {{'pose': {pose_data}, 'robot': '{robot_model}'}}")
        
        # 计算哈希（现在应该和保存时一致）
        pose_hash = CachePathTools.compute_data_hash({
            'pose': pose_data,
            'robot': robot_model
        })[:12]
        print(f"[调试加载] pose_hash={pose_hash}")
        
        base_filename = f"ik_{pose_hash}"
        print(f"[调试加载] base_filename={base_filename}")
        
        # 先尝试无序号文件
        single_file = CachePathTools.get_cache_file('kinematics', 'ik_solutions', f"{base_filename}.json")
        print(f"[调试加载] 尝试无序号文件: {single_file}")
        print(f"[调试加载] 文件存在? {single_file.exists()}")
        
        if single_file.exists():
            data = CachePathTools.load_from_cache(single_file)
            print(f"[调试加载] 加载成功? {data is not None}")
            return data
        
        return None
    # ========== FK结果缓存方法 ==========
    
    def save_fk_result(self,
                      joint_state: List[float],
                      end_effector_pose: List[float],
                      robot_model: str,
                      metadata: Optional[Dict] = None) -> str:
        """保存FK结果到缓存"""
        # 获取路径
        filepath = CachePathTools.get_fk_result_path(joint_state, robot_model)
        
        # 准备数据
        fk_data = {
            'joint_state': joint_state,
            'end_effector_pose': end_effector_pose,
            'robot_model': robot_model,
            'metadata': metadata or {}
        }
        
        # 保存
        if CachePathTools.save_to_cache(filepath, fk_data):
            return str(filepath)
        return ""
    
    def load_fk_result(self,
                      joint_state: List[float],
                      robot_model: str) -> Optional[Dict]:
        """加载FK结果缓存"""
        filepath = CachePathTools.get_fk_result_path(joint_state, robot_model)
        return CachePathTools.load_from_cache(filepath)
    def _create_object_symbolic_link(self, object_id: str, ik_filepath: Path):
        """为物体ID创建符号链接"""
        try:
            import hashlib
            
            # 生成物体ID的哈希
            obj_hash = hashlib.md5(object_id.encode()).hexdigest()[:12]
            
            # 符号链接路径
            links_dir = Path(ik_filepath).parent / "object_links"
            links_dir.mkdir(exist_ok=True)
            
            link_path = links_dir / f"obj_{obj_hash}.json"
            
            # 创建符号链接指向原始IK文件
            if link_path.exists():
                link_path.unlink()
            
            link_path.symlink_to(Path(ik_filepath).absolute())
            
            print(f"[KinematicsCache] 创建物体链接: {object_id} -> {ik_filepath.name}")
            
        except Exception as e:
            print(f"[KinematicsCache] 创建符号链接失败: {e}")    
    # ========== 缓存管理方法 ==========
    
    def clear_ik_cache(self):
        """清理IK缓存"""
        ik_dir = CachePathTools.get_cache_file('kinematics', 'ik_solutions', '')
        if ik_dir.exists():
            for file in ik_dir.glob('*.json'):
                file.unlink()
            print(f"[KinematicsCache] 已清理IK缓存: {ik_dir}")
    
    def get_ik_cache_stats(self) -> Dict:
        """获取IK缓存统计"""
        files = CachePathTools.find_in_cache('kinematics', 'ik_solutions', '*.json')
        
        total_size = 0
        for file in files:
            total_size += file.stat().st_size
        
        return {
            'file_count': len(files),
            'total_size_mb': total_size / (1024 * 1024),
            'directory': str(CachePathTools.get_cache_file('kinematics', 'ik_solutions', ''))
        }