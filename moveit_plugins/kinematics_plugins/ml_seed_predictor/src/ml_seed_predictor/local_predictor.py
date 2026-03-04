#!/usr/bin/env python3
"""
局部预测器 - 为每个解族单独训练模型
"""
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
import joblib
import yaml
from pathlib import Path
import json

class LocalPredictor:
    """局部预测器"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.models = {}  # cluster_id -> model_info
        
        package_dir = Path(__file__).parent.parent
        self.models_dir = package_dir / 'data' / 'local_models'
        self.models_dir.mkdir(exist_ok=True)
        
        self._load_models()
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "local_model": {
                "type": "knn",  # knn, random_forest
                "n_neighbors": 3,
                "min_samples": 5,
                "random_forest_params": {
                    "n_estimators": 50,
                    "max_depth": 8
                }
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "local_model" in user_config:
                    default_config["local_model"].update(user_config["local_model"])
        else:
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "local_model" in user_config:
                        default_config["local_model"].update(user_config["local_model"])
        
        return default_config
    
    def train_cluster(self, cluster_id, samples):
        """为特定解族训练模型"""
        if len(samples) < self.config["local_model"]["min_samples"]:
            return False
        
        # 准备数据
        X = np.array([s["pose"] for s in samples])
        y = np.array([s["solution"] for s in samples])
        
        # 选择模型
        model_type = self.config["local_model"]["type"]
        if model_type == "knn":
            n_neighbors = min(self.config["local_model"]["n_neighbors"], len(X))
            model = KNeighborsRegressor(n_neighbors=n_neighbors)
        elif model_type == "random_forest":
            params = self.config["local_model"]["random_forest_params"]
            model = RandomForestRegressor(**params)
        else:
            model = KNeighborsRegressor(n_neighbors=3)
        
        # 训练
        model.fit(X, y)
        
        # 计算训练误差
        predictions = model.predict(X)
        errors = np.linalg.norm(predictions - y, axis=1)
        avg_error = np.mean(errors)
        
        # 保存模型
        self.models[cluster_id] = {
            "model": model,
            "samples": len(samples),
            "avg_error": avg_error,
            "bounds": {
                "min": np.min(y, axis=0).tolist(),
                "max": np.max(y, axis=0).tolist()
            },
            "center": np.mean(y, axis=0).tolist()
        }
        
        # 持久化
        self._save_model(cluster_id)
        
        print(f"[局部模型] 训练 {cluster_id}: {len(samples)}样本, 平均误差 {avg_error:.3f} rad")
        return True
    
    def train_region_clusters(self, region, clusters):
        """训练区域内的所有解族"""
        trained = 0
        for cluster_id, cluster_info in clusters.items():
            if cluster_id.startswith(region):
                if self.train_cluster(cluster_id, cluster_info["samples"]):
                    trained += 1
        return trained
    
    def train_all_clusters(self, all_clusters):
        """训练所有解族"""
        trained = 0
        for cluster_id, cluster_info in all_clusters.items():
            if self.train_cluster(cluster_id, cluster_info["samples"]):
                trained += 1
        return trained
    
    def predict(self, cluster_id, pose):
        """用指定解族的模型预测"""
        if cluster_id not in self.models:
            return None
        
        model_info = self.models[cluster_id]
        pose_array = np.array(pose).reshape(1, -1)
        
        try:
            prediction = model_info["model"].predict(pose_array)[0]
            
            # 约束在合理范围内
            bounds_min = np.array(model_info["bounds"]["min"])
            bounds_max = np.array(model_info["bounds"]["max"])
            prediction = np.clip(prediction, bounds_min, bounds_max)
            
            return prediction
        except Exception as e:
            print(f"[局部模型] 预测失败 {cluster_id}: {e}")
            return model_info["center"]  # 返回中心作为fallback
    
    def get_model_count(self):
        """获取模型数量"""
        return len(self.models)
    
    def _save_model(self, cluster_id):
        """保存模型到文件"""
        if cluster_id in self.models:
            model_info = self.models[cluster_id]
            model_path = self.models_dir / f"{cluster_id}.pkl"
            joblib.dump(model_info["model"], model_path)
            
            # 保存元数据
            meta_path = self.models_dir / f"{cluster_id}_meta.json"
            with open(meta_path, 'w') as f:
                json.dump({
                    "samples": model_info["samples"],
                    "avg_error": model_info["avg_error"],
                    "bounds": model_info["bounds"],
                    "center": model_info["center"]
                }, f, indent=2)
    
    def _load_models(self):
        """加载所有模型"""
        for model_path in self.models_dir.glob("*.pkl"):
            cluster_id = model_path.stem
            meta_path = self.models_dir / f"{cluster_id}_meta.json"
            
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        meta = json.load(f)
                    
                    model = joblib.load(model_path)
                    self.models[cluster_id] = {
                        "model": model,
                        "samples": meta["samples"],
                        "avg_error": meta["avg_error"],
                        "bounds": meta["bounds"],
                        "center": meta["center"]
                    }
                    print(f"[局部模型] 加载 {cluster_id}: {meta['samples']}样本")
                except Exception as e:
                    print(f"[局部模型] 加载失败 {cluster_id}: {e}")