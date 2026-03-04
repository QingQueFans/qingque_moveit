#!/usr/bin/env python3
"""
接触分析器 - 分析物体间的接触信息（使用缓存数据）
"""
from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import os
import json

class ContactAnalyzer:
    """接触分析器（使用缓存数据）"""
    
    def __init__(self, scene_client):
        """
        初始化接触分析器
        
        Args:
            scene_client: PlanningSceneClient 实例
        """
        self.client = scene_client
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            print(f"[缓存] 接触分析器: 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            print(f"[缓存] 接触分析器: 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[缓存] 接触分析器: 加载缓存失败: {e}")
            return {}
    
    def analyze_contacts(self, object1_id: str, object2_id: str) -> Dict[str, Any]:
        """
        分析两个物体间的接触（使用缓存数据）
        
        Args:
            object1_id: 第一个物体ID
            object2_id: 第二个物体ID
            
        Returns:
            Dict: 接触分析结果
        """
        try:
            # 从缓存获取物体数据
            cache = self._load_cache()
            
            if object1_id not in cache:
                return {"error": f"找不到物体: {object1_id}", "source": "cache"}
            if object2_id not in cache:
                return {"error": f"找不到物体: {object2_id}", "source": "cache"}
            
            obj1_data = cache[object1_id]
            obj2_data = cache[object2_id]            # 提取位置和尺寸
            pos1 = self._extract_position(obj1_data)
            pos2 = self._extract_position(obj2_data)
            size1 = self._extract_size(obj1_data)
            size2 = self._extract_size(obj2_data)
            
            print(f"[接触分析] 分析 {object1_id} ↔ {object2_id}")
            
            # 检查是否接触
            contact, contact_info = self._check_contact(pos1, size1, pos2, size2)
            
            if not contact:
                return {
                    "contact": False,
                    "object1": object1_id,
                    "object2": object2_id,
                    "message": "物体未接触",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "cache"
                }
            
            result = {
                "contact": True,
                "object1": object1_id,
                "object2": object2_id,
                "contact_type": contact_info["type"],
                "estimated_contact_area": contact_info["area"],
                "force_direction": contact_info["force_direction"],
                "penetration_depth": contact_info["penetration"],
                "contact_center": contact_info["center"],
                "overlaps": contact_info.get("overlaps", {}),
                "position1": pos1,
                "position2": pos2,
                "size1": size1,
                "size2": size2,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "analysis": self._generate_contact_analysis(contact_info["type"], contact_info),
                "source": "cache"
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "source": "cache"}
    
    def _check_contact(self, pos1: List[float], size1: List[float], 
                      pos2: List[float], size2: List[float]) -> Tuple[bool, Dict[str, Any]]:
        """
        检查两个物体的接触情况
        
        Returns:
            Tuple[bool, Dict]: (是否接触, 接触详细信息)
        """
        # 计算各个轴上的重叠
        overlap_x = max(0, (size1[0]/2 + size2[0]/2) - abs(pos1[0] - pos2[0]))
        overlap_y = max(0, (size1[1]/2 + size2[1]/2) - abs(pos1[1] - pos2[1]))
        overlap_z = max(0, (size1[2]/2 + size2[2]/2) - abs(pos1[2] - pos2[2]))
        
        # 是否接触（三个轴都有重叠）
        contact = overlap_x > 0 and overlap_y > 0 and overlap_z > 0
        
        if not contact:
            return False, {
                "type": "no_contact",
                "area": 0.0,
                "force_direction": [0.0, 0.0, 0.0],
                "penetration": 0.0,
                "center": [0.0, 0.0, 0.0]
            }
        
        # 确定接触类型
        contact_type = self._determine_contact_type(overlap_x, overlap_y, overlap_z)        # 计算接触面积（近似）
        contact_area = self._estimate_contact_area(contact_type, overlap_x, overlap_y, overlap_z)
        
        # 计算接触中心
        contact_center = [
            (min(pos1[0] + size1[0]/2, pos2[0] + size2[0]/2) + max(pos1[0] - size1[0]/2, pos2[0] - size2[0]/2)) / 2,
            (min(pos1[1] + size1[1]/2, pos2[1] + size2[1]/2) + max(pos1[1] - size1[1]/2, pos2[1] - size2[1]/2)) / 2,
            (min(pos1[2] + size1[2]/2, pos2[2] + size2[2]/2) + max(pos1[2] - size1[2]/2, pos2[2] - size2[2]/2)) / 2
        ]
        
        # 计算力方向（从物体1指向物体2，垂直于接触面）
        force_dir = self._calculate_force_direction(contact_type, pos1, pos2)
        
        # 计算穿透深度（最小重叠量）
        penetration = min(overlap_x, overlap_y, overlap_z)
        
        return True, {
            "type": contact_type,
            "area": contact_area,
            "force_direction": force_dir,
            "penetration": penetration,
            "center": contact_center,
            "overlaps": {"x": overlap_x, "y": overlap_y, "z": overlap_z}
        }
    
    def _determine_contact_type(self, overlap_x: float, overlap_y: float, overlap_z: float) -> str:
        """确定接触类型"""
        # 找出最小重叠量
        overlaps = [overlap_x, overlap_y, overlap_z]
        min_overlap = min(overlaps)
        
        # 如果最小重叠接近0，可能是面/边/角接触
        if min_overlap < 0.001:
            zero_count = sum(1 for ov in overlaps if ov < 0.001)
            
            if zero_count == 1:
                # 一个轴重叠接近0：面接触
                if overlap_x < 0.001:
                    return "x_face_contact"  # X轴面接触
                elif overlap_y < 0.001:
                    return "y_face_contact"  # Y轴面接触
                else:
                    return "z_face_contact"  # Z轴面接触
            elif zero_count == 2:
                # 两个轴重叠接近0：边接触
                if overlap_x > 0.001:
                    return "yz_edge_contact"  # YZ边接触
                elif overlap_y > 0.001:
                    return "xz_edge_contact"  # XZ边接触
                else:
                    return "xy_edge_contact"  # XY边接触
            elif zero_count == 3:
                # 三个轴重叠都接近0：角接触
                return "corner_contact"
        
        # 三个轴都有显著重叠：体接触
        return "volume_contact"
    
    def _estimate_contact_area(self, contact_type: str, overlap_x: float, 
                              overlap_y: float, overlap_z: float) -> float:
        """估计接触面积"""
        if contact_type == "x_face_contact":
            return overlap_y * overlap_z  # YZ平面面积
        elif contact_type == "y_face_contact":
            return overlap_x * overlap_z  # XZ平面面积
        elif contact_type == "z_face_contact":
            return overlap_x * overlap_y  # XY平面面积
        elif "edge" in contact_type:            # 边接触：面积较小
            return max(overlap_x, overlap_y, overlap_z) * 0.01  # 近似
        elif contact_type == "corner_contact":
            return 0.0001  # 很小
        else:  # volume_contact
            # 体接触：取最大可能接触面积
            return max(overlap_x * overlap_y, overlap_x * overlap_z, overlap_y * overlap_z)
    
    def _calculate_force_direction(self, contact_type: str, pos1: List[float], 
                                  pos2: List[float]) -> List[float]:
        """计算力方向"""
        # 基础方向：从物体1指向物体2
        direction = [pos2[0] - pos1[0], pos2[1] - pos1[1], pos2[2] - pos1[2]]
        
        # 归一化
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = [d/norm for d in direction]
        
        # 根据接触类型调整
        if contact_type == "x_face_contact":
            return [-1.0 if direction[0] > 0 else 1.0, 0.0, 0.0]
        elif contact_type == "y_face_contact":
            return [0.0, -1.0 if direction[1] > 0 else 1.0, 0.0]
        elif contact_type == "z_face_contact":
            return [0.0, 0.0, -1.0 if direction[2] > 0 else 1.0]
        else:
            return direction
    
    def _generate_contact_analysis(self, contact_type: str, contact_info: Dict[str, Any]) -> str:
        """生成接触分析文本"""
        analyses = {
            "volume_contact": "物体体接触，三个轴都有重叠，接触面积最大。",
            "x_face_contact": "物体X轴面接触，主要接触面垂直于X轴。",
            "y_face_contact": "物体Y轴面接触，主要接触面垂直于Y轴。",
            "z_face_contact": "物体Z轴面接触，主要接触面垂直于Z轴。",
            "xy_edge_contact": "物体XY边接触，接触线平行于Z轴。",
            "xz_edge_contact": "物体XZ边接触，接触线平行于Y轴。",
            "yz_edge_contact": "物体YZ边接触，接触线平行于X轴。",
            "corner_contact": "物体角接触，接触点非常小。",
            "no_contact": "物体未接触。"
        }
        
        base_analysis = analyses.get(contact_type, "未知接触类型。")
        
        # 添加具体信息
        if "area" in contact_info:
            base_analysis += f" 估计接触面积: {contact_info['area']:.6f} m²."
        if "penetration" in contact_info:
            base_analysis += f" 穿透深度: {contact_info['penetration']:.4f} m."
        
        return base_analysis
    
    def get_all_contacts(self) -> Dict[str, Any]:
        """
        获取场景中所有接触
        
        Returns:
            Dict: 所有接触分析结果
        """
        try:
            # 从缓存获取所有物体
            cache = self._load_cache()
            object_ids = list(cache.keys())
            
            if len(object_ids) < 2:
                return {
                    "total_objects": len(object_ids),
                    "total_contacts": 0,
                    "contacts": [],
                    "message": "物体太少，无法分析接触",
                    "source": "cache"
                }
            
            # 检查所有物体对的接触
            contacts = []
            
            for i in range(len(object_ids)):
                for j in range(i + 1, len(object_ids)):
                    obj1_id = object_ids[i]
                    obj2_id = object_ids[j]
                    
                    contact_info = self.analyze_contacts(obj1_id, obj2_id)
                    if "error" not in contact_info and contact_info.get("contact", False):
                        contacts.append(contact_info)
            
            result = {
                "total_objects": len(object_ids),
                "total_contacts": len(contacts),
                "contacts": contacts,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "cache"
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "source": "cache"}
    
    def analyze_grasp_contacts(self, gripper_object_id: str, target_object_id: str) -> Dict[str, Any]:
        """
        分析抓取接触（专门用于抓取分析）
        
        Args:
            gripper_object_id: 夹爪物体ID
            target_object_id: 目标物体ID
            
        Returns:
            Dict: 抓取接触分析
        """
        try:
            # 分析接触
            contact_info = self.analyze_contacts(gripper_object_id, target_object_id)
            
            if "error" in contact_info:
                return contact_info
            
            if not contact_info["contact"]:
                return {
                    **contact_info,
                    "grasp_quality": 0.0,
                    "grasp_stable": False,
                    "recommendation": "未接触，无法抓取"
                }            # 评估抓取质量
            grasp_quality = self._evaluate_grasp_quality(contact_info)
            
            # 判断抓取稳定性
            grasp_stable = grasp_quality > 0.5  # 简单阈值
            
            # 生成建议
            recommendation = self._generate_grasp_recommendation(contact_info, grasp_quality)
            
            result = {
                **contact_info,
                "grasp_quality": float(grasp_quality),
                "grasp_stable": grasp_stable,
                "recommendation": recommendation,
                "analysis_type": "grasp_contact",
                "source": "cache"
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "source": "cache"}
    
    def _evaluate_grasp_quality(self, contact_info: Dict[str, Any]) -> float:
        """评估抓取质量（0-1）"""
        quality = 0.0
        
        # 1. 基于接触类型
        contact_type_weights = {
            "volume_contact": 0.9,
            "x_face_contact": 0.8,
            "y_face_contact": 0.8,
            "z_face_contact": 0.8,
            "xy_edge_contact": 0.5,
            "xz_edge_contact": 0.5,
            "yz_edge_contact": 0.5,
            "corner_contact": 0.2,
            "no_contact": 0.0
        }
        
        contact_type = contact_info.get("contact_type", "no_contact")
        quality += contact_type_weights.get(contact_type, 0.3) * 0.4
        
        # 2. 基于接触面积
        contact_area = contact_info.get("estimated_contact_area", 0.0)
        area_score = min(contact_area * 100, 1.0)  # 缩放
        quality += area_score * 0.3
        
        # 3. 基于力方向（简化：如果主要是垂直方向则较好）
        force_dir = contact_info.get("force_direction", [0, 0, 1])
        vertical_component = abs(force_dir[2])
        direction_score = vertical_component
        quality += direction_score * 0.3
        
        return min(quality, 1.0)
    
    def _generate_grasp_recommendation(self, contact_info: Dict[str, Any], grasp_quality: float) -> str:
        """生成抓取建议"""
        if grasp_quality > 0.7:
            return "抓取质量良好，可以安全抓取。"
        elif grasp_quality > 0.4:
            return "抓取质量一般，建议调整抓取位置或增加接触面积。"
        else:
            return "抓取质量较差，不建议抓取或需要显著调整。"
    
    def _extract_position(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取位置"""
        if 'position' in obj_data:
            return obj_data['position']
        elif 'pose' in obj_data and 'position' in obj_data['pose']:
            return obj_data['pose']['position']
        else:
            return [0.0, 0.0, 0.0]
    
    def _extract_size(self, obj_data: Dict) -> List[float]:
        """从缓存数据提取尺寸"""
        if 'dimensions' in obj_data:
            return obj_data['dimensions']
        elif 'size' in obj_data:
            return obj_data['size']
        else:
            return [0.1, 0.1, 0.1]

