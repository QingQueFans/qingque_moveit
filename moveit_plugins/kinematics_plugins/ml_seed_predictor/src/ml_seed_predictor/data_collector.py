#!/usr/bin/env python3
"""
数据收集器 - 管理训练数据
"""
import json
import time
import numpy as np
from pathlib import Path
import yaml

class DataCollector:
    """训练数据收集器"""
    
    def __init__(self, config_path=None):
        self.data = []
        self.config = self._load_config(config_path)
        
        # 文件路径
        package_dir = Path(__file__).parent.parent
        self.data_dir = package_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        self.data_path = self.data_dir / 'training_data.json'
        self._load_data()
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "max_samples": 1000,
            "save_frequency": 1
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        else:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
        
        return default_config
    
    def add_sample(self, target_pose, successful_seed, error_mm=0, object_id=None):
        """添加样本"""
        self.data.append({
            "target_pose": [float(x) for x in target_pose],
            "seed": [float(x) for x in successful_seed],
            "error": float(error_mm),
            "object_id": object_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 限制样本数量
        if len(self.data) > self.config["max_samples"]:
            self.data = self.data[-self.config["max_samples"]:]
        
        self._save_data()
    
    def get_training_data(self):
        """获取训练数据"""
        if len(self.data) < 3:
            return [], []
        
        X = []
        y = []
        for d in self.data:
            X.append(d["target_pose"])
            y.append(d["seed"])
        
        return np.array(X), np.array(y)
    
    def size(self):
        """样本数量"""
        return len(self.data)
    
    def _save_data(self):
        """保存数据到文件"""
        with open(self.data_path, 'w') as f:
            json.dump({
                "samples": self.data,
                "count": len(self.data),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    
    def _load_data(self):
        """从文件加载数据"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    self.data = data.get("samples", [])
                print(f"[数据收集] 已加载 {len(self.data)} 个样本")
            except Exception as e:
                print(f"[数据收集] 加载失败: {e}")
                self.data = []
    def get_training_data_with_metadata(self):
        """获取训练数据和元数据"""
        if len(self.data) < 3:
            return [], [], []
        
        X = []
        y = []
        metadata = []
        for d in self.data:
            X.append(d["target_pose"])
            y.append(d["seed"])
            metadata.append({
                "error": d.get("error", 0),
                "object_id": d.get("object_id"),
                "timestamp": d.get("timestamp")
            })
        
        return np.array(X), np.array(y), metadata    
    def clear(self):
        """清空数据"""
        self.data = []
        self._save_data()