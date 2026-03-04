#!/usr/bin/env python3
"""
planning_context.py - 规划上下文
三级模块：抓取任务单元
完全基于一行调用接口
"""
import json
from pathlib import Path
# ========== 一行调用接口导入 ==========
# 轨迹执行器
from trajectory_execution import execute_trajectory

# 夹爪计算器
from grasping.gripper_controller import get_gripper_params

# 抓取服务器
from capability_servers_core import smart_grab, quick_grab

import time


class PlanningContext:
    """
    规划上下文 - 抓取任务的工作记忆
    """
    
    def __init__(self):
        # ===== 任务记忆 =====
        self.current_object = None
        self.current_pose = None
        self.grasp_strategy = None
        
        # ===== 计算结果 =====
        self.move_result = None
        self.grasp_result = None
        
        # ===== 状态信息 =====
        self.status = "idle"
        self.start_time = None
        self.error_message = None
        
        print("[PlanningContext] ✅ 就绪")
    
    def grasp_object(self, object_id, strategy="top_grasp", width_mm=None):
        """
        抓取场景中已存在的物体
        """
        print(f"\n🎯 [抓取任务] 物体: {object_id}")
        
        # ----- 1. 记录上下文 -----
        self.current_object = object_id
        self.grasp_strategy = strategy
        self.status = "running"
        self.start_time = time.time()
        self.error_message = None
        
        # ----- 2. 计算夹爪参数 -----
        print("1️⃣ 计算夹爪参数...")
        if width_mm:
            width = width_mm / 1000.0
            force = 30.0
            strategy_used = strategy
            print(f"   手动宽度: {width_mm}mm")
        else:
            width, force, _ = get_gripper_params(object_id)
            strategy_used = strategy
            print(f"   智能计算: 宽度={width*1000:.1f}mm, 力={force:.1f}N, 策略={strategy_used}")
        
        # ----- 3. 从物体缓存读取位姿 -----
        print("2️⃣ 读取物体位姿...")
        pose = self._get_object_pose_from_cache(object_id)
        if not pose:
            return self._error_result(f"缓存中未找到物体: {object_id}")
        
        print(f"   物体位姿: {pose[:3]}")
        
        # ----- 4. 规划器执行抓取 -----
        print("3️⃣ 规划器执行抓取...")
        self.move_result = execute_trajectory(
            {"pose": pose},  # 直接用读出的位姿
            use_cache=True,
            timeout=8.0
        )
        
        if not self.move_result.get("success", False):
            return self._error_result("移动失败", self.move_result)
        
        # ----- 5. 执行抓取 -----
        print("4️⃣ 执行抓取...")
        if width_mm:
            self.grasp_result = quick_grab(object_id, width_mm)
        else:
            self.grasp_result = smart_grab(object_id, strategy_used)
        
        if not self.grasp_result.get("success", False):
            return self._error_result("抓取失败", self.grasp_result)
        
        # ----- 6. 成功返回 -----
        self.status = "success"
        elapsed = time.time() - self.start_time
        
        result = {
            "success": True,
            "object_id": object_id,
            "grasp_width_mm": width * 1000,
            "grasp_force": force,
            "grasp_strategy": strategy_used,
            "execution_time": elapsed,
            "cache_hit": self.move_result.get("cache_info", {}).get("hit", False),
            "timestamp": self.move_result.get("timestamp", ""),
            "message": f"✅ 成功抓取物体 {object_id}"
        }
        
        print(f"\n✅ 抓取完成！耗时: {elapsed:.2f}s")
        return result

    def grasp_pose(self, pose, object_id="target", strategy="top_grasp", width_mm=50):
        """
        抓取指定位姿（不依赖物体ID）
        
        参数:
            pose: 抓取位姿 [x,y,z,qx,qy,qz,qw]
            object_id: 物体标识（仅用于日志）
            strategy: 抓取策略
            width_mm: 夹爪宽度（毫米）
        """
        print(f"\n🎯 [抓取位姿] 位置: {pose[:3]}")
        
        self.current_pose = pose
        self.current_object = object_id
        self.status = "running"
        self.start_time = time.time()
        
        # ----- 让规划器全权负责（给位姿）-----
        print("1️⃣ 规划器执行抓取...")
        self.move_result = execute_trajectory(
            {"pose": pose},  # 给位姿，让规划器自己算IK
            use_cache=True
        )
        
        if not self.move_result.get("success", False):
            return self._error_result("移动失败", self.move_result)
        
        # ----- 抓取 -----
        print("2️⃣ 执行抓取...")
        self.grasp_result = quick_grab(object_id, width_mm)
        
        self.status = "success" if self.grasp_result.get("success") else "failed"
        elapsed = time.time() - self.start_time
        
        return {
            "success": self.grasp_result.get("success", False),
            "object_id": object_id,
            "pose": pose,
            "grasp_width_mm": width_mm,
            "execution_time": elapsed,
            "timestamp": self.move_result.get("timestamp", ""),
            "message": f"✅ 成功抓取位姿物体" if self.grasp_result.get("success") else "❌ 抓取失败"
        }

    def _get_object_pose_from_cache(self, object_id):
        """直接从物体缓存文件读取位姿"""
        try:
            import json
            from pathlib import Path
            
            cache_dir = Path("/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data/core/objects")
            
            if not cache_dir.exists():
                print(f"[物体缓存] 目录不存在: {cache_dir}")
                return None
            
            for cache_file in cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    object_data = data.get('data', {}).get('data', {})
                    obj_id = object_data.get('id') or data.get('data', {}).get('object_id')
                    
                    if obj_id == object_id:
                        position = object_data.get('position', [0,0,0])
                        orientation = object_data.get('orientation', [0,0,0,1])
                        pose = position + orientation
                        print(f"[物体缓存] ✅ 找到 {object_id}: {cache_file.name}")
                        return pose
                        
                except Exception as e:
                    continue
            
            print(f"[物体缓存] ❌ 未找到物体 {object_id}")
            return None
            
        except Exception as e:
            print(f"[物体缓存] 错误: {e}")
            return None
    # ========== 状态查询 ==========
    
    def get_current_task_info(self):
        """获取当前任务状态"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            "current_object": self.current_object,
            "status": self.status,
            "elapsed_time": f"{elapsed:.1f}s",
            "grasp_strategy": self.grasp_strategy,
            "move_success": self.move_result.get("success") if self.move_result else None,
            "grasp_success": self.grasp_result.get("success") if self.grasp_result else None,
            "cache_hit": self.move_result.get("cache_info", {}).get("hit", False) if self.move_result else None,
            "error": self.error_message
        }
    
    def _error_result(self, error_message, original_result=None):
        """统一错误处理"""
        self.status = "failed"
        self.error_message = error_message
        
        result = {
            "success": False,
            "object_id": self.current_object,
            "error": error_message,
            "timestamp": original_result.get("timestamp", "") if original_result else ""
        }
        
        if original_result and "error" in original_result:
            result["original_error"] = original_result["error"]
        
        print(f"❌ 抓取失败: {error_message}")
        return result


# ========== 单例实例 ==========
_planning_context_instance = None

def get_planning_context():
    """获取全局规划上下文单例"""
    global _planning_context_instance
    if _planning_context_instance is None:
        _planning_context_instance = PlanningContext()
    return _planning_context_instance