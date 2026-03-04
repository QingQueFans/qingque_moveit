# rollback_manager.py
import time
import json
import os
from typing import List, Dict, Any, Optional
from collections import deque

class RollbackManager:
    """轨迹回退管理器 - 独立类"""
    
    def __init__(self, max_history=10, cache_dir="~/.trajectory_rollback"):
        """
        初始化回退管理器
        
        Args:
            max_history: 最大历史记录数
            cache_dir: 缓存目录
        """
        self.max_history = max_history
        self.cache_dir = os.path.expanduser(cache_dir)
        self.states = deque(maxlen=max_history)
        self.current_state_id = 0
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载保存的状态
        self._load_states()
    
    def _load_states(self):
        """从文件加载保存的状态"""
        cache_file = os.path.join(self.cache_dir, "states.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.states = deque(data.get("states", []), maxlen=self.max_history)
                    self.current_state_id = data.get("current_state_id", 0)
                print(f"[回退管理器] 已加载 {len(self.states)} 个历史状态")
            except Exception as e:
                print(f"[回退管理器] 加载状态失败: {e}")
    
    def _save_states(self):
        """保存状态到文件"""
        cache_file = os.path.join(self.cache_dir, "states.json")
        try:
            data = {
                "states": list(self.states),
                "current_state_id": self.current_state_id,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[回退管理器] 保存状态失败: {e}")
    
    def add_state(self, state_data: Dict[str, Any]):
        """添加新状态"""
        state_id = self.current_state_id + 1
        self.current_state_id = state_id
        
        state_record = {
            "state_id": state_id,
            "state_data": state_data,
            "added_at": time.time()
        }
        
        self.states.append(state_record)
        self._save_states()
        
        return state_id
    
    def get_previous_state(self) -> Optional[Dict]:
        """获取上一个状态"""
        if not self.states:
            return None
        
        # 获取倒数第二个状态（最后一个是最新状态）
        if len(self.states) >= 2:
            return self.states[-2]["state_data"]
        return self.states[-1]["state_data"]
    
    def get_state_by_id(self, state_id: int) -> Optional[Dict]:
        """根据ID获取状态"""
        for state_record in reversed(self.states):
            if state_record["state_id"] == state_id:
                return state_record["state_data"]
        return None
    
    def get_available_states(self) -> List[Dict]:
        """获取所有可用状态"""
        return [record["state_data"] for record in self.states]
    
    def has_states(self) -> bool:
        """检查是否有状态记录"""
        return len(self.states) > 0
    
    @property
    def state_count(self) -> int:
        """状态数量"""
        return len(self.states)
    
    def clear_states(self):
        """清除所有状态"""
        self.states.clear()
        self.current_state_id = 0
        self._save_states()
        print("[回退管理器] 所有状态已清除")
    
    def export_states(self, filepath: str):
        """导出状态到文件"""
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "states": list(self.states),
                    "metadata": {
                        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "state_count": len(self.states)
                    }
                }, f, indent=2)
            return True
        except Exception as e:
            print(f"[回退管理器] 导出失败: {e}")
            return False