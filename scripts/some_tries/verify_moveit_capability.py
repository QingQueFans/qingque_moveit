#!/usr/bin/env python3
"""
验证MoveIt 2真实功能支持
"""
import rclpy
from rclpy.node import Node
import sys

class MoveItCapabilityChecker(Node):
    def __init__(self):
        super().__init__('moveit_capability_checker')
    
    def check_all(self):
        print("="*60)
        print("MoveIt 2 功能支持验证")
        print("="*60)
        
        # 1. 检查基本ROS环境
        print("\n1. 检查ROS环境:")
        print(f"   Node名称: {self.get_name()}")
        print(f"   命名空间: {self.get_namespace()}")
        print("  ✅ ROS 2节点运行正常")
        
        # 2. 检查可用服务（关键！）
        print("\n2. 检查MoveIt相关服务:")
        services = self.get_service_names_and_types()
        moveit_services = []
        
        for name, types in services:
            if any(keyword in name.lower() for keyword in ['moveit', 'planning', 'collision', 'scene']):
                moveit_services.append(name)
        
        if moveit_services:
            print(f"  ✅ 找到 {len(moveit_services)} 个MoveIt相关服务")
            print("  重要服务:")
            important_services = [s for s in moveit_services if any(kw in s for kw in 
                ['/get_planning_scene', '/apply_planning_scene', '/compute_fk', '/compute_ik'])]
            for svc in important_services[:5]:
                print(f"    - {svc}")
        else:
            print("  ❌ 未找到MoveIt服务")
        
        # 3. 检查Python模块
        print("\n3. 检查Python模块支持:")
        
        modules_to_check = [
            ('moveit_msgs', 'MoveIt消息'),
            ('moveit_ros_planning_interface', '规划接口'),
            ('moveit_ros_move_group', 'MoveGroup'),
            ('moveit_ros_planning', '规划核心'),
        ]
        
        for module_name, description in modules_to_check:
            try:
                __import__(module_name)
                print(f"  ✅ {description}: 可用")
            except ImportError:
                print(f"  ❌ {description}: 不可用")
        
        # 4. 检查规划场景服务是否可调用
        print("\n4. 测试规划场景服务连接:")
        try:
            # 尝试创建服务客户端
            from moveit_msgs.srv import GetPlanningScene
            client = self.create_client(GetPlanningScene, '/get_planning_scene')
            if client.wait_for_service(timeout_sec=2.0):
                print("  ✅ /get_planning_scene 服务可用")
            else:
                print("  ❌ /get_planning_scene 服务不可用")
        except Exception as e:
            print(f"  ⚠️  服务测试失败: {e}")
        
        print("\n" + "="*60)
        print("验证完成！")
        print("="*60)

def main():
    rclpy.init()
    checker = MoveItCapabilityChecker()
    
    try:
        checker.check_all()
    finally:
        checker.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
