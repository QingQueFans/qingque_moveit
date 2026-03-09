import sys
print("Python路径:", sys.path)
import os
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/planning_interface/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/install/pymoveit2/local/lib/python3.10/dist-packages')

import rclpy
from rclpy.node import Node
from robot_interfaces.srv import GraspObject, MoveToPose, AddObject, RemoveObject,ListObjects
from planning_interface import Task


class RobotServiceNode(Node):
    def __init__(self):
        super().__init__('robot_service_node')
        self.task = Task()
        
        # 创建所有服务
        self.srv_grasp = self.create_service(
            GraspObject, '/grasp_object', self.grasp_callback)
        self.srv_move = self.create_service(
            MoveToPose, '/move_to_pose', self.move_callback)
        self.srv_add = self.create_service(
            AddObject, '/add_object', self.add_callback)
        self.srv_remove = self.create_service(
            RemoveObject, '/remove_object', self.remove_callback)
        # 在 __init__ 里注册
        self.srv_list = self.create_service(
            ListObjects, '/list_objects', self.list_callback)
        self.get_logger().info('✅ 机器人服务节点已启动')
    
    def grasp_callback(self, request, response):
        self.get_logger().info(f'抓取请求: {request.object_id}')
        result = self.task.grasp_object(request.object_id)
        response.success = result.get('success', False)
        response.message = result.get('message', '')
        return response
    
    def move_callback(self, request, response):
        self.get_logger().info(f'移动请求: {request.pose[:3]}')
        result = self.task.move_to_pose(request.pose)
        response.success = result.get('success', False)
        response.message = result.get('message', '')
        return response
    
    def add_callback(self, request, response):
        self.get_logger().info(f'添加物体: {request.object_id}')
        if request.type == 'box':
            result = self.task.add_object(
                request.object_id, 
                request.position, 
                request.size)
        elif request.type == 'sphere':
            result = self.task.add_sphere(
                request.object_id,
                request.position,
                request.radius)
        elif request.type == 'cylinder':
            result = self.task.add_cylinder(
                request.object_id,
                request.position,
                request.radius,
                request.height)
        response.success = result.get('success', False)
        response.message = result.get('message', '')
        return response
    
    def remove_callback(self, request, response):
        self.get_logger().info(f'移除物体: {request.object_id}')
        result = self.task.remove_object(request.object_id)
        response.success = result.get('success', False)
        response.message = result.get('message', '')
        return response

    def list_callback(self, request, response):
        self.get_logger().info('📋 列出物体')
        try:
            # ✅ 像 plan-object 一样调用
            objects = self.task.list_objects()
            self.get_logger().info(f'找到 {len(objects)} 个物体')
            
            response.objects = objects
            response.success = True
            response.message = f"找到 {len(objects)} 个物体"
            
        except Exception as e:
            self.get_logger().error(f'❌ 列出物体失败: {str(e)}')
            response.success = False
            response.message = str(e)
        
        return response
def main():
    rclpy.init()
    node = RobotServiceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()