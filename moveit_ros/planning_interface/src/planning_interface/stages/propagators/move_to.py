# planning_interface/src/planning_interface/stages/propagators/move_to.py
"""
MoveTo Stage - 移动到目标位姿或关节位置
"""
import sys
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap
from typing import Dict, Any, Optional, Union, List
import time

from ..base import Stage
from trajectory_execution import execute_trajectory


class MoveTo(Stage):
    """
    移动到目标位姿或关节位置
    
    封装 execute_trajectory，提供 Stage 接口
    """
    
    def __init__(self, name: str, executor=None):
        """
        初始化 MoveTo Stage
        
        Args:
            name: Stage 名称
            executor: 执行函数（默认用 execute_trajectory）
        """
        super().__init__(name, "propagator")
        self.executor = executor or execute_trajectory
        self.config = {
            "timeout": 5.0,
            "use_cache": True,
            "algorithm": "rrt_connect"
        }
    
    # ========== 核心执行 ==========
    


    def run(self, target=None, **kwargs) -> Dict[str, Any]:
        """
        执行移动到目标
        
        支持两种调用方式：
        1. stage.run(pose)                    # 直接传 target
        2. stage.set_target(pose).run()       # 链式调用，不传参数
        
        Args:
            target: 目标位姿/关节（可选）
            **kwargs: 覆盖默认配置
            
        Returns:
            执行结果字典
        """
        self.start_time = time.time()
        
        # ===== 兼容两种调用方式 =====
        if target is None:
            # 链式调用：从 self._target 取
            if not hasattr(self, '_target') or self._target is None:
                self.last_error = "未指定目标，请直接传参或先调用 set_target()"
                self.last_result = {"success": False, "error": self.last_error}
                return self.last_result
            target = self._target
        else:
            # 直接调用：同时更新 self._target 供后续查询
            self._target = target
        
        # 合并配置
        config = {**self.config, **kwargs}
        
        try:
            # 标准化输入
            goal = self._normalize_target(target)
            
            # 执行移动
            self.last_result = self.executor(
                goal,
                timeout=config["timeout"],
                use_cache=config["use_cache"],
                algorithm=config["algorithm"]
            )
            
        except Exception as e:
            self.last_error = str(e)
            self.last_result = {
                "success": False,
                "error": str(e)
            }
        
        self.end_time = time.time()
        return self.last_result
    # ========== 目标标准化 ==========
    
    def _normalize_target(self, target) -> Dict:
        """将各种输入格式标准化为 execute_trajectory 需要的格式"""
        
        # 如果是物体ID，尝试从缓存获取位姿
        if isinstance(target, str):
            # 这里需要 knowledge 支持，暂时先抛异常
            raise ValueError(f"物体ID模式需要 knowledge 支持: {target}")
        
        # 如果是列表
        if isinstance(target, (list, tuple)):
            if len(target) == 7:  # 完整位姿
                return {"pose": list(target)}
            elif len(target) == 3:  # 只有位置，加默认方向
                return {"pose": list(target) + [0, 0, 0, 1]}
            else:  # 假设是关节
                return {"joints": list(target)}
        
        # 如果是字典
        if isinstance(target, dict):
            if "pose" in target or "joints" in target:
                return target
            if "position" in target:  # 可能是物体信息
                pos = target.get("position", [0,0,0])
                orient = target.get("orientation", [0,0,0,1])
                return {"pose": pos + orient}
        
        # 默认
        return {"pose": list(target) if hasattr(target, '__iter__') else [0,0,0,0,0,0,1]}
    
    # ========== 链式配置 ==========
    
    def set_timeout(self, timeout: float):
        """设置超时时间"""
        self.config["timeout"] = timeout
        return self
    
    def set_cache(self, use_cache: bool):
        """设置是否使用缓存"""
        self.config["use_cache"] = use_cache
        return self
    
    def set_algorithm(self, algorithm: str):
        """设置规划算法"""
        self.config["algorithm"] = algorithm
        return self
    
    # ========== 静态工厂方法 ==========
    
    @classmethod
    def to_pose(cls, pose: List[float], **kwargs) -> Dict:
        """一行调用：移动到指定位姿"""
        stage = cls("static_move")
        return stage.run(pose, **kwargs)
    
    @classmethod
    def to_joints(cls, joints: List[float], **kwargs) -> Dict:
        """一行调用：移动到指定关节"""
        stage = cls("static_move")
        return stage.run({"joints": joints}, **kwargs)
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["config"] = self.config.copy()
        if self.last_result:
            base_dict["planning_time"] = self.last_result.get("planning_time", 0)
            base_dict["point_count"] = self.last_result.get("point_count", 0)
        return base_dict


# ========== 快捷函数 ==========

def move_to_pose(pose: List[float], **kwargs) -> Dict:
    """快捷移动到指定位姿"""
    return MoveTo.to_pose(pose, **kwargs)

def move_to_joints(joints: List[float], **kwargs) -> Dict:
    """快捷移动到指定关节"""
    return MoveTo.to_joints(joints, **kwargs)
# 临时测试
if __name__ == "__main__":
    stage = MoveTo("test")
    
    # 测试位姿
    result = stage.run([0.5, 0.0, 0.3, 0,0,0,1], timeout=3.0)
    print(f"结果: {result.get('success')}")
    print(f"Stage: {stage}")
    
    # 测试链式调用
    result = (MoveTo("chain")
              .set_timeout(8.0)
              .set_cache(True)
              .set_target([0.5, 0.0, 0.3])
              .execute())
    print(f"链式结果: {result.get('success')}")