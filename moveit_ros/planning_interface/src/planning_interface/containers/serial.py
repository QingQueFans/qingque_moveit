# planning_interface/src/planning_interface/containers/serial.py
"""
SerialContainer - 串行执行多个 Stage
"""

import sys
import os
import time
from typing import Dict, Any, Optional, List

# ========== 暴力引入路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

from ..core.container import Container
from ..stages.base import Stage


class SerialContainer(Container):
    """
    串行容器 - 按顺序执行所有子 Stage
    
    如果某个 Stage 失败，可以选择停止或继续
    """
    
    def __init__(self, name: str, stop_on_failure: bool = True):
        """
        初始化串行容器
        
        Args:
            name: 容器名称
            stop_on_failure: 失败时是否停止后续执行
        """
        super().__init__(name, "serial")
        self.stop_on_failure = stop_on_failure
        self.stages: List[Stage] = []
    
    # ========== 添加 Stage ==========
    
    def add(self, stage: Stage) -> 'SerialContainer':
        """添加子 Stage"""
        self.stages.append(stage)
        return self
    
    def add_stages(self, stages: List[Stage]) -> 'SerialContainer':
        """批量添加子 Stage"""
        self.stages.extend(stages)
        return self
    
    # ========== 核心执行 ==========
    
    def run(self) -> Dict[str, Any]:
        """
        按顺序执行所有子 Stage
        
        Returns:
            执行结果，包含每个 stage 的结果
        """
        self.start_time = time.time()
        
        results = []
        all_success = True
        
        print(f"\n[SerialContainer] 开始执行 {len(self.stages)} 个 Stage")
        
        for i, stage in enumerate(self.stages):
            print(f"  [{i+1}/{len(self.stages)}] 执行 {stage.name}...")
            
            try:
                # 执行子 Stage
                result = stage.run()
                results.append({
                    "name": stage.name,
                    "type": stage.type,
                    "success": result.get("success", False),
                    "result": result,
                    "duration": stage.get_duration()
                })
                
                if not result.get("success", False):
                    all_success = False
                    print(f"    ❌ 失败: {result.get('error', '未知错误')}")
                    if self.stop_on_failure:
                        print(f"    ⛔ 停止后续执行")
                        break
                else:
                    print(f"    ✅ 成功")
                    
            except Exception as e:
                all_success = False
                results.append({
                    "name": stage.name,
                    "type": stage.type,
                    "success": False,
                    "error": str(e)
                })
                print(f"    ❌ 异常: {e}")
                if self.stop_on_failure:
                    break
        
        self.end_time = time.time()
        
        # 汇总结果
        self.last_result = {
            "success": all_success,
            "stage_count": len(self.stages),
            "executed_count": len(results),
            "stage_results": results,
            "total_duration": self.get_duration()
        }
        
        print(f"[SerialContainer] 完成，总体成功: {all_success}")
        return self.last_result
    
    # ========== 配置方法 ==========
    
    def set_stop_on_failure(self, stop: bool) -> 'SerialContainer':
        """设置失败时是否停止"""
        self.stop_on_failure = stop
        return self
    
    # ========== 查询方法 ==========
    
    def get_stages(self) -> List[Stage]:
        """获取所有子 Stage"""
        return self.stages
    
    def get_stage_by_name(self, name: str) -> Optional[Stage]:
        """根据名称查找子 Stage"""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None
    
    def get_successful_stages(self) -> List[Stage]:
        """获取成功的子 Stage"""
        if not self.last_result:
            return []
        successful_names = [r["name"] for r in self.last_result["stage_results"] if r["success"]]
        return [s for s in self.stages if s.name in successful_names]
    
    def get_failed_stages(self) -> List[Stage]:
        """获取失败的子 Stage"""
        if not self.last_result:
            return []
        failed_names = [r["name"] for r in self.last_result["stage_results"] if not r["success"]]
        return [s for s in self.stages if s.name in failed_names]
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "stop_on_failure": self.stop_on_failure,
            "stage_count": len(self.stages),
            "stages": [s.to_dict() for s in self.stages]
        })
        if self.last_result:
            base_dict["executed_count"] = self.last_result.get("executed_count", 0)
            base_dict["stage_results"] = self.last_result.get("stage_results", [])
        return base_dict
    
    def __repr__(self) -> str:
        return (f"SerialContainer(name='{self.name}', "
                f"stages={len(self.stages)}, "
                f"stop_on_failure={self.stop_on_failure}, "
                f"success={self.was_successful()})")


# ========== 快捷函数 ==========

def serial(name: str, *stages: Stage, stop_on_failure: bool = True) -> SerialContainer:
    """创建串行容器"""
    container = SerialContainer(name, stop_on_failure)
    for stage in stages:
        container.add(stage)
    return container


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 SerialContainer ===\n")
    
    # 创建一些模拟 Stage 用于测试
    from ..stages.base import Stage
    
    class DummyStage(Stage):
        def __init__(self, name: str, should_succeed: bool = True):
            super().__init__(name, "dummy")
            self.should_succeed = should_succeed
        
        def run(self):
            self.start_time = time.time()
            time.sleep(0.1)  # 模拟执行时间
            self.last_result = {
                "success": self.should_succeed,
                "value": 42
            }
            self.end_time = time.time()
            return self.last_result
    
    # 测试全部成功
    print("测试1: 全部成功")
    container = SerialContainer("test1")
    container.add(DummyStage("stage1", True))
    container.add(DummyStage("stage2", True))
    container.add(DummyStage("stage3", True))
    result = container.run()
    print(f"结果: {result['success']}")
    print(f"执行了 {result['executed_count']}/{result['stage_count']} 个 Stage")
    print(f"容器: {container}")
    
    # 测试中途失败
    print("\n测试2: 中途失败（stop_on_failure=True）")
    container = SerialContainer("test2", stop_on_failure=True)
    container.add(DummyStage("stage1", True))
    container.add(DummyStage("stage2", False))
    container.add(DummyStage("stage3", True))
    result = container.run()
    print(f"结果: {result['success']}")
    print(f"执行了 {result['executed_count']}/{result['stage_count']} 个 Stage")
    
    # 测试失败继续
    print("\n测试3: 失败继续（stop_on_failure=False）")
    container = SerialContainer("test3", stop_on_failure=False)
    container.add(DummyStage("stage1", True))
    container.add(DummyStage("stage2", False))
    container.add(DummyStage("stage3", True))
    result = container.run()
    print(f"结果: {result['success']}")
    print(f"执行了 {result['executed_count']}/{result['stage_count']} 个 Stage")
    
    # 测试快捷函数
    print("\n测试4: 快捷函数")
    stage1 = DummyStage("quick1", True)
    stage2 = DummyStage("quick2", True)
    container = serial("quick", stage1, stage2)
    result = container.run()
    print(f"结果: {result['success']}")
    print(f"容器: {container}")
    
    # 显示调试信息
    print(f"\n调试信息: {container.to_dict()}")