# planning_interface/src/planning_interface/stages/base.py
"""
Stage 基类
所有 Stage 的祖宗，提供统一接口
"""

from typing import Optional, Dict, Any, List
import time


class Stage:
    """
    所有 Stage 的基类
    
    每个 Stage 都是一个可执行单元，有名字、能运行、能查结果
    """
    
    def __init__(self, name: str, stage_type: str = "generic"):
        """
        初始化 Stage
        
        Args:
            name: Stage 名称（用于调试和日志）
            stage_type: Stage 类型（generator/propagator/connector/modifier）
        """
        self.name = name
        self.type = stage_type
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._target = None
    
    # ========== 核心执行 ==========
    
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        执行 Stage 的核心逻辑
        子类必须重写这个方法
        """
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 run() 方法")
    
    # ========== 结果查询 ==========
    
    def was_successful(self) -> bool:
        """检查上一次执行是否成功"""
        if not self.last_result:
            return False
        return self.last_result.get("success", False)
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """获取上一次执行的结果"""
        return self.last_result
    
    def get_error(self) -> Optional[str]:
        """获取错误信息"""
        return self.last_error
    
    def get_duration(self) -> float:
        """获取执行耗时"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    # ========== 链式调用支持 ==========
    
    def set_target(self, target):
        """设置目标（链式调用用）"""
        self._target = target
        return self
    
    def execute(self, **kwargs):
        """执行预设的目标（链式调用用）"""
        if self._target is None:
            raise ValueError(f"Stage '{self.name}' 未设置目标，请先调用 set_target()")
        return self.run(self._target, **kwargs)
    
    # ========== 配置方法 ==========
    
    def configure(self, **kwargs):
        """批量设置配置"""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于调试和日志"""
        return {
            "name": self.name,
            "type": self.type,
            "success": self.was_successful(),
            "duration": self.get_duration(),
            "error": self.last_error
        }
    
    def __repr__(self) -> str:
        status = "✓" if self.was_successful() else "✗" if self.last_result else "○"
        return f"{self.__class__.__name__}(name='{self.name}', {status})"
    
    def __str__(self) -> str:
        return self.__repr__()


# ========== 容器基类（可选） ==========

class Container(Stage):
    """
    容器基类
    可以包含多个子 Stage
    """
    
    def __init__(self, name: str, container_type: str = "serial"):
        super().__init__(name, f"container_{container_type}")
        self.stages: List[Stage] = []
        self.stop_on_failure = True
    
    def add(self, stage: Stage):
        """添加子 Stage"""
        self.stages.append(stage)
        return self
    
    def get_stages(self) -> List[Stage]:
        """获取所有子 Stage"""
        return self.stages
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["stages"] = [s.to_dict() for s in self.stages]
        base_dict["stage_count"] = len(self.stages)
        return base_dict