# moveit_planners/src/ompl_planner/ompl_algorithm_manager.py
"""
OMPL算法管理器 - 规划器特有组件
管理不同的OMPL算法及其参数配置
"""
from typing import Dict, Any, List, Optional
import rclpy
from rclpy.node import Node
import yaml
import os
import time

class OMPLAlgorithmManager(Node):
    """OMPL算法管理器 - 规划器特有的算法管理"""
    
    def __init__(self, node_name="ompl_algorithm_manager"):
        super().__init__(node_name)
        
        # 算法配置
        self.algorithms = {}
        self.algorithm_params = {}
        
        # 加载算法配置
        self._load_algorithms()
        
        self.get_logger().info("OMPL算法管理器初始化完成")
    
    def _load_algorithms(self):
        """加载算法配置"""
        # 这里应该从配置文件加载
        # 暂时使用硬编码的算法配置
        
        self.algorithms = {
            "rrt_connect": {
                "description": "快速探索随机树连接算法",
                "type": "geometric::RRTConnect",
                "category": "sampling_based",
                "optimal": False,
                "parameters": ["range", "goal_bias", "max_planning_time"]
            },
            "rrt_star": {
                "description": "渐进最优RRT算法", 
                "type": "geometric::RRTstar",
                "category": "sampling_based",
                "optimal": True,
                "parameters": ["range", "goal_bias", "delay_collision_checking"]
            },
            "prm": {
                "description": "概率路图算法",
                "type": "geometric::PRM", 
                "category": "sampling_based",
                "optimal": False,
                "parameters": ["max_nearest_neighbors", "roadmap_vertices"]
            }
        }
        
        self.get_logger().info(f"加载了 {len(self.algorithms)} 个OMPL算法")
    
    def get_available_algorithms(self) -> List[str]:
        """获取可用算法列表"""
        return list(self.algorithms.keys())
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict[str, Any]:
        """获取算法详细信息"""
        if algorithm_name not in self.algorithms:
            return {"error": f"算法不存在: {algorithm_name}"}
        
        return self.algorithms[algorithm_name]
    
    def set_algorithm_parameters(self, algorithm_name: str, parameters: Dict) -> Dict[str, Any]:
        """设置算法参数"""
        if algorithm_name not in self.algorithms:
            return {"success": False, "error": f"算法不存在: {algorithm_name}"}
        
        # 这里应该验证参数
        self.algorithm_params[algorithm_name] = parameters
        
        return {
            "success": True,
            "algorithm": algorithm_name,
            "parameters": parameters
        }
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "node_name": self.get_name(),
            "algorithms_loaded": len(self.algorithms),
            "available_algorithms": self.get_available_algorithms(),
            "parameter_sets": len(self.algorithm_params),
            "timestamp": time.time() if 'time' in globals() else 0
        }
    
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("OMPL算法管理器正在关闭...")
        super().destroy_node()