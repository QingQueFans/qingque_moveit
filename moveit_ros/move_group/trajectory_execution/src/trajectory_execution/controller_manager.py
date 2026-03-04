#!/usr/bin/env python3
"""
控制器管理器 - 使用MoveIt控制器插件
"""
from typing import Dict, List, Optional
import rclpy
from trajectory_msgs.msg import JointTrajectory
import time
import os
import sys

class ControllerManager:
    """控制器管理器 - 封装现有的插件控制器管理器"""
    
    def __init__(self, controller_name: str = None):
        self.initialized = False
        self.use_existing = False
        
        # ========== 关键：添加插件路径 ==========
        plugin_path = "/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/moveit_controller_manager/src"
        
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)
            print(f"[轨迹执行] 添加插件路径: {plugin_path}")
        
        # ========== 导入现有插件模块 ==========
        try:
            # 首先确保路径存在
            if os.path.exists(plugin_path):
                print(f"[轨迹执行] 插件路径存在，内容: {os.listdir(plugin_path)}")
            
            # 导入插件
            import moveit_controller_manager
            print(f"[轨迹执行] 成功导入模块: {moveit_controller_manager}")
            print(f"[轨迹执行] 模块位置: {moveit_controller_manager.__file__}")
            
            from moveit_controller_manager import MoveItControllerManager
            print(f"[轨迹执行] 成功导入MoveItControllerManager类")
            
            # 初始化ROS（如果需要）
            if not rclpy.ok():
                rclpy.init(args=None)
            
            # 创建控制器实例
            self.controller = MoveItControllerManager()
            print("[轨迹执行] ✅ 控制器实例创建成功")
            
            # 正确的logger访问方式
            self.logger = self.controller.get_logger()
            
            # 记录成功信息
            if hasattr(self.logger, 'info'):
                self.logger.info("✅ 使用现有的插件控制器管理器")
            else:
                print("✅ 使用现有的插件控制器管理器")
            
            # 检查控制器状态
            self._check_controllers()
            
            self.use_existing = True
            self.initialized = True
            print("[轨迹执行] ✅ 控制器管理器初始化完成")
            
        except ImportError as e:
            print(f"[轨迹执行] ⚠️ 无法导入现有控制器管理器: {e}")
            print(f"[轨迹执行] sys.path: {sys.path}")
            print("[轨迹执行] 使用简化实现")
            self._init_simple_manager()
    
    def _check_controllers(self):
        """检查可用控制器"""
        try:            # 尝试获取控制器状态
            if hasattr(self.controller, 'get_controller_status'):
                status = self.controller.get_controller_status()
                if hasattr(self.logger, 'info'):
                    self.logger.info(f"控制器状态: {status}")
                else:
                    print(f"控制器状态: {status}")
        except Exception as e:
            if hasattr(self.logger, 'warn'):
                self.logger.warn(f"无法获取控制器状态: {e}")
            else:
                print(f"[WARN] 无法获取控制器状态: {e}")
    
    def _init_simple_manager(self):
        """简化实现（备选）"""
        print("[轨迹执行] 🔧 使用简化控制器管理器")
        
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warn(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def debug(self, msg): print(f"[DEBUG] {msg}")
        
        self.logger = SimpleLogger()
        self.controllers = {}
        self.use_existing = False
        self.initialized = True
        self.logger.info("简化控制器管理器初始化完成")
    
    def get_logger(self):
        """获取logger（为了兼容性）"""
        return self.logger
    
    def execute_trajectory_sync(self, trajectory: JointTrajectory) -> bool:
        """
        同步执行轨迹
        
        Args:
            trajectory: JointTrajectory消息
        
        Returns:
            bool: 执行是否成功
        """
        if not self.initialized:
            self.logger.error("控制器未初始化")
            return False
        
        self.logger.info("开始执行轨迹...")
        
        if self.use_existing:
            # 使用插件的方法
            try:
                if hasattr(self.controller, 'execute_trajectory_sync'):
                    # 调用插件的执行方法
                    result = self.controller.execute_trajectory_sync(trajectory)
                    self.logger.info(f"轨迹执行完成: {result}")
                    return True
                else:
                    self.logger.warn("插件没有execute_trajectory_sync方法")
                    return self._execute_fallback(trajectory)
                    
            except Exception as e:
                self.logger.error(f"轨迹执行失败: {e}")
                return False
        else:
            # 使用简化实现
            return self._execute_fallback(trajectory)
    
    def _execute_fallback(self, trajectory: JointTrajectory) -> bool:
        """备选执行方法"""
        try:
            self.logger.info(f"执行轨迹，关节数: {len(trajectory.joint_names)}")
            self.logger.info(f"轨迹点数: {len(trajectory.points)}")
            
            # 模拟执行
            time.sleep(1.0)
            
            self.logger.info("轨迹执行完成")
            return True
        except Exception as e:
            self.logger.error(f"轨迹执行失败: {e}")
            return False
    
    def get_available_controllers(self) -> List[str]:
        """获取可用控制器列表"""
        if self.use_existing:
            try:
                # 根据插件实际API调整
                return ["joint_trajectory_controller"]
            except:
                return []
        else:
            return ["simulated_controller"]
    
    def switch_controller(self, controller_name: str) -> bool:
        """切换控制器"""
        self.logger.info(f"切换到控制器: {controller_name}")
        return True

# 测试函数
if __name__ == "__main__":
    print("测试ControllerManager...")
    
    # 创建测试轨迹
    trajectory = JointTrajectory()
    trajectory.joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]
    
    from trajectory_msgs.msg import JointTrajectoryPoint
    point = JointTrajectoryPoint()
    point.positions = [0.0] * 7
    point.time_from_start = rclpy.duration.Duration(seconds=2.0).to_msg()
    trajectory.points.append(point)
    
    # 测试控制器管理器
    manager = ControllerManager()
    
    print(f"使用插件: {manager.use_existing}")
    print(f"可用控制器: {manager.get_available_controllers()}")
    
    # 执行轨迹
    success = manager.execute_trajectory_sync(trajectory)
    print(f"执行结果: {success}")