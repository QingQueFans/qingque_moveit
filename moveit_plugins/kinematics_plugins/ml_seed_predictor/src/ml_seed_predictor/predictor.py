#!/usr/bin/env python3
"""
ML种子预测器 - 核心预测逻辑（增强版）
"""
import numpy as np
import time
from pathlib import Path
from .model_manager import ModelManager
from .data_collector import DataCollector

# ===== 新增导入 =====
from .space_partitioner import WorkspacePartitioner
from .cluster_analyzer import SolutionClusterClassifier
from .local_predictor import LocalPredictor
from .smart_collector import SmartDataCollector

class MLSeedPredictor:
    """机器学习种子预测器（增强版）"""
    
    def __init__(self, config_path=None):
        # 原有组件
        self.data_collector = DataCollector(config_path)
        self.model_manager = ModelManager(config_path)
        self.joint_limits = None
        
        # ===== 新增组件 =====
        self.partitioner = WorkspacePartitioner(config_path)
        self.clusterer = SolutionClusterClassifier(config_path)
        self.local_predictors = LocalPredictor(config_path)
        self.collector = SmartDataCollector(config_path)
        # ===================
        
        # 成功历史
        self.success_history = []
        
        # 从已有数据初始化增强功能
        self._initialize_enhanced()
        
        print(f"[ML] 初始化完成，样本数: {self.data_collector.size()}")
        if hasattr(self, 'clusterer'):
            print(f"[ML] 解族数: {self.clusterer.get_total_clusters()}")
    
    def _initialize_enhanced(self):
        """从已有数据初始化增强功能"""
        try:
            X, y, metadata = self.data_collector.get_training_data_with_metadata()
            
            if len(X) > 0:
                print(f"[ML] 正在分析 {len(X)} 个历史样本...")
                
                for i in range(len(X)):
                    pose = X[i]
                    solution = y[i]
                    error = metadata[i].get("error", 100)
                    object_id = metadata[i].get("object_id")
                    
                    # 确定区域
                    region = self.partitioner.get_region(pose)
                    
                    # 添加到聚类系统
                    self.clusterer.add_solution(pose, solution, region, error, object_id)
                    
                    # 更新收集器统计
                    self.collector.sample_counts[region] = self.collector.sample_counts.get(region, 0) + 1
                
                # 进行聚类分析
                cluster_stats = self.clusterer.analyze_all_regions()
                print(f"[ML] 聚类完成: 发现 {self.clusterer.get_total_clusters()} 个解族")
                
                # 为每个解族训练模型
                all_clusters = self.clusterer.get_all_clusters()
                trained = self.local_predictors.train_all_clusters(all_clusters)
                print(f"[ML] 已训练 {trained} 个局部模型")
        except Exception as e:
            print(f"[ML] 增强初始化失败: {e}")
    
    def add_sample(self, target_pose, successful_seed, error_mm=0, object_id=None):
        """添加训练样本（增强版）"""
        # 原有逻辑
        self.data_collector.add_sample(target_pose, successful_seed, error_mm, object_id)
        
        # ===== 新增增强逻辑 =====
        try:
            # 确定区域
            region = self.partitioner.get_region(target_pose)
            
            # 判断是否需要收集
            should_collect, reason = self.collector.should_collect(
                target_pose, successful_seed, error_mm, region, self.clusterer
            )
            
            if should_collect:
                # 添加到聚类系统
                self.clusterer.add_solution(target_pose, successful_seed, region, error_mm, object_id)
                print(f"[ML] 收集样本: {reason}")
                
                # 检查是否需要重新聚类
                if self.collector.should_recluster(region):
                    print(f"[ML] 重新聚类区域 {region}...")
                    self.clusterer.cluster_region(region)
                    
                # 检查是否需要重新训练
                if self.collector.should_retrain(region):
                    clusters = self.clusterer.get_region_clusters(region)
                    self.local_predictors.train_region_clusters(region, clusters)
                
                # 记录成功
                self.success_history.append(error_mm)
        except Exception as e:
            # 增强功能失败不影响原有功能
            pass
        
        # 自动训练（原有）
        if self.data_collector.size() >= 10 and self.data_collector.size() % 5 == 0:
            self.train()
    
    def train(self):
        """训练模型（增强版）"""
        # 原有训练
        X, y = self.data_collector.get_training_data()
        if len(X) < 3:
            print(f"[ML] 样本不足 ({len(X)}/3)，跳过训练")
            return False
        
        success = self.model_manager.train(X, y)
        if success:
            print(f"[ML] 基础模型训练完成，样本数: {len(X)}")
        
        # 增强训练（重新聚类）
        try:
            self.clusterer.analyze_all_regions()
            all_clusters = self.clusterer.get_all_clusters()
            self.local_predictors.train_all_clusters(all_clusters)
        except Exception as e:
            print(f"[ML] 增强训练失败: {e}")
        
        return success
    
    def predict(self, target_pose):
        """
        基础预测 - 使用全局模型
        
        Args:
            target_pose: 目标位姿 [x, y, z, ...]
            
        Returns:
            预测种子 (7维向量) 或 None
        """
        # 使用 model_manager 预测
        prediction = self.model_manager.predict(target_pose)
        
        # 应用关节限位
        if prediction is not None and self.joint_limits:
            prediction = np.clip(prediction,
                            [l[0] for l in self.joint_limits],
                            [l[1] for l in self.joint_limits])
        
        return prediction
        
    def generate_seeds(self, target_pose, num_seeds=5):
        """生成多个候选种子（新增方法）"""
        seeds = []
        
        # 1. 确定区域
        region = self.partitioner.get_region(target_pose)
        
        # 2. 获取该区域的所有可能解族
        clusters = self.clusterer.get_region_clusters(region)
        
        if clusters:
            # 3. 预测最可能的解族
            main_cluster, confidence = self.clusterer.predict_cluster(target_pose, region)
            
            if main_cluster and confidence > 0.3:
                # 主预测
                main_seed = self.local_predictors.predict(main_cluster, target_pose)
                if main_seed is not None:
                    seeds.append(main_seed)
                    
                    # 围绕主预测生成扰动
                    for i in range(min(3, num_seeds-1)):
                        noise = np.random.normal(0, 0.2, 7)
                        perturbed = main_seed + noise
                        if self.joint_limits:
                            perturbed = np.clip(perturbed,
                                              [l[0] for l in self.joint_limits],
                                              [l[1] for l in self.joint_limits])
                        seeds.append(perturbed)
            
            # 4. 如果种子不够，尝试其他解族
            if len(seeds) < num_seeds:
                for cid in clusters.keys():
                    if cid != main_cluster and len(seeds) < num_seeds:
                        seed = self.local_predictors.predict(cid, target_pose)
                        if seed is not None:
                            seeds.append(seed)
        
        # 5. 如果还不够，用原始预测补充
        while len(seeds) < num_seeds:
            pred = self.model_manager.predict(target_pose)
            if pred is not None:
                seeds.append(pred)
            else:
                break
        
        return seeds[:num_seeds]
    
    def set_joint_limits(self, limits):
        """设置关节限位"""
        self.joint_limits = limits
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            "samples": self.data_collector.size(),
            "model_trained": self.model_manager.is_trained(),
            "model_type": self.model_manager.config.get("model_type", "knn")
        }
        
        # 确保stats属性存在（用于兼容性）
        self.stats = stats
        
        # 添加增强信息
        try:
            stats["enhanced"] = {
                "clusters": self.clusterer.get_total_clusters(),
                "local_models": self.local_predictors.get_model_count(),
                "collection_phase": self.collector.current_phase
            }
        except:
            pass
        
        return stats
    
    def get_enhanced_stats(self):
        """获取增强统计信息（新增方法）"""
        return {
            "samples": self.data_collector.size(),
            "clusters": self.clusterer.get_total_clusters(),
            "local_models": self.local_predictors.get_model_count(),
            "regions": self.partitioner.get_region_stats(),
            "collection_phase": self.collector.current_phase,
            "sample_counts": self.collector.sample_counts
        }
    
    def is_trained(self):
        """是否已训练"""
        return self.model_manager.is_trained()