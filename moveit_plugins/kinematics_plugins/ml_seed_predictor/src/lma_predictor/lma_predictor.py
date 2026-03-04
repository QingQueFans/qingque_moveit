#!/usr/bin/env python3
"""
LMA专用预测器 - 整合数据收集、聚类和模型训练
"""
import numpy as np
from pathlib import Path
import yaml
import json
import time

from .lma_data_collector import LMADataCollector
from .lma_model_trainer import LMAModelTrainer
from .lma_cluster_analyzer import LMAClusterAnalyzer
from .lma_local_predictor import LMALocalPredictor
from .lma_space_partitioner import LMASpacePartitioner

class LMAPredictor:
    """LMA专用预测器 - 完整版"""
    
    def __init__(self, config_path=None):
        """
        初始化LMA预测器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # ===== 设置数据目录 =====
    # ===== 使用绝对路径 =====
        self.data_dir = Path('/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data')
        
        print(f"[LMA预测器] 初始化，数据目录: {self.data_dir}")
        
        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True, parents=True)
        (self.data_dir / 'models').mkdir(exist_ok=True)
        (self.data_dir / 'clusters').mkdir(exist_ok=True)
        (self.data_dir / 'stats').mkdir(exist_ok=True)
        
        # ===== 核心组件 =====
        # 1. 数据收集器 - 存储LMA成功案例
        self.data_collector = LMADataCollector(self.data_dir)
        
        # 2. 全局模型训练器 - 用于全局预测
        self.model_trainer = LMAModelTrainer(self.data_dir)
        
        # 3. 空间分区器 - 将工作空间分区
        self.space_partitioner = LMASpacePartitioner(config_path)
        
        # 4. 聚类分析器 - 识别不同的解族
        self.cluster_analyzer = LMAClusterAnalyzer(config_path, self.data_dir)
        
        # 5. 局部预测器 - 为每个解族单独训练模型
        self.local_predictor = LMALocalPredictor(self.data_dir)
        
        # ===== 统计信息 =====
        self.stats = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "avg_uncertainty": 0,
            "last_training": None,
            "last_clustering": None
        }
        
        # ===== 从已有数据初始化 =====
        self._initialize_from_existing()
        
        print(f"[LMA预测器] 初始化完成")
        print(f"  - 样本数: {self.data_collector.get_stats()['count']}")
        print(f"  - 解族数: {self.cluster_analyzer.get_total_clusters()}")
        print(f"  - 局部模型: {self.local_predictor.get_model_count()}")
        print(f"  - 全局模型已训练: {self.model_trainer.model is not None}")
    
    def _initialize_from_existing(self):
        """从已有数据初始化聚类和局部模型"""
        try:
            # 获取所有样本
            X, y = self.data_collector.get_training_data()
            
            if len(X) > 0:
                print(f"[LMA预测器] 正在分析 {len(X)} 个历史样本...")
                
                # 为每个样本添加到聚类系统
                for i in range(len(X)):
                    pose = X[i].tolist() if hasattr(X[i], 'tolist') else X[i]
                    solution = y[i].tolist() if hasattr(y[i], 'tolist') else y[i]
                    
                    # 获取区域
                    region = self.space_partitioner.get_region(pose)
                    
                    # 获取误差（如果有）
                    error = 50.0  # 默认误差
                    
                    # 添加到聚类
                    self.cluster_analyzer.add_solution(
                        pose=pose,
                        solution=solution,
                        region=region,
                        error=error
                    )
                
                # 训练局部模型
                if self.cluster_analyzer.get_total_clusters() > 0:
                    self.local_predictor.train_all_clusters(
                        self.cluster_analyzer.region_clusters
                    )
                    
        except Exception as e:
            print(f"[LMA预测器] 初始化历史数据失败: {e}")
    
    # ========== 预测方法 ==========
    
    def predict(self, target_pose):
        """
        基础预测 - 使用全局模型
        """
        # 确保stats字典有所有必要的键
        if "total_predictions" not in self.stats:
            self.stats["total_predictions"] = 0
        if "successful_predictions" not in self.stats:
            self.stats["successful_predictions"] = 0
        if "avg_uncertainty" not in self.stats:
            self.stats["avg_uncertainty"] = 0
        
        self.stats["total_predictions"] += 1
        
        # 默认种子（当模型未训练时使用）
        default_seed = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        
        # 如果模型未训练，直接返回默认种子
        if self.model_trainer.model is None:
            print("  [LMA] 模型未训练，使用默认种子")
            return default_seed, 1.0
        
        try:
            # 带不确定度的预测
            prediction, uncertainty = self.model_trainer.predict_with_uncertainty(target_pose)
            
            if prediction is not None:
                # 确保没有None值
                prediction = [0.0 if x is None else float(x) for x in prediction]
                self.stats["successful_predictions"] += 1
                # 更新平均不确定度
                total = self.stats["successful_predictions"]
                old_avg = self.stats["avg_uncertainty"]
                self.stats["avg_uncertainty"] = (old_avg * (total - 1) + uncertainty) / total
                return prediction, uncertainty
            else:
                print("  [LMA] 预测失败，使用默认种子")
                return default_seed, 1.0
                
        except Exception as e:
            print(f"  [LMA] 预测异常: {e}")
            return default_seed, 1.0
    def predict_with_clustering(self, target_pose):
        """
        基于聚类的增强预测
        
        Args:
            target_pose: 目标位姿 [x, y, z, ...]
            
        Returns:
            tuple: (预测种子, 置信度, 所属解族ID)
        """
        # 1. 确定所属区域
        region = self.space_partitioner.get_region(target_pose)
        
        # 2. 预测最可能的解族
        cluster_id, confidence = self.cluster_analyzer.predict_cluster(target_pose, region)
        
        # 3. 如果找到了高置信度的解族，用局部模型预测
        if cluster_id and confidence > 0.3:
            prediction = self.local_predictor.predict(cluster_id, target_pose)
            if prediction is not None:
                self.stats["total_predictions"] += 1
                self.stats["successful_predictions"] += 1
                return prediction, confidence, cluster_id
        
        # 4. 回退到全局模型
        prediction, uncertainty = self.predict(target_pose)
        return prediction, 1.0 - uncertainty, None
    
    def predict_batch(self, target_poses, use_clustering=True):
        """
        批量预测
        
        Args:
            target_poses: 多个目标位姿的列表
            use_clustering: 是否使用聚类
            
        Returns:
            list: 每个位姿的预测结果
        """
        results = []
        for pose in target_poses:
            if use_clustering:
                pred, conf, cid = self.predict_with_clustering(pose)
                results.append((pred, conf, cid))
            else:
                pred, unc = self.predict(pose)
                results.append((pred, unc, None))
        return results
    
    # ========== 数据收集方法 ==========
    
    def add_success(self, target_pose, solution, error_mm, seed_used=None, metadata=None):
        """
        添加成功案例（标准方法）
        
        Args:
            target_pose: 目标位姿
            solution: 求解得到的关节角度
            error_mm: 误差(mm)
            seed_used: 使用的种子
            metadata: 元数据
        """
        # 1. 添加到数据收集器
        self.data_collector.add_sample(
            target_pose=target_pose,
            solution=solution,
            error_mm=error_mm,
            seed_used=seed_used,
            metadata=metadata
        )
        
        # 2. 同时添加到聚类系统（如果质量好）
        if error_mm < 100:  # 只对高质量解进行聚类
            self.add_solution_with_clustering(
                target_pose=target_pose,
                solution=solution,
                error_mm=error_mm
            )
        
        # 3. 检查是否需要自动训练
        stats = self.data_collector.get_stats()
        freq = self.config['collection']['auto_train_frequency']
        if stats['count'] > 0 and stats['count'] % freq == 0:
            self.train()
    
    def add_solution_with_clustering(self, target_pose, solution, error_mm, region=None):
        """
        添加解并更新聚类
        
        Args:
            target_pose: 目标位姿
            solution: 关节角度解
            error_mm: 误差
            region: 区域（如果为None则自动确定）
        """
        # 确定区域
        if region is None:
            region = self.space_partitioner.get_region(target_pose)
        
        # 添加到聚类分析器
        self.cluster_analyzer.add_solution(
            pose=target_pose,
            solution=solution,
            region=region,
            error=error_mm
        )
        
        self.stats["last_clustering"] = time.time()
        
        # 如果聚类有更新，重新训练局部模型
        if self.cluster_analyzer.get_total_clusters() > 0:
            trained = self.local_predictor.train_all_clusters(
                self.cluster_analyzer.region_clusters
            )
            if trained > 0:
                print(f"[LMA预测器] 已更新 {trained} 个局部模型")
    
    # ========== 训练方法 ==========
    
    def train(self, train_global=True, train_local=True):
        """
        训练所有模型
        
        Args:
            train_global: 是否训练全局模型
            train_local: 是否训练局部模型
            
        Returns:
            bool: 是否成功
        """
        success = False
        
        # 1. 训练全局模型
        if train_global:
            X, y, weights = self.data_collector.get_weighted_training_data()
            min_samples = self.config['training']['min_samples']
            
            if len(X) >= min_samples:
                print(f"[LMA预测器] 训练全局模型 ({len(X)}样本)...")
                global_success = self.model_trainer.train(X, y, weights)
                if global_success:
                    self.stats["last_training"] = time.time()
                    success = True
        
        # 2. 训练局部模型（基于聚类）
        if train_local and self.cluster_analyzer.get_total_clusters() > 0:
            print(f"[LMA预测器] 训练局部模型...")
            local_success = self.local_predictor.train_all_clusters(
                self.cluster_analyzer.region_clusters
            )
            if local_success > 0:
                success = True
        
        return success
    
    def force_recluster(self):
        """强制重新聚类"""
        print("[LMA预测器] 强制重新聚类...")
        
        # 重新分析所有区域
        for region in self.cluster_analyzer.region_clusters:
            self.cluster_analyzer.cluster_region(region)
        
        # 重新训练局部模型
        if self.cluster_analyzer.get_total_clusters() > 0:
            self.local_predictor.train_all_clusters(
                self.cluster_analyzer.region_clusters
            )
        
        print(f"[LMA预测器] 重新聚类完成，当前解族数: {self.cluster_analyzer.get_total_clusters()}")
    
    # ========== 统计和状态方法 ==========
    
    def get_stats(self):
        """获取完整统计信息"""
        # 确保stats字典有所有必要的键
        required_keys = ["total_predictions", "successful_predictions", "avg_uncertainty", 
                        "last_training", "last_clustering"]
        for key in required_keys:
            if key not in self.stats:
                self.stats[key] = 0 if "predictions" in key or "uncertainty" in key else None
        
        data_stats = self.data_collector.get_stats()
        cluster_count = self.cluster_analyzer.get_total_clusters()
        
        return {
            "data": data_stats,
            "clusters": {
                "total": cluster_count,
                "by_region": {
                    region: len(rinfo.get("clusters", {}))
                    for region, rinfo in self.cluster_analyzer.region_clusters.items()
                }
            },
            "models": {
                "global": {
                    "trained": self.model_trainer.model is not None,
                    "type": self.model_trainer.model_type
                },
                "local": {
                    "count": self.local_predictor.get_model_count()
                }
            },
            "predictions": self.stats,
            "space_partition": {
                "regions": self.space_partitioner.get_region_count(),
                "mode": self.space_partitioner.config.get("partition_mode", "unknown")
            }
        }
        
    def get_simple_stats(self):
        """获取简略统计信息"""
        data_stats = self.data_collector.get_stats()
        return {
            "samples": data_stats['count'],
            "clusters": self.cluster_analyzer.get_total_clusters(),
            "local_models": self.local_predictor.get_model_count(),
            "global_trained": self.model_trainer.model is not None
        }
    
    # ========== 配置加载方法 ==========
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "collection": {
                "max_samples": 300,
                "auto_train_frequency": 10,
                "quality_threshold": 100
            },
            "training": {
                "min_samples": 5,
                "model_type": "ensemble"
            },
            "clustering": {
                "eps": 0.8,
                "min_samples": 3
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "lma_model" in user_config:
                    lma_config = user_config["lma_model"]
                    for key in default_config:
                        if key in lma_config:
                            default_config[key].update(lma_config[key])
        else:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent.parent / 'config' / 'lma_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "lma_model" in user_config:
                        lma_config = user_config["lma_model"]
                        for key in default_config:
                            if key in lma_config:
                                default_config[key].update(lma_config[key])
        
        return default_config
    
    # ========== 工具方法 ==========
    
    def clear_all_data(self):
        """清空所有数据（危险操作）"""
        print("[LMA预测器] ⚠️ 清空所有数据...")
        confirm = input("确定要清空所有LMA数据吗? (yes/no): ")
        if confirm == "yes":
            self.data_collector.clear()
            self.cluster_analyzer.region_clusters = {}
            self.local_predictor.models = {}
            self.model_trainer.model = None
            print("[LMA预测器] 所有数据已清空")
        else:
            print("[LMA预测器] 操作取消")
    
    def export_data(self, export_path=None):
        """导出所有数据"""
        if export_path is None:
            export_path = self.data_dir / 'export'
        
        export_path = Path(export_path)
        export_path.mkdir(exist_ok=True)
        
        # 导出训练数据
        X, y = self.data_collector.get_training_data()
        np.save(export_path / 'X.npy', X)
        np.save(export_path / 'y.npy', y)
        
        # 导出统计信息
        with open(export_path / 'stats.json', 'w') as f:
            json.dump(self.get_stats(), f, indent=2)
        
        print(f"[LMA预测器] 数据已导出到: {export_path}")
        return str(export_path)


# ========== 便捷函数 ==========

def create_lma_predictor(config_path=None):
    """创建LMA预测器的便捷函数"""
    return LMAPredictor(config_path)


def test_lma_predictor():
    """测试LMA预测器"""
    predictor = LMAPredictor()
    print("\nLMA预测器测试:")
    print(f"  样本数: {predictor.get_simple_stats()['samples']}")
    print(f"  解族数: {predictor.get_simple_stats()['clusters']}")
    
    # 测试预测
    test_points = [
        [0.55, -0.1, 0.6],
        [0.4, 0.0, 0.5],
        [0.5, 0.0, 0.5]
    ]
    
    print("\n测试预测:")
    for point in test_points:
        pred, unc = predictor.predict(point)
        if pred is not None:
            print(f"  {point} -> [{pred[0]:.3f}, {pred[1]:.3f}, {pred[2]:.3f}...] 不确定度:{unc:.3f}")
        else:
            print(f"  {point} -> 预测失败")


if __name__ == "__main__":
    test_lma_predictor()