#!/usr/bin/env python3
"""
LMA专用解族聚类分析器 - 独立于原ML的聚类系统
"""
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import yaml
from pathlib import Path
import json
import time

class LMAClusterAnalyzer:
    """LMA专用解族分类器"""
    
    def __init__(self, config_path=None, data_dir=None):
        self.config = self._load_config(config_path)
        
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / 'data' / 'lma_data'
        
        self.data_dir = Path(data_dir)
        self.cluster_dir = self.data_dir / 'clusters'
        self.cluster_dir.mkdir(exist_ok=True)
        
        self.region_clusters = {}  # region -> {cluster_id: info}
        self.cluster_counter = 0
        self.cluster_path = self.cluster_dir / 'lma_clusters.json'
        
        self._load_clusters()
        
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "clustering": {
                "eps": 0.8,           # LMA可能用更小的eps
                "min_samples": 3,
                "feature_weights": [1.0] * 7
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "lma_clustering" in user_config:
                    default_config["clustering"].update(user_config["lma_clustering"])
        
        return default_config
    
    def add_solution(self, pose, solution, region, error=0, object_id=None):
        """添加LMA解到聚类"""
        if region not in self.region_clusters:
            self.region_clusters[region] = {
                "samples": [],
                "clusters": {},
                "last_cluster_time": 0
            }
        
        # 添加样本
        self.region_clusters[region]["samples"].append({
            "pose": pose.tolist() if isinstance(pose, np.ndarray) else pose,
            "solution": solution.tolist() if isinstance(solution, np.ndarray) else solution,
            "error": error,
            "object_id": object_id,
            "timestamp": time.time()
        })
        
        # 自动聚类
        min_samples = self.config["clustering"]["min_samples"]
        if len(self.region_clusters[region]["samples"]) >= min_samples * 3:
            self.cluster_region(region)
    
    def cluster_region(self, region):
        """对区域内的LMA解进行聚类"""
        if region not in self.region_clusters:
            return []
        
        samples = self.region_clusters[region]["samples"]
        if len(samples) < self.config["clustering"]["min_samples"]:
            return []
        
        # 提取关节角度
        X = np.array([s["solution"] for s in samples])
        
        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN聚类 - LMA可能用不同的参数
        eps = self.config["clustering"]["eps"]
        min_samples = self.config["clustering"]["min_samples"]
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X_scaled)
        
        # 处理聚类结果
        new_clusters = {}
        unique_labels = set(clustering.labels_)
        
        for label in unique_labels:
            if label == -1:
                continue
            
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_samples = [samples[i] for i in cluster_indices]
            
            solutions = np.array([s["solution"] for s in cluster_samples])
            center = np.mean(solutions, axis=0)
            bounds_min = np.min(solutions, axis=0)
            bounds_max = np.max(solutions, axis=0)
            
            cluster_id = f"lma_{region}_cluster_{len(new_clusters)}"
            
            new_clusters[cluster_id] = {
                "center": center.tolist(),
                "bounds": [bounds_min.tolist(), bounds_max.tolist()],
                "samples": cluster_samples,
                "size": len(cluster_samples),
                "avg_error": np.mean([s["error"] for s in cluster_samples]),
                "scaler": scaler
            }
        
        # 更新簇
        old_count = len(self.region_clusters[region].get("clusters", {}))
        new_count = len(new_clusters)
        
        self.region_clusters[region]["clusters"] = new_clusters
        self.region_clusters[region]["last_cluster_time"] = time.time()
        
        if new_count != old_count:
            print(f"\n[LMA聚类] 区域 {region}: 发现 {new_count} 个LMA解族 (之前 {old_count}个)")
            for cid, info in new_clusters.items():
                print(f"       簇 {cid}: {info['size']}个样本, 平均误差 {info['avg_error']:.1f}mm")
        
        self._save_clusters()
        return new_clusters
    
    def predict_cluster(self, pose, region):
        """预测位姿属于哪个LMA解族"""
        if region not in self.region_clusters:
            return None, 0.0
        
        clusters = self.region_clusters[region]["clusters"]
        if not clusters:
            return None, 0.0
        
        pose_array = np.array(pose[:3])
        
        best_cluster = None
        best_score = -1
        
        for cid, cinfo in clusters.items():
            samples = cinfo["samples"]
            if not samples:
                continue
            
            sample_poses = np.array([s["pose"][:3] for s in samples])
            distances = np.linalg.norm(sample_poses - pose_array, axis=1)
            
            avg_dist = np.mean(distances)
            if avg_dist < 0.01:
                density = len(samples) * 100
            else:
                density = len(samples) / avg_dist
            
            error_weight = 1.0 / (np.mean([s["error"] for s in samples]) + 1)
            score = density * error_weight
            
            if score > best_score:
                best_score = score
                best_cluster = cid
        
        confidence = min(1.0, best_score / 10.0) if best_score > 0 else 0
        return best_cluster, confidence
    
    def get_total_clusters(self):
        """获取总LMA解族数"""
        total = 0
        for rinfo in self.region_clusters.values():
            total += len(rinfo.get("clusters", {}))
        return total
    
    def _save_clusters(self):
        """保存LMA聚类信息"""
        try:
            serializable = {}
            for region, rinfo in self.region_clusters.items():
                serializable[region] = {
                    "sample_count": len(rinfo["samples"]),
                    "clusters": {}
                }
                for cid, cinfo in rinfo.get("clusters", {}).items():
                    serializable[region]["clusters"][cid] = {
                        "center": cinfo["center"],
                        "bounds": cinfo["bounds"],
                        "size": cinfo["size"],
                        "avg_error": cinfo["avg_error"]
                    }
            
            with open(self.cluster_path, 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            print(f"[LMA聚类] 保存失败: {e}")
    
    def _load_clusters(self):
        """加载LMA聚类信息"""
        if self.cluster_path.exists():
            try:
                with open(self.cluster_path, 'r') as f:
                    data = json.load(f)
                print(f"[LMA聚类] 已加载 {len(data)} 个区域的LMA聚类信息")
            except Exception as e:
                print(f"[LMA聚类] 加载失败: {e}")
