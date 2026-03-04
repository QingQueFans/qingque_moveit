#!/usr/bin/env python3
"""
解族聚类分析器 - 识别不同的解族
"""
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import yaml
from pathlib import Path
import json
import time

class SolutionClusterClassifier:
    """解族分类器"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.region_clusters = {}  # region -> {cluster_id: {samples, center, bounds}}
        self.cluster_counter = 0
        
        # 持久化存储
        package_dir = Path(__file__).parent.parent
        self.data_dir = package_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.cluster_path = self.data_dir / 'clusters.json'
        self._load_clusters()
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "clustering": {
                "eps": 1.0,           # DBSCAN邻域半径
                "min_samples": 3,      # 最小样本数
                "feature_weights": [1.0] * 7  # 关节角度特征权重
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "clustering" in user_config:
                    default_config["clustering"].update(user_config["clustering"])
        else:
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "clustering" in user_config:
                        default_config["clustering"].update(user_config["clustering"])
        
        return default_config
    
    def add_solution(self, pose, solution, region, error=0, object_id=None):
        """添加解到待聚类列表"""
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
        
        # 如果样本足够，自动聚类
        if len(self.region_clusters[region]["samples"]) >= self.config["clustering"]["min_samples"] * 3:
            self.cluster_region(region)
    
    def cluster_region(self, region):
        """对区域内的解进行聚类"""
        if region not in self.region_clusters:
            return []
        
        samples = self.region_clusters[region]["samples"]
        if len(samples) < self.config["clustering"]["min_samples"]:
            return []
        
        # 提取关节角度
        X = np.array([s["solution"] for s in samples])
        
        # 应用特征权重
        weights = np.array(self.config["clustering"]["feature_weights"])
        X_weighted = X * weights
        
        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_weighted)
        
        # DBSCAN聚类
        eps = self.config["clustering"]["eps"]
        min_samples = self.config["clustering"]["min_samples"]
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X_scaled)
        
        # 处理聚类结果
        new_clusters = {}
        unique_labels = set(clustering.labels_)
        
        for label in unique_labels:
            if label == -1:  # 噪声点
                continue
            
            # 获取这个簇的样本索引
            cluster_indices = np.where(clustering.labels_ == label)[0]
            cluster_samples = [samples[i] for i in cluster_indices]
            
            # 计算簇中心
            solutions = np.array([s["solution"] for s in cluster_samples])
            center = np.mean(solutions, axis=0)
            
            # 计算边界
            bounds_min = np.min(solutions, axis=0)
            bounds_max = np.max(solutions, axis=0)
            
            # 生成簇ID
            cluster_id = f"{region}_cluster_{len(new_clusters)}"
            
            new_clusters[cluster_id] = {
                "center": center.tolist(),
                "bounds": [bounds_min.tolist(), bounds_max.tolist()],
                "samples": cluster_samples,
                "size": len(cluster_samples),
                "avg_error": np.mean([s["error"] for s in cluster_samples]),
                "scaler": scaler,  # 保存scaler用于预测
                "feature_weights": weights
            }
        
        # ===== 【修改】只在解族数量变化时输出 =====
        old_clusters = self.region_clusters[region].get("clusters", {})
        old_count = len(old_clusters)
        new_count = len(new_clusters)
        
        # 更新簇
        self.region_clusters[region]["clusters"] = new_clusters
        self.region_clusters[region]["last_cluster_time"] = time.time()
        
        # 只在数量变化时输出
        if new_count != old_count:
            print(f"\n[聚类] 区域 {region}: 发现 {new_count} 个解族 (之前 {old_count}个)")
            for cid, info in new_clusters.items():
                print(f"       簇 {cid}: {info['size']}个样本, 平均误差 {info['avg_error']:.1f}mm")
        
        self._save_clusters()
        return new_clusters
    def predict_cluster(self, pose, region):
        """预测位姿属于哪个解族"""
        if region not in self.region_clusters:
            return None, 0.0
        
        clusters = self.region_clusters[region]["clusters"]
        if not clusters:
            return None, 0.0
        
        pose_array = np.array(pose[:3])  # 只使用位置
        
        best_cluster = None
        best_score = -1
        best_confidence = 0.0
        
        for cid, cinfo in clusters.items():
            # 计算位姿到该簇所有样本的距离
            samples = cinfo["samples"]
            if not samples:
                continue
            
            sample_poses = np.array([s["pose"][:3] for s in samples])
            distances = np.linalg.norm(sample_poses - pose_array, axis=1)
            
            # 分数 = 样本密度 / 平均距离
            avg_dist = np.mean(distances)
            if avg_dist < 0.01:  # 太近，避免除零
                density = len(samples) * 100
            else:
                density = len(samples) / avg_dist
            
            # 考虑误差权重
            error_weight = 1.0 / (np.mean([s["error"] for s in samples]) + 1)
            score = density * error_weight
            
            if score > best_score:
                best_score = score
                best_cluster = cid
                best_confidence = min(1.0, density / 10.0)  # 归一化置信度
        
        return best_cluster, best_confidence
    
    def get_region_clusters(self, region):
        """获取区域的所有解族"""
        if region not in self.region_clusters:
            return {}
        return self.region_clusters[region]["clusters"]
    
    def get_all_clusters(self):
        """获取所有解族"""
        all_clusters = {}
        for region, rinfo in self.region_clusters.items():
            for cid, cinfo in rinfo["clusters"].items():
                all_clusters[cid] = cinfo
        return all_clusters
    
    def get_total_clusters(self):
        """获取总解族数"""
        total = 0
        for rinfo in self.region_clusters.values():
            total += len(rinfo.get("clusters", {}))
        return total
    
    def analyze_all_regions(self):
        """分析所有区域"""
        stats = {}
        for region in self.region_clusters:
            if len(self.region_clusters[region]["samples"]) >= self.config["clustering"]["min_samples"]:
                clusters = self.cluster_region(region)
                stats[region] = len(clusters)
        return stats
    
    def _save_clusters(self):
        """保存聚类信息"""
        try:
            # 保存可序列化的信息
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
            print(f"[聚类] 保存失败: {e}")
    
    def _load_clusters(self):
        """加载聚类信息"""
        if self.cluster_path.exists():
            try:
                with open(self.cluster_path, 'r') as f:
                    data = json.load(f)
                # 只加载统计信息，实际样本需要从data_collector加载
                print(f"[聚类] 已加载 {len(data)} 个区域的聚类信息")
            except Exception as e:
                print(f"[聚类] 加载失败: {e}")