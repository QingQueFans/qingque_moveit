#!/usr/bin/env python3
"""
智能数据收集器 - 判断是否需要收集样本
"""
import numpy as np
import yaml
from pathlib import Path

class SmartDataCollector:
    """智能数据收集器"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.sample_counts = {}  # region -> count
        self.last_collection_time = {}  # region -> timestamp
        
        # 质量阈值
        self.error_thresholds = {
            "exploration": 100,   # 探索阶段
            "transition": 50,     # 过渡阶段
            "exploitation": 20    # 利用阶段
        }
        self.current_phase = "exploration"
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "collection": {
                "max_samples_per_region": 200,
                "min_samples_for_cluster": 10,
                "diversity_threshold": 0.3,  # 关节角度差异阈值
                "position_threshold": 0.05,   # 位置差异阈值
                "auto_recluster_frequency": 20  # 每20个样本重新聚类
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "collection" in user_config:
                    default_config["collection"].update(user_config["collection"])
        else:
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "collection" in user_config:
                        default_config["collection"].update(user_config["collection"])
        
        return default_config
    
    def should_collect(self, pose, solution, error, region, clusterer):
        """判断是否应该收集这个样本"""
        
        # 1. 质量检查
        current_threshold = self.error_thresholds[self.current_phase]
        if error > current_threshold:
            return False, f"误差太大 ({error:.1f}mm > {current_threshold}mm)"
        
        # 2. 区域样本数检查
        self.sample_counts[region] = self.sample_counts.get(region, 0) + 1
        if self.sample_counts[region] > self.config["collection"]["max_samples_per_region"]:
            return False, f"区域 {region} 样本已达上限"
        
        # 3. 检查是否是新解族
        clusters = clusterer.get_region_clusters(region)
        if not clusters:
            return True, "新区域需要样本"
        
        # 4. 检查这个解属于哪个族
        solution_array = np.array(solution)
        found_cluster = None
        min_dist = float('inf')
        
        for cid, cinfo in clusters.items():
            center = np.array(cinfo["center"])
            dist = np.linalg.norm(solution_array - center)
            if dist < min_dist:
                min_dist = dist
                found_cluster = cid
        
        # 5. 如果是新解族（距离现有中心太远）
        if min_dist > self.config["collection"]["diversity_threshold"] * 7:  # 7个关节
            # 检查是否有足够样本形成新簇
            similar_solutions = 0
            for cid, cinfo in clusters.items():
                other_center = np.array(cinfo["center"])
                if np.linalg.norm(solution_array - other_center) < self.config["collection"]["diversity_threshold"] * 5:
                    similar_solutions += 1
            
            if similar_solutions < 3:  # 还没有形成簇
                return True, f"潜在新解族 (距离 {min_dist:.2f})"
        
        # 6. 多样性检查
        if found_cluster:
            cluster_info = clusters[found_cluster]
            
            # 检查位姿多样性
            sample_poses = [s["pose"][:3] for s in cluster_info["samples"]]
            if sample_poses:
                pose_array = np.array(pose[:3])
                pose_dists = [np.linalg.norm(pose_array - np.array(p)) for p in sample_poses]
                min_pose_dist = min(pose_dists)
                
                if min_pose_dist < self.config["collection"]["position_threshold"]:
                    # 位姿太近，检查解是否足够不同
                    solution_dists = [np.linalg.norm(solution_array - np.array(s["solution"])) 
                                    for s in cluster_info["samples"] 
                                    if np.linalg.norm(pose_array - np.array(s["pose"][:3])) < self.config["collection"]["position_threshold"]]
                    
                    if solution_dists and min(solution_dists) < self.config["collection"]["diversity_threshold"]:
                        return False, f"重复样本 (位姿差 {min_pose_dist:.3f}m, 解差 {min(solution_dists):.2f})"
        
        # 7. 高质量样本优先
        if error < 20:
            return True, "高质量样本"
        
        # 8. 检查是否需要更多样本来完善现有簇
        if found_cluster and len(cluster_info["samples"]) < self.config["collection"]["min_samples_for_cluster"]:
            return True, f"完善解族 (现有 {len(cluster_info['samples'])}/{self.config['collection']['min_samples_for_cluster']})"
        
        # 9. 随机采样一些边界样本
        if np.random.random() < 0.1:  # 10%概率收集边界样本
            return True, "边界采样"
        
        return False, "样本充足"
    
    def should_recluster(self, region):
        """判断是否需要重新聚类"""
        if region not in self.sample_counts:
            return False
        
        count = self.sample_counts[region]
        freq = self.config["collection"]["auto_recluster_frequency"]
        
        return count > 0 and count % freq == 0
    
    def should_retrain(self, region):
        """判断是否需要重新训练"""
        # 每次收集新样本都重新训练太频繁，可以每5个样本训练一次
        if region not in self.sample_counts:
            return False
        
        return self.sample_counts[region] % 5 == 0
    
    def update_phase(self, success_rate):
        """更新收集阶段"""
        if success_rate > 0.8 and self.current_phase == "exploration":
            self.current_phase = "transition"
            print(f"[收集器] 🔄 升级到过渡阶段 (阈值: {self.error_thresholds['transition']}mm)")
        elif success_rate > 0.9 and self.current_phase == "transition":
            self.current_phase = "exploitation"
            print(f"[收集器] 🎯 升级到利用阶段 (阈值: {self.error_thresholds['exploitation']}mm)")
    
    def get_total_samples(self):
        """获取总样本数"""
        return sum(self.sample_counts.values())