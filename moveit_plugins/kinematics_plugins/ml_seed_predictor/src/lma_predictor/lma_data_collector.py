#!/usr/bin/env python3
"""
LMA专用数据收集器 - 专门收集LMA求解器的成功案例
"""
import json
import numpy as np
from pathlib import Path
import time

class LMADataCollector:
    """LMA求解器专用数据收集器"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            # 默认路径：moveit_plugins/kinematics_plugins/ml_seed_predictor/data/lma_data
            base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / 'data' / 'lma_data'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        self.data_path = self.data_dir / 'lma_training_data.json'
        self.stats_path = self.data_dir / 'stats' / 'lma_stats.json'
        self.stats_path.parent.mkdir(exist_ok=True)
        
        self.data = []
        self._load_data()
        
    def add_sample(self, target_pose, solution, error_mm, seed_used=None, metadata=None):
        """
        添加样本（智能去重版）
        """
        # 提取点位信息
        if isinstance(target_pose, (list, tuple)) and len(target_pose) >= 3:
            point_key = f"{target_pose[0]:.2f}_{target_pose[1]:.2f}_{target_pose[2]:.2f}"
        else:
            point_key = "unknown"
        
        # 获取区域（如果metadata中有）
        region = metadata.get('region', 'unknown') if metadata else 'unknown'
        
        # ===== 1. 质量过滤 =====
        if error_mm > 400:  # 硬阈值
            print(f"  ⚠️ 误差{error_mm:.1f}mm > 400，跳过")
            return False
        
        # ===== 2. 检查该点位是否已有太多样本 =====
        point_samples = [s for s in self.data if s.get('point_key') == point_key]
        
        if point_samples:
            # 已有样本，找出最好的
            best_error = min(s['error_mm'] for s in point_samples)
            
            # 如果比最好的差太多，且已有足够样本，跳过
            if error_mm > best_error * 1.5 and len(point_samples) >= 5:
                print(f"  ⚠️ 点位已有{len(point_samples)}个样本，最好{best_error:.1f}mm，当前{error_mm:.1f}mm，跳过")
                return False
            
            # 检查是否与现有解重复
            for existing in point_samples:
                sol_diff = np.linalg.norm(
                    np.array(existing['solution']) - np.array(solution)
                )
                if sol_diff < 0.1:  # 解太相似
                    print(f"  ⚠️ 解重复 (差异{sol_diff:.3f})，跳过")
                    return False
        
        # ===== 3. 区域样本数限制 =====
        region_samples = [s for s in self.data if s.get('region') == region]
        if len(region_samples) >= 50:  # 每个区域最多50个
            print(f"  ⚠️ 区域{region}样本已满(50)，跳过")
            return False
        
        # ===== 4. 创建样本 =====
        sample = {
            "target_pose": [float(x) for x in target_pose[:3]],
            "target_full": [float(x) for x in target_pose] if len(target_pose) > 3 else None,
            "solution": [float(x) for x in solution],
            "error_mm": float(error_mm),
            "seed_used": [float(x) for x in seed_used] if seed_used is not None else None,
            "timestamp": time.time(),
            "point_key": point_key,
            "region": region,
            "metadata": metadata or {}
        }
        
        self.data.append(sample)
        print(f"  📚 添加样本! 点位:{point_key}, 误差:{error_mm:.1f}mm")
        
        # 限制总样本数量
        max_samples = 300
        if len(self.data) > max_samples:
            # 保留质量最高的300个
            self.data.sort(key=lambda x: x['error_mm'])
            self.data = self.data[:max_samples]
            print(f"  ✂️ 裁剪到{max_samples}个最佳样本")
        
        self._save_data()
        self._update_stats()
        return True
        
    def get_training_data(self):
        """获取训练数据"""
        if len(self.data) < 5:
            return np.array([]), np.array([])
        
        X = np.array([s["target_pose"][:3] for s in self.data])
        y = np.array([s["solution"] for s in self.data])
        
        return X, y
    
    def get_weighted_training_data(self):
        """获取带权重的训练数据"""
        if len(self.data) < 5:
            return np.array([]), np.array([]), np.array([])
        
        X = []
        y = []
        weights = []
        
        for s in self.data:
            X.append(s["target_pose"][:3])
            y.append(s["solution"])
            # 误差越小权重越大，但避免权重为0
            weight = 1.0 / (s["error_mm"] + 10.0)  # +10避免除零
            weights.append(weight)
        
        # 归一化权重
        weights = np.array(weights)
        weights = weights / np.sum(weights) * len(weights)
        
        return np.array(X), np.array(y), weights
    
    def get_stats(self):
        """获取统计信息"""
        if not self.data:
            return {"count": 0}
        
        errors = [s["error_mm"] for s in self.data]
        
        return {
            "count": len(self.data),
            "avg_error": float(np.mean(errors)),
            "min_error": float(np.min(errors)),
            "max_error": float(np.max(errors)),
            "std_error": float(np.std(errors)),
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _save_data(self):
        """保存数据"""
        with open(self.data_path, 'w') as f:
            json.dump({
                "samples": self.data,
                "count": len(self.data),
                "last_updated": time.time()
            }, f, indent=2)
    
    def _load_data(self):
        """加载数据"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    self.data = data.get("samples", [])
                print(f"[LMA数据] 已加载 {len(self.data)} 个样本")
            except Exception as e:
                print(f"[LMA数据] 加载失败: {e}")
    
    def _update_stats(self):
        """更新统计文件"""
        stats = self.get_stats()
        with open(self.stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
    def prune_low_quality(self, keep_best=200):
        """
        清理低质量样本，只保留最好的
        """
        if len(self.data) <= keep_best:
            return
        
        # 按误差排序，保留最好的
        self.data.sort(key=lambda x: x['error_mm'])
        old_count = len(self.data)
        self.data = self.data[:keep_best]
        
        print(f"  ✂️ 清理样本: {old_count} -> {keep_best}")
        self._save_data()
        self._update_stats()