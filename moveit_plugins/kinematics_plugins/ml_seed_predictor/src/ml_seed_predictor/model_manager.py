#!/usr/bin/env python3
"""
模型管理器 - 训练和保存模型
"""
import numpy as np
from pathlib import Path
import joblib
import yaml
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor

class ModelManager:
    """模型管理器"""
    
    def __init__(self, config_path=None):
        self.model = None
        self.config = self._load_config(config_path)
        
        package_dir = Path(__file__).parent.parent
        self.model_path = package_dir / 'data' / 'model.pkl'
        
        self._load_model()
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "model_type": "knn",
            "n_neighbors": 3,
            "random_forest_params": {
                "n_estimators": 100,
                "max_depth": 10
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        else:
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
        
        return default_config
    
    def train(self, X, y):
        """训练模型"""
        try:
            if self.config["model_type"] == "knn":
                n_neighbors = min(self.config["n_neighbors"], len(X))
                self.model = KNeighborsRegressor(n_neighbors=n_neighbors)
            
            elif self.config["model_type"] == "random_forest":
                params = self.config["random_forest_params"]
                self.model = RandomForestRegressor(**params)
            
            self.model.fit(X, y)
            
            # 评估
            score = self.model.score(X, y)
            print(f"[模型管理] 训练完成，R²分数: {score:.3f}")
            
            self._save_model()
            return True
            
        except Exception as e:
            print(f"[模型管理] 训练失败: {e}")
            return False
    
    def predict(self, X):
        """预测"""
        if self.model is None:
            return None
        
        X = np.array(X).reshape(1, -1)
        return self.model.predict(X)[0]
    
    def is_trained(self):
        """是否已训练"""
        return self.model is not None
    
    def _save_model(self):
        """保存模型"""
        if self.model:
            joblib.dump(self.model, self.model_path)
            print(f"[模型管理] 模型已保存到: {self.model_path}")
    
    def _load_model(self):
        """加载模型"""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                print(f"[模型管理] 已加载模型: {self.model_path}")
            except Exception as e:
                print(f"[模型管理] 加载失败: {e}")
                self.model = None