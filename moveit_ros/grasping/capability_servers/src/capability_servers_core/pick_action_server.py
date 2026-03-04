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
# ========== 路径设置（按照你的参考修正） ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)

try:
    from ps_core.scene_client import PlanningSceneClient
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
    
    设计原则：
    1. 必须接收scene_client用于物体连接
    2. 只负责夹爪控制和物体连接
    3. 假设机械臂已由轨迹执行器移动到合适位置
    4. 提供一行调用接口
    """
    
    def __init__(self, scene_client=None):
        """初始化 - 必须接收scene_client用于物体连接"""
        if not HAS_DEPENDENCIES:
            raise ImportError("依赖导入失败")
        
        if scene_client is None:
            scene_client = PlanningSceneClient()
        
        self.client = scene_client  # 用于attach/detach
        
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
        return self.gripper_controller is not None    # ========== 核心抓取方法 ==========
    
    def grab(self, object_id: str, width: Optional[float] = None, effort: float = 30.0, 
            auto_calculate: bool = False) -> Dict:
        """
        抓取物体 - 支持智能计算宽度
        
        Args:
            object_id: 物体ID
            width: 夹爪宽度 [m]（可选，默认智能计算）
            effort: 夹紧力 [N]
            auto_calculate: 是否自动计算宽度（当width=None时有效）
            
        Returns:
            标准化结果字典
        """
        start_time = time.time()
        
        try:
            # 1. 检查控制器
            if not self._check_controller():
                return {
                    "success": False,
                    "error": "夹爪控制器不可用",
                    "operation": "grab"
                }
            
            print(f"🤖 开始抓取物体: {object_id}")
            
            # 2. 🎯 确定夹爪宽度（关键修改！）
            if width is None:
                if auto_calculate:
                    # 智能计算宽度
                    width = self._calculate_grasp_width(object_id)
                    print(f"📊 智能计算宽度: {width*1000:.1f}mm")
                else:
                    width = 0.06  # 默认60mm
                    print(f"📏 使用默认宽度: {width*1000:.1f}mm")
            else:
                print(f"📏 使用指定宽度: {width*1000:.1f}mm")
            
            print(f"💪 夹紧力: {effort}N")
            
            # 3. 控制夹爪闭合
            print("🔧 控制夹爪闭合...")
            grasp_success = self._control_gripper(target_width=width, effort=effort)
            if not grasp_success:
                return {
                    "success": False,
                    "error": "夹爪控制失败",
                    "operation": "grab"
                }
            
            # 4. 连接物体到夹爪
            print("🔗 连接物体到夹爪...")
            attach_success = self.attach_object(object_id)
            if not attach_success:
                return {
                    "success": False, 
                    "error": "物体连接失败",
                    "operation": "grab"
                }
            
            elapsed_time = time.time() - start_time
            
            # 5. 返回成功结果
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
        """
        释放物体
        
        Args:
            object_id: 要释放的物体ID（可选，不提供则释放当前连接物体）
            width_after: 释放后夹爪宽度 [m]（默认80mm）
            effort: 夹紧力 [N]（释放时使用较小力）
            
        Returns:
            标准化结果字典
        """
        start_time = time.time()
        
        try:
            # ===== 【修复】确保夹爪控制器已初始化 =====
            if self.gripper_controller is None:
                print("  ⚠️ 夹爪控制器未初始化，尝试初始化...")
                self._init_controller()
                if self.gripper_controller is None:
                    return {
                        "success": False,
                        "error": "夹爪控制器不可用",
                        "operation": "release",
                        "timestamp": self._get_timestamp()
                    }
                print("  ✅ 夹爪控制器初始化成功")
            
            # 1. 确定要释放的物体
            if object_id is None:
                object_id = self.attached_object
                if object_id is None:
                    return {
                        "success": False,
                        "error": "没有物体需要释放",
                        "operation": "release",
                        "timestamp": self._get_timestamp()
                    }
            
            print(f"🔄 开始释放物体: {object_id}")
            
            # 2. 断开物体连接
            print("🔗 断开物体连接...")
            detach_success = self.detach_object(object_id)
            if not detach_success:
                return {
                    "success": False,
                    "error": "断开连接失败",
                    "operation": "release",
                    "timestamp": self._get_timestamp()
                }
            
            # 3. 张开夹爪
            print(f"🔧 张开夹爪到 {width_after*1000:.1f}mm...")
            release_success = self._control_gripper(target_width=width_after, effort=effort)
            if not release_success:
                return {
                    "success": False,
                    "error": "夹爪张开失败",
                    "operation": "release",
                    "timestamp": self._get_timestamp()
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
        """
        连接物体到夹爪
        
        Args:
            object_id: 物体ID
            
        Returns:
            是否成功
        """
        try:
            # 使用MoveIt的attach_object方法
            self.client.attach_object(
                object_id=object_id,
                link_name=self.robot_config["gripper_link"],
                touch_links=[
                    "panda_hand",
                    "panda_leftfinger", 
                    "panda_rightfinger",
                    "panda_finger_joint1",
                    "panda_finger_joint2"
                ]
            )
            
            self.attached_object = object_id
            print(f"  ✅ 物体 {object_id} 已连接到夹爪")
            return True
            
        except Exception as e:
            print(f"  ❌ 物体连接失败: {e}")            # 如果attach_object方法不存在，尝试其他方法
            try:
                # 备选方案：使用planning scene直接操作
                import moveit_msgs.msg
                from moveit_msgs.msg import AttachedCollisionObject
                
                attached_object = AttachedCollisionObject()
                attached_object.object.id = object_id
                attached_object.link_name = self.robot_config["gripper_link"]
                attached_object.touch_links = [
                    "panda_hand",
                    "panda_leftfinger",
                    "panda_rightfinger"
                ]
                
                # 添加到规划场景
                self.client.update_attached_objects([attached_object])
                
                self.attached_object = object_id
                print(f"  ✅ 物体 {object_id} 已连接（备选方法）")
                return True
                
            except Exception as e2:
                print(f"  ❌ 备选方法也失败: {e2}")
                return False
    
    def detach_object(self, object_id: str) -> bool:
        """
        从夹爪断开物体
        
        Args:
            object_id: 物体ID
            
        Returns:
            是否成功
        """
        try:
            # 使用MoveIt的detach_object方法
            self.client.detach_object(object_id)
            
            if self.attached_object == object_id:
                self.attached_object = None
            
            print(f"  ✅ 物体 {object_id} 已断开连接")
            return True
            
        except Exception as e:
            print(f"  ❌ 断开连接失败: {e}")
            
            # 备选方案
            try:
                # 通过清空attached objects来断开
                import moveit_msgs.msg
                from moveit_msgs.msg import AttachedCollisionObject
                
                attached_object = AttachedCollisionObject()
                attached_object.object.id = object_id
                attached_object.link_name = self.robot_config["gripper_link"]
                attached_object.object.operation = attached_object.object.REMOVE
                
                self.client.update_attached_objects([attached_object])
                
                if self.attached_object == object_id:
                    self.attached_object = None
                
                print(f"  ✅ 物体 {object_id} 已断开（备选方法）")
                return True
                
            except Exception as e2:
                print(f"  ❌ 备选方法也失败: {e2}")
                return False
    
    # ========== 夹爪控制 ==========
    
    def _control_gripper(self, target_width: float, effort: float = 30.0) -> bool:
        """控制夹爪张开/闭合"""
        try:
            print(f"  目标宽度: {target_width*1000:.1f}mm, 力: {effort}N")
            
            # 调用夹爪控制器
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
            return False    # ========== 状态查询 ==========
    
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
        """导入并设置正确的命名空间"""
        import importlib.util
        import sys
        
        MODULE_PATH = "/home/diyuanqiongyu/qingfu_moveit/moveit_ros/grasping/grasp_execution/src/grasping/gripper_controller.py"
        
        # 1. 动态导入
        spec = importlib.util.spec_from_file_location("gripper_controller", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 2. ✅ 关键：把模块添加到 sys.modules 的正确位置
        sys.modules['grasping.gripper_controller'] = module
        sys.modules['grasping'] = type(sys)('grasping')  # 创建虚拟的grasping包
        
        # 3. 确保 grasping 包有 gripper_controller 属性
        grasping_module = sys.modules['grasping']
        grasping_module.gripper_controller = module
        
        print(f"[导入] ✅ 已设置 grasping.gripper_controller 命名空间")
        return module.GripperCalculator
            
    def _calculate_grasp_width(self, object_id: str) -> float:
        """智能计算夹爪宽度"""
        print(f"[DEBUG] 开始计算 {object_id} 的夹爪宽度")
        
        try:
            # 使用导入函数
            GripperCalculator = self._import_gripper_calculator()
            print(f"[DEBUG] GripperCalculator 类: {GripperCalculator}")
            
            print(f"[DEBUG] 调用 calculate 方法...")
            result = GripperCalculator.calculate(
                object_input=object_id,
                strategy="auto",
                use_cache=True,
                verbose=True  # ← 改为True查看详细输出
            )
            
            print(f"[DEBUG] calculate 返回结果: {result}")
            
            if result.get("success"):
                grasp_width = result.get("gripper_width", 0.06)
                print(f"[DEBUG] ✅ 成功获取宽度: {grasp_width} ({grasp_width*1000}mm)")
                return grasp_width
            else:
                print(f"[DEBUG] ❌ 计算失败，使用默认值 0.06")
                return 0.06
                    
        except ImportError as e:
            print(f"[DEBUG] ❌ 导入异常: {e}")
            return 0.06
        except Exception as e:
            print(f"[DEBUG] ❌ 其他异常: {e}")
            import traceback
            traceback.print_exc()
            return 0.06
    
    def _get_timestamp(self):
        """获取时间戳"""
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 一行调用接口（完整版） ==========

class GraspAction:
    """
    抓取动作 - 完整的一行调用接口
    支持：手动指定宽度、自动计算宽度、多种抓取策略
    """
    
    _instance = None
    
    @classmethod
    def grab(cls, object_id: str, width: Optional[float] = None, 
             auto_calculate: bool = False, **kwargs) -> Dict:
        """
        一行调用：抓取物体
        
        参数：
        object_id: 物体ID（必须存在于规划场景中）
        width: 夹爪宽度 [m]（可选）
        auto_calculate: 是否自动计算宽度（当width=None时有效）
        
        **kwargs: 可选参数
            - effort: 夹紧力 [N]（默认30）
            - strategy: 抓取策略（auto/side_grasp/top_grasp，auto_calculate=True时有效）
            - scene_client: PlanningSceneClient实例（可选，会自动创建）
            
        返回：
            标准化结果字典
        """
        # 获取或创建单例
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        return cls._instance._grab_internal(object_id, width, auto_calculate, **kwargs)
    
    @classmethod
    def release(cls, object_id: Optional[str] = None, width_after: float = 0.08, **kwargs) -> Dict:
        """
        一行调用：释放物体
        
        参数：
        object_id: 要释放的物体ID（可选，不提供则释放当前连接物体）
        width_after: 释放后夹爪宽度 [m]（默认80mm）
        
        **kwargs: 可选参数
            - effort: 夹紧力 [N]（默认20）
            
        返回：
            标准化结果字典
        """
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        return cls._instance._release_internal(object_id, width_after, **kwargs)
    
    @classmethod
    def status(cls) -> Dict:
        """
        一行调用：获取状态
        
        返回：
            当前状态字典
        """
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        return cls._instance._status_internal()
    
    @classmethod
    def _create_instance(cls):
        """创建内部实例"""
        scene_client = PlanningSceneClient()
        executor = _GraspActionExecutor(scene_client)
        executor._setup()
        return executor


class _GraspActionExecutor:
    """内部实现类"""
    
    def __init__(self, scene_client):
        self.scene_client = scene_client
        self.grasp_server = None
    
    def _setup(self):
        """初始化内部组件"""
        self.grasp_server = PickActionServer(self.scene_client)
        print("[GraspAction] 智能抓取接口就绪")
    
    def _grab_internal(self, object_id, width, auto_calculate, **kwargs):
        """内部抓取逻辑"""
        effort = kwargs.get('effort', 30.0)
        return self.grasp_server.grab(object_id, width, effort, auto_calculate)
    
    def _release_internal(self, object_id, width_after, **kwargs):
        """内部释放逻辑"""
        effort = kwargs.get('effort', 20.0)
        return self.grasp_server.release(object_id, width_after, effort)
    
    def _status_internal(self):
        """内部状态查询"""
        return self.grasp_server.get_status()# ========== 便捷函数（最常用） ==========

def grab_object(object_id: str, width: Optional[float] = None, **kwargs) -> Dict:
    """
    全局便捷函数 - 抓取物体
    
    示例：
    result = grab_object("test_cube")                    # 默认宽度
    result = grab_object("qingque", width=0.05)          # 指定50mm
    result = grab_object("box_1", effort=25.0)           # 指定夹紧力
    """
    return GraspAction.grab(object_id, width, **kwargs)


def quick_grab(object_id: str, width_mm: float = 60.0) -> Dict:
    """
    快速抓取 - 使用毫米单位
    
    示例：
    result = quick_grab("test_cube")                     # 60mm宽度
    result = quick_grab("qingque", 50)                   # 50mm宽度
    result = quick_grab("small_object", 40)              # 40mm宽度
    """
    width = width_mm / 1000.0  # 转换为米
    return grab_object(object_id, width=width)


def smart_grab(object_id: str, strategy: str = "auto") -> Dict:
    """
    智能抓取 - 自动计算夹爪宽度
    
    示例：
    result = smart_grab("qingque")                       # 自动计算
    result = smart_grab("test_cube", strategy="side_grasp") # 指定策略
    result = smart_grab("cylinder", strategy="top_grasp")   # 顶部抓取
    """
    return GraspAction.grab(object_id, width=None, auto_calculate=True)


def release_object(object_id: Optional[str] = None, width_mm: float = 80.0) -> Dict:
    """
    释放物体 - 使用毫米单位
    
    示例：
    result = release_object("test_cube")                 # 释放后张开80mm
    result = release_object(width_mm=100)                # 释放后张开100mm
    result = release_object()                           # 释放当前物体
    """
    width_after = width_mm / 1000.0
    return GraspAction.release(object_id, width_after)


def get_grasp_status() -> Dict:
    """
    获取抓取状态
    
    示例：
    status = get_grasp_status()
    print(f"夹爪就绪: {status['gripper_ready']}")
    print(f"连接物体: {status['attached_object']}")
    """
    return GraspAction.status()


# ========== 测试函数 ==========

def test_smart_grab():
    """测试智能抓取功能"""
    print("🧪 测试智能抓取功能")
    
    test_cases = [
        ("test_cube", "auto"),
        ("qingque", "side_grasp"),
        ("cylinder_object", "top_grasp"),
    ]
    
    for object_id, strategy in test_cases:
        print(f"\n测试物体: {object_id}, 策略: {strategy}")
        try:
            result = smart_grab(object_id, strategy)
            if result.get("success"):
                width_mm = result.get("grasp_width", 0) * 1000
                print(f"  ✅ 成功！计算宽度: {width_mm:.1f}mm")
            else:
                print(f"  ❌ 失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"  ❌ 异常: {e}")
    
    print("\n✅ 智能抓取测试完成")


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 抓取服务器完整功能测试 ===")
    
    # 测试1: 基本抓取
    print("\n测试1: 基本抓取（默认宽度）")
    result1 = quick_grab("test_cube")
    print(f"  成功: {result1.get('success', False)}")
    print(f"  宽度: {result1.get('grasp_width', 0)*1000:.1f}mm")
    
    # 测试2: 智能抓取
    print("\n测试2: 智能抓取（自动计算）")
    result2 = smart_grab("qingque")
    print(f"  成功: {result2.get('success', False)}")
    print(f"  宽度: {result2.get('grasp_width', 0)*1000:.1f}mm")
    print(f"  来源: {result2.get('width_source', 'unknown')}")
    
    # 测试3: 获取状态
    print("\n测试3: 获取状态")
    status = get_grasp_status()
    print(f"  夹爪就绪: {status.get('gripper_ready', False)}")
    print(f"  连接物体: {status.get('attached_object', 'None')}")
    
    # 测试4: 释放物体
    print("\n测试4: 释放物体")
    result3 = release_object()
    print(f"  成功: {result3.get('success', False)}")
    
    print("\n✅ 所有测试完成！")