# planning_interface/src/planning_interface/stages/modifiers/attach.py
"""
AttachObject Stage - 抓取物体（夹爪闭合 + 附着）
"""

import sys
import os
import time
from typing import Dict, Any, Optional

# ========== 暴力引入路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
import moveit_bootstrap

from ..base import Stage
from capability_servers_core.pick_action_server import smart_grab, quick_grab


class AttachObject(Stage):
    """
    抓取物体 Stage
    
    封装 smart_grab/quick_grab，提供 Stage 接口
    负责：夹爪闭合 + 物体附着
    """
    
    def __init__(self, name: str):
        """
        初始化 AttachObject Stage
        
        Args:
            name: Stage 名称
        """
        super().__init__(name, "modifier")
        self.config = {
            "effort": 30.0,      # 默认夹紧力
            "strategy": "auto",   # 默认抓取策略
        }
        self.object_id = None
    
    # ========== 核心执行 ==========
    
# planning_interface/src/planning_interface/stages/modifiers/attach.py

    def run(self, object_id=None, **kwargs) -> Dict[str, Any]:
        """
        执行抓取
        
        支持两种调用方式：
        1. stage.run("train_1")                    # 直接传 object_id
        2. stage.set_object("train_1").run()       # 链式调用，不传参数
        
        Args:
            object_id: 要抓取的物体ID（可选）
            **kwargs: 覆盖默认配置
                
        Returns:
            抓取结果字典
        """
        self.start_time = time.time()
        
        # ===== 兼容两种调用方式 =====
        if object_id is None:
            # 链式调用：从 self.object_id 取
            if not hasattr(self, 'object_id') or self.object_id is None:
                self.last_error = "未指定物体ID，请直接传参或先调用 set_object()"
                self.last_result = {"success": False, "error": self.last_error}
                return self.last_result
            object_id = self.object_id
        else:
            # 直接调用：同时更新 self.object_id 供后续查询
            self.object_id = object_id
        
        # 合并配置
        config = {**self.config, **kwargs}
        width_mm = kwargs.get('width')
        
        try:
            if width_mm is not None:
                self.last_result = quick_grab(
                    object_id,
                    width_mm=width_mm,
                    effort=config["effort"]
                )
            else:
                self.last_result = smart_grab(
                    object_id,
                    strategy=config["strategy"]
                )
        except Exception as e:
            self.last_error = str(e)
            self.last_result = {"success": False, "error": str(e)}
        
        self.end_time = time.time()
        return self.last_result
    # ========== 链式配置 ==========
    
    def set_object(self, object_id: str):
        """设置要抓取的物体"""
        self.object_id = object_id
        self._target = object_id
        return self
    
    def set_width(self, width_mm: float):
        """设置夹爪宽度（毫米）"""
        self.config["width"] = width_mm
        return self
    
    def set_effort(self, effort: float):
        """设置夹紧力（牛顿）"""
        self.config["effort"] = effort
        return self
    
    def set_strategy(self, strategy: str):
        """设置抓取策略"""
        self.config["strategy"] = strategy
        return self
    
    # ========== 静态工厂方法 ==========
    
    @classmethod
    def grab(cls, object_id: str, **kwargs) -> Dict:
        """一行调用：抓取物体"""
        stage = cls("static_grab")
        return stage.run(object_id, **kwargs)
    
    @classmethod
    def grab_with_width(cls, object_id: str, width_mm: float, **kwargs) -> Dict:
        """一行调用：指定宽度抓取"""
        stage = cls("static_grab")
        kwargs['width'] = width_mm
        return stage.run(object_id, **kwargs)
    
    # ========== 结果查询 ==========
    
    def get_grasp_width(self) -> Optional[float]:
        """获取实际使用的夹爪宽度（毫米）"""
        if self.last_result:
            return self.last_result.get("grasp_width_mm")
        return None
    
    def get_grasp_force(self) -> Optional[float]:
        """获取实际使用的夹紧力"""
        if self.last_result:
            return self.last_result.get("grasp_force")
        return None
    
    # ========== 调试方法 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["object_id"] = self.object_id
        base_dict["config"] = self.config.copy()
        if self.last_result:
            base_dict["grasp_width_mm"] = self.get_grasp_width()
            base_dict["grasp_force"] = self.get_grasp_force()
        return base_dict


# ========== 快捷函数 ==========

def attach_object(object_id: str, **kwargs) -> Dict:
    """快捷抓取物体"""
    return AttachObject.grab(object_id, **kwargs)

def attach_with_width(object_id: str, width_mm: float, **kwargs) -> Dict:
    """快捷指定宽度抓取"""
    return AttachObject.grab_with_width(object_id, width_mm, **kwargs)


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 测试 AttachObject Stage ===\n")
    
    # 测试基础 run
    stage = AttachObject("test_grasp")
    result = stage.run("train_1")
    print(f"基础抓取: {result.get('success')}")
    print(f"Stage: {stage}")
    
    # 测试链式调用
    result = (AttachObject("chain_grasp")
              .set_object("train_1")
              .set_width(40)
              .set_effort(35)
              .execute())
    print(f"链式抓取: {result.get('success')}")
    
    # 测试静态方法
    result = AttachObject.grab("train_1", width=45)
    print(f"静态抓取: {result.get('success')}")
    
    # 显示调试信息
    print(f"\n调试信息: {stage.to_dict()}")