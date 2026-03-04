#!/usr/bin/env python3
"""
LMA专用局部预测器 - 为每个LMA解族单独训练模型
"""
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
import joblib
import json
from pathlib import Path

class LMALocalPredictor:
    """LMA专用局部预测器"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.models_dir = self.data_dir / 'local_models'
        self.models_dir.mkdir(exist_ok=True)
        
        self.models = {}  # cluster_id -> model_info
        
    def train_cluster(self, cluster_id, samples):
        """为特定LMA解族训练模型"""
        if len(samples) < 3:
            return False
        
        X = np.array([s["pose"][:3] for s in samples])  # 只使用位置
        y = np.array([s["solution"] for s in samples])
        
        # 使用简单的KNN
        n_neighbors = min(3, len(X))
        model = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')
        model.fit(X, y)
        
        # 计算误差
        predictions = model.predict(X)
        errors = np.linalg.norm(predictions - y, axis=1)
        avg_error = np.mean(errors)
        
        self.models[cluster_id] = {
            "model": model,
            "samples": len(samples),
            "avg_error": avg_error,
            "center": np.mean(y, axis=0).tolist()
        }
        
        # 保存模型
        model_path = self.models_dir / f"{cluster_id}.pkl"
        joblib.dump(model, model_path)
        
        print(f"[LMA局部] 训练 {cluster_id}: {len(samples)}样本, 误差 {avg_error:.3f}")
        return True
    
    def train_all_clusters(self, region_clusters):
        """训练所有LMA解族"""
        trained = 0
        for region, rinfo in region_clusters.items():
            for cluster_id, cinfo in rinfo.get("clusters", {}).items():
                if self.train_cluster(cluster_id, cinfo["samples"]):
                    trained += 1
        return trained
    
    def predict(self, cluster_id, pose):
        """用指定解族的模型预测"""
        if cluster_id not in self.models:
            return None
        
        model_info = self.models[cluster_id]
        pose_array = np.array(pose[:3]).reshape(1, -1)
        
        try:
            prediction = model_info["model"].predict(pose_array)[0]
            return prediction
        except Exception as e:
            print(f"[LMA局部] 预测失败: {e}")
            return model_info["center"]
    
    def get_model_count(self):
        return len(self.models)
