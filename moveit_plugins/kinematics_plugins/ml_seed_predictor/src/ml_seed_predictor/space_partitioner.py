#!/usr/bin/env python3
"""
空间分区器 - 将工作空间分区
"""
import numpy as np
import yaml
from pathlib import Path

class WorkspacePartitioner:
    """工作空间分区器"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.regions = self._define_regions()
        self.region_stats = {name: {"samples": 0, "clusters": 0} for name in self.regions.keys()}
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "partition_mode": "radial_z",  # radial_z, cartesian, custom
            "radial_boundaries": [0.3, 0.5, 0.7],  # 径向分区边界
            "z_boundaries": [0.3, 0.6, 0.9],       # 高度分区边界
            "y_boundaries": [-0.2, 0.2],            # 侧向分区边界
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "partitioner" in user_config:
                    default_config.update(user_config["partitioner"])
        else:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "partitioner" in user_config:
                        default_config.update(user_config["partitioner"])
        
        return default_config
    
    def _define_regions(self):
        """定义工作空间区域"""
        regions = {}
        
        if self.config["partition_mode"] == "radial_z":
            # 径向+高度分区
            radial_bounds = self.config["radial_boundaries"]
            z_bounds = self.config["z_boundaries"]
            
            # 添加近、中、远区域
            for i, r_max in enumerate(radial_bounds):
                r_min = 0 if i == 0 else radial_bounds[i-1]
                
                for j, z_max in enumerate(z_bounds):
                    z_min = 0 if j == 0 else z_bounds[j-1]
                    
                    region_name = f"r{i+1}_z{j+1}"
                    regions[region_name] = {
                        "r_range": [r_min, r_max],
                        "z_range": [z_min, z_max],
                        "y_range": [-0.3, 0.3],  # 默认y范围
                        "type": "normal"
                    }
            
            # 添加侧向区域
            y_left = self.config["y_boundaries"][0]
            y_right = self.config["y_boundaries"][1]
            
            regions["side_left"] = {
                "r_range": [0.3, 0.7],
                "z_range": [0.2, 0.8],
                "y_range": [-0.5, y_left],
                "type": "side"
            }
            
            regions["side_right"] = {
                "r_range": [0.3, 0.7],
                "z_range": [0.2, 0.8],
                "y_range": [y_right, 0.5],
                "type": "side"
            }
        
        elif self.config["partition_mode"] == "cartesian":
            # 笛卡尔网格分区
            x_bounds = [0.3, 0.5, 0.7]
            y_bounds = [-0.2, 0.0, 0.2]
            z_bounds = [0.3, 0.6, 0.9]
            
            for i, x_max in enumerate(x_bounds):
                x_min = 0.2 if i == 0 else x_bounds[i-1]
                for j, y_max in enumerate(y_bounds):
                    y_min = -0.3 if j == 0 else y_bounds[j-1]
                    for k, z_max in enumerate(z_bounds):
                        z_min = 0.1 if k == 0 else z_bounds[k-1]
                        
                        name = f"x{i+1}_y{j+1}_z{k+1}"
                        regions[name] = {
                            "x_range": [x_min, x_max],
                            "y_range": [y_min, y_max],
                            "z_range": [z_min, z_max]
                        }
        
        return regions
    
    def get_region(self, pose):
        """获取位姿所属区域"""
        x, y, z = pose[:3]
        r = np.sqrt(x**2 + y**2)
        
        # 先检查侧向区域
        for name, region in self.regions.items():
            if region.get("type") == "side":
                if (region["r_range"][0] <= r <= region["r_range"][1] and
                    region["z_range"][0] <= z <= region["z_range"][1] and
                    region["y_range"][0] <= y <= region["y_range"][1]):
                    return name
        
        # 检查常规区域
        for name, region in self.regions.items():
            if region.get("type") != "side":
                if ("r_range" in region):
                    if (region["r_range"][0] <= r <= region["r_range"][1] and
                        region["z_range"][0] <= z <= region["z_range"][1]):
                        return name
                elif ("x_range" in region):
                    if (region["x_range"][0] <= x <= region["x_range"][1] and
                        region["y_range"][0] <= y <= region["y_range"][1] and
                        region["z_range"][0] <= z <= region["z_range"][1]):
                        return name
        
        return "unknown"
    
    def get_region_center(self, region):
        """获取区域中心点"""
        if region not in self.regions:
            return None
        
        reg = self.regions[region]
        if "r_range" in reg:
            r_center = (reg["r_range"][0] + reg["r_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            return [r_center, 0, z_center]
        else:
            x_center = (reg["x_range"][0] + reg["x_range"][1]) / 2
            y_center = (reg["y_range"][0] + reg["y_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            return [x_center, y_center, z_center]
    
    def update_stats(self, region):
        """更新区域统计"""
        if region in self.region_stats:
            self.region_stats[region]["samples"] += 1
    
    def get_region_stats(self):
        """获取区域统计"""
        return self.region_stats
    
    def get_region_count(self):
        """获取区域数量"""
        return len(self.regions)#!/usr/bin/env python3
"""
空间分区器 - 将工作空间分区
"""
import numpy as np
import yaml
from pathlib import Path

class WorkspacePartitioner:
    """工作空间分区器"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.regions = self._define_regions()
        self.region_stats = {name: {"samples": 0, "clusters": 0} for name in self.regions.keys()}
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "partition_mode": "radial_z",  # radial_z, cartesian, custom
            "radial_boundaries": [0.3, 0.5, 0.7],  # 径向分区边界
            "z_boundaries": [0.3, 0.6, 0.9],       # 高度分区边界
            "y_boundaries": [-0.2, 0.2],            # 侧向分区边界
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if "partitioner" in user_config:
                    default_config.update(user_config["partitioner"])
        else:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent / 'config' / 'ml_config.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if "partitioner" in user_config:
                        default_config.update(user_config["partitioner"])
        
        return default_config
    
    def _define_regions(self):
        """定义工作空间区域"""
        regions = {}
        
        if self.config["partition_mode"] == "radial_z":
            # 径向+高度分区
            radial_bounds = self.config["radial_boundaries"]
            z_bounds = self.config["z_boundaries"]
            
            # 添加近、中、远区域
            for i, r_max in enumerate(radial_bounds):
                r_min = 0 if i == 0 else radial_bounds[i-1]
                
                for j, z_max in enumerate(z_bounds):
                    z_min = 0 if j == 0 else z_bounds[j-1]
                    
                    region_name = f"r{i+1}_z{j+1}"
                    regions[region_name] = {
                        "r_range": [r_min, r_max],
                        "z_range": [z_min, z_max],
                        "y_range": [-0.3, 0.3],  # 默认y范围
                        "type": "normal"
                    }
            
            # 添加侧向区域
            y_left = self.config["y_boundaries"][0]
            y_right = self.config["y_boundaries"][1]
            
            regions["side_left"] = {
                "r_range": [0.3, 0.7],
                "z_range": [0.2, 0.8],
                "y_range": [-0.5, y_left],
                "type": "side"
            }
            
            regions["side_right"] = {
                "r_range": [0.3, 0.7],
                "z_range": [0.2, 0.8],
                "y_range": [y_right, 0.5],
                "type": "side"
            }
        
        elif self.config["partition_mode"] == "cartesian":
            # 笛卡尔网格分区
            x_bounds = [0.3, 0.5, 0.7]
            y_bounds = [-0.2, 0.0, 0.2]
            z_bounds = [0.3, 0.6, 0.9]
            
            for i, x_max in enumerate(x_bounds):
                x_min = 0.2 if i == 0 else x_bounds[i-1]
                for j, y_max in enumerate(y_bounds):
                    y_min = -0.3 if j == 0 else y_bounds[j-1]
                    for k, z_max in enumerate(z_bounds):
                        z_min = 0.1 if k == 0 else z_bounds[k-1]
                        
                        name = f"x{i+1}_y{j+1}_z{k+1}"
                        regions[name] = {
                            "x_range": [x_min, x_max],
                            "y_range": [y_min, y_max],
                            "z_range": [z_min, z_max]
                        }
        
        return regions
    
    def get_region(self, pose):
        """获取位姿所属区域"""
        x, y, z = pose[:3]
        r = np.sqrt(x**2 + y**2)
        
        # 先检查侧向区域
        for name, region in self.regions.items():
            if region.get("type") == "side":
                if (region["r_range"][0] <= r <= region["r_range"][1] and
                    region["z_range"][0] <= z <= region["z_range"][1] and
                    region["y_range"][0] <= y <= region["y_range"][1]):
                    return name
        
        # 检查常规区域
        for name, region in self.regions.items():
            if region.get("type") != "side":
                if ("r_range" in region):
                    if (region["r_range"][0] <= r <= region["r_range"][1] and
                        region["z_range"][0] <= z <= region["z_range"][1]):
                        return name
                elif ("x_range" in region):
                    if (region["x_range"][0] <= x <= region["x_range"][1] and
                        region["y_range"][0] <= y <= region["y_range"][1] and
                        region["z_range"][0] <= z <= region["z_range"][1]):
                        return name
        
        return "unknown"
    
    def get_region_center(self, region):
        """获取区域中心点"""
        if region not in self.regions:
            return None
        
        reg = self.regions[region]
        if "r_range" in reg:
            r_center = (reg["r_range"][0] + reg["r_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            return [r_center, 0, z_center]
        else:
            x_center = (reg["x_range"][0] + reg["x_range"][1]) / 2
            y_center = (reg["y_range"][0] + reg["y_range"][1]) / 2
            z_center = (reg["z_range"][0] + reg["z_range"][1]) / 2
            return [x_center, y_center, z_center]
    
    def update_stats(self, region):
        """更新区域统计"""
        if region in self.region_stats:
            self.region_stats[region]["samples"] += 1
    
    def get_region_stats(self):
        """获取区域统计"""
        return self.region_stats
    
    def get_region_count(self):
        """获取区域数量"""
        return len(self.regions)