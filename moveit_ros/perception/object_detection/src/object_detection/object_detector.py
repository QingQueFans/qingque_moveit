#!/usr/bin/env python3
"""
纯净物体检测器 - 只负责检测物体，不包含抓取逻辑
提供标准化的物体数据接口
"""
import sys
import os
import json
import time
from typing import Dict, List, Optional

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)
MOVEIT_CORE_ROOT = os.path.join(PROJECT_ROOT, '..', '..')

# 关键路径
CORE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'core_functions', 'src')
OBJ_SRC = os.path.join(MOVEIT_CORE_ROOT, 'planning_scene', 'collision_objects', 'src')
CACHE_SRC = os.path.join(MOVEIT_CORE_ROOT, 'cache_manager', 'src')

sys.path.insert(0, CACHE_SRC)
sys.path.insert(0, OBJ_SRC)
sys.path.insert(0, CORE_SRC)

try:
    from ps_core.scene_client import PlanningSceneClient
    from ps_objects.object_manager import ObjectManager
    from ps_cache import CachePathTools, ObjectCache
    
    
    HAS_DEPENDENCIES = True
    print("[物体检测器] ✓ 依赖导入成功")
    
except ImportError as e:
    print(f"[物体检测器] ✗ 依赖导入失败: {e}")
    HAS_DEPENDENCIES = False


class PureObjectDetector:
    """
    纯净物体检测器 - 只负责物体检测
    
    职责：
    1. 从各种来源检测物体
    2. 提供标准化的物体数据
    3. 管理物体缓存
    4. 不包含任何抓取、运动学等逻辑
    """
    
    def __init__(self, scene_client=None, object_manager=None):
        """初始化纯净检测器"""
        if not HAS_DEPENDENCIES:
            raise ImportError("依赖导入失败")
        
        self.client = scene_client
        self.object_manager = object_manager
        
        # 初始化缓存
        CachePathTools.initialize()
        self.object_cache = ObjectCache()
        
        # 检测模式
        self.mode = "hybrid"  # hybrid, cache_only, detection_only
        
        # 标准化的物体数据结构
        self.object_schema = {
            "required_fields": ["id", "type", "position"],
            "optional_fields": ["dimensions", "orientation", "color", "confidence"]
        }
        
        print(f"[纯净检测器] 初始化完成，模式: {self.mode}")
    
    # ========== 核心检测接口 ==========
    
    def detect(self, 
              use_cache: bool = True,
              scene_id: Optional[str] = None) -> Dict:
        """
        检测物体 - 纯净接口
        
        Returns:
            {
                "success": bool,
                "objects": [标准化物体数据],
                "metadata": {检测信息},
                "timestamp": str
            }
        """
        start_time = time.time()
        
        try:
            objects = []
            sources = []
            
            # 1. 从缓存获取（如果启用）
            if use_cache:
                cached_objects = self._get_cached_objects(scene_id)
                if cached_objects:
                    objects.extend(cached_objects)
                    sources.append("cache")            # 2. 如果缓存不够或需要新鲜数据，进行检测
            if self.mode in ["hybrid", "detection_only"] or not objects:
                detected_objects = self._perform_detection(scene_id)
                if detected_objects:
                    objects.extend(detected_objects)
                    sources.append("detection")
                    
                    # 保存新检测的物体到缓存
                    if detected_objects and use_cache:
                        self._cache_detected_objects(detected_objects, scene_id)
            
            # 3. 标准化物体数据
            standardized_objects = []
            for obj in objects:
                standardized = self._standardize_object_data(obj)
                if standardized:
                    standardized_objects.append(standardized)
            
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "objects": standardized_objects,
                "count": len(standardized_objects),
                "sources": sources,
                "processing_time": elapsed,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "schema_version": "1.0"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_object(self, object_id: str) -> Dict:
        """
        获取单个物体
        
        Args:
            object_id: 物体标识符
        
        Returns:
            标准化的物体数据
        """
        try:
            # 1. 从缓存尝试
            cached = self.object_cache.load_object_info(object_id)
            if cached and "data" in cached:
                standardized = self._standardize_object_data(cached["data"])
                if standardized:
                    return {
                        "success": True,
                        "object": standardized,
                        "source": "cache",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            # 2. 从场景尝试
            if self.client:
                scene_objects = self._get_objects_from_scene()
                for obj in scene_objects:
                    if obj.get("id") == object_id:
                        standardized = self._standardize_object_data(obj)
                        if standardized:
                            # 保存到缓存
                            self.object_cache.save_object_info(
                                object_id=object_id,
                                object_data=standardized,
                                object_type=standardized.get("type", "unknown")
                            )
                            
                            return {
                                "success": True,
                                "object": standardized,
                                "source": "scene",
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
            
            return {
                "success": False,
                "error": f"未找到物体: {object_id}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    # ========== 私有方法：检测实现 ==========
    
    def _get_cached_objects(self, scene_id: Optional[str] = None) -> List[Dict]:
        """从缓存获取物体"""
        objects = []
        
        try:
            if scene_id:
                # 获取场景缓存
                scene_data = self.object_cache.load_scene_objects(scene_id, "workspace")
                if scene_data and "objects" in scene_data:
                    objects = scene_data["objects"]
            else:
                # 获取所有缓存物体
                objects = self._get_all_cached_objects()
            
            print(f"[缓存] 加载了 {len(objects)} 个缓存物体")
            
        except Exception as e:
            print(f"[缓存] 加载失败: {e}")
        
        return objects
    
    def _perform_detection(self, scene_id: Optional[str] = None) -> List[Dict]:
        """
        执行物体检测
        
        注意：这里是模拟检测，实际应该集成：
        1. 点云处理
        2. 图像识别
        3. 传感器融合
        """
        detected = []
        
        try:            # 模拟检测：从PlanningScene获取
            if self.client:
                scene_objects = self._get_objects_from_scene()
                detected.extend(scene_objects)
            
            # 如果没有客户端，生成测试数据
            if not detected:
                detected = self._generate_test_objects()
            
            print(f"[检测] 检测到 {len(detected)} 个物体")
            
        except Exception as e:
            print(f"[检测] 异常: {e}")
            detected = []
        
        return detected
    
    def _get_objects_from_scene(self) -> List[Dict]:
        """从PlanningScene获取物体"""
        objects = []
        
        try:
            if self.client and hasattr(self.client, 'get_collision_objects'):
                obj_ids = self.client.get_collision_objects()
                
                for obj_id in obj_ids:
                    # 获取物体详细信息
                    obj_data = self._extract_object_info(obj_id)
                    if obj_data:
                        objects.append(obj_data)
            
        except Exception as e:
            print(f"[场景获取] 异常: {e}")
        
        return objects
    def _extract_object_info(self, object_id: str) -> Optional[Dict]:
        """从场景提取物体信息 - 修复版：优先使用缓存"""
        try:
            # 1. 首先尝试从缓存获取完整信息
            if hasattr(self, 'object_cache') and self.object_cache:
                cached_data = self._get_complete_object_from_cache(object_id)
                if cached_data:
                    print(f"[信息提取] 使用缓存数据: {object_id}")
                    return cached_data
            
            # 2. 尝试从场景获取真实信息
            scene_data = self._get_real_info_from_scene(object_id)
            if scene_data:
                print(f"[信息提取] 使用场景数据: {object_id}")
                return scene_data
            
            # 3. 如果都没有，但缓存中有同名物体，使用最近的缓存
            cached_objects = self._get_all_cached_objects()
            for obj in cached_objects:
                if obj.get("id") == object_id:
                    print(f"[信息提取] 使用历史缓存: {object_id}")
                    return obj
            
            # 4. 实在没有，返回None，不要返回默认值！
            print(f"[信息提取] 警告：无法获取物体 {object_id} 的信息")
            return None
            
        except Exception as e:
            print(f"[信息提取] 错误 {object_id}: {e}")
            return None

    def _get_complete_object_from_cache(self, object_id: str) -> Optional[Dict]:
        """从缓存获取完整物体信息"""
        try:
            # 尝试从缓存管理器获取
            if hasattr(self.object_cache, 'load_object_info'):
                cached = self.object_cache.load_object_info(object_id, "box")
                if cached and "data" in cached:
                    return cached["data"]
            
            # 或者直接从缓存文件读取
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
            cache_dir = os.path.join(cache_root, "core", "objects")
            
            import glob, json
            # 查找所有相关缓存文件
            patterns = [
                f"object_*_{object_id}.json",  # 如果文件名包含ID
                f"object_*.json"  # 所有文件，逐个检查
            ]
            
            for pattern in patterns:
                for cache_file in glob.glob(os.path.join(cache_dir, pattern)):
                    try:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                        
                        # 提取物体数据
                        if "data" in data:
                            layer1 = data["data"]
                            if "data" in layer1:
                                obj_data = layer1["data"]
                                if obj_data.get("id") == object_id:
                                    print(f"[缓存读取] 找到物体 {object_id} 在 {os.path.basename(cache_file)}")
                                    return obj_data
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"[缓存读取] 错误: {e}")
            return None    

    # ========== 数据标准化 ==========
    def _standardize_object_data(self, raw_data: Dict) -> Dict:
        """标准化物体数据 - 修复版：不生成unknown"""
        if not raw_data:
            return {}
        
        # 如果原始数据已经是"unknown"，直接返回
        if raw_data.get("type") == "unknown":
            print(f"[标准化] 警告：收到unknown类型数据，跳过标准化")
            return {}  # 返回空，让上层处理
        
        # 只复制已有的字段，不补充默认值
        standardized = {}
        for key in ["id", "type", "dimensions", "position", "orientation", 
                    "operation", "frame_id", "primitive_type", "cached_at"]:
            if key in raw_data:
                standardized[key] = raw_data[key]
        
        # 如果必要字段不全，返回空
        required = ["id", "type", "dimensions"]
        if not all(k in standardized for k in required):
            print(f"[标准化] 错误：数据不完整，缺少: {[k for k in required if k not in standardized]}")
            return {}
        
        # 添加元数据
        standardized["standardized_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        standardized["schema"] = "object_detector_v1"
        
        return standardized    
    def _cache_detected_objects(self, objects: List[Dict], scene_id: Optional[str] = None):
        """缓存检测到的物体 - 修复版：只保存完整数据"""
        saved_count = 0
        skipped_count = 0
        
        for obj in objects:
            # 严格检查数据完整性
            if not obj:
                skipped_count += 1
                continue
                
            # 必须有这些字段
            required = ["id", "type", "dimensions"]
            if not all(k in obj for k in required):
                print(f"[缓存] 跳过：物体 {obj.get('id', '未知')} 缺少必要字段")
                skipped_count += 1
                continue
            
            # 类型不能是unknown
            if obj["type"] == "unknown":
                print(f"[缓存] 跳过：物体 {obj['id']} 类型为unknown")
                skipped_count += 1
                continue
            
            # 保存到缓存
            try:
                if hasattr(self, 'object_cache') and self.object_cache:
                    self.object_cache.save_object_info(
                        object_id=obj["id"],
                        object_data=obj,
                        object_type=obj["type"]
                    )
                    saved_count += 1
                    print(f"[缓存] 保存完整物体: {obj['id']} ({obj['type']})")
            except Exception as e:
                print(f"[缓存] 保存失败 {obj['id']}: {e}")
                skipped_count += 1
        
        print(f"[缓存] 完成: 保存 {saved_count} 个，跳过 {skipped_count} 个不完整物体")

    # ========== 辅助方法 ==========

    def _get_all_cached_objects(self) -> List[Dict]:
        """完整实现：读取缓存目录中的所有物体"""
        import glob
        import os
        
        objects = []
        
        try:
            # 获取缓存根目录
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
            cache_dir = os.path.join(cache_root, "core", "objects")
            
            if not os.path.exists(cache_dir):
                print(f"[缓存] 缓存目录不存在: {cache_dir}")
                return objects
            
            # 查找所有物体缓存文件
            pattern = os.path.join(cache_dir, "object_*.json")
            cache_files = glob.glob(pattern)
            
            print(f"[缓存] 找到 {len(cache_files)} 个缓存文件")
            
            for filepath in cache_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 调试：打印文件结构
                    filename = os.path.basename(filepath)
                    print(f"\n[缓存] 解析文件: {filename}")
                    
                    # 根据缓存文件格式解析
                    if "data" in data:
                        layer1 = data["data"]
                        if isinstance(layer1, dict):
                            # 现在检查正确的结构
                            if "data" in layer1:
                                # 这是真正的物体数据
                                obj_data = layer1["data"]
                                print(f"  ✓ 找到物体数据层")
                            else:
                                # 可能是其他格式，尝试直接使用layer1
                                obj_data = layer1
                                print(f"  ℹ️ 使用第一层作为物体数据")
                        else:
                            obj_data = data["data"]
                            print(f"  ℹ️ 直接使用data字段")
                    else:
                        # 格式2：直接是物体数据
                        obj_data = data
                        print(f"  ℹ️ 直接使用文件内容")                # 确保有必要的字段
                    if not isinstance(obj_data, dict):
                        print(f"  ✗ 物体数据不是字典: {type(obj_data)}")
                        continue
                    
                    # 如果没有id，尝试从数据结构中提取
                    if "id" not in obj_data:
                        # 从文件名推断
                        if filename.startswith("object_"):
                            parts = filename.split("_")
                            if len(parts) >= 2:
                                # 尝试从object_box_abc123.json提取
                                obj_type = parts[1] if len(parts) > 1 else "unknown"
                                obj_hash = parts[2].split('.')[0] if len(parts) > 2 else "unknown"
                                obj_data["id"] = f"{obj_type}_{obj_hash}"
                        else:
                            # 从数据结构中查找
                            for key in ["object_id", "name", "label"]:
                                if key in obj_data:
                                    obj_data["id"] = obj_data[key]
                                    break
                    
                    # 如果没有type，尝试推断
                    if "type" not in obj_data:
                        # 从文件名推断
                        if filename.startswith("object_"):
                            parts = filename.split("_")
                            if len(parts) >= 2:
                                obj_data["type"] = parts[1]  # box, cylinder, sphere等
                        # 或者从数据结构中查找
                        elif "object_type" in obj_data:
                            obj_data["type"] = obj_data["object_type"]
                        elif "primitive_type" in obj_data:
                            # 根据primitive_type映射
                            type_map = {1: "box", 2: "sphere", 3: "cylinder", 4: "cone"}
                            obj_data["type"] = type_map.get(obj_data["primitive_type"], "unknown")
                    
                    # 确保有必要的字段
                    if "id" not in obj_data:
                        print(f"  ✗ 跳过：没有ID的物体数据")
                        continue
                    
                    # 添加文件路径信息
                    obj_data["cache_file"] = filepath
                    obj_data["source"] = "unified_cache"
                    
                    objects.append(obj_data)
                    
                    print(f"  ✓ 加载物体: {obj_data.get('id')} (类型: {obj_data.get('type', 'unknown')})")
                    
                except json.JSONDecodeError as e:
                    print(f"[缓存] JSON解析失败 {filepath}: {e}")
                except Exception as e:
                    print(f"[缓存] 读取失败 {filepath}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"\n[缓存] 成功加载 {len(objects)} 个物体")
            
        except Exception as e:
            print(f"[缓存] 扫描缓存目录失败: {e}")
            import traceback
            traceback.print_exc()
        
        return objects
    def detect_from_cache(self, scene_id=None):
        """从缓存检测物体 - 完整版"""
        try:
            # 获取缓存目录（通过CachePathTools）
            from ps_cache.cache_manager import CachePathTools
            cache_root = CachePathTools.get_cache_root()
            cache_dir = cache_root / "core" / "objects"
            
            objects = self._get_all_cached_objects()
            
            return {
                "success": True,
                "source": "unified_cache",
                "count": len(objects),
                "objects": objects,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cache_dir": str(cache_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }   

    def get_cache_stats(self):
        """获取缓存统计信息 - 返回字典"""
        try:
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
            cache_dir = os.path.join(cache_root, "core", "objects")
            
            import os
            if os.path.exists(cache_dir):
                import glob
                files = glob.glob(os.path.join(cache_dir, "*.json"))
                
                return {
                    "success": True,
                    "stats": {
                        "cache_dir": cache_dir,
                        "file_count": len(files),
                        "files": files[:10] if files else []  # 最多显示10个文件
                    },
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    "success": False,
                    "error": f"缓存目录不存在: {cache_dir}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    def _generate_test_objects(self) -> List[Dict]:
        """生成测试物体（用于开发）"""
        return [
            {
                "id": "test_cube_1",
                "type": "box",
                "position": [0.5, 0.0, 0.2],
                "dimensions": [0.1, 0.1, 0.1],
                "orientation": [0.0, 0.0, 0.0, 1.0],
                "confidence": 0.95,
                "source": "simulation"
            },
            {
                "id": "test_sphere_1",
                "type": "sphere",
                "position": [0.3, 0.2, 0.3],
                "dimensions": [0.08],  # 半径
                "orientation": [0.0, 0.0, 0.0, 1.0],
                "confidence": 0.90,
                "source": "simulation"
            }
        ]
    
    # ========== 工具方法 ==========
    
    def get_detector_info(self) -> Dict:
        """获取检测器信息"""
        return {
            "name": "PureObjectDetector",
            "version": "1.0",
            "mode": self.mode,
            "schema": self.object_schema,
            "dependencies": {
                "cache": "available" if HAS_DEPENDENCIES else "unavailable",
                "scene_client": "available" if self.client else "unavailable",
                "object_manager": "available" if self.object_manager else "unavailable"
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def set_mode(self, mode: str):
        """设置检测模式"""
        valid_modes = ["hybrid", "cache_only", "detection_only"]
        if mode in valid_modes:
            self.mode = mode
            print(f"[检测器] 模式设置为: {mode}")
        else:
            print(f"[检测器] 无效模式: {mode}，有效模式: {valid_modes}")

# ... 类的定义 ...

# ========== 文件结尾 ==========
if __name__ == "__main__":
    # 这里可以是空的，或者只包含：
    print("请使用独立的命令行脚本: object_detection/scripts/ros-detect-objects")
    sys.exit(0)
