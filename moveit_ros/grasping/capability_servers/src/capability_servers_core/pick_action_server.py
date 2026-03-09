#!/usr/bin/env python3
"""
抓取动作服务器完整版 - PickActionServer
包含：抓取、释放、连接物体 + 一行调用接口
"""

import sys
import os
import time
from typing import Dict, List, Optional

sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

# ========== 路径设置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)

try:
    # 【修改】用 ObjectManager 替换 PlanningSceneClient
    from ps_objects.object_manager import ObjectManager
    from gripper_controller_manager import GripperControllerManager
    
    HAS_DEPENDENCIES = True
    print("✓ 成功导入所有依赖")
    
except ImportError as e:
    print(f"[警告] 导入依赖失败: {e}")
    HAS_DEPENDENCIES = False


class PickActionServer:
    """
    抓取动作服务器完整版
    包含：抓取、释放、连接/断开物体功能
    """
    
    def __init__(self, object_manager=None):
        """初始化 - 必须接收object_manager用于物体连接"""
        if not HAS_DEPENDENCIES:
            raise ImportError("依赖导入失败")
        
        # 【修改】用 ObjectManager 代替 PlanningSceneClient
        if object_manager is None:
            from ps_objects.object_manager import ObjectManager
            self.object_manager = ObjectManager()
        else:
            self.object_manager = object_manager
        
        # 控制器（延迟初始化）
        self.gripper_controller = None
        
        # 机器人配置
        self.robot_config = {
            "name": "panda",
            "gripper_link": "panda_hand",
        }
        
        # 当前连接的物体
        self.attached_object = None
        
        print(f"[抓取服务器] 初始化完成")
    
    # ========== 控制器初始化 ==========
    
    def _init_controller(self):
        """初始化夹爪控制器"""
        if self.gripper_controller is None:
            try:
                self.gripper_controller = GripperControllerManager()
                print("[抓取服务器] 夹爪控制器就绪")
            except Exception as e:
                print(f"[抓取服务器] 夹爪控制器失败: {e}")
    
    def _check_controller(self) -> bool:
        """检查夹爪控制器是否可用"""
        self._init_controller()
        return self.gripper_controller is not None
    
    # ========== 核心抓取方法 ==========
    
    def grab(self, object_id: str, width: Optional[float] = None, effort: float = 30.0, 
            auto_calculate: bool = False) -> Dict:
        """抓取物体 - 支持智能计算宽度"""
        start_time = time.time()
        
        try:
            if not self._check_controller():
                return {
                    "success": False,
                    "error": "夹爪控制器不可用",
                    "operation": "grab"
                }
            
            print(f"🤖 开始抓取物体: {object_id}")
            
            # 确定夹爪宽度
            if width is None:
                if auto_calculate:
                    width = self._calculate_grasp_width(object_id)
                    print(f"📊 智能计算宽度: {width*1000:.1f}mm")
                else:
                    width = 0.06
                    print(f"📏 使用默认宽度: {width*1000:.1f}mm")
            else:
                print(f"📏 使用指定宽度: {width*1000:.1f}mm")
            
            print(f"💪 夹紧力: {effort}N")
            
            # 控制夹爪闭合
            print("🔧 控制夹爪闭合...")
            grasp_success = self._control_gripper(target_width=width, effort=effort)
            if not grasp_success:
                return {
                    "success": False,
                    "error": "夹爪控制失败",
                    "operation": "grab"
                }
            
            # 【修改】用 ObjectManager 连接物体
            print("🔗 连接物体到夹爪...")
            attach_success = self.attach_object(object_id)
            if not attach_success:
                return {
                    "success": False, 
                    "error": "物体连接失败",
                    "operation": "grab"
                }
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "operation": "grab",
                "object_id": object_id,
                "grasp_width": width,
                "grasp_effort": effort,
                "execution_time": elapsed_time,
                "timestamp": self._get_timestamp(),
                "message": f"成功抓取物体 {object_id}",
                "width_source": "calculated" if (width is None and auto_calculate) else "specified"
            }
            
        except Exception as e:
            return {
                "success": False,
                "operation": "grab",
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def release(self, object_id: Optional[str] = None, width_after: float = 0.08, effort: float = 20.0) -> Dict:
        """释放物体"""
        start_time = time.time()
        
        try:
            if self.gripper_controller is None:
                self._init_controller()
                if self.gripper_controller is None:
                    return {
                        "success": False,
                        "error": "夹爪控制器不可用",
                        "operation": "release"
                    }
            
            # 确定要释放的物体
            if object_id is None:
                object_id = self.attached_object
                if object_id is None:
                    return {
                        "success": False,
                        "error": "没有物体需要释放",
                        "operation": "release"
                    }
            
            print(f"🔄 开始释放物体: {object_id}")
            
            # 【修改】用 ObjectManager 断开物体
            print("🔗 断开物体连接...")
            detach_success = self.detach_object(object_id)
            if not detach_success:
                return {
                    "success": False,
                    "error": "断开连接失败",
                    "operation": "release"
                }
            
            # 张开夹爪
            print(f"🔧 张开夹爪到 {width_after*1000:.1f}mm...")
            release_success = self._control_gripper(target_width=width_after, effort=effort)
            if not release_success:
                return {
                    "success": False,
                    "error": "夹爪张开失败",
                    "operation": "release"
                }
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "operation": "release",
                "object_id": object_id,
                "width_after": width_after,
                "effort": effort,
                "execution_time": elapsed_time,
                "timestamp": self._get_timestamp(),
                "message": f"成功释放物体 {object_id}"
            }
            
        except Exception as e:
            print(f"❌ 释放异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "operation": "release",
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    # ========== 物体连接管理 ==========
    
    def attach_object(self, object_id: str) -> bool:
        """连接物体到夹爪"""
        try:
            # 【修改】用 ObjectManager 的 attach 方法
            success = self.object_manager.attach_object(
                object_id=object_id,
                link_name=self.robot_config["gripper_link"]
            )
            
            if success:
                self.attached_object = object_id
                print(f"  ✅ 物体 {object_id} 已连接到夹爪")
                return True
            else:
                print(f"  ❌ 物体连接失败")
                return False
            
        except Exception as e:
            print(f"  ❌ 物体连接异常: {e}")
            return False
    
    def detach_object(self, object_id: str) -> bool:
        """从夹爪断开物体"""
        try:
            # 【修改】用 ObjectManager 的 detach 方法
            success = self.object_manager.detach_object(object_id)
            
            if success:
                if self.attached_object == object_id:
                    self.attached_object = None
                print(f"  ✅ 物体 {object_id} 已断开连接")
                return True
            else:
                print(f"  ❌ 断开连接失败")
                return False
            
        except Exception as e:
            print(f"  ❌ 断开连接异常: {e}")
            return False
    
    # ========== 夹爪控制 ==========
    
    def _control_gripper(self, target_width: float, effort: float = 30.0) -> bool:
        """控制夹爪张开/闭合"""
        try:
            print(f"  目标宽度: {target_width*1000:.1f}mm, 力: {effort}N")
            
            result = self.gripper_controller.grasp_sync(
                width=target_width,
                effort=effort
            )
            
            if result.get("success", False):
                print("  ✅ 夹爪控制成功")
                return True
            else:
                error_msg = result.get('error', '未知错误')
                print(f"  ❌ 夹爪控制失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"  ❌ 夹爪控制异常: {e}")
            return False
    def attach_object(self, object_id: str) -> bool:
        """连接物体到夹爪"""
        try:
            if hasattr(self.object_manager, 'moveit2') and self.object_manager.moveit2:
                self.object_manager.moveit2.attach_collision_object(
                    id=object_id,  # ← 参数名是 id！
                    link_name=self.robot_config["gripper_link"],
                    touch_links=[  # 可选的接触链
                        "panda_hand",
                        "panda_leftfinger", 
                        "panda_rightfinger"
                    ]
                )
                self.attached_object = object_id
                print(f"  ✅ 物体 {object_id} 已连接到夹爪")
                return True
            else:
                print(f"  ❌ moveit2 不可用")
                return False
                
        except Exception as e:
            print(f"  ❌ 物体连接异常: {e}")
            return False

    def detach_object(self, object_id: str) -> bool:
        """从夹爪断开物体"""
        try:
            if hasattr(self.object_manager, 'moveit2') and self.object_manager.moveit2:
                self.object_manager.moveit2.detach_collision_object(
                    id=object_id  # ← detach 应该也是 id
                )
                
                if self.attached_object == object_id:
                    self.attached_object = None
                print(f"  ✅ 物体 {object_id} 已断开连接")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"  ❌ 断开连接异常: {e}")
            return False
    # ========== 状态查询 ==========
    
    def get_status(self) -> Dict:
        """获取服务器状态"""
        return {
            "server": "pick_action_server",
            "active": True,
            "gripper_ready": self.gripper_controller is not None,
            "attached_object": self.attached_object,
            "timestamp": self._get_timestamp()
        }
    
    def is_object_attached(self, object_id: str = None) -> bool:
        """检查物体是否已连接"""
        if object_id:
            return self.attached_object == object_id
        return self.attached_object is not None
    
    def _import_gripper_calculator(self):
        """导入夹爪计算器（保持不变）"""
        import importlib.util
        
        MODULE_PATH = "/home/diyuanqiongyu/qingfu_moveit/moveit_ros/grasping/grasp_execution/src/grasping/gripper_controller.py"
        
        spec = importlib.util.spec_from_file_location("gripper_controller", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        import sys
        sys.modules['grasping.gripper_controller'] = module
        
        return module.GripperCalculator
    
    def _calculate_grasp_width(self, object_id: str) -> float:
        """智能计算夹爪宽度（保持不变）"""
        print(f"[DEBUG] 开始计算 {object_id} 的夹爪宽度")
        
        try:
            GripperCalculator = self._import_gripper_calculator()
            result = GripperCalculator.calculate(
                object_input=object_id,
                strategy="auto",
                use_cache=True
            )
            
            if result.get("success"):
                return result.get("gripper_width", 0.06)
            else:
                return 0.06
                    
        except Exception:
            return 0.06
    
    def _get_timestamp(self):
        """获取时间戳"""
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 一行调用接口（保持不变） ==========

class GraspAction:
    """抓取动作 - 完整的一行调用接口"""
    
    _instance = None
    
    @classmethod
    def grab(cls, object_id: str, width: Optional[float] = None, 
             auto_calculate: bool = False, **kwargs) -> Dict:
        if cls._instance is None:
            cls._instance = cls._create_instance()
        return cls._instance._grab_internal(object_id, width, auto_calculate, **kwargs)
    
    @classmethod
    def release(cls, object_id: Optional[str] = None, width_after: float = 0.08, **kwargs) -> Dict:
        if cls._instance is None:
            cls._instance = cls._create_instance()
        return cls._instance._release_internal(object_id, width_after, **kwargs)
    
    @classmethod
    def status(cls) -> Dict:
        if cls._instance is None:
            cls._instance = cls._create_instance()
        return cls._instance._status_internal()
    
    @classmethod
    def _create_instance(cls):
        # 【修改】用 ObjectManager 代替 PlanningSceneClient
        from ps_objects.object_manager import ObjectManager
        object_manager = ObjectManager()
        executor = _GraspActionExecutor(object_manager)
        executor._setup()
        return executor


class _GraspActionExecutor:
    """内部实现类"""
    
    def __init__(self, object_manager):
        self.object_manager = object_manager
        self.grasp_server = None
    
    def _setup(self):
        self.grasp_server = PickActionServer(self.object_manager)
        print("[GraspAction] 智能抓取接口就绪")
    
    def _grab_internal(self, object_id, width, auto_calculate, **kwargs):
        effort = kwargs.get('effort', 30.0)
        return self.grasp_server.grab(object_id, width, effort, auto_calculate)
    
    def _release_internal(self, object_id, width_after, **kwargs):
        effort = kwargs.get('effort', 20.0)
        return self.grasp_server.release(object_id, width_after, effort)
    
    def _status_internal(self):
        return self.grasp_server.get_status()


# ========== 便捷函数（保持不变） ==========

def grab_object(object_id: str, width: Optional[float] = None, **kwargs) -> Dict:
    return GraspAction.grab(object_id, width, **kwargs)

def quick_grab(object_id: str, width_mm: float = 60.0) -> Dict:
    width = width_mm / 1000.0
    return grab_object(object_id, width=width)

def smart_grab(object_id: str, strategy: str = "auto") -> Dict:
    return GraspAction.grab(object_id, width=None, auto_calculate=True)

def release_object(object_id: Optional[str] = None, width_mm: float = 80.0) -> Dict:
    width_after = width_mm / 1000.0
    return GraspAction.release(object_id, width_after)

def get_grasp_status() -> Dict:
    return GraspAction.status()


if __name__ == "__main__":
    print("=== 抓取服务器完整功能测试 ===")
    
    # 测试1: 基本抓取
    print("\n测试1: 基本抓取（默认宽度）")
    result1 = quick_grab("test_cube")
    print(f"  成功: {result1.get('success', False)}")
    
    print("\n✅ 所有测试完成！")