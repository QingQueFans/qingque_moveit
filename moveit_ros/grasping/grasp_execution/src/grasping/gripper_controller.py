#!/usr/bin/env python3
"""
夹爪控制器 - Grasp Execution 子模块
基于感知模块提供的物体信息，计算夹爪参数
"""

import sys
import os
import math
from typing import Dict, List, Optional, Tuple
import numpy as np

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
GRASPING_ROOT = os.path.dirname(MODULE_ROOT)
PROJECT_ROOT = os.path.dirname(os.path.dirname(GRASPING_ROOT))



# 添加缓存模块路径
CACHE_SRC = os.path.join(PROJECT_ROOT, 'moveit_core', 'cache_manager', 'src')
sys.path.insert(0, CACHE_SRC)

try:
    
    from ps_cache import CachePathTools
    HAS_DEPENDENCIES = True
    print("[夹爪控制器] ✓ 依赖导入成功")
except ImportError as e:
    print(f"[夹爪控制器] ✗ 依赖导入失败: {e}")
    HAS_DEPENDENCIES = False


class GripperController:
    """
    夹爪控制器 - 基于物体信息计算夹爪参数
    
    职责：
    1. 从感知模块获取物体信息
    2. 计算夹爪张开宽度、夹紧力、抓取姿态
    3. 提供抓取参数建议
    4. 管理夹爪状态
    """
    
    def __init__(self):
        """
        初始化夹爪控制器
        
        Args:
            detector: 可选的感知检测器实例
        """
        if not HAS_DEPENDENCIES:
            raise ImportError("缺少必要依赖")
        
        
        
        # 夹爪配置
        self.gripper_config = {
            "min_width": 0.0,      # 最小张开宽度 [m]
            "max_width": 0.1,      # 最大张开宽度 [m]
            "min_force": 1.0,      # 最小夹紧力 [N]
            "max_force": 50.0,     # 最大夹紧力 [N]
            "finger_length": 0.05, # 夹爪手指长度 [m]
            "finger_thickness": 0.01,  # 夹爪厚度 [m]
        }
        
        # 抓取策略配置
        self.grasp_strategies = {
            "box": {
                "default": "side_grasp",
                "options": ["side_grasp", "top_grasp", "corner_grasp"]
            },
            "cylinder": {
                "default": "side_grasp", 
                "options": ["side_grasp", "top_grasp"]
            },
            "sphere": {
                "default": "encompassing_grasp",
                "options": ["encompassing_grasp", "pinch_grasp"]
            }
        }
        
        # 夹爪状态
        self.current_width = 0.0
        self.current_force = 0.0
        self.is_grasping = False
        
        print("[夹爪控制器] 初始化完成")
    
    # ========== 核心接口 ==========
    
    def calculate_grasp_parameters(self, 
                                  object_info: Dict,
                                  strategy: str = "auto") -> Dict:
        """
        基于物体信息计算抓取参数
        
        Args:
            object_info: 物体信息字典
                {
                    "type": "box/cylinder/sphere",
                    "dimensions": [x, y, z] 或 [radius, height],
                    "position": [x, y, z],
                    "orientation": [qx, qy, qz, qw]
                }
            strategy: 抓取策略 ("auto" 或具体策略)
            
        Returns:
            抓取参数字典
        """
        try:
            obj_type = object_info.get("type", "unknown")
            dimensions = object_info.get("dimensions", [])
            
            if not dimensions:
                raise ValueError("物体尺寸信息缺失")
            
            # 确定抓取策略
            if strategy == "auto":
                grasp_strategy = self._select_grasp_strategy(obj_type, dimensions)
            else:
                grasp_strategy = strategy
            
            # 计算夹爪参数
            grasp_params = self._compute_grasp_parameters(
                obj_type, dimensions, grasp_strategy
            )            # 计算抓取点
            grasp_points = self._compute_grasp_points(
                object_info, grasp_params, grasp_strategy
            )
            
            # 组装结果
            result = {
                "success": True,
                "grasp_strategy": grasp_strategy,
                "gripper_width": grasp_params["width"],
                "gripper_force": grasp_params["force"],
                "grasp_points": grasp_points,
                "approach_direction": grasp_params["approach"],
                "grasp_depth": grasp_params["depth"],
                "confidence": grasp_params["confidence"],
                "object_type": obj_type,
                "recommendation": grasp_params["recommendation"]
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "gripper_width": self.gripper_config["min_width"],
                "gripper_force": self.gripper_config["min_force"]
            }
    def get_grasp_for_object(self, object_id, strategy="auto"):
        """为指定物体计算抓取参数 - 禁用额外缓存"""
        print(f"[模式] 直接缓存读取，禁用感知模块保存")
        
        try:
            # 完全绕过感知模块，直接读取缓存文件
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects"
            
            # 查找所有 box 相关的缓存文件
            import glob, json
            cache_files = glob.glob(os.path.join(cache_root, f"object_box_*.json"))
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # 提取物体ID
                    object_data = data["data"]["data"]
                    if object_data.get("id") == object_id:
                        print(f"[缓存] 找到物体: {object_id} 在 {os.path.basename(cache_file)}")
                        
                        # 计算抓取参数
                        grasp_params = self.calculate_grasp_parameters(object_data, strategy)
                        
                        return {
                            "success": True,
                            "object_id": object_id,
                            "object_info": object_data,
                            "grasp_parameters": grasp_params,
                            "source": "direct_cache",
                            "cache_file": os.path.basename(cache_file)
                        }
                        
                except Exception as e:
                    continue
            
            return {"success": False, "error": f"缓存中未找到物体: {object_id}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
        '''
        
    def get_grasp_for_object(self, object_id, strategy="auto"):
        """为指定物体计算抓取参数"""
        print(f"[调试] 请求物体: {object_id}")
        
        try:
            # 方法1：尝试使用感知模块
            if self.detector:
                detection_result = self.detector.get_object(object_id)
                print(f"[调试] 感知模块返回: {detection_result}")
                
                if detection_result.get("success"):
                    # 提取物体信息
                    object_info = detection_result.get("object", detection_result)
                    print(f"[调试] 提取的物体信息: {object_info}")
                    
                    if object_info and "dimensions" in object_info:
                        # 信息完整，使用它
                        return self._compute_from_detection(object_info, object_id, strategy)
            
            # 方法2：感知模块失败，直接读取缓存文件
            print(f"[调试] 感知模块失败，尝试直接读取缓存...")
            cache_file = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects/object_box_34be958a.json"
            
            import json
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # 提取物体数据（根据缓存结构）
            object_data = cache_data["data"]["data"]
            print(f"[调试] 从缓存读取的物体数据: {object_data}")
            
            # 计算抓取参数
            grasp_params = self.calculate_grasp_parameters(object_data, strategy)
            
            return {
                "success": True,
                "object_id": object_id,
                "object_info": object_data,
                "grasp_parameters": grasp_params,
                "source": "direct_cache"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            '''
        # ========== 计算核心 ==========
        
    def _select_grasp_strategy(self, 
                              obj_type: str, 
                              dimensions: List[float]) -> str:
        """选择抓取策略"""
        strategies = self.grasp_strategies.get(obj_type, {})
        default = strategies.get("default", "side_grasp")
        
        if obj_type == "box":
            # 对于盒子，根据尺寸比例选择策略
            if len(dimensions) >= 3:
                L, W, H = dimensions[:3]
                aspect_ratio = max(L, W) / min(L, W)
                
                if H < min(L, W) * 0.3:
                    # 非常薄的物体，用面抓取
                    return "top_grasp"
                elif aspect_ratio > 2.0:
                    # 长条物体，用侧抓取
                    return "side_grasp"
        
        return default
    
    def _compute_grasp_parameters(self,
                                 obj_type: str,
                                 dimensions: List[float],
                                 strategy: str) -> Dict:
        """计算夹爪参数"""
        params = {
            "width": self.gripper_config["min_width"],
            "force": self.gripper_config["min_force"],
            "depth": 0.02,  # 默认抓取深度
            "approach": [0, 0, -1],  # 默认从上方接近
            "confidence": 0.7,
            "recommendation": ""
        }
        
        # 根据物体类型和策略计算
        if obj_type == "box" and len(dimensions) >= 3:
            params = self._compute_for_box(dimensions, strategy, params)
        elif obj_type == "cylinder" and len(dimensions) >= 2:
            params = self._compute_for_cylinder(dimensions, strategy, params)
        elif obj_type == "sphere" and len(dimensions) >= 1:
            params = self._compute_for_sphere(dimensions, strategy, params)
        
        # 应用夹爪物理限制
        params["width"] = self._apply_gripper_limits(params["width"])
        params["force"] = self._apply_force_limits(params["force"])
        
        return params
    
    def _compute_for_box(self, 
                        dimensions: List[float],
                        strategy: str,
                        base_params: Dict) -> Dict:
        """计算盒子的抓取参数"""
        L, W, H = dimensions[:3]
        
        if strategy == "side_grasp":
            # 侧抓取：抓最小面的中间
            min_side = min(L, W)
            grasp_width = min_side * 0.8  # 80%的宽度
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(L * W * H)
            base_params["depth"] = H * 0.3
            base_params["approach"] = [0, 1, 0] if W < L else [1, 0, 0]
            base_params["confidence"] = 0.8
            base_params["recommendation"] = f"侧向抓取，夹爪张开{grasp_width*1000:.1f}mm"
            
        elif strategy == "top_grasp":
            # 顶抓取：抓顶部
            grasp_width = min(L, W) * 0.6
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(L * W * H) * 1.2
            base_params["depth"] = min(L, W) * 0.2
            base_params["approach"] = [0, 0, -1]
            base_params["confidence"] = 0.7
            base_params["recommendation"] = f"顶部抓取，夹爪张开{grasp_width*1000:.1f}mm"
        
        return base_params
    
    def _compute_for_cylinder(self,
                             dimensions: List[float],
                             strategy: str,
                             base_params: Dict) -> Dict:
        """计算圆柱体的抓取参数"""
        radius, height = dimensions[0], dimensions[1] if len(dimensions) > 1 else dimensions[0]
        
        if strategy == "side_grasp":
            # 侧抓取
            grasp_width = 2.1 * radius  # 比直径略大
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(math.pi * radius**2 * height)
            base_params["depth"] = height * 0.3
            base_params["approach"] = [0, 1, 0]
            base_params["confidence"] = 0.85
            base_params["recommendation"] = f"侧向抓取圆柱，夹爪张开{grasp_width*1000:.1f}mm"
            
        elif strategy == "top_grasp":            # 顶抓取（适合矮圆柱）
            grasp_width = min(2.2 * radius, height * 0.8)
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(math.pi * radius**2 * height) * 1.5
            base_params["depth"] = height * 0.4
            base_params["approach"] = [0, 0, -1]
            base_params["confidence"] = 0.75
            base_params["recommendation"] = f"顶部抓取圆柱，夹爪张开{grasp_width*1000:.1f}mm"
        
        return base_params
    
    def _compute_for_sphere(self,
                           dimensions: List[float],
                           strategy: str,
                           base_params: Dict) -> Dict:
        """计算球体的抓取参数"""
        radius = dimensions[0]
        
        if strategy == "encompassing_grasp":
            # 包裹式抓取
            grasp_width = 2.1 * radius
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(4/3 * math.pi * radius**3)
            base_params["depth"] = radius * 0.5
            base_params["approach"] = [0, 0, -1]
            base_params["confidence"] = 0.9
            base_params["recommendation"] = f"包裹式抓取球体，夹爪张开{grasp_width*1000:.1f}mm"
            
        elif strategy == "pinch_grasp":
            # 捏取（适合小球）
            grasp_width = 1.5 * radius
            
            base_params["width"] = grasp_width
            base_params["force"] = self._estimate_force_from_volume(4/3 * math.pi * radius**3) * 2.0
            base_params["depth"] = radius * 0.3
            base_params["approach"] = [0, 1, 0]
            base_params["confidence"] = 0.6
            base_params["recommendation"] = f"捏取球体，夹爪张开{grasp_width*1000:.1f}mm"
        
        return base_params
    
    def _compute_grasp_points(self,
                             object_info: Dict,
                             grasp_params: Dict,
                             strategy: str) -> List[List[float]]:
        """计算抓取点位置"""
        position = object_info.get("position", [0, 0, 0])
        dimensions = object_info.get("dimensions", [])
        obj_type = object_info.get("type", "unknown")
        
        # 默认两个抓取点（夹爪的两个手指）
        if obj_type == "box" and len(dimensions) >= 3:
            L, W, H = dimensions[:3]
            if strategy == "side_grasp":
                # 在最小面的两侧
                if W < L:
                    # 抓宽度方向
                    return [
                        [position[0], position[1] - W/2, position[2]],
                        [position[0], position[1] + W/2, position[2]]
                    ]
                else:
                    # 抓长度方向
                    return [
                        [position[0] - L/2, position[1], position[2]],
                        [position[0] + L/2, position[1], position[2]]
                    ]
        
        # 默认：关于物体中心对称
        grasp_width = grasp_params["width"]
        return [
            [position[0], position[1] - grasp_width/2, position[2]],
            [position[0], position[1] + grasp_width/2, position[2]]
        ]
    
    # ========== 辅助方法 ==========
    
    def _estimate_force_from_volume(self, volume: float) -> float:
        """根据物体体积估算所需夹紧力"""        # 简单线性关系：每立方厘米需要0.1N力
        volume_cm3 = volume * 1e6  # 转换为cm³
        force = max(self.gripper_config["min_force"], 
                   min(self.gripper_config["max_force"], 
                       volume_cm3 * 0.1))
        return force
    
    def _apply_gripper_limits(self, width: float) -> float:
        """应用夹爪宽度限制"""
        return max(self.gripper_config["min_width"],
                  min(self.gripper_config["max_width"], width))
    
    def _apply_force_limits(self, force: float) -> float:
        """应用夹紧力限制"""
        return max(self.gripper_config["min_force"],
                  min(self.gripper_config["max_force"], force))
    
    def _cache_grasp_parameters(self, object_id: str, grasp_data: Dict):
        """缓存抓取参数"""
        try:
            cache_root = CachePathTools.get_cache_root()
            cache_dir = cache_root / "grasping" / "grasp_parameters"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_file = cache_dir / f"grasp_{object_id}.json"
            
            data = {
                "object_id": object_id,
                "grasp_data": grasp_data,
                "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
            
            with open(cache_file, 'w') as f:
                import json
                json.dump(data, f, indent=2)
                
            print(f"[缓存] 抓取参数已保存: {cache_file}")
            
        except Exception as e:
            print(f"[缓存] 保存抓取参数失败: {e}")
    
    def set_gripper_config(self, config: Dict):
        """设置夹爪配置"""
        self.gripper_config.update(config)
        print(f"[配置] 夹爪配置已更新")
    
    def get_status(self) -> Dict:
        """获取夹爪状态"""
        return {
            "success":True,
            "current_width": self.current_width,
            "current_force": self.current_force,
            "is_grasping": self.is_grasping,
            "config": self.gripper_config
        }

# ========== 一行调用接口 ==========

class GripperCalculator:
    """
    夹爪计算器 - 简化调用接口
    在现有 GripperController 基础上包装
    """
    
    _instance = None
    
    @classmethod
    def calculate(cls, object_input, **kwargs):
        """
        一行调用：计算夹爪参数
        
        参数：
        object_input: 可以是：
            - 字符串: 物体ID (如 "test_cube")
            - 字典: 完整的物体信息
            - 列表: 物体尺寸 [长,宽,高] 或 [半径,高]
        
        **kwargs: 可选参数
            - type: 物体类型 (如果object_input是尺寸列表)
            - strategy: 抓取策略
            - position: 物体位置
            - use_cache: 是否使用缓存
            - verbose: 详细输出
            
        返回：
            标准化结果字典
        """
        # 获取或创建单例
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        return cls._instance._calculate_internal(object_input, **kwargs)
    
    @classmethod
    def _create_instance(cls):
        """创建内部实例"""
        calculator = _GripperCalculator()
        calculator._setup()
        return calculator


class _GripperCalculator:
    """内部实现类"""
    
    def _setup(self):
        """初始化内部组件"""
        from grasping.gripper_controller import GripperController
        
        # 创建控制器实例
        self.controller = GripperController()  # ✅ 不传参数
        
        # 尝试设置 detector（可选）
        try:
            from object_detection.object_detector import PureObjectDetector
            detector = PureObjectDetector(None, None)
            detector.set_mode("cache_only")
            
            # 使用属性设置或方法设置
            self.controller.detector = detector  # 如果支持属性
            # 或者
            if hasattr(self.controller, 'set_detector'):
                self.controller.set_detector(detector)
                
            self.has_detector = True
        except ImportError:
            self.has_detector = False
        
        print("[GripperCalculator] 就绪")
    
    def _calculate_internal(self, object_input, **kwargs):
        """内部计算逻辑"""
        try:
            # 解析输入
            object_info = self._parse_input(object_input, kwargs)
            
            # 计算抓取参数
            result = self.controller.calculate_grasp_parameters(
                object_info, 
                strategy=kwargs.get("strategy", "auto")
            )
            
            # 标准化输出
            return self._standardize_output(result, object_info)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "gripper_width": 0.0,
                "gripper_force": 1.0
            }
    
    def _parse_input(self, object_input, kwargs):
        """解析多种输入格式"""
        if isinstance(object_input, str):
            # 物体ID模式
            if self.has_detector:                # 使用感知模块获取物体信息
                detection = self.controller.detector.get_object(object_input)
                if detection.get("success"):
                    return detection.get("object", {})
            
            # 感知模块不可用或失败，创建默认信息
            return {
                "id": object_input,
                "type": kwargs.get("type", "box"),
                "dimensions": kwargs.get("dimensions", [0.05, 0.05, 0.05]),
                "position": kwargs.get("position", [0.7, 0.0, 0.2])
            }
            
        elif isinstance(object_input, dict):
            # 直接物体信息
            return object_input
        elif isinstance(object_input, (list, tuple)):
            # ========== 添加验证代码 ==========
            # 1. 检查列表是否为空
            if not object_input:
                raise ValueError("尺寸列表不能为空")
            
            # 2. 检查每个尺寸是否有效
            for i, dim in enumerate(object_input):
                if not isinstance(dim, (int, float)):
                    raise ValueError(f"尺寸{i+1}必须是数值类型")
                if dim <= 0:
                    raise ValueError(f"尺寸{i+1}必须大于0，实际为: {dim}")
                if dim > 2.0:  # 2米作为上限
                    raise ValueError(f"尺寸{i+1}过大: {dim}")
            
            # 3. 验证类型参数
            obj_type = kwargs.get("type", "box")
            valid_types = ["box", "cylinder", "sphere", "cone"]
            if obj_type not in valid_types:
                raise ValueError(f"无效的物体类型: {obj_type}")
            
            # 4. 验证尺寸数量与类型匹配
            if obj_type == "box" and len(object_input) != 3:
                raise ValueError(f"盒子类型需要3个尺寸[长,宽,高]")
            elif obj_type == "cylinder" and len(object_input) != 2:
                raise ValueError(f"圆柱类型需要2个尺寸[半径,高]")
            elif obj_type == "sphere" and len(object_input) != 1:
                raise ValueError(f"球体类型需要1个尺寸[半径]")
            elif obj_type == "cone" and len(object_input) != 2:
                raise ValueError(f"圆锥类型需要2个尺寸[底面半径,高]")
            # ========== 验证结束 ==========
            
            # 原有的返回语句
            return {
                "type": obj_type,
                "dimensions": list(object_input),
                "position": kwargs.get("position", [0.7, 0.0, 0.2])
            }            
        
        
        else:
            raise ValueError(f"不支持的输入类型: {type(object_input)}")
    
    def _standardize_output(self, result, object_info):
        """标准化输出格式"""
        if not result.get("success"):
            return result
        
        # 添加额外信息
        result["object_id"] = object_info.get("id", "unknown")
        result["object_type"] = object_info.get("type", "unknown")
        
        # 确保有默认值
        result.setdefault("gripper_width", 0.0)
        result.setdefault("gripper_force", 1.0)
        result.setdefault("grasp_strategy", "unknown")
        result.setdefault("confidence", 0.0)
        
        return result


# ========== 便捷函数 ==========

def calculate_gripper(object_input, **kwargs):
    """
    全局便捷函数 - 一行调用
    
    示例：
    result = calculate_gripper("test_cube")
    result = calculate_gripper([0.05, 0.05, 0.05], type="box")
    result = calculate_gripper({"type": "box", "dimensions": [0.1, 0.1, 0.1]})
    """
    return GripperCalculator.calculate(object_input, **kwargs)


def get_gripper_width(object_input, **kwargs):
    """
    快速获取夹爪宽度（毫米）
    
    示例：
    width_mm = get_gripper_width("test_cube")
    """
    result = GripperCalculator.calculate(object_input, **kwargs)
    
    if result["success"]:
        return result["gripper_width"] * 1000  # 转换为毫米
    else:
        return 0.0


def get_gripper_params(object_input, **kwargs):
    """
    快速获取主要参数（宽度、力、策略）
    
    示例：
    width, force, strategy = get_gripper_params("test_cube")
    """
    result = GripperCalculator.calculate(object_input, **kwargs)
    
    if result["success"]:
        return (
            result["gripper_width"] * 1000,  # 毫米
            result["gripper_force"],         # 牛顿
            result["grasp_strategy"]         # 策略
        )
    else:
        return (0.0, 1.0, "error")
    
    
# ========== 测试代码 ==========
if __name__ == "__main__":
    import time
    
    print("=== 夹爪控制器测试 ===")
    
    # 创建测试物体信息
    test_objects = [
        {
            "id": "test_cube",
            "type": "box",
            "dimensions": [0.05, 0.05, 0.05],
            "position": [0.7, 0.0, 0.2],
            "orientation": [0, 0, 0, 1]
        },
        {
            "id": "test_cylinder",
            "type": "cylinder", 
            "dimensions": [0.03, 0.12],  # 半径3cm，高12cm
            "position": [0.6, 0.1, 0.2],
            "orientation": [0, 0, 0, 1]
        },
        {
            "id": "test_sphere",
            "type": "sphere",
            "dimensions": [0.04],  # 半径4cm
            "position": [0.5, -0.1, 0.2],
            "orientation": [0, 0, 0, 1]
        }
    ]
    
    # 创建控制器
    try:
        controller = GripperController()
        
        # 测试每个物体
        for obj in test_objects:
            print(f"\n=== 测试物体: {obj['id']} ===")
            
            # 计算抓取参数
            result = controller.calculate_grasp_parameters(obj)
            
            if result["success"]:
                print(f"抓取策略: {result['grasp_strategy']}")
                print(f"夹爪宽度: {result['gripper_width']*1000:.1f} mm")
                print(f"夹紧力: {result['gripper_force']:.1f} N")
                print(f"置信度: {result['confidence']:.2f}")
                print(f"建议: {result['recommendation']}")
            else:
                print(f"失败: {result['error']}")
                
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()