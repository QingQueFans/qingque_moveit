#!/usr/bin/env python3
"""
验证规划器是否真的可用
"""
import sys
import os

# 添加规划器路径
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_planners/src')

# 测试导入
try:
    from ompl_planner.ompl_interface import OMPLInterface
    from ompl_planner.ros2_moveit_client import MoveItROS2Client
    
    print("✅ 导入成功！")
    
    # 测试客户端
    import rclpy
    rclpy.init()
    
    print("\n1. 测试MoveIt客户端...")
    client = MoveItROS2Client()
    
    if client.is_available():
        print("   ✅ MoveIt服务可用")
        
        # 测试规划
        result = client.plan_to_joints([0,0.5,0,-1,0,1,0], planning_time=3.0)
        print(f"   ✅ 规划结果: 成功={result.get('success')}")
        print(f"      错误代码: {result.get('error_code')}")
        print(f"      轨迹点数: {result.get('point_count', 0)}")
    else:
        print("   ❌ MoveIt服务不可用")
    
    client.destroy()
    
    print("\n2. 测试OMPL接口...")
    interface = OMPLInterface()
    status = interface.get_interface_status()
    
    print(f"   ✅ OMPL接口状态:")
    print(f"      规划模式: {status.get('planning_mode')}")
    print(f"      服务可用: {status.get('moveit_service_available')}")
    print(f"      可用算法: {status.get('available_algorithms')}")
    
    interface.destroy_node()
    
    rclpy.shutdown()
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 测试异常: {e}")
    import traceback
    traceback.print_exc()