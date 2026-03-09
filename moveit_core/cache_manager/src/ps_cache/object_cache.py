#!/usr/bin/env python3
"""
物体信息专用缓存管理器
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import os
import time

# 导入通用缓存管理器
from .cache_manager import CachePathTools  # ⭐️ 使用正确的类名

class ObjectCache:
    """物体信息专用缓存管理器"""
    
    def __init__(self):
        """初始化物体缓存"""
        CachePathTools.initialize()
        print("[ObjectCache] 物体缓存管理器初始化完成")
    
    # ========== 物体信息缓存 ==========
    
    def get_object_info_path(self,
                           object_id: str,
                           object_type: str = "mesh") -> Path:
        """
        获取物体信息缓存路径
        
        Args:
            object_id: 物体ID
            object_type: 物体类型 (box, sphere, cylinder, mesh)
        
        Returns:
            物体信息缓存文件路径
        """
        # 计算哈希
        data_hash = CachePathTools.compute_data_hash(object_id)[:8]
        filename = f"object_{object_type}_{data_hash}.json"
        
        return CachePathTools.get_cache_file('core', 'objects', filename)
    
    def save_object_info(self,
                        object_id: str,
                        object_data: Dict,
                        object_type: str = "mesh") -> str:
        """
        保存物体信息到缓存
        
        Returns:
            缓存文件路径
        """
        filepath = self.get_object_info_path(object_id, object_type)
        
        # 增强物体数据
        object_info = {
            'object_id': object_id,
            'object_type': object_type,
            'data': object_data,
            'saved_at': CachePathTools._get_timestamp(),
            'version': '1.0'
        }
        
        if CachePathTools.save_to_cache(filepath, object_info):
            print(f"[ObjectCache] 物体信息已保存: {filepath}")
            return str(filepath)
        return ""
    
    def load_object_info(self,
                        object_id: str,
                        object_type: str = None) -> Optional[Dict]:
        """
        加载物体信息缓存
        
        Args:
            object_id: 物体ID
            object_type: 物体类型（如果指定，只搜索该类型）
        
        Returns:
            物体的核心数据（包含 id, type, dimensions, position, orientation）
            如果找不到返回 None
        """
        # 1. 如果指定了类型，先尝试精确匹配
        if object_type:
            filepath = self.get_object_info_path(object_id, object_type)
            data = CachePathTools.load_from_cache(filepath)
            if data:
                # ✅ 返回核心数据层
                core_data = data.get('data', {}).get('data', {})
                if core_data:
                    return core_data
                return data
        
        # 2. 搜索所有物体缓存文件
        objects_dir = CachePathTools.get_cache_file('core', 'objects', '')
        if not objects_dir.exists():
            return None
        
        for cache_file in objects_dir.glob("object_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # 解析物体ID
                obj_info = data.get('data', {})
                obj_id = obj_info.get('object_id') or obj_info.get('data', {}).get('id')
                
                if obj_id == object_id:
                    print(f"[ObjectCache] 找到物体 {object_id}: {cache_file.name}")
                    # ✅ 返回核心数据层
                    core_data = obj_info.get('data', {})
                    if core_data:
                        return core_data
                    return obj_info
                    
            except Exception as e:
                continue
        
        return None
    
    # ========== 批量物体缓存 ==========
    
    def save_scene_objects(self,
                          scene_id: str,
                          objects: List[Dict],
                          scene_type: str = "workspace") -> str:
        """保存场景中的多个物体"""
        data_hash = CachePathTools.compute_data_hash(scene_id)[:8]
        filename = f"scene_{scene_type}_{data_hash}.json"
        filepath = CachePathTools.get_cache_file('core', 'objects', filename)
        
        scene_data = {
            'scene_id': scene_id,
            'scene_type': scene_type,
            'objects': objects,
            'object_count': len(objects),
            'saved_at': CachePathTools._get_timestamp()
        }
        
        if CachePathTools.save_to_cache(filepath, scene_data):
            return str(filepath)
        return ""
    
    def load_all_cached_objects(self) -> List[Dict]:
        """加载所有缓存的物体（返回核心数据）"""
        cached_objects = []
        
        objects_dir = CachePathTools.get_cache_file('core', 'objects', '')
        
        if not objects_dir.exists():
            print(f"[ObjectCache] 缓存目录不存在: {objects_dir}")
            return cached_objects
        
        cache_files = list(objects_dir.glob("object_*.json"))
        print(f"[ObjectCache] 发现 {len(cache_files)} 个缓存文件")
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 正确提取物体核心数据
                obj_info = data.get('data', {})
                core_data = obj_info.get('data', {})
                
                if core_data and core_data.get("id"):
                    obj_id = core_data.get("id")
                    obj_type = core_data.get("type", "未知")
                    print(f"[ObjectCache] 加载物体: {obj_id} ({obj_type})")
                    cached_objects.append(core_data)
                else:
                    print(f"[警告] 文件 {cache_file.name} 中的物体数据无效")
                        
            except Exception as e:
                print(f"[错误] 无法读取缓存文件 {cache_file.name}: {e}")
        
        print(f"[ObjectCache] 总共加载 {len(cached_objects)} 个物体")
        return cached_objects
    
    # ========== 物体检测结果缓存 ==========
    
    def save_detection_results(self,
                              detection_id: str,
                              results: List[Dict],
                              detector: str = "yolo",
                              metadata: Optional[Dict] = None) -> str:
        """保存物体检测结果"""
        data_hash = CachePathTools.compute_data_hash(detection_id)[:8]
        filename = f"detection_{detector}_{data_hash}.json"
        filepath = CachePathTools.get_cache_file('core', 'objects', filename)
        
        detection_data = {
            'detection_id': detection_id,
            'detector': detector,
            'results': results,
            'detected_count': len(results),
            'metadata': metadata or {}
        }
        
        if CachePathTools.save_to_cache(filepath, detection_data):
            return str(filepath)
        return ""
    
    # ========== 物体位姿缓存 ==========
    
    def save_object_pose(self,
                        object_id: str,
                        pose: List[float],
                        timestamp: Optional[str] = None) -> str:
        """保存物体位姿"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        filename = f"pose_{object_id}_{timestamp}.json"
        filepath = CachePathTools.get_cache_file('core', 'objects', filename)
        
        pose_data = {
            'object_id': object_id,
            'pose': pose,
            'timestamp': timestamp
        }
        
        if CachePathTools.save_to_cache(filepath, pose_data):
            return str(filepath)
        return ""
    
    # ========== 缓存管理 ==========
    def remove_object(self, object_id: str) -> bool:
        """从缓存中移除物体"""
        print(f"[ObjectCache] 从缓存移除物体: {object_id}")
        try:
            objects_dir = CachePathTools.get_cache_file('core', 'objects', '')
            if not objects_dir.exists():
                return False
            
            deleted = False
            # 查找所有匹配该 object_id 的缓存文件
            for cache_file in objects_dir.glob("object_*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # 从 data.data.id 或 data.object_id 提取物体ID
                    obj_info = data.get('data', {})
                    obj_data = obj_info.get('data', {})
                    cached_id = obj_data.get('id') or obj_info.get('object_id')
                    
                    if cached_id == object_id:
                        cache_file.unlink()  # 删除文件
                        print(f"[ObjectCache] 已删除缓存文件: {cache_file.name}")
                        deleted = True
                        
                except Exception as e:
                    print(f"[ObjectCache] 读取文件 {cache_file.name} 时出错: {e}")
                    continue
            
            # 同时删除位置缓存文件
            for pose_file in objects_dir.glob(f"pose_{object_id}_*.json"):
                pose_file.unlink()
                print(f"[ObjectCache] 已删除位姿文件: {pose_file.name}")
                deleted = True
            
            if deleted:
                print(f"[ObjectCache] 物体 {object_id} 已从缓存移除")
                return True
            else:
                print(f"[ObjectCache] 未找到物体 {object_id} 的缓存文件")
                return False
                
        except Exception as e:
            print(f"[ObjectCache] 移除物体失败: {e}")
            return False
    def clear_object_cache(self, max_age_days: Optional[int] = None):
        """清理物体缓存"""
        objects_dir = CachePathTools.get_cache_file('core', 'objects', '')
        
        if not objects_dir.exists():
            return
        
        deleted = 0
        current_time = time.time()
        
        for file in objects_dir.glob('*.json'):
            if max_age_days is not None:
                # 检查文件年龄
                file_age = current_time - file.stat().st_mtime
                max_age_seconds = max_age_days * 24 * 3600
                if file_age <= max_age_seconds:
                    continue
            
            file.unlink()
            deleted += 1
        
        print(f"[ObjectCache] 已清理 {deleted} 个物体缓存文件")
    
    # ========== 物体位置更新机制 ==========
    
    def update_object_position(self, 
                            object_id: str, 
                            new_position: List[float],
                            new_orientation: Optional[List[float]] = None,
                            source: str = "detection",
                            confidence: float = 1.0) -> str:
        """
        更新物体位置
        
        Args:
            object_id: 物体ID
            new_position: [x, y, z]
            new_orientation: [qx, qy, qz, qw] (可选)
            source: 位置来源 ('detection', 'tracking', 'user_input', 'simulation')
            confidence: 位置置信度 [0-1]
        
        Returns:
            更新的缓存文件路径
        """
        # 1. 加载现有物体信息
        object_info = self.load_object_info(object_id)
        
        if object_info is None:
            # 如果没有缓存，创建一个新的
            object_info = {
                'id': object_id,
                'type': 'unknown',
                'position': new_position,
                'orientation': new_orientation or [0,0,0,1],
                'created_at': CachePathTools._get_timestamp(),
                'position_history': []
            }
        else:
            # 确保有位置历史记录
            if 'position_history' not in object_info:
                object_info['position_history'] = []
        
        # 2. 创建新的位置记录
        new_position_record = {
            'position': new_position,
            'timestamp': int(time.time()),
            'source': source,
            'confidence': confidence
        }
        
        if new_orientation:
            new_position_record['orientation'] = new_orientation
        
        # 3. 添加到历史记录
        object_info['position_history'].append(new_position_record)
        if len(object_info['position_history']) > 50:
            object_info['position_history'] = object_info['position_history'][-50:]
        
        # 4. 更新最新位置
        object_info['position'] = new_position
        if new_orientation:
            object_info['orientation'] = new_orientation
        object_info['last_updated'] = CachePathTools._get_timestamp()
        object_info['update_source'] = source
        object_info['confidence'] = confidence
        
        # 5. 保存更新后的信息
        return self.save_object_info(object_id, object_info)
    
    def get_object_position(self, 
                        object_id: str,
                        use_filtered: bool = True,
                        max_age_seconds: Optional[int] = None) -> Optional[Dict]:
        """
        获取物体当前位置（可过滤）
        
        Args:
            object_id: 物体ID
            use_filtered: 是否使用滤波后的位置
            max_age_seconds: 最大允许的时间差（秒）
        
        Returns:
            包含位置、方向、置信度的字典
        """
        object_info = self.load_object_info(object_id)
        if not object_info:
            return None
        
        # 检查是否有位置信息
        if 'position' not in object_info:
            return None
        
        # 检查时间有效性
        if max_age_seconds and 'last_updated_timestamp' in object_info:
            age = time.time() - float(object_info['last_updated_timestamp'])
            if age > max_age_seconds:
                print(f"[警告] 物体 {object_id} 位置已过期 {age:.1f}秒")
                return None
        
        return {
            'position': object_info.get('position'),
            'orientation': object_info.get('orientation'),
            'confidence': object_info.get('confidence', 1.0),
            'source': object_info.get('update_source', 'unknown'),
            'timestamp': object_info.get('last_updated')
        }