#!/usr/bin/env python3
"""
LMA验证器 - 验证LMA预测的质量
"""
import numpy as np
import json
from pathlib import Path
import time

class LMAValidator:
    """LMA验证器"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / 'data' / 'lma_data'
        self.data_dir = Path(data_dir)
        
        self.validation_log = self.data_dir / 'stats' / 'validation_log.json'
        self.validation_log.parent.mkdir(exist_ok=True)
        
        self.history = []
        self._load_history()
        
    def validate_prediction(self, target_pose, predicted_seed, actual_solution, error_mm):
        """验证预测质量"""
        validation = {
            "timestamp": time.time(),
            "target_pose": [float(x) for x in target_pose[:3]],
            "predicted_seed": [float(x) for x in predicted_seed] if predicted_seed is not None else None,
            "actual_solution": [float(x) for x in actual_solution] if actual_solution is not None else None,
            "error_mm": float(error_mm),
            "success": error_mm < 50  # 50mm以下算成功
        }
        
        self.history.append(validation)
        
        # 只保留最近1000条记录
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        self._save_history()
        
        return validation
    
    def get_validation_stats(self):
        """获取验证统计"""
        if not self.history:
            return {}
        
        recent = self.history[-100:]  # 最近100条
        
        errors = [v["error_mm"] for v in self.history]
        recent_errors = [v["error_mm"] for v in recent]
        successes = [v["success"] for v in self.history]
        recent_successes = [v["success"] for v in recent]
        
        return {
            "total_validations": len(self.history),
            "overall": {
                "avg_error": float(np.mean(errors)),
                "min_error": float(np.min(errors)),
                "max_error": float(np.max(errors)),
                "success_rate": float(np.mean(successes))
            },
            "recent_100": {
                "avg_error": float(np.mean(recent_errors)) if recent_errors else 0,
                "success_rate": float(np.mean(recent_successes)) if recent_successes else 0
            },
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _save_history(self):
        """保存验证历史"""
        with open(self.validation_log, 'w') as f:
            json.dump({
                "history": self.history,
                "count": len(self.history)
            }, f, indent=2)
    
    def _load_history(self):
        """加载验证历史"""
        if self.validation_log.exists():
            try:
                with open(self.validation_log, 'r') as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
            except Exception as e:
                print(f"[LMA验证] 加载失败: {e}")
