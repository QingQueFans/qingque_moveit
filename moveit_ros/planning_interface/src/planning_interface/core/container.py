# planning_interface/src/planning_interface/core/container.py
"""
Container 基类 - 所有容器的祖宗
定义容器应该有的基本接口
"""

import sys
import os
from typing import List, Optional, Dict, Any

# ========== 暴力引入路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

from ..stages.base import Stage


class Container(Stage):
    """
    容器基类
    可以包含多个子 Stage，定义它们如何执行
    
    所有具体容器（Serial, Parallel, Alternative 等）都应继承此类
    """
    
    def __init__(self, name: str, container_type: str = "generic"):
        """
        初始化容器
        
        Args:
            name: 容器名称
            container_type: 容器类型（serial/parallel/alternative等）
        """
        super().__init__(name, f"container_{container_type}")
        self.stages: List[Stage] = []
    
    # ========== 子 Stage 管理 ==========
    
    def add(self, stage: Stage) -> 'Container':
        """
        添加子 Stage
        
        Args:
            stage: 要添加的 Stage
            
        Returns:
            self（支持链式调用）
        """
        self.stages.append(stage)
        return self
    
    def add_stages(self, stages: List[Stage]) -> 'Container':
        """批量添加子 Stage"""
        self.stages.extend(stages)
        return self
    
    def insert(self, index: int, stage: Stage) -> 'Container':
        """在指定位置插入子 Stage"""
        self.stages.insert(index, stage)
        return self
    
    def remove(self, stage: Stage) -> 'Container':
        """移除指定的子 Stage"""
        if stage in self.stages:
            self.stages.remove(stage)
        return self
    
    def remove_by_name(self, name: str) -> 'Container':
        """根据名称移除子 Stage"""
        self.stages = [s for s in self.stages if s.name != name]
        return self
    
    def clear(self) -> 'Container':
        """清空所有子 Stage"""
        self.stages.clear()
        return self
    
    # ========== 查询方法 ==========
    
    def get_stages(self) -> List[Stage]:
        """获取所有子 Stage"""
        return self.stages.copy()
    
    def get_stage_by_name(self, name: str) -> Optional[Stage]:
        """根据名称查找子 Stage"""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None
    
    def get_stage_by_index(self, index: int) -> Optional[Stage]:
        """根据索引获取子 Stage"""
        if 0 <= index < len(self.stages):
            return self.stages[index]
        return None
    
    def get_stage_count(self) -> int:
        """获取子 Stage 数量"""
        return len(self.stages)
    
    def has_stage(self, name: str) -> bool:
        """检查是否存在指定名称的 Stage"""
        return self.get_stage_by_name(name) is not None
    
    # ========== 执行相关（子类必须实现） ==========
    
    def run(self) -> Dict[str, Any]:
        """
        执行容器
        
        子类必须实现这个方法，定义子 Stage 的执行顺序和逻辑
        
        Returns:
            执行结果字典
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 run() 方法"
        )
    
    # ========== 结果查询 ==========
    
    def get_stage_results(self) -> List[Dict[str, Any]]:
        """获取所有子 Stage 的执行结果"""
        if not self.last_result:
            return []
        return self.last_result.get("stage_results", [])
    
    def get_successful_stages(self) -> List[Stage]:
        """获取成功的子 Stage"""
        if not self.last_result:
            return []
        successful_names = [
            r["name"] for r in self.last_result.get("stage_results", [])
            if r.get("success")
        ]
        return [s for s in self.stages if s.name in successful_names]
    
    def get_failed_stages(self) -> List[Stage]:
        """获取失败的子 Stage"""
        if not self.last_result:
            return []
        failed_names = [
            r["name"] for r in self.last_result.get("stage_results", [])
            if not r.get("success")
        ]
        return [s for s in self.stages if s.name in failed_names]
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "stage_count": len(self.stages),
            "stages": [s.to_dict() for s in self.stages]
        })
        return base_dict
    
    def print_stages(self, indent: int = 0) -> None:
        """打印所有子 Stage"""
        prefix = "  " * indent
        print(f"{prefix}Container '{self.name}' 包含 {len(self.stages)} 个 Stage:")
        for i, stage in enumerate(self.stages):
            print(f"{prefix}  [{i+1}] {stage}")
            if hasattr(stage, 'print_stages'):  # 如果子 Stage 也是容器
                stage.print_stages(indent + 1)
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"stages={len(self.stages)}, success={self.was_successful()})")


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 Container 基类 ===\n")
    
    # 创建一些模拟 Stage 用于测试
    from ..stages.base import Stage
    
    class DummyStage(Stage):
        def __init__(self, name: str):
            super().__init__(name, "dummy")
        
        def run(self):
            self.last_result = {"success": True}
            return self.last_result
    
    # 测试容器创建
    container = Container("test_container")
    print(f"创建容器: {container}")
    
    # 测试添加 Stage
    stage1 = DummyStage("stage1")
    stage2 = DummyStage("stage2")
    
    container.add(stage1).add(stage2)
    print(f"添加后: {container}")
    print(f"Stage 数量: {container.get_stage_count()}")
    
    # 测试查询
    found = container.get_stage_by_name("stage1")
    print(f"查找 stage1: {found}")
    
    # 测试移除
    container.remove_by_name("stage1")
    print(f"移除后: {container}")
    
    # 测试清空
    container.clear()
    print(f"清空后: {container}")
    
    # 测试 run 方法（应该抛出异常）
    try:
        container.run()
    except NotImplementedError as e:
        print(f"预期中的异常: {e}")
    
    # 显示调试信息
    print(f"\n调试信息: {container.to_dict()}")