# 物体缓存接口 - ObjectCache
# moveit_core/cache_manager/src/ps_cache/object_cache.py
#!/usr/bin/env python3
"""
物体信息专用缓存管理器
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import os

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
                        object_type: str = "mesh") -> Optional[Dict]:
        """加载物体信息缓存"""
        filepath = self.get_object_info_path(object_id, object_type)
        return CachePathTools.load_from_cache(filepath)
    
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
        """加载所有缓存的物体"""
        cached_objects = []
        
        # 获取缓存目录
        cache_dir = os.path.join(self.cache_root, "core", "objects")
        
        if not os.path.exists(cache_dir):
            print(f"[ObjectCache] 缓存目录不存在: {cache_dir}")
            return cached_objects
        
        # 列出所有缓存文件
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
        print(f"[ObjectCache] 发现 {len(cache_files)} 个缓存文件")
        
        for filename in cache_files:
            # 只处理物体文件
            if filename.startswith('object_'):
                filepath = os.path.join(cache_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 正确提取物体数据
                    if isinstance(data, dict) and "data" in data:
                        layer1 = data["data"]
                        if isinstance(layer1, dict) and "data" in layer1:
                            object_data = layer1["data"]
                            if isinstance(object_data, dict) and object_data.get("id"):
                                obj_id = object_data.get("id")
                                obj_type = object_data.get("type", "未知")
                                print(f"[ObjectCache] 加载物体: {obj_id} ({obj_type})")
                                cached_objects.append(object_data)
                            else:
                                print(f"[警告] 文件 {filename} 中的物体数据无效")
                        else:
                            print(f"[警告] 文件 {filename} 数据结构不正确")
                    else:
                        print(f"[警告] 文件 {filename} 没有data字段")
                        
                except Exception as e:
                    print(f"[错误] 无法读取缓存文件 {filename}: {e}")
        
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
        return ""    # ========== 物体位姿缓存 ==========
    
    def save_object_pose(self,
                        object_id: str,
                        pose: List[float],
                        timestamp: Optional[str] = None) -> str:
        """保存物体位姿"""
        import time as tm
        
        if timestamp is None:
            timestamp = str(int(tm.time()))
        
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
    
    def clear_object_cache(self, max_age_days: Optional[int] = None):
        """清理物体缓存"""
        objects_dir = CachePathTools.get_cache_file('core', 'objects', '')
        
        if not objects_dir.exists():
            return
        
        deleted = 0
        import time
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

    # 在 ObjectCache 类中添加

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
        import time
        
        # 1. 加载现有物体信息
        object_info = self.load_object_info(object_id)
        
        if object_info is None:
            # 如果没有缓存，创建一个新的
            object_info = {
                'object_id': object_id,
                'object_type': 'unknown',
                'data': {},
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
        
        # 3. 添加到历史记录（限制长度，最多保存最近50个位置）
        object_info['position_history'].append(new_position_record)
        if len(object_info['position_history']) > 50:
            object_info['position_history'] = object_info['position_history'][-50:]
        
        # 4. 更新最新位置
        object_info['data']['latest_position'] = new_position
        object_info['data']['latest_orientation'] = new_orientation
        object_info['data']['last_updated'] = CachePathTools._get_timestamp()
        object_info['data']['update_source'] = source
        object_info['data']['confidence'] = confidence
        
        # 5. 计算物体类型（如果未知）
        if object_info['object_type'] == 'unknown':
            # 可以根据位置变化模式猜测类型
            # 静止物体 vs 移动物体
            object_info['object_type'] = self._infer_object_type(object_info['position_history'])
        
        # 6. 保存更新后的信息
        return self.save_object_info(object_id, object_info['data'])

    def _infer_object_type(self, position_history: List[Dict]) -> str:
        """根据位置历史推断物体类型"""
        if len(position_history) < 2:
            return "static"
        
        # 计算位置变化
        positions = [record['position'] for record in position_history]
        
        # 计算平均移动距离
        total_movement = 0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            dz = positions[i][2] - positions[i-1][2]
            distance = (dx**2 + dy**2 + dz**2) ** 0.5
            total_movement += distance
        
        avg_movement = total_movement / (len(positions) - 1)
        
        if avg_movement < 0.001:  # 小于1mm
            return "static"
        elif avg_movement < 0.01:  # 小于1cm
            return "slightly_movable"
        else:
            return "dynamic"# ========== 位置查询和过滤 ==========

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
        
        # 检查是否有最新位置
        if 'latest_position' not in object_info['data']:
            return None
        
        # 检查时间有效性
        if max_age_seconds:
            import time
            last_updated = object_info['data'].get('last_updated_timestamp')
            if last_updated:
                age = time.time() - float(last_updated)
                if age > max_age_seconds:
                    print(f"[警告] 物体 {object_id} 位置已过期 {age:.1f}秒")
                    return None
        
        if use_filtered and 'position_history' in object_info:
            # 使用滤波算法（如卡尔曼滤波或移动平均）
            filtered_position = self._filter_position(object_info['position_history'])
            return {
                'position': filtered_position,
                'orientation': object_info['data'].get('latest_orientation'),
                'confidence': object_info['data'].get('confidence', 1.0),
                'source': object_info['data'].get('update_source', 'unknown'),
                'timestamp': object_info['data'].get('last_updated')
            }
        else:
            # 返回原始最新位置
            return {
                'position': object_info['data']['latest_position'],
                'orientation': object_info['data'].get('latest_orientation'),
                'confidence': object_info['data'].get('confidence', 1.0),
                'source': object_info['data'].get('update_source', 'unknown'),
                'timestamp': object_info['data'].get('last_updated')
            }

    def _filter_position(self, position_history: List[Dict]) -> List[float]:
        """滤波位置数据（简单的移动平均）"""
        if not position_history:
            return [0, 0, 0]
        
        # 取最近5个位置的平均
        recent_positions = position_history[-5:]
        
        sum_x = sum(p['position'][0] for p in recent_positions)
        sum_y = sum(p['position'][1] for p in recent_positions)
        sum_z = sum(p['position'][2] for p in recent_positions)
        
        count = len(recent_positions)
        return [
            sum_x / count,
            sum_y / count,
            sum_z / count
        ]

    # ========== 批量更新和同步 ==========

    def batch_update_positions(self, 
                            updates: List[Dict],
                            scene_id: Optional[str] = None) -> Dict:
        """
        批量更新多个物体的位置
        
        Args:
            updates: [{'object_id': 'cube1', 'position': [x,y,z], ...}, ...]
            scene_id: 场景ID（可选，用于关联更新）
        
        Returns:
            更新统计信息
        """
        results = {
            'total': len(updates),
            'successful': 0,
            'failed': 0,
            'updated_objects': []
        }
        
        for update in updates:
            try:
                object_id = update['object_id']
                position = update['position']
                orientation = update.get('orientation')
                source = update.get('source', 'batch_update')
                confidence = update.get('confidence', 0.8)            # 更新单个物体
                path = self.update_object_position(
                    object_id=object_id,
                    new_position=position,
                    new_orientation=orientation,
                    source=source,
                    confidence=confidence
                )
                
                if path:
                    results['successful'] += 1
                    results['updated_objects'].append(object_id)
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                print(f"[批量更新] 更新失败 {update.get('object_id', 'unknown')}: {e}")
                results['failed'] += 1
        
        # 如果有场景ID，保存场景快照
        if scene_id and results['successful'] > 0:
            scene_data = {
                'scene_id': scene_id,
                'update_time': CachePathTools._get_timestamp(),
                'updated_objects': results['updated_objects'],
                'total_updates': results['total']
            }
            self.save_scene_objects(scene_id, updates, "batch_update")
        
        return results

    # ========== 位置预测（用于移动物体） ==========

    def predict_object_position(self,
                            object_id: str,
                            time_ahead: float = 1.0) -> Optional[Dict]:
        """
        预测物体未来位置（线性预测）
        
        Args:
            object_id: 物体ID
            time_ahead: 预测多少秒后的位置
        
        Returns:
            预测位置和方向
        """
        object_info = self.load_object_info(object_id)
        if not object_info or 'position_history' not in object_info:
            return None
        
        history = object_info['position_history']
        if len(history) < 3:
            return None  # 数据不足
        
        # 计算平均速度
        recent = history[-3:]  # 取最近3个位置
        velocities = []
        
        for i in range(1, len(recent)):
            dt = recent[i]['timestamp'] - recent[i-1]['timestamp']
            if dt <= 0:
                continue
            
            dx = recent[i]['position'][0] - recent[i-1]['position'][0]
            dy = recent[i]['position'][1] - recent[i-1]['position'][1]
            dz = recent[i]['position'][2] - recent[i-1]['position'][2]
            
            velocities.append([dx/dt, dy/dt, dz/dt])
        
        if not velocities:
            return None
        
        # 平均速度
        avg_vx = sum(v[0] for v in velocities) / len(velocities)
        avg_vy = sum(v[1] for v in velocities) / len(velocities)
        avg_vz = sum(v[2] for v in velocities) / len(velocities)
        
        # 最新位置
        latest = history[-1]['position']
        
        # 预测未来位置
        predicted_position = [
            latest[0] + avg_vx * time_ahead,
            latest[1] + avg_vy * time_ahead,
            latest[2] + avg_vz * time_ahead
        ]
        
        return {
            'predicted_position': predicted_position,
            'velocity': [avg_vx, avg_vy, avg_vz],
            'prediction_time': time_ahead,
            'confidence': min(1.0, len(history) / 10.0)  # 数据越多越可信
        }