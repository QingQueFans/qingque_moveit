#!/usr/bin/env python3
"""
LMA专用空间分区器 - 为LMA求解器优化的工作空间分区
"""
import numpy as np
import yaml
from pathlib import Path

class LMASpacePartitioner:
    """LMA专用工作空间分区器"""
    
    def __init__(self, config_path=None):
        """
        初始化LMA空间分区器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.regions = self._define_regions()
        self.region_stats = {name: {"samples": 0, "clusters": 0, "success_rate": 0.0} 
                            for name in self.regions.keys()}
        
        print(f"[LMA分区器] 初始化完成，分区模式: {self.config['partition_mode']}")
        print(f"[LMA分区器] 共 {len(self.regions)} 个区域")
    
    def _load_config(self, config_path):
        """加载LMA专用配置"""
        default_config = {
            "partition_mode": "radial_z",      # radial_z, cartesian, reachability
            "radial_boundaries": [0.35, 0.55, 0.75],  # LMA可能用不同的边界
            "z_boundaries": [0.25, 0.5, 0.8],         # 高度分区边界
            "y_boundaries": [-0.25, 0.25],            # 侧向分区边界
            "use_fine_regions": True,                  # LMA可能用更细的分区
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # 尝试从LMA配置中读取
                if "lma_space_partitioner" in user_config:
                    default_config.update(user_config["lma_space_partitioner"])
                # 或者从原分区器配置读取但加上LMA前缀
                elif "partitioner" in user_config:
                    # 使用原配置但调整参数
                    base_config = user_config["partitioner"]
                    default_config.update(base_config)
                    # LMA可能用更细的粒度
                    if default_config["use_fine_regions"]:
                        default_config["radial_boundaries"] = [0.3, 0.45, 0.6, 0.75]
                        default_config["z_boundaries"] = [0.2, 0.4, 0.6, 0.8]
        else:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent.parent / 'config' / 'lma_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "lma_space_partitioner" in user_config:
                        default_config.update(user_config["lma_space_partitioner"])
        
        return default_config
    
    def _define_regions(self):
        """定义LMA工作空间区域"""
        regions = {}
        
        if self.config["partition_mode"] == "radial_z":
            # 径向+高度分区
            radial_bounds = self.config["radial_boundaries"]
            z_bounds = self.config["z_boundaries"]
            
            # 添加径向-高度区域
            for i, r_max in enumerate(radial_bounds):
                r_min = 0 if i == 0 else radial_bounds[i-1]
                
                for j, z_max in enumerate(z_bounds):
                    z_min = 0 if j == 0 else z_bounds[j-1]
                    
                    region_name = f"lma_r{i+1}_z{j+1}"
                    regions[region_name] = {
                        "r_range": [r_min, r_max],
                        "z_range": [z_min, z_max],
                        "y_range": [-0.3, 0.3],
                        "type": "normal",
                        "index": (i, j)
                    }
            
            # 添加侧向区域（LMA可能更容易收敛到侧向解）
            y_left = self.config["y_boundaries"][0]
            y_right = self.config["y_boundaries"][1]
            
            # 左侧区域
            for i, r_max in enumerate(radial_bounds):
                r_min = 0 if i == 0 else radial_bounds[i-1]
                for j, z_max in enumerate(z_bounds):
                    z_min = 0 if j == 0 else z_bounds[j-1]
                    
                    region_name = f"lma_left_r{i+1}_z{j+1}"
                    regions[region_name] = {
                        "r_range": [r_min, r_max],
                        "z_range": [z_min, z_max],
                        "y_range": [-0.5, y_left],
                        "type": "side",
                        "side": "left",
                        "index": (i, j)
                    }
            
            # 右侧区域
            for i, r_max in enumerate(radial_bounds):
                r_min = 0 if i == 0 else radial_bounds[i-1]
                for j, z_max in enumerate(z_bounds):
                    z_min = 0 if j == 0 else z_bounds[j-1]
                    
                    region_name = f"lma_right_r{i+1}_z{j+1}"
                    regions[region_name] = {
                        "r_range": [r_min, r_max],
                        "z_range": [z_min, z_max],
                        "y_range": [y_right, 0.5],
                        "type": "side",
                        "side": "right",
                        "index": (i, j)
                    }
        
        elif self.config["partition_mode"] == "cartesian":
            # 笛卡尔网格分区（LMA可能用更细的网格）
            x_bounds = [0.3, 0.45, 0.6, 0.75]
            y_bounds = [-0.25, -0.1, 0.1, 0.25]
            z_bounds = [0.2, 0.4, 0.6, 0.8]
            
            for i, x_max in enumerate(x_bounds):
                x_min = 0.2 if i == 0 else x_bounds[i-1]
                for j, y_max in enumerate(y_bounds):
                    y_min = -0.3 if j == 0 else y_bounds[j-1]
                    for k, z_max in enumerate(z_bounds):
                        z_min = 0.1 if k == 0 else z_bounds[k-1]
                        
                        name = f"lma_x{i+1}_y{j+1}_z{k+1}"
                        regions[name] = {
                            "x_range": [x_min, x_max],
                            "y_range": [y_min, y_max],
                            "z_range": [z_min, z_max],
                            "type": "cartesian",
                            "index": (i, j, k)
                        }
        
        elif self.config["partition_mode"] == "reachability":
            # 基于可达性的分区（LMA特有）
            # 近处区域
            regions["lma_near_high"] = {
                "r_range": [0.0, 0.4],
                "z_range": [0.5, 0.9],
                "type": "reachability",
                "reachability": "high"
            }
            regions["lma_near_mid"] = {
                "r_range": [0.0, 0.4],
                "z_range": [0.2, 0.5],
                "type": "reachability",
                "reachability": "mid"
            }
            regions["lma_near_low"] = {
                "r_range": [0.0, 0.4],
                "z_range": [0.0, 0.2],
                "type": "reachability",
                "reachability": "low"
            }
            
            # 中等距离区域
            regions["lma_mid_high"] = {
                "r_range": [0.4, 0.6],
                "z_range": [0.5, 0.9],
                "type": "reachability",
                "reachability": "high"
            }
            regions["lma_mid_mid"] = {
                "r_range": [0.4, 0.6],
                "z_range": [0.2, 0.5],
                "type": "reachability",
                "reachability": "mid"
            }
            regions["lma_mid_low"] = {
                "r_range": [0.4, 0.6],
                "z_range": [0.0, 0.2],
                "type": "reachability",
                "reachability": "low"
            }
            
            # 远处区域
            regions["lma_far_high"] = {
                "r_range": [0.6, 0.8],
                "z_range": [0.5, 0.9],
                "type": "reachability",
                "reachability": "high"
            }
            regions["lma_far_mid"] = {
                "r_range": [0.6, 0.8],
                "z_range": [0.2, 0.5],
                "type": "reachability",
                "reachability": "mid"
            }
            regions["lma_far_low"] = {
                "r_range": [0.6, 0.8],
                "z_range": [0.0, 0.2],
                "type": "reachability",
                "reachability": "low"
            }
        
        return regions
    
    def get_region(self, pose):
        """
        获取位姿所属的LMA区域
        
        Args:
            pose: 位姿 [x, y, z, ...] 或 [x, y, z]
            
        Returns:
            str: 区域名称
        """
        x, y, z = pose[:3]
        r = np.sqrt(x**2 + y**2)
        
        # 根据配置模式选择不同的分区逻辑
        if self.config["partition_mode"] == "radial_z":
            return self._get_region_radial_z(x, y, z, r)
        elif self.config["partition_mode"] == "cartesian":
            return self._get_region_cartesian(x, y, z)
        elif self.config["partition_mode"] == "reachability":
            return self._get_region_reachability(x, y, z, r)
        else:
            return "lma_unknown"
    
    def _get_region_radial_z(self, x, y, z, r):
        """径向-高度分区逻辑"""
        # 先检查侧向区域
        for name, region in self.regions.items():
            if region.get("type") == "side":
                if (region["r_range"][0] <= r <= region["r_range"][1] and
                    region["z_range"][0] <= z <= region["z_range"][1] and
                    region["y_range"][0] <= y <= region["y_range"][1]):
                    return name
        
        # 检查常规区域
        for name, region in self.regions.items():
            if region.get("type") == "normal":
                if (region["r_range"][0] <= r <= region["r_range"][1] and
                    region["z_range"][0] <= z <= region["z_range"][1]):
                    return name
        
        return "lma_unknown"
    
    def _get_region_cartesian(self, x, y, z):
        """笛卡尔分区逻辑"""
        for name, region in self.regions.items():
            if region.get("type") == "cartesian":
                if (region["x_range"][0] <= x <= region["x_range"][1] and
                    region["y_range"][0] <= y <= region["y_range"][1] and
                    region["z_range"][0] <= z <= region["z_range"][1]):
                    return name
        return "lma_unknown"
    
    def _get_region_reachability(self, x, y, z, r):
        """可达性分区逻辑"""
        # 基于距离和高度的简单分区
        if r < 0.4:
            zone = "near"
        elif r < 0.6:
            zone = "mid"
        else:
            zone = "far"
        
        if z > 0.5:
            height = "high"
        elif z > 0.2:
            height = "mid"
        else:
            height = "low"
        
        region_name = f"lma_{zone}_{height}"
        
        # 验证区域是否存在
        if region_name in self.regions:
            return region_name
        
        return "lma_unknown"
    
    def get_region_center(self, region):
        """获取区域中心点"""
        if region not in self.regions:
            return None
        
        reg = self.regions[region]
        
        if "r_range" in reg:
            r_center = (reg["r_range"][0] + reg["r_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            
            if "y_range" in reg:
                y_center = (reg["y_range"][0] + reg["y_range"][1]) / 2
            else:
                y_center = 0.0
            
            # 对于径向分区，返回近似的x,y
            if abs(y_center) < 0.01:
                return [r_center, 0, z_center]
            else:
                # 对于侧向区域，用y方向
                return [r_center * 0.7, y_center, z_center]
        
        elif "x_range" in reg:
            x_center = (reg["x_range"][0] + reg["x_range"][1]) / 2
            y_center = (reg["y_range"][0] + reg["y_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            return [x_center, y_center, z_center]
        
        return None
    
    def update_stats(self, region, success=False):
        """更新区域统计"""
        if region in self.region_stats:
            self.region_stats[region]["samples"] += 1
            if success:
                # 更新成功率（滑动平均）
                old_rate = self.region_stats[region]["success_rate"]
                n = self.region_stats[region]["samples"]
                self.region_stats[region]["success_rate"] = (old_rate * (n-1) + 1) / n
    
    def update_cluster_count(self, region, count):
        """更新区域的解族数量"""
        if region in self.region_stats:
            self.region_stats[region]["clusters"] = count
    
    def get_region_stats(self):
        """获取区域统计"""
        return self.region_stats
    
    def get_best_regions(self, top_k=3):
        """获取成功率最高的区域"""
        regions = []
        for name, stats in self.region_stats.items():
            if stats["samples"] > 0:
                regions.append((name, stats["success_rate"]))
        
        regions.sort(key=lambda x: x[1], reverse=True)
        return regions[:top_k]
    
    def get_region_count(self):
        """获取区域数量"""
        return len(self.regions)
    
    def get_region_names(self):
        """获取所有区域名称"""
        return list(self.regions.keys())
    
    def get_regions_by_type(self, region_type):
        """获取指定类型的区域"""
        return [name for name, reg in self.regions.items() 
                if reg.get("type") == region_type]
    
    def is_side_region(self, region):
        """判断是否是侧向区域"""
        return region in self.regions and self.regions[region].get("type") == "side"
    
    def get_region_bounds(self, region):
        """获取区域边界"""
        if region not in self.regions:
            return None
        return self.regions[region]
    
    def get_neighboring_regions(self, region):
        """获取相邻区域（用于探索）"""
        if region not in self.regions:
            return []
        
        reg = self.regions[region]
        neighbors = []
        
        if "index" in reg:
            idx = reg["index"]
            # 根据索引找相邻区域
            for name, other in self.regions.items():
                if "index" in other:
                    oidx = other["index"]
                    # 检查是否相邻（曼哈顿距离为1）
                    if sum(abs(a-b) for a, b in zip(idx, oidx)) == 1:
                        neighbors.append(name)
        
        return neighbors
    
    def visualize_regions(self):
        """打印区域信息（调试用）"""
        print("\nLMA空间分区:")
        print("=" * 50)
        for name, reg in self.regions.items():
            if "r_range" in reg:
                print(f"  {name}: r={reg['r_range']}, z={reg['z_range']}, type={reg.get('type', 'unknown')}")
            elif "x_range" in reg:
                print(f"  {name}: x={reg['x_range']}, y={reg['y_range']}, z={reg['z_range']}")
        
        print("\n区域统计:")
        for name, stats in self.region_stats.items():
            if stats["samples"] > 0:
                print(f"  {name}: {stats['samples']}样本, {stats['clusters']}解族, {stats['success_rate']:.1%}成功率")


# ===== 便捷函数 =====

def create_lma_partitioner(config_path=None):
    """创建LMA分区器的便捷函数"""
    return LMASpacePartitioner(config_path)


def test_lma_partitioner():
    """测试LMA分区器"""
    partitioner = LMASpacePartitioner()
    
    print("\n测试点分区:")
    test_points = [
        [0.55, -0.1, 0.6],
        [0.4, 0.0, 0.5],
        [0.45, -0.15, 0.45],
        [0.6, 0.2, 0.7],
        [0.3, 0.0, 0.3]
    ]
    
    for point in test_points:
        region = partitioner.get_region(point)
        print(f"  {point} -> {region}")
    
    print(f"\n总区域数: {partitioner.get_region_count()}")
    partitioner.visualize_regions()


if __name__ == "__main__":
    test_lma_partitioner()
