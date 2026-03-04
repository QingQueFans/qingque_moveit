#!/usr/bin/env python3
"""
调试MoveIt消息结构
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import MotionPlanRequest

class MoveItDebugger(Node):
    def __init__(self):
        super().__init__('moveit_debugger')
        
        # 创建一个MotionPlanRequest对象
        req = MotionPlanRequest()
        
        print("=" * 60)
        print("MotionPlanRequest对象属性:")
        print("=" * 60)
        
        # 列出所有属性
        for attr in dir(req):
            if not attr.startswith('_') and not attr.startswith('deserialize') and not attr.endswith('__'):
                print(f"  {attr}")
        
        print("\n" + "=" * 60)
        print("关键字段检查:")
        print("=" * 60)
        
        # 检查关键字段
        important_fields = [
            'group_name', 'start_state', 'goal_constraints',
            'workspace_parameters', 'planning_options',
            'planning_time', 'planner_id'
        ]
        
        for field in important_fields:
            has_field = hasattr(req, field)
            print(f"  {field}: {'✓' if has_field else '✗'}")
        
        # 创建服务请求来检查实际使用的消息
        self.get_logger().info("调试完成")

def main():
    rclpy.init()
    debugger = MoveItDebugger()
    rclpy.spin_once(debugger, timeout_sec=1.0)
    debugger.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()