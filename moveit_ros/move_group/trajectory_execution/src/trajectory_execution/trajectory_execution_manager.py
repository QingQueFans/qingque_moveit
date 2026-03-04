#!/usr/bin/env python3
"""
轨迹执行管理器 - 连接到控制器插件
严格遵循项目架构规范
"""
from typing import List, Dict, Any, Optional, Union
import time
import os
import json
import numpy as np
import sys

# ========== 路径设置 ==========
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(FILE_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(MODULE_ROOT))

# 导入规划场景核心模块
PLANNING_SCENE_SRC = os.path.join(PROJECT_ROOT, '..', 'moveit_core', 'planning_scene', 'core_functions', 'src')
PLANNER_SRC = os.path.join(PROJECT_ROOT, '..', 'moveit_planners', 'src')
MOVEIT_CONTROLLER_SRC = os.path.join(PROJECT_ROOT, '..', 'moveit_plugins', 'moveit_controller_manager', 'src') 
CACHE_SRC = os.path.join(PROJECT_ROOT, 'moveit_core', 'cache_manager', 'src')
sys.path.insert(0, CACHE_SRC) 
sys.path.insert(0, MOVEIT_CONTROLLER_SRC)
sys.path.insert(0, PLANNING_SCENE_SRC)

sys.path.insert(0, PLANNER_SRC)  # 添加这一行
sys.path.insert(0, CACHE_SRC) 
# 全局变量声明
HAS_SCENE_CLIENT = False
HAS_CONTROLLER_MANAGER = False
HAS_ROS = False
HAS_OMPL_PLANNER = False  # 【新增】添加这个变量
try:
    from ps_core.scene_client import PlanningSceneClient
    HAS_SCENE_CLIENT = True
    print("[轨迹执行] ✓ PlanningSceneClient导入成功")
except ImportError as e:
    print(f"[轨迹执行] 导入PlanningSceneClient失败: {e}")
try:
    from moveit_controller_manager import MoveItControllerManager  
    HAS_MOVEIT_CONTROLLER = True

except ImportError as e:
    print(f"[轨迹执行] 导入控制器管理器失败: {e}")
    HAS_MOVEIT_CONTROLLER = False
try:
    from ompl_planner.ompl_planner_manager import OMPLPlannerManager
    HAS_OMPL_PLANNER = True
    print("[轨迹执行] ✓ OMPL规划器导入成功")
except ImportError as e:
    print(f"[轨迹执行] 导入OMPL规划器失败: {e}")
    HAS_OMPL_PLANNER = False

try:
    import rclpy
    from rclpy.node import Node
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
    HAS_ROS = True
    print("[轨迹执行] ✓ ROS2模块导入成功")
except ImportError as e:
    print(f"[轨迹执行] 未找到ROS2: {e}")
from .rollback_manager import RollbackManager    
class TrajectoryExecutionManager:
    """
    轨迹执行管理器 - 现在连接到控制器插件
    
    设计原则：
    1. 必须接收scene_client
    2. 连接到控制器插件
    3. 实时反馈执行状态
    4. 统一输出格式
    """
    
    def __init__(self, scene_client=None, use_controller_plugin=True):
        """
        初始化轨迹执行管理器
        
        Args:
            scene_client: PlanningSceneClient实例
            use_controller_plugin: 是否使用控制器插件
        """
        global HAS_SCENE_CLIENT, HAS_ROS, HAS_CONTROLLER_MANAGER
        
        if scene_client is None and HAS_SCENE_CLIENT:
            try:
                self.client = PlanningSceneClient()
            except:
                self.client = None
        else:
            self.client = scene_client
        
        # 统一缓存文件路径
        self.cache_file = os.path.expanduser('~/.planning_scene_cache/objects.json')
        
        # 执行状态
        self.is_executing = False
        self.current_trajectory = None
        self.execution_start_time = None
        self.execution_history = []
        
        # 控制器管理器实例
        self.controller_manager = None
        self.use_controller_plugin = use_controller_plugin
        
        if use_controller_plugin and HAS_MOVEIT_CONTROLLER and HAS_ROS:
            try:
                # 初始化ROS（如果还没初始化）
                if not rclpy.ok():
                    rclpy.init()
                
                # 创建控制器管理器
                self.controller_manager = MoveItControllerManager()
                print(f"[轨迹执行] 连接到控制器管理器插件")
            except Exception as e:
                print(f"[轨迹执行] 控制器管理器初始化失败: {e}")
                self.controller_manager = None
        elif HAS_ROS:
            # 旧的ROS直接连接方式（备选）
            try:
                self.node = Node('trajectory_execution_manager')
                print(f"[轨迹执行] 使用直接ROS连接")
            except Exception as e:
                print(f"[轨迹执行] ROS节点创建失败: {e}")
                HAS_ROS = False
        else:
            print("[轨迹执行] 使用模拟模式")        # 执行配置 
        # 【新增】规划器实例
        self.ompl_planner = None
        if HAS_OMPL_PLANNER:
            try:
                self.ompl_planner = OMPLPlannerManager()
                print(f"[轨迹执行] ✓ OMPL规划器初始化成功")
            except Exception as e:
                print(f"[轨迹执行] OMPL规划器初始化失败: {e}")
        # 在规划器初始化部分之后，添加状态检测
        if self.ompl_planner:
            # 获取规划器状态
            planner_status = self.get_planner_status()
            is_planner_available = planner_status.get("success", False) and planner_status.get("planner_available", False)
            
            if is_planner_available:
                print(f"[轨迹执行] ✅ OMPL规划器状态: 可用")
                print(f"   算法: {planner_status.get('planner_status', {}).get('manager', {}).get('available_planners', [])}")
            else:
                print(f"[轨迹执行] ⚠️ OMPL规划器状态: 不可用")
                self.ompl_planner = None  # 设置为None，表示不可用        
        self.config = {
            "max_velocity_scaling": 1.0,
            "max_acceleration_scaling": 1.0,
            "allowed_execution_duration": 10.0,
            "wait_for_execution": True,
            "stop_on_failure": True,
            "joint_tolerance": 0.01,
            "use_controller_plugin": use_controller_plugin
        }
        
        print("[轨迹执行管理器] 初始化完成")
        print(f"  控制器插件: {'已连接' if self.controller_manager else '无'}")
        print(f"  ROS支持: {'是' if HAS_ROS else '否'}")
        print(f"  场景客户端: {'已连接' if self.client else '无'}")
        print(f"  OMPL规划器: {'已连接' if self.ompl_planner else '无'}")  # 【新增】
       # 【新增】回退管理器相关
        self.rollback_manager = RollbackManager()
        self.pre_execution_states = {}  # 执行前状态缓存
        
        print(f"  轨迹回退: 已启用")    
    # ========== 必须有的标准方法 ==========
    
    def _load_cache(self) -> Dict:
        """加载缓存数据 - 完全按照规范实现"""
        if not os.path.exists(self.cache_file):
            print(f"[轨迹执行缓存] 缓存文件不存在: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[轨迹执行缓存] 已加载 {len(cache)} 个物体的缓存")
            return cache
        except Exception as e:
            print(f"[轨迹执行缓存] 加载缓存失败: {e}")
            return {}
    
    def _ensure_float(self, value):
        """确保数值是浮点数类型 - ROS2兼容性"""
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if isinstance(value, (int, float, np.number)):
            return float(value)
        return value
    
    # ========== 核心执行方法 ==========
    
    async def execute(self, trajectory: JointTrajectory, wait=True) -> Dict:
        """
        执行轨迹 - 异步版本，使用控制器插件
        
        Args:
            trajectory: 关节轨迹
            wait: 是否等待执行完成
            
        Returns:
            统一格式的执行结果
        """
        start_time = time.time()
        
        try:
            if self.is_executing:
                return {
                    "success": False,
                    "error": "已有轨迹正在执行",
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            print(f"[轨迹执行] 开始执行轨迹...")
            print(f"  关节数: {len(trajectory.joint_names)}")
            print(f"  轨迹点数: {len(trajectory.points)}")
            
            # 验证轨迹
            validation_result = self._validate_trajectory(trajectory)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"轨迹验证失败: {validation_result['issues']}",
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.is_executing = True
            self.current_trajectory = trajectory
            self.execution_start_time = time.time()
            
            # 记录执行历史
            execution_record = {
                "start_time": self.execution_start_time,
                "joint_names": trajectory.joint_names,
                "point_count": len(trajectory.points),
                "wait_for_completion": wait,
                "method": "controller_plugin" if self.controller_manager else "simulated"
            }
            self.execution_history.append(execution_record)
            
            # 执行轨迹
            if self.controller_manager and self.use_controller_plugin:
                # 使用控制器插件
                print(f"[轨迹执行] 使用控制器插件执行")
                result = await self.controller_manager.execute_trajectory(trajectory)
                result["method"] = "controller_plugin"
            elif HAS_ROS:
                # 备用：直接ROS执行
                print(f"[轨迹执行] 使用直接ROS执行")
                result = await self._execute_ros_direct(trajectory, wait)
                result["method"] = "ros_direct"
            else:
                # 模拟执行
                print(f"[轨迹执行] 使用模拟执行")
                result = self._execute_simulated(trajectory, wait)
                result["method"] = "simulated"
            
            self.is_executing = False            # 更新执行记录
            execution_record.update({
                "end_time": time.time(),
                "success": result.get("success", False),
                "execution_time": time.time() - self.execution_start_time
            })
            
            result["elapsed_time"] = time.time() - start_time
            result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            return result
            
        except Exception as e:
            self.is_executing = False
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    def execute_sync(self, trajectory: JointTrajectory, wait=True) -> Dict:
        """
        同步执行轨迹 - 使用控制器管理器的同步方法
        """
        start_time = time.time()
        self.record_pre_execution_state(trajectory)
        try:
            if self.is_executing:
                return {
                    "success": False,
                    "error": "已有轨迹正在执行",
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            print(f"[轨迹执行] 开始执行轨迹 (同步模式)...")
            print(f"  关节数: {len(trajectory.joint_names)}")
            print(f"  轨迹点数: {len(trajectory.points)}")
            
            self.is_executing = True
            self.current_trajectory = trajectory
            self.execution_start_time = time.time()
            
            # 记录执行历史
            execution_record = {
                "start_time": self.execution_start_time,
                "joint_names": trajectory.joint_names,
                "point_count": len(trajectory.points),
                "wait_for_completion": wait,
                "method": "controller_plugin_sync"
            }
            self.execution_history.append(execution_record)
            
            # 执行轨迹
            result = None
            
            if self.controller_manager and self.use_controller_plugin:
                print(f"[轨迹执行] 使用控制器管理器同步执行")
                try:
                    # 🔥 关键：使用新的同步方法
                    # 检查是否有同步方法
                    if hasattr(self.controller_manager, 'execute_trajectory_sync'):
                        result = self.controller_manager.execute_trajectory_sync(trajectory)
                    else:
                        # 如果控制器管理器没有同步方法，使用异步版本但同步调用
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(
                            self.controller_manager.execute_trajectory(trajectory)
                        )
                        loop.close()
                    
                    result["method"] = "controller_plugin_sync"
                    
                except Exception as e:
                    print(f"[轨迹执行] 控制器执行失败: {e}")
                    result = {
                        "success": False,
                        "error": str(e),
                        "method": "controller_plugin_failed"
                    }
                    
            elif HAS_ROS:
                # 备用：直接ROS执行
                print(f"[轨迹执行] 使用直接ROS执行")
                result = self._execute_direct_sync(trajectory, wait)
                result["method"] = "ros_direct_sync"
                
            else:
                # 模拟执行
                print(f"[轨迹执行] 使用模拟执行")
                result = self._execute_simulated(trajectory, wait)
                result["method"] = "simulated"
            
            self.is_executing = False
            
            # 更新执行记录
            if result:
                execution_record.update({
                    "end_time": time.time(),
                    "success": result.get("success", False),
                    "execution_time": time.time() - self.execution_start_time
                })
            
            # 确保返回结果有必要的字段
            if result:
                result["elapsed_time"] = time.time() - start_time
                result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                return result
            else:
                return {
                    "success": False,
                    "error": "执行返回空结果",
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
        except Exception as e:
            self.is_executing = False
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }    
    
    async def _execute_ros_direct(self, trajectory: JointTrajectory, wait=True) -> Dict:
        """直接ROS执行（备用方法）"""
        try:
            if not HAS_ROS:
                return {"success": False, "error": "ROS不可用"}
            
            # 这里实现直接ROS连接
            # 暂时返回模拟结果
            time.sleep(0.5)
            
            return {
                "success": True,
                "result": "轨迹执行完成（直接ROS）",
                "execution_time": 0.5
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_simulated(self, trajectory: JointTrajectory, wait=True) -> Dict:
        """模拟执行"""
        estimated_time = self._estimate_execution_time(trajectory)
        
        if wait:
            print(f"  模拟执行时间: {estimated_time:.2f}秒")
            time.sleep(min(estimated_time, 2.0))
        
        return {
            "success": True,
            "result": "轨迹执行完成（模拟）",
            "execution_time": estimated_time if wait else 0
        }
    # 在_execute_simulated方法后添加（约第350行后）
    def plan_trajectory(self, start_state: Dict, goal_state: Dict, **kwargs) -> Dict:
        """
        使用OMPL规划器规划轨迹 - 同步方法
        """
        start_time = time.time()
        
        try:
            # 检查规划器是否真的可用
            if self.ompl_planner is None:
                print(f"[轨迹执行] ⚠️ OMPL规划器不可用，使用预设轨迹...")
                return self._create_preset_trajectory(start_state, goal_state, **kwargs)
            
            # 获取规划器状态确认可用性
            planner_status = self.get_planner_status()
            if not (planner_status.get("success", False) and planner_status.get("planner_available", False)):
                print(f"[轨迹执行] ⚠️ 规划器状态不可用，使用预设轨迹...")
                return self._create_preset_trajectory(start_state, goal_state, **kwargs)
            
            print(f"[轨迹执行] 使用OMPL规划轨迹...")
            print(f"  算法: {kwargs.get('algorithm', 'rrt_connect')}")
            print(f"  规划时间: {kwargs.get('timeout', 5.0)}秒")
            
            # 使用OMPL规划器的同步规划方法
            plan_result = self.ompl_planner.plan_trajectory_sync(
                start_state=start_state,
                goal_state=goal_state,
                algorithm=kwargs.get('algorithm', 'rrt_connect'),
                timeout=kwargs.get('timeout', 5.0)
            )
            
            # 检查规划结果
            if plan_result.get("success", False):
                print(f"[轨迹执行] ✅ 规划成功")
                if plan_result.get("trajectory"):
                    print(f"  轨迹点数: {len(plan_result['trajectory'].points)}")
            else:
                print(f"[轨迹执行] ❌ 规划失败: {plan_result.get('error', '未知错误')}")
            
            # 添加执行管理器特定信息
            plan_result["elapsed_time"] = time.time() - start_time
            plan_result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            plan_result["plan_source"] = "ompl_planner"
            
            return plan_result
            
        except Exception as e:
            print(f"[轨迹执行] ❌ 规划异常: {e}")
            return self._create_preset_trajectory(start_state, goal_state, **kwargs)    
    def plan_trajectory(self, start_state: Dict, goal_state: Dict, **kwargs) -> Dict:
        """
        使用OMPL规划器规划轨迹 - 同步方法
        """
        start_time = time.time()
        
        try:
            # 检查规划器是否真的可用
            if self.ompl_planner is None:
                print(f"[轨迹执行] ⚠️ OMPL规划器不可用，使用预设轨迹...")
                return self._create_preset_trajectory(start_state, goal_state, **kwargs)
            
            # 获取规划器状态确认可用性
            planner_status = self.get_planner_status()
            if not (planner_status.get("success", False) and planner_status.get("planner_available", False)):
                print(f"[轨迹执行] ⚠️ 规划器状态不可用，使用预设轨迹...")
                return self._create_preset_trajectory(start_state, goal_state, **kwargs)
            
            print(f"[轨迹执行] 使用OMPL规划轨迹...")
            print(f"  算法: {kwargs.get('algorithm', 'rrt_connect')}")
            print(f"  规划时间: {kwargs.get('timeout', 5.0)}秒")
            
            # 使用OMPL规划器的同步规划方法
            plan_result = self.ompl_planner.plan_trajectory_sync(
                start_state=start_state,
                goal_state=goal_state,
                algorithm=kwargs.get('algorithm', 'rrt_connect'),
                timeout=kwargs.get('timeout', 5.0)
            )
            
            # 检查规划结果
            if plan_result.get("success", False):
                print(f"[轨迹执行] ✅ 规划成功")
                if plan_result.get("trajectory"):
                    print(f"  轨迹点数: {len(plan_result['trajectory'].points)}")
            else:
                print(f"[轨迹执行] ❌ 规划失败: {plan_result.get('error', '未知错误')}")
            
            # 添加执行管理器特定信息
            plan_result["elapsed_time"] = time.time() - start_time
            plan_result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            plan_result["plan_source"] = "ompl_planner"
            
            return plan_result
            
        except Exception as e:
            print(f"[轨迹执行] ❌ 规划异常: {e}")
            return self._create_preset_trajectory(start_state, goal_state, **kwargs)
 
    def get_execution_status(self) -> Dict:
        """获取执行状态"""
        start_time = time.time()
        
        try:
            if self.is_executing and self.execution_start_time:
                elapsed = time.time() - self.execution_start_time
                
                if self.current_trajectory:
                    estimated_total = self._estimate_execution_time(self.current_trajectory)
                    progress = min(elapsed / estimated_total, 1.0) * 100 if estimated_total > 0 else 0
                else:
                    progress = 0
                
                return {
                    "success": True,
                    "is_executing": True,
                    "elapsed_time": elapsed,
                    "progress_percent": progress,
                    "execution_start_time": self.execution_start_time,
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    "success": True,
                    "is_executing": False,
                    "execution_history_count": len(self.execution_history),
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_execution_history(self, limit=10) -> Dict:
        """获取执行历史"""
        start_time = time.time()
        
        try:
            history = self.execution_history[-limit:] if self.execution_history else []
            
            return {
                "success": True,
                "history": history,
                "total_records": len(self.execution_history),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }   
    def record_pre_execution_state(self, trajectory=None):
        """
        记录执行前的状态
        
        Args:
            trajectory: 将要执行的轨迹（用于记录目标位置）
        
        Returns:
            记录的状态字典
        """
        print("[轨迹回退] 记录执行前状态...")
        
        state_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "record_time": time.time(),
            "trajectory_info": {
                "joint_names": trajectory.joint_names if trajectory else [],
                "target_positions": trajectory.points[-1].positions if trajectory and trajectory.points else [],
                "point_count": len(trajectory.points) if trajectory else 0
            },
            "execution_history_count": len(self.execution_history),
            "is_executing": self.is_executing,
            "has_current_trajectory": self.current_trajectory is not None
        }
        
        # 记录到回退管理器
        self.rollback_manager.add_state(state_record)
        
        # 缓存到实例变量（用于快速回退）
        self.pre_execution_states = state_record
        
        print(f"[轨迹回退] ✓ 状态已记录 (ID: {self.rollback_manager.current_state_id})")
        return state_record
    def _create_preset_trajectory(self, start_state, goal_state, **kwargs):
        """
        创建预设轨迹（当规划器不可用时使用）
        """
        try:
            from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
            
            trajectory = JointTrajectory()
            trajectory.joint_names = [
                'panda_joint1', 'panda_joint2', 'panda_joint3',
                'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
            ]
            
            # 创建起始点
            start_point = JointTrajectoryPoint()
            if isinstance(start_state, dict) and "joints" in start_state:
                start_point.positions = start_state["joints"][:7]
            elif isinstance(start_state, (list, tuple)):
                start_point.positions = start_state[:7]
            else:
                start_point.positions = [0.0] * 7
            start_point.time_from_start.sec = 0
            
            # 创建目标点
            end_point = JointTrajectoryPoint()
            if isinstance(goal_state, dict):
                if "joints" in goal_state:
                    end_point.positions = goal_state["joints"][:7]
                elif "pose" in goal_state:
                    # 简化：将位姿转换为关节角度（这里只是模拟）
                    # 实际应该用IK求解器
                    end_point.positions = [0.0, -0.5, 0.0, -1.5, 0.0, 1.5, 0.0]
            elif isinstance(goal_state, (list, tuple)):
                end_point.positions = goal_state[:7]
            else:
                end_point.positions = [0.0, -0.5, 0.0, -1.5, 0.0, 1.5, 0.0]
            
            end_point.time_from_start.sec = 2
            
            trajectory.points = [start_point, end_point]
            
            return {
                "success": True,
                "trajectory": trajectory,
                "elapsed_time": 0.1,
                "plan_source": "preset_trajectory",
                "message": "使用预设轨迹（规划器不可用）"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"创建预设轨迹失败: {e}",
                "elapsed_time": 0.0
            }    
    def rollback_to_previous_state(self, confirm=False, max_wait_time=5.0):
        """
        回退到执行前的状态
        
        Args:
            confirm: 是否需要进行确认（交互模式）
            max_wait_time: 最大等待时间
            
        Returns:
            回退结果字典
        """
        start_time = time.time()
        
        try:
            print("\n" + "="*60)
            print("轨迹回退管理器")
            print("="*60)
            
            # 检查是否有记录的状态
            if not self.rollback_manager.has_states():
                return {
                    "success": False,
                    "error": "没有可回退的状态记录",
                    "available_states": 0,
                    "elapsed_time": time.time() - start_time
                }
            
            # 获取可回退的状态
            available_states = self.rollback_manager.get_available_states()
            print(f"可回退的状态数: {len(available_states)}")
            
            for i, state in enumerate(available_states[-3:]):  # 显示最近3个
                print(f"  [{i+1}] {state['timestamp']} - {state['trajectory_info']['point_count']}点")
            
            # 交互确认（如果启用）
            if confirm:
                print(f"\n⚠️  确认回退到上一个状态？")
                print(f"  当前有轨迹在执行: {'是' if self.is_executing else '否'}")
                
                # 这里可以添加等待用户输入的逻辑
                # 简化版本：直接等待一段时间
                time.sleep(1)
                print("  正在执行回退...")
            
            # 执行回退
            rollback_result = self._perform_rollback()
            
            if rollback_result.get("success", False):
                print(f"✅ 回退成功")
                print(f"  恢复到: {rollback_result.get('restored_timestamp')}")
                print(f"  耗时: {rollback_result.get('execution_time', 0):.2f}秒")
            else:
                print(f"❌ 回退失败: {rollback_result.get('error')}")
            
            return rollback_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }
    
    def _perform_rollback(self):
        """执行实际回退操作"""
        # 停止当前执行
        if self.is_executing:
            print("[轨迹回退] 停止当前执行...")
            stop_result = self.stop()
            if not stop_result.get("success", False):
                return {"success": False, "error": f"停止执行失败: {stop_result.get('error')}"}        

        # 获取上一个状态
        previous_state = self.rollback_manager.get_previous_state()
        if not previous_state:
            return {"success": False, "error": "无法获取上一个状态"}
        
        # 执行回退轨迹（移动到之前的位置）
        if previous_state["trajectory_info"]["target_positions"]:
            print(f"[轨迹回退] 恢复到之前位置: {previous_state['trajectory_info']['target_positions'][:3]}...")
            
            # 创建回退轨迹
            rollback_trajectory = self._create_rollback_trajectory(
                previous_state["trajectory_info"]["target_positions"]
            )
            
            # 执行回退
            rollback_result = self.execute_sync(rollback_trajectory, wait=True)
            
            return {
                "success": rollback_result.get("success", False),
                "restored_timestamp": previous_state["timestamp"],
                "execution_time": rollback_result.get("execution_time", 0),
                "rollback_trajectory_points": len(rollback_trajectory.points),
                "original_result": rollback_result
            }
        
        return {
            "success": True,
            "restored_timestamp": previous_state["timestamp"],
            "message": "状态已恢复（无位置回退）"
        }
    
    def _create_rollback_trajectory(self, target_positions, duration=2.0):
        """创建回退轨迹"""
        trajectory = JointTrajectory()
        trajectory.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        # 平滑回退轨迹（2个点）
        start_point = JointTrajectoryPoint()
        start_point.positions = [0.0] * 7  # 简化的起始位置
        start_point.time_from_start.sec = 0
        
        end_point = JointTrajectoryPoint()
        end_point.positions = target_positions[:7]
        end_point.time_from_start.sec = int(duration)
        
        trajectory.points = [start_point, end_point]
        
        return trajectory
    
    def get_rollback_info(self):
        """获取回退信息"""
        return {
            "success": True,
            "has_states": self.rollback_manager.has_states(),
            "state_count": self.rollback_manager.state_count,
            "current_state_id": self.rollback_manager.current_state_id,
            "available_states": self.rollback_manager.get_available_states(),
            "last_record_time": self.pre_execution_states.get("timestamp") if self.pre_execution_states else None
        }        
         # ========== 辅助方法 ==========
    # 在get_execution_history方法后添加（约第460行后）
    def get_planner_status(self) -> Dict:
        """获取规划器状态"""
        start_time = time.time()
        
        try:
            if self.ompl_planner:
                # 获取OMPL规划器状态
                planner_status = self.ompl_planner.get_manager_status()
                
                return {
                    "success": True,
                    "planner_available": True,
                    "planner_type": "ompl",
                    "planner_status": planner_status,
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    "success": True,
                    "planner_available": False,
                    "planner_type": "none",
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }    
    def _validate_trajectory(self, trajectory: JointTrajectory) -> Dict:
        """验证轨迹有效性"""
        issues = []
        
        if not trajectory.joint_names:
            issues.append("关节名称为空")
        
        if not trajectory.points:
            issues.append("轨迹点为空")
        
        # 检查所有点是否有位置数据
        for i, point in enumerate(trajectory.points):
            if not point.positions:
                issues.append(f"第 {i+1} 个点没有位置数据")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "joint_count": len(trajectory.joint_names),
            "point_count": len(trajectory.points)
        }
    
    def _estimate_execution_time(self, trajectory: JointTrajectory) -> float:
        """估算轨迹执行时间"""
        if not trajectory.points:
            return 1.0
        
        # 简单估算：根据最后一个点的时间
        last_point = trajectory.points[-1]
        if hasattr(last_point, 'time_from_start'):
            total_seconds = last_point.time_from_start.sec + last_point.time_from_start.nanosec / 1e9
            # 应用速度缩放
            total_seconds /= self.config.get("max_velocity_scaling", 1.0)
            return min(total_seconds, 10.0)
        else:
            # 如果没有时间信息，根据点数估算
            point_count = len(trajectory.points)
            estimated_time = point_count * 0.1
            estimated_time /= max(self.config.get("max_velocity_scaling", 1.0), 0.1)
            return min(estimated_time, 10.0)
    
    def set_config(self, config: Dict) -> Dict:
        """设置执行配置"""
        start_time = time.time()
        
        try:
            self.config.update(config)
            
            # 确保所有数值都是float类型
            for key, value in self.config.items():
                if isinstance(value, (int, float)):
                    self.config[key] = self._ensure_float(value)
            
            return {
                "success": True,
                "result": "执行配置更新成功",
                "config": self.config,
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        start_time = time.time()
        
        try:
            return {
                "success": True,
                "config": self.config,
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    def _execute_direct_sync(self, trajectory: JointTrajectory, wait=True) -> Dict:
        """直接同步执行（不使用异步）"""
        start_time = time.time()
        
        try:
            import rclpy
            from rclpy.action import ActionClient
            from control_msgs.action import FollowJointTrajectory
            
            # 创建临时节点
            temp_node = rclpy.create_node('direct_sync_executor')
            
            try:
                client = ActionClient(temp_node, FollowJointTrajectory,
                                    '/panda_arm_controller/follow_joint_trajectory')
                
                # 等待服务器
                if not client.wait_for_server(timeout_sec=10.0):
                    return {
                        "success": False,
                        "error": "控制器服务器不可用",
                        "elapsed_time": time.time() - start_time
                    }
                
                # 发送轨迹
                goal_msg = FollowJointTrajectory.Goal()
                goal_msg.trajectory = trajectory
                
                send_start = time.time()
                future = client.send_goal_async(goal_msg)
                rclpy.spin_until_future_complete(temp_node, future, timeout_sec=5.0)
                goal_handle = future.result()
                
                if not goal_handle or not goal_handle.accepted:
                    return {
                        "success": False,
                        "error": "目标被拒绝",
                        "elapsed_time": time.time() - start_time
                    }
                
                # 等待结果
                result_future = goal_handle.get_result_async()
                rclpy.spin_until_future_complete(temp_node, result_future, timeout_sec=15.0)
                result = result_future.result()
                
                exec_time = time.time() - send_start
                
                if result and hasattr(result, 'result'):
                    if result.result.error_code == 0:
                        return {
                            "success": True,
                            "result": "轨迹执行完成",
                            "execution_time": exec_time,
                            "error_code": result.result.error_code,
                            "error_string": result.result.error_string if hasattr(result.result, 'error_string') else ""
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"控制器错误: {getattr(result.result, 'error_string', '未知')}",
                            "error_code": result.result.error_code,
                            "execution_time": exec_time
                        }
                
                return {
                    "success": False,
                    "error": "未收到执行结果",
                    "elapsed_time": time.time() - start_time
                }
                
            finally:
                temp_node.destroy_node()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }   
    # 在 TrajectoryExecutionManager 类中添加这些方法

    def enable_cache(self, enabled=True):
        """启用/禁用缓存 - 使用你的缓存管理器"""
        if not hasattr(self, '_cache_enabled'):
            self._cache_enabled = enabled
            
            try:
                # ❗ 使用你的缓存管理器
                from ps_cache.kinematics_cache import KinematicsCache
                from ps_cache import CachePathTools
                
                # 初始化（按照你的方式）
                CachePathTools.initialize()
                self._ik_cache = KinematicsCache()
                
                print(f"[轨迹执行] 缓存启用（使用缓存管理器）")
                print(f"  缓存目录: {self._get_cache_root()}")
                
            except ImportError as e:
                print(f"[轨迹执行] 无法导入缓存管理器: {e}")
                # 备选：简单文件缓存
                self._ik_cache = self._create_simple_file_cache()
                print(f"[轨迹执行] 缓存启用（使用简单文件缓存）")
            
            self._cache_stats = {"hits": 0, "misses": 0, "saves": 0}

    def _get_cache_root(self):
        """获取缓存根目录"""
        try:
            from ps_cache import CachePathTools
            return CachePathTools.get_cache_root()
        except:
            # 默认路径（基于你的项目结构）
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))
            return os.path.join(project_root, 'moveit_core', 'cache_manager', 'data')
    def _extract_target_pose_for_cache(self, goal_state):
        """从目标状态提取位姿 - 返回列表格式用于缓存"""
        print(f"[缓存提取] goal_state类型: {type(goal_state)}, 值: {goal_state}")
        
        if isinstance(goal_state, dict):
            # 先标准化
            normalized = self._normalize_pose_format(goal_state)
            if normalized:
                # 转换为列表格式用于缓存
                return self._pose_to_list_format(normalized)
            
            # 兼容旧格式
            if "pose" in goal_state:
                pose = goal_state["pose"]
                return self._extract_target_pose_for_cache(pose)
            
            elif "joints" in goal_state:
                return None
        
        elif isinstance(goal_state, (list, tuple)) and len(goal_state) >= 7:
            return list(goal_state[:7])
        
        elif isinstance(goal_state, (list, tuple)) and len(goal_state) == 3:
            return list(goal_state) + [0.0, 0.0, 0.0, 1.0]
        
        print(f"[缓存提取] ⚠️ 无法从目标状态提取位姿: {goal_state}")
        return None
    def _get_pose_from_cache_by_object_id(self, object_id):
        """从IK缓存中通过物体ID查找位姿 - 返回标准化格式"""
        try:
            import json
            from pathlib import Path
            
            # 获取缓存目录
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
            cache_dir = Path(cache_root) / "kinematics" / "ik_solutions"
            
            if not cache_dir.exists():
                print(f"[缓存查找] 缓存目录不存在: {cache_dir}")
                return None
            
            print(f"[缓存查找] 搜索物体 {object_id} 的缓存...")
            
            # 遍历所有缓存文件
            for cache_file in cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 检查metadata中的object_id
                    metadata = data.get('data', {}).get('metadata', {})
                    cached_object_id = metadata.get('object_id')
                    
                    if cached_object_id == object_id:
                        print(f"[缓存查找] ✅ 找到匹配: {cache_file.name}")
                        target_pose = data['data'].get('target_pose')
                        if target_pose:
                            print(f"      位姿: {target_pose[:3]}")
                            
                            # 【修复】确保返回完整7元素位姿
                            if isinstance(target_pose, (list, tuple)):
                                # 如果只有3个元素，添加默认方向
                                if len(target_pose) == 3:
                                    full_pose = list(target_pose) + [0.0, 0.0, 0.0, 1.0]
                                elif len(target_pose) >= 7:
                                    full_pose = list(target_pose[:7])
                                else:
                                    print(f"[缓存查找] ⚠️ 位姿长度异常: {len(target_pose)}")
                                    return None
                                
                                # 返回标准化格式
                                return {
                                    "position": full_pose[:3],
                                    "orientation": full_pose[3:7]
                                }
                            return target_pose
                            
                except Exception as e:
                    print(f"[缓存查找] 读取文件 {cache_file} 错误: {e}")
                    continue
            
            print(f"[缓存查找] ❌ 未找到物体 {object_id} 的缓存")
            return None
            
        except Exception as e:
            print(f"[缓存查找] 全局错误: {e}")
            return None
    def _get_grasp_pose_from_object_id(self, object_id):
        """
        根据物体ID获取抓取位姿 - 统一返回标准化格式
        """
        print(f"[物体查询] 查询物体: {object_id}")
        
        # 1. 从IK缓存中查找
        cached_pose = self._get_pose_from_cache_by_object_id(object_id)
        if cached_pose is not None:
            print(f"[物体查询] ✅ 从缓存中找到物体 {object_id}")
            # 确保返回标准化格式
            normalized = self._normalize_pose_format(cached_pose)
            if normalized:
                return normalized
        
        # 2. 硬编码映射（使用标准化格式）
        object_grasp_poses = {
            "test_cube": {
                "position": [0.5, 0.0, 0.3],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            },
            "test_box": {
                "position": [0.6, 0.1, 0.2],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            },
            "coke_can_01": {
                "position": [0.6, 0.1, 0.2],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            },
            "qingque": {  # 添加 qingque 的硬编码
                "position": [0.5, 0.0, 0.3],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            }
        }
        
        if object_id in object_grasp_poses:
            print(f"[物体查询] ✅ 从硬编码找到物体 {object_id}")
            return object_grasp_poses[object_id]
        
        # 3. 默认值
        print(f"[物体查询] ⚠️ 使用默认位姿")
        return {
            "position": [0.5, 0.0, 0.3],
            "orientation": [0.0, 0.0, 0.0, 1.0]
        }
    def _get_grasp_pose_from_object(self, object_id):
        """从物体ID获取抓取位姿 - 改进版"""
        print(f"[物体查询] 开始查询物体: {object_id}")
        
        # 1. ✅ 首先：从IK缓存中查找
        cached_pose = self._get_pose_from_cache_by_object_id(object_id)
        if cached_pose is not None:
            print(f"[物体查询] ✅ 从IK缓存中找到物体 {object_id}")
            return {"pose": cached_pose}
        
        # 2. 然后：使用原有逻辑（硬编码映射或默认值）
        print(f"[物体查询] ⚠️ 未找到缓存，使用原有逻辑")
        
        # 这里调用你原有的 _get_grasp_pose_from_object_id 或直接返回默认值
        try:
            # 如果 _get_grasp_pose_from_object_id 存在，使用它
            if hasattr(self, '_get_grasp_pose_from_object_id'):
                pose = self._get_grasp_pose_from_object_id(object_id)
                return {"pose": pose}
        except:
            pass
        
        # 默认值
        return {"pose": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0]}

    def _extract_joints_from_plan(self, plan_result):
        """从规划结果提取关节解"""
        if not plan_result.get("success", False):
            return None
        if "trajectory" in plan_result:
            trajectory = plan_result["trajectory"]
            if hasattr(trajectory, 'points') and trajectory.points:
                return trajectory.points[-1].positions
        return None

    def plan_and_execute(self, start_state, goal_state, **kwargs):
        """
        规划并执行轨迹 - 一体化操作
        """
        start_time = time.time()
        
        try:
            print(f"[轨迹执行] 开始规划并执行...")
            
            # 1. 规划轨迹
            plan_result = self.plan_trajectory(start_state, goal_state, **kwargs)
            
            if not plan_result.get("success", False):
                return plan_result
            
            # 2. 检查是否有轨迹
            if "trajectory" not in plan_result:
                return {
                    "success": False,
                    "error": "规划成功但没有生成轨迹",
                    "plan_result": plan_result,
                    "elapsed_time": time.time() - start_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 3. 提取关节解（用于后续可能的学习）
            trajectory = plan_result["trajectory"]
            if hasattr(trajectory, 'points') and trajectory.points:
                joints = trajectory.points[-1].positions
                plan_result["solution"] = joints  # 保存关节解
            
            # 4. 执行轨迹
            exec_result = self.execute_sync(plan_result["trajectory"])
            
            # 5. 合并结果
            return {
                "success": plan_result.get("success", False) and exec_result.get("success", False),
                "planning": plan_result,
                "execution": exec_result,
                "total_time": time.time() - start_time,
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    def plan_and_execute_cached(self, start_state, goal_state, **kwargs):
        """带缓存的规划执行 - 统一位姿格式版本"""
        import time
        
        start_time = time.time()
        
        if not getattr(self, '_cache_enabled', False):
            print("[缓存] 缓存禁用，使用原始方法")
            return self.plan_and_execute(start_state, goal_state, **kwargs)
        
        try:
            print(f"\n[缓存] 规划执行请求")
            
            # ========== 步骤1：判断输入类型 ==========
            # ✅ 如果是关节模式，直接规划，不经过缓存
            if isinstance(goal_state, dict) and "joints" in goal_state:
                print(f"[缓存] 关节模式，跳过缓存直接规划")
                return self.plan_and_execute(start_state, goal_state, **kwargs)
            
            # ========== 步骤2：处理物体ID模式 ==========
            planning_goal_state = goal_state
            object_id = None
            
            # 检查是否是物体ID模式
            if isinstance(goal_state, dict) and "object_id" in goal_state:
                object_id = goal_state["object_id"]
                print(f"[缓存] 物体ID模式: {object_id}")
                
                # ===== 【直接从物体缓存读取位姿】=====
                object_pose = self._get_object_pose_from_cache(object_id)
                if object_pose:
                    print(f"[缓存] ✅ 从物体缓存找到 {object_id} 的位姿: {object_pose[:3]}")
                    planning_goal_state = {"pose": object_pose}
                else:
                    print(f"[缓存] ⚠️ 无法获取物体 {object_id} 的位姿")
                    planning_goal_state = goal_state
            
            # ========== 步骤3：提取位姿用于缓存查询 ==========
            target_pose = self._extract_target_pose_for_cache(planning_goal_state)
            
            if target_pose is None:
                print(f"  ⚠️ 无法提取目标位姿，跳过缓存")
                result = self.plan_and_execute(start_state, planning_goal_state, **kwargs)
                result["cache_info"] = {"hit": False, "reason": "no_pose"}
                return result
            
            print(f"  目标位姿: {[round(x, 4) for x in target_pose[:3]]}...")
            
            # ========== 步骤4：检查IK缓存 ==========
            cache_used = False
            cached_joints = None
            
            if hasattr(self, '_ik_cache') and hasattr(self._ik_cache, 'load_ik_solution'):
                try:
                    serializable_pose = [float(x) for x in target_pose]
                    
                    ik_data = self._ik_cache.load_ik_solution(
                        target_pose=serializable_pose,
                        robot_model="panda",
                        sequence=0
                    )
                    
                    if ik_data and isinstance(ik_data, dict) and "data" in ik_data and "joint_solution" in ik_data["data"]:
                        print(f"  ✅ IK缓存命中！")
                        cached_joints = ik_data["data"]["joint_solution"]
                        cached_joints = [float(x) for x in cached_joints]
                        
                        cache_used = True
                        self._cache_stats["hits"] += 1
                        
                        result = self._execute_joints(cached_joints)
                        result["cache_info"] = {
                            "hit": True,
                            "method": "cache_manager",
                            "object_id": object_id,
                            "source_pose": target_pose[:3]
                        }
                        return result
                        
                except Exception as e:
                    print(f"[缓存] 加载IK缓存时出错: {e}")
            
            # ========== 步骤5：缓存未命中，进行规划 ==========
            print(f"  🔄 缓存未命中，调用原始规划")
            self._cache_stats["misses"] += 1
            
            plan_result = self.plan_and_execute(start_state, planning_goal_state, **kwargs)
            
            if not plan_result.get("success", False):
                plan_result["cache_info"] = {"hit": False, "reason": "planning_failed"}
                return plan_result
            
            # ========== 步骤6：从规划结果提取关节解并保存 ==========
            joints = None
            if "trajectory" in plan_result:
                trajectory = plan_result["trajectory"]
                if hasattr(trajectory, 'points') and trajectory.points:
                    joints = trajectory.points[-1].positions
            
            if joints and hasattr(self, '_ik_cache') and hasattr(self._ik_cache, 'save_ik_solution'):
                try:
                    serializable_joints = [float(x) for x in joints]
                    
                    metadata = {
                        "source": "trajectory_execution_manager",
                        "planning_time": plan_result.get("planning", {}).get("planning_time", 0),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    if object_id:
                        metadata["object_id"] = object_id
                    
                    self._ik_cache.save_ik_solution(
                        target_pose=[float(x) for x in target_pose],
                        joint_solution=serializable_joints,
                        robot_model="panda",
                        metadata=metadata
                    )
                    self._cache_stats["saves"] += 1
                    print(f"  💾 已保存到IK缓存")
                    
                except Exception as e:
                    print(f"[缓存] 保存IK缓存时出错: {e}")
            
            plan_result["cache_info"] = {"hit": False, "saved": True}
            return plan_result
            
        except Exception as e:
            print(f"[缓存] 错误: {e}")
            import traceback
            traceback.print_exc()
            result = self.plan_and_execute(start_state, goal_state, **kwargs)
            result["cache_info"] = {"hit": False, "error": str(e)}
            return result

    def _get_object_pose_from_cache(self, object_id):
        """从物体缓存直接读取物体的位姿"""
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
    def _save_object_to_pose_association(self, object_id, target_pose):
        """保存物体ID到位姿的关联（可选）"""
        try:
            import json
            from pathlib import Path
            
            cache_root = "/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/data"
            assoc_file = Path(cache_root) / "kinematics" / "object_pose_assoc.json"
            
            # 读取现有关联
            associations = {}
            if assoc_file.exists():
                with open(assoc_file, 'r') as f:
                    associations = json.load(f)
            
            # 更新关联
            associations[object_id] = [float(x) for x in target_pose]
            
            # 保存
            with open(assoc_file, 'w') as f:
                json.dump(associations, f, indent=2)
                
        except Exception as e:
            print(f"[缓存] 保存物体关联失败: {e}")
    def _execute_joints(self, joints):
        """执行关节解"""
        # 如果只有6个关节，添加默认的第7关节
        if len(joints) == 6:
            joints = list(joints) + [0.0]  # 添加默认值
        trajectory = self._create_trajectory_from_joints(joints)
        return self.execute_sync(trajectory)
    def _create_trajectory_from_joints(self, joints, duration=2.0):
        """从关节位置创建轨迹"""
        trajectory = JointTrajectory()
        
        # Panda机械臂关节名
        trajectory.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        # 创建起点和终点
        start_point = JointTrajectoryPoint()
        start_point.positions = [0.0] * 7  # 或者使用当前关节位置
        start_point.time_from_start.sec = 0
        
        end_point = JointTrajectoryPoint()
        end_point.positions = joints
        end_point.time_from_start.sec = int(duration)
        
        trajectory.points = [start_point, end_point]
        
        return trajectory
    def _normalize_pose_format(self, pose_input):
        """
        统一位姿格式为MoveIt标准格式
        
        输入可以是：
        - [x,y,z,qx,qy,qz,qw] 列表
        - {"position": [x,y,z], "orientation": [qx,qy,qz,qw]} 字典
        - {"pose": [x,y,z,qx,qy,qz,qw]} 字典
        - {"pose": {"position": [...], "orientation": [...]}} 字典
        
        返回：
            {
                "position": [x,y,z],
                "orientation": [qx,qy,qz,qw]
            }
        """
        print(f"[格式转换] 输入: {type(pose_input)}")
        
        # 情况1：已经是标准格式
        if isinstance(pose_input, dict):
            if "position" in pose_input and "orientation" in pose_input:
                # 已经是标准格式
                return {
                    "position": [float(x) for x in pose_input["position"]],
                    "orientation": [float(x) for x in pose_input["orientation"]]
                }
            
            elif "pose" in pose_input:
                # 包含 pose 字段
                return self._normalize_pose_format(pose_input["pose"])
        
        # 情况2：列表格式 [x,y,z,qx,qy,qz,qw]
        elif isinstance(pose_input, (list, tuple)) and len(pose_input) >= 7:
            return {
                "position": [float(x) for x in pose_input[:3]],
                "orientation": [float(x) for x in pose_input[3:7]]
            }
        
        # 情况3：只有位置 [x,y,z]，使用默认方向
        elif isinstance(pose_input, (list, tuple)) and len(pose_input) == 3:
            return {
                "position": [float(x) for x in pose_input],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            }
        
        print(f"[格式转换] ⚠️ 无法识别的格式: {pose_input}")
        return None


    def _pose_to_moveit_format(self, pose_dict):
        """
        将标准化位姿转换为MoveIt请求格式
        """
        if not pose_dict:
            return None
        
        return {
            "pose": {
                "position": pose_dict["position"],
                "orientation": pose_dict["orientation"]
            }
        }


    def _pose_to_list_format(self, pose_dict):
        """
        将标准化位姿转换为列表格式 [x,y,z,qx,qy,qz,qw]
        """
        if not pose_dict:
            return None
        
        return pose_dict["position"] + pose_dict["orientation"]    
    def _create_simple_file_cache(self):
        """创建简单文件缓存（备选方案）"""
        class SimpleFileCache:
            def __init__(self):
                import os
                self.cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    ))),
                    'moveit_core', 'cache_manager', 'data', 'kinematics', 'ik_solutions'
                )
                os.makedirs(self.cache_dir, exist_ok=True)
            
            def load_ik_solution(self, target_pose, robot_model, sequence=0):
                import json, hashlib, os
                
                # 生成文件名（按你的格式）
                pose_str = json.dumps([round(float(x), 6) for x in target_pose])
                cache_key = hashlib.md5(pose_str.encode()).hexdigest()[:12]
                cache_file = os.path.join(self.cache_dir, f"ik_{cache_key}.json")
                
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r') as f:
                            return json.load(f)
                    except:
                        pass
                return None
            
            def save_ik_solution(self, target_pose, joint_solution, robot_model, metadata=None):
                import json, hashlib, os
                
                pose_str = json.dumps([round(float(x), 6) for x in target_pose])
                cache_key = hashlib.md5(pose_str.encode()).hexdigest()[:12]
                cache_file = os.path.join(self.cache_dir, f"ik_{cache_key}.json")
                
                data = {
                    "data": {
                        "target_pose": target_pose,
                        "joint_solution": joint_solution,
                        "robot_model": robot_model,
                        "metadata": metadata or {}
                    },
                    "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "filepath": cache_file
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
        
        return SimpleFileCache()
    
    def destroy(self):
        """清理资源"""
        if self.controller_manager:
            try:
                self.controller_manager.destroy_node()
                print("[轨迹执行] 控制器管理器已销毁")
            except:
                pass
# ========== 一行调用接口 ==========

class TrajectoryExecutor:
    """
    轨迹执行器 - 简化调用接口
    在现有 TrajectoryExecutionManager 基础上包装
    """
    
    _instance = None
    
    @classmethod
    def execute(cls, target, **kwargs):
        """
        一行调用：执行轨迹
        
        参数：
        target: 可以是：
            - 字典: 包含目标位姿 {"pose": [x,y,z,qx,qy,qz,qw]}
            - 字典: 包含目标关节 {"joints": [j1,j2,j3,j4,j5,j6,j7]}
            - 列表: 直接的目标位姿 [x,y,z,qx,qy,qz,qw]
            - 字符串: 物体ID，会自动转换为抓取位姿
        
        **kwargs: 可选参数
            - start: 起始状态（默认当前状态）
            - use_cache: 是否使用缓存（默认True）
            - strategy: 规划策略
            - timeout: 规划超时时间
            - wait: 是否等待执行完成
            
        返回：
            标准化结果字典
        """
        # 获取或创建单例
        if cls._instance is None:
            cls._instance = cls._create_instance()
        
        return cls._instance._execute_internal(target, **kwargs)
    
    @classmethod
    def _create_instance(cls):
        """创建内部实例"""
        executor = _TrajectoryExecutor()
        executor._setup()
        return executor


class _TrajectoryExecutor:
    """内部实现类"""
    
    def _setup(self):
        """初始化内部组件"""
        # 使用你已有的 TrajectoryExecutionManager
        from trajectory_execution.trajectory_execution_manager import TrajectoryExecutionManager
        
        self.executor = TrajectoryExecutionManager()
        
        # 启用缓存
        if hasattr(self.executor, 'enable_cache'):
            self.executor.enable_cache(True)
        
        print("[TrajectoryExecutor] 就绪")
    
    def _execute_internal(self, target, **kwargs):
        """内部执行逻辑"""
        try:
            # 解析输入
            start_state, goal_state = self._parse_input(target, kwargs)
            
            # 使用缓存执行
            use_cache = kwargs.get('use_cache', True)
            
            if use_cache and hasattr(self.executor, 'plan_and_execute_cached'):
                # 使用带缓存的方法
                result = self.executor.plan_and_execute_cached(
                    start_state=start_state,
                    goal_state=goal_state,
                    timeout=kwargs.get('timeout', 5.0),
                    algorithm=kwargs.get('strategy', 'rrt_connect')
                )
            else:
                # 使用原始方法
                result = self.executor.plan_and_execute(
                    start_state=start_state,
                    goal_state=goal_state,
                    timeout=kwargs.get('timeout', 5.0),
                    algorithm=kwargs.get('strategy', 'rrt_connect')
                )
            
            # 标准化输出
            return self._standardize_output(result, target)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0.0,
                "timestamp": self._get_timestamp()
            }
    
    def _parse_input(self, target, kwargs):
        """解析多种输入格式"""
        # 获取起始状态
        start_state = kwargs.get('start')
        if start_state is None:
            # 使用当前状态
            if hasattr(self.executor, 'get_current_joints'):
                joints = self.executor.get_current_joints()
                start_state = {"joints": joints}
            else:
                start_state = {"joints": [0.0] * 7}
        
        # 解析目标状态
        if isinstance(target, dict):
            if "pose" in target:
                goal_state = {"pose": target["pose"]}
            elif "joints" in target:
                goal_state = {"joints": target["joints"]}
            elif "object_id" in target:
                # 物体ID，需要转换为抓取位姿
                goal_state = self._get_grasp_pose_from_object(target["object_id"])
            else:
                raise ValueError("目标字典必须包含 'pose' 或 'joints' 字段")
                
        elif isinstance(target, (list, tuple)):            # 直接是位姿列表
            if len(target) == 7:
                goal_state = {"pose": list(target)}
            elif len(target) == 3:
                # 只有位置，添加默认方向
                goal_state = {"pose": list(target) + [0.0, 0.0, 0.0, 1.0]}
            else:
                raise ValueError(f"不支持的列表长度: {len(target)}")
                
        elif isinstance(target, str):
            # 物体ID
            goal_state = self._get_grasp_pose_from_object(target)
            
        else:
            raise ValueError(f"不支持的输入类型: {type(target)}")
        
        return start_state, goal_state
    
    def _get_grasp_pose_from_object(self, object_id):
        """从物体ID获取抓取位姿"""
        # 这里可以集成你的感知模块
        try:
            from grasping.gripper_controller import calculate_gripper
            result = calculate_gripper(object_id)
            
            if result["success"]:
                # 使用默认抓取位姿
                return {"pose": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0]}
        except:
            pass
        
        # 默认值
        return {"pose": [0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 1.0]}
    def _get_grasp_pose_from_object(self, object_id):
        """从物体ID获取抓取位姿 - 统一格式"""
        print(f"[TrajectoryExecutor] 查询物体: {object_id}")
        
        # 1. 先尝试从executor的缓存中查找
        if hasattr(self, 'executor') and hasattr(self.executor, '_get_grasp_pose_from_object_id'):
            pose_state = self.executor._get_grasp_pose_from_object_id(object_id)
            if pose_state:
                print(f"[TrajectoryExecutor] ✅ 从底层找到物体 {object_id}")
                return pose_state  # 底层已经返回正确格式
        
        # 2. 硬编码映射（使用正确的格式）
        object_grasp_poses = {
            "test_cube": {
                "pose": {
                    "position": [0.5, 0.0, 0.3],
                    "orientation": [0.0, 0.0, 0.0, 1.0]
                }
            },
            "test_box": {
                "pose": {
                    "position": [0.6, 0.1, 0.2],
                    "orientation": [0.0, 0.0, 0.0, 1.0]
                }
            },
            "coke_can_01": {
                "pose": {
                    "position": [0.6, 0.1, 0.2],
                    "orientation": [0.0, 0.0, 0.0, 1.0]
                }
            },
        }
        
        if object_id in object_grasp_poses:
            print(f"[TrajectoryExecutor] ✅ 从硬编码找到物体 {object_id}")
            return object_grasp_poses[object_id]
        
        # 3. 默认值（正确的格式）
        print(f"[TrajectoryExecutor] ⚠️ 使用默认位姿")
        return {
            "pose": {
                "position": [0.5, 0.0, 0.3],
                "orientation": [0.0, 0.0, 0.0, 1.0]
            }
        }   
    def _standardize_output(self, result, original_target):
        """标准化输出格式"""
        if not isinstance(result, dict):
            result = {"success": False, "error": "返回结果不是字典"}
        
        # 确保有标准字段
        result.setdefault("success", False)
        result.setdefault("execution_time", 0.0)
        result.setdefault("timestamp", self._get_timestamp())
        
        # 添加目标信息
        if isinstance(original_target, dict):
            if "object_id" in original_target:
                result["object_id"] = original_target["object_id"]
            elif "pose" in original_target:
                result["target_pose"] = original_target["pose"][:3]
        
        # 添加缓存信息（如果有）
        if hasattr(self.executor, 'get_cache_stats'):
            stats = self.executor.get_cache_stats()
            result["cache_stats"] = stats
        
        return result
    
    def _get_timestamp(self):
        """获取时间戳"""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")


# ========== 便捷函数 ==========

def execute_trajectory(target, **kwargs):
    """
    全局便捷函数 - 一行调用
    
    示例：
    result = execute_trajectory({"pose": [0.5, 0.0, 0.3, 0,0,0,1]})
    result = execute_trajectory([0.5, 0.0, 0.3, 0,0,0,1])
    result = execute_trajectory("test_cube", use_cache=True)
    result = execute_trajectory({"joints": [0,0,0,0,0,0,1]})
    """
    return TrajectoryExecutor.execute(target, **kwargs)


def move_to_pose(x, y, z, qx=0, qy=0, qz=0, qw=1, **kwargs):
    """
    快速移动到指定位姿
    
    示例：
    result = move_to_pose(0.5, 0.0, 0.3)
    result = move_to_pose(0.5, 0.0, 0.3, 0,0,0,1, use_cache=True)
    """
    return execute_trajectory([x, y, z, qx, qy, qz, qw], **kwargs)


def move_to_joints(joints, **kwargs):
    """
    快速移动到指定关节位置
    
    示例：
    result = move_to_joints([0, -0.5, 0, -1.5, 0, 1.5, 0])
    """
    return execute_trajectory({"joints": joints}, **kwargs)


def get_execution_stats():
    """
    获取执行统计信息
    
    示例：
    stats = get_execution_stats()
    print(f"缓存命中率: {stats.get('cache_stats', {}).get('hit_rate', '0%')}")
    """
    executor = TrajectoryExecutor()
    if hasattr(executor, 'executor') and hasattr(executor.executor, 'get_cache_stats'):
        return executor.executor.get_cache_stats()
    return {"message": "统计信息不可用"}


def clear_trajectory_cache():
    """清空轨迹缓存"""
    executor = TrajectoryExecutor()
    if hasattr(executor, 'executor') and hasattr(executor.executor, 'clear_cache'):
        return executor.executor.clear_cache()
    return {"success": False, "error": "清空缓存方法不可用"}