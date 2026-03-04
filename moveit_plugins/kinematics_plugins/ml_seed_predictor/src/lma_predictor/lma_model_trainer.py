#!/usr/bin/env python3
"""
LMA专用模型训练器 - 针对LMA求解器特性优化
"""
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import json
from pathlib import Path
import time

class LMAModelTrainer:
    """LMA专用模型训练器"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / 'data' / 'lma_data'
        self.data_dir = Path(data_dir)
        self.model_dir = self.data_dir / 'models'
        self.model_dir.mkdir(exist_ok=True)
        
        self.model = None
        self.scaler = StandardScaler()
        self.model_type = "none"
        self.model_path = self.model_dir / 'latest.pkl'
        self.scaler_path = self.model_dir / 'scaler.pkl'
        self.metadata_path = self.model_dir / 'model_metadata.json'
        
        self._load_model()
        
    def train(self, X, y, weights=None):
        """训练LMA专用模型"""
        if len(X) < 5:
            return False
        
        try:
            # 标准化特征 - 这里会fit scaler
            X_scaled = self.scaler.fit_transform(X)
            
            # 根据数据量选择不同策略
            if len(X) < 20:
                # 小样本：用KNN
                n_neighbors = min(3, len(X))
                self.model = KNeighborsRegressor(
                    n_neighbors=n_neighbors,
                    weights='distance'
                )
                self.model_type = "knn"
                self.model.fit(X_scaled, y)
                
            elif len(X) < 50:
                # 中等样本：用随机森林
                self.model = RandomForestRegressor(
                    n_estimators=50,
                    max_depth=8,
                    random_state=42
                )
                self.model_type = "random_forest"
                if weights is not None:
                    self.model.fit(X_scaled, y, sample_weight=weights)
                else:
                    self.model.fit(X_scaled, y)
            else:
                # 大样本：用梯度提升
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                )
                self.model_type = "gradient_boosting"
                if weights is not None:
                    self.model.fit(X_scaled, y, sample_weight=weights)
                else:
                    self.model.fit(X_scaled, y)
            
            # 评估
            predictions = self.model.predict(X_scaled)
            errors = np.linalg.norm(predictions - y, axis=1)
            avg_error = np.mean(errors)
            
            # 保存模型
            self._save_model()
            
            # 保存元数据
            with open(self.metadata_path, 'w') as f:
                json.dump({
                    "model_type": self.model_type,
                    "samples": len(X),
                    "avg_error": float(avg_error),
                    "features": X.shape[1],
                    "output_dim": y.shape[1],
                    "timestamp": time.time()
                }, f, indent=2)
            
            print(f"[LMA模型] 训练完成: {self.model_type}, 样本数:{len(X)}, 平均误差:{avg_error:.3f}")
            return True
            
        except Exception as e:
            print(f"[LMA模型] 训练失败: {e}")
            return False
    def predict(self, pose):
        """预测种子"""
        if self.model is None:
            return None
        
        X = np.array(pose[:3]).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        try:
            prediction = self.model.predict(X_scaled)[0]
            return prediction
        except Exception as e:
            print(f"[LMA模型] 预测失败: {e}")
            return None
    
    def predict_with_uncertainty(self, pose):
        """带不确定度的预测"""
        # 默认种子
        default_seed = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        
        # 检查模型和scaler是否都已训练
        if self.model is None:
            print("  [LMA模型] 模型未训练，使用默认种子")
            return default_seed, 1.0
        
        # 检查scaler是否已fit
        if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
            print("  [LMA模型] Scaler未训练，使用默认种子")
            return default_seed, 1.0
        
        try:
            X = np.array(pose[:3]).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            if hasattr(self.model, 'estimators_'):
                # 对于随机森林
                predictions = np.array([tree.predict(X_scaled)[0] for tree in self.model.estimators_])
                mean = np.mean(predictions, axis=0)
                std = np.std(predictions, axis=0)
                mean = np.nan_to_num(mean, nan=0.0)
                uncertainty = float(np.mean(std)) if not np.isnan(np.mean(std)) else 0.5
                return mean.tolist(), uncertainty
            else:
                # 对于其他模型
                prediction = self.model.predict(X_scaled)[0]
                prediction = np.nan_to_num(prediction, nan=0.0)
                return prediction.tolist(), 0.3
                
        except Exception as e:
            print(f"  [LMA模型] 预测失败: {e}")
            return default_seed, 1.0
    
    def _save_model(self):
        """保存模型"""
        if self.model:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
    
    def _load_model(self):
        """加载模型"""
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'r') as f:
                        meta = json.load(f)
                        self.model_type = meta.get('model_type', 'unknown')
                print(f"[LMA模型] 已加载 {self.model_type} 模型")
            except Exception as e:
                print(f"[LMA模型] 加载失败: {e}")
