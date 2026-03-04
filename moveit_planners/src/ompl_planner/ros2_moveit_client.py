# ros2_moveit_client.py - 最终修复版
#!/usr/bin/env python3
"""
ROS2 MoveIt服务客户端 - 最终修复版
基于实际消息结构，已验证工作正常
"""
import rclpy
from rclpy.node import Node
import time
import sys
from moveit_msgs.srv import GetMotionPlan
from moveit_msgs.msg import (
    MotionPlanRequest, RobotState, Constraints, JointConstraint,
    WorkspaceParameters,PositionConstraint,OrientationConstraint,BoundingVolume,MoveItErrorCodes
)
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from geometry_msgs.msg import Pose,PoseStamped
from shape_msgs.msg import SolidPrimitive
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import fcl
class MoveItROS2Client(Node):
    """ROS2 MoveIt服务客户端 - 最终修复版"""
    
    def __init__(self, node_name="moveit_ros2_client"):
        super().__init__(node_name)
        
        self.plan_service_name = '/plan_kinematic_path'
        
        # 连接到规划服务
        self.plan_client = self.create_client(
            GetMotionPlan,
            self.plan_service_name
        )
        
        if not self.plan_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().warning(f"规划服务不可用: {self.plan_service_name}")
            self.service_available = False
        else:
            self.get_logger().info(f"✓ 连接到规划服务: {self.plan_service_name}")
            self.service_available = True
    
    def is_available(self):
        """检查服务是否可用"""
        return self.service_available
    
    def create_valid_robot_state(self):
        """创建有效的机器人状态"""
        robot_state = RobotState()
        
        # 关节状态
        joint_state = JointState()
        joint_state.header = Header()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.header.frame_id = "panda_link0"
        
        # Panda的所有关节（包括手指）
        joint_state.name = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        joint_state.position = [
            0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785,
            0.04, 0.04
        ]
        
        robot_state.joint_state = joint_state
        robot_state.is_diff = False  # 提供完整状态
        
        return robot_state
    
    def plan_to_joints(self, target_joints, group_name="panda_arm", 
                      planner_id="RRTConnect", planning_time=5.0):
        """
        规划到关节位置
        
        Args:
            target_joints: 目标关节角度列表 (7个值)
            group_name: 规划组名称
            planner_id: 规划器ID
            planning_time: 规划时间限制
        
        Returns:
            规划结果字典
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "MoveIt规划服务不可用",
                "service": self.plan_service_name,
                "error_code": -25  # 通信失败
            }
        
        try:
            self.get_logger().info(f"规划到关节: {target_joints}")            # 创建请求
            request = GetMotionPlan.Request()
            motion_request = MotionPlanRequest()
            
            # 1. 设置必需字段
            motion_request.group_name = group_name
            motion_request.num_planning_attempts = 3
            motion_request.allowed_planning_time = planning_time
            motion_request.planner_id = planner_id
            
            # 2. 设置可选但推荐的字段
            motion_request.max_velocity_scaling_factor = 0.1
            motion_request.max_acceleration_scaling_factor = 0.1
            
            # 3. 起始状态
            motion_request.start_state = self.create_valid_robot_state()
            
            # 4. 目标约束
            constraints = Constraints()
            
            # Panda机械臂的7个关节
            joint_names = [
                "panda_joint1", "panda_joint2", "panda_joint3",
                "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
            ]
            
            for i, joint_name in enumerate(joint_names):
                if i < len(target_joints):
                    joint_constraint = JointConstraint()
                    joint_constraint.joint_name = joint_name
                    joint_constraint.position = float(target_joints[i])
                    joint_constraint.tolerance_above = 0.5
                    joint_constraint.tolerance_below = 0.5
                    joint_constraint.weight = 1.0
                    constraints.joint_constraints.append(joint_constraint)
            
            motion_request.goal_constraints = [constraints]
            
            # 5. 工作空间参数（必需！）
            motion_request.workspace_parameters = WorkspaceParameters()
            motion_request.workspace_parameters.header.frame_id = "panda_link0"
            motion_request.workspace_parameters.header.stamp = self.get_clock().now().to_msg()
            motion_request.workspace_parameters.min_corner.x = -1.0
            motion_request.workspace_parameters.min_corner.y = -1.0
            motion_request.workspace_parameters.min_corner.z = -1.0
            motion_request.workspace_parameters.max_corner.x = 1.0
            motion_request.workspace_parameters.max_corner.y = 1.0
            motion_request.workspace_parameters.max_corner.z = 1.0
            
            # 6. 设置其他可选字段
            motion_request.pipeline_id = ""
            
            request.motion_plan_request = motion_request
            
            # 发送请求
            future = self.plan_client.call_async(request)            # 等待响应
            start_time = time.time()
            timeout_sec = planning_time + 2.0
            
            while rclpy.ok() and not future.done():
                rclpy.spin_once(self, timeout_sec=0.1)
                if time.time() - start_time > timeout_sec:
                    return {
                        "success": False,
                        "error": "规划请求超时",
                        "error_code": -6,  # 超时
                        "planning_time": time.time() - start_time
                    }
            
            if future.result() is not None:
                response = future.result()
                error_code = response.motion_plan_response.error_code.val
                plan_time = time.time() - start_time
                
                result = {
                    "success": error_code == 1,
                    "error_code": error_code,
                    "error_message": self.error_code_to_string(error_code),
                    "planning_time": plan_time,
                    "algorithm": planner_id,
                    "planning_mode": "real"
                }
                
                if result["success"]:
                    if hasattr(response.motion_plan_response, 'trajectory'):
                        traj = response.motion_plan_response.trajectory
                        if hasattr(traj, 'joint_trajectory') and traj.joint_trajectory.points:
                            result["trajectory"] = traj.joint_trajectory
                            result["joint_names"] = traj.joint_trajectory.joint_names
                            result["point_count"] = len(traj.joint_trajectory.points)
                
                return result
            else:
                return {
                    "success": False,
                    "error": "服务无响应",
                    "error_code": -999,
                    "planning_time": time.time() - start_time
                }
                
        except Exception as e:
            self.get_logger().error(f"规划失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": -1,
                "planning_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    def plan_to_pose(self, target_pose, group_name="panda_arm",
                    planner_id="RRTConnect", planning_time=5.0):
        """
        使用OMPL规划器进行位姿规划
        """
            # 如果传入的是列表，转换为字典格式
        if isinstance(target_pose, (list, tuple)) and len(target_pose) >= 7:
            target_pose = {
                'position': target_pose[:3],
                'orientation': target_pose[3:7]
            }
        try:
            self.get_logger().info(f"规划到位姿: {target_pose}")
            
            # 创建PoseStamped消息
            from geometry_msgs.msg import PoseStamped
            pose_stamped = PoseStamped()
            pose_stamped.header.frame_id = "panda_link0"
            pose_stamped.header.stamp = self.get_clock().now().to_msg()
            
            # 设置位置
            pose_stamped.pose.position.x = float(target_pose['position'][0])
            pose_stamped.pose.position.y = float(target_pose['position'][1])
            pose_stamped.pose.position.z = float(target_pose['position'][2])
            
            # 设置方向
            if 'orientation' in target_pose and len(target_pose['orientation']) == 4:
                pose_stamped.pose.orientation.x = float(target_pose['orientation'][0])
                pose_stamped.pose.orientation.y = float(target_pose['orientation'][1])
                pose_stamped.pose.orientation.z = float(target_pose['orientation'][2])
                pose_stamped.pose.orientation.w = float(target_pose['orientation'][3])
            else:
                pose_stamped.pose.orientation.w = 1.0  # 默认方向
            
            # 使用OMPL规划器直接规划
            # 假设OMPL规划器有plan_to_pose方法
            if hasattr(self, 'ompl_planner'):
                result = self.ompl_planner.plan_to_pose(
                    pose_stamped=pose_stamped,
                    group_name=group_name,
                    planner_id=planner_id,
                    planning_time=planning_time
                )
                return result
            else:
                # 如果没有OMPL规划器，使用原始的规划服务
                return self._plan_via_service(pose_stamped, group_name, planner_id, planning_time)
                
        except Exception as e:
            self.get_logger().error(f"位姿规划异常: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "error_code": -1
            }
    def create_pose_constraint(self, pose, link_name, frame_id="panda_link0"):
        """
        创建位姿约束
        """
        constraints = Constraints()
        
        # 位置约束
        position_constraint = PositionConstraint()
        position_constraint.header.frame_id = frame_id
        position_constraint.link_name = link_name
        
        # 创建约束区域
        bounding_volume = BoundingVolume()
        
        # 使用球体约束
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [0.02]  # 2cm容差
        
        bounding_volume.primitives.append(sphere)
        
        if isinstance(pose, PoseStamped):
            bounding_volume.primitive_poses.append(pose.pose)
        else:
            bounding_volume.primitive_poses.append(pose)
        
        position_constraint.constraint_region = bounding_volume
        position_constraint.weight = 1.0
        constraints.position_constraints.append(position_constraint)
        
        # 方向约束
        orientation_constraint = OrientationConstraint()
        orientation_constraint.header.frame_id = frame_id
        orientation_constraint.link_name = link_name
        
        if isinstance(pose, PoseStamped):
            orientation_constraint.orientation = pose.pose.orientation
        else:
            orientation_constraint.orientation = pose.orientation
        
        orientation_constraint.absolute_x_axis_tolerance = 0.087  # ~5度
        orientation_constraint.absolute_y_axis_tolerance = 0.087
        orientation_constraint.absolute_z_axis_tolerance = 0.087
        orientation_constraint.weight = 1.0
        constraints.orientation_constraints.append(orientation_constraint)
        
        return constraints
    def _plan_via_service(self, pose_stamped, group_name, planner_id, planning_time):
        """
        通过MoveIt规划服务进行位姿规划
        """
        try:
            # 创建规划请求
            request = GetMotionPlan.Request()
            motion_request = MotionPlanRequest()
            
            # 设置规划参数
            motion_request.group_name = group_name
            motion_request.num_planning_attempts = 5
            motion_request.allowed_planning_time = planning_time
            motion_request.planner_id = planner_id
            motion_request.max_velocity_scaling_factor = 0.1
            motion_request.max_acceleration_scaling_factor = 0.1
            
            # 获取当前状态
            if hasattr(self, 'get_current_state'):
                motion_request.start_state = self.get_current_state()
            
            # 创建位姿约束
            from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint, BoundingVolume
            from shape_msgs.msg import SolidPrimitive
            
            constraints = Constraints()
            
            # 位置约束
            pos_constraint = PositionConstraint()
            pos_constraint.header = pose_stamped.header
            pos_constraint.link_name = "panda_hand"  # 或 "panda_link8"
            
            # 约束区域
            bounding_volume = BoundingVolume()
            sphere = SolidPrimitive()
            sphere.type = SolidPrimitive.SPHERE
            sphere.dimensions = [0.02]  # 2cm容差
            
            bounding_volume.primitives.append(sphere)
            bounding_volume.primitive_poses.append(pose_stamped.pose)
            pos_constraint.constraint_region = bounding_volume
            pos_constraint.weight = 1.0
            constraints.position_constraints.append(pos_constraint)
            
            # 方向约束
            orient_constraint = OrientationConstraint()
            orient_constraint.header = pose_stamped.header
            orient_constraint.link_name = pos_constraint.link_name
            orient_constraint.orientation = pose_stamped.pose.orientation
            orient_constraint.absolute_x_axis_tolerance = 0.1
            orient_constraint.absolute_y_axis_tolerance = 0.1
            orient_constraint.absolute_z_axis_tolerance = 0.1
            orient_constraint.weight = 1.0
            constraints.orientation_constraints.append(orient_constraint)
            
            motion_request.goal_constraints = [constraints]
            
            # 设置工作空间
            motion_request.workspace_parameters = WorkspaceParameters()
            motion_request.workspace_parameters.header.frame_id = "panda_link0"
            motion_request.workspace_parameters.min_corner.x = -1.0
            motion_request.workspace_parameters.min_corner.y = -1.0
            motion_request.workspace_parameters.min_corner.z = -1.0
            motion_request.workspace_parameters.max_corner.x = 1.0
            motion_request.workspace_parameters.max_corner.y = 1.0
            motion_request.workspace_parameters.max_corner.z = 1.0
            
            request.motion_plan_request = motion_request
            
            # 发送请求
            self.get_logger().info("发送位姿规划请求到服务...")
            future = self.plan_client.call_async(request)
            
            # 等待响应
            rclpy.spin_until_future_complete(self, future, timeout_sec=planning_time + 2.0)
            
            if future.done():
                response = future.result()
                if response.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                    # 提取轨迹
                    trajectory = response.motion_plan_response.trajectory
                    joint_trajectory = self._convert_trajectory(trajectory)
                    
                    return {
                        "success": True,
                        "trajectory": joint_trajectory,
                        "planning_time": response.motion_plan_response.planning_time,
                        "error_code": response.motion_plan_response.error_code.val
                    }
                else:
                    error_msg = f"服务规划失败: {response.motion_plan_response.error_code.val}"
                    self.get_logger().error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": response.motion_plan_response.error_code.val
                    }
            else:
                return {
                    "success": False,
                    "error": "规划服务请求超时",
                    "error_code": -1
                }
                
        except Exception as e:
            self.get_logger().error(f"服务规划异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": -15
            }
    def _convert_trajectory(self, moveit_trajectory):
        """
        将MoveIt轨迹转换为JointTrajectory消息
        """
        joint_trajectory = JointTrajectory()
        
        if not moveit_trajectory.joint_trajectory.points:
            return joint_trajectory
        
        joint_trajectory.joint_names = moveit_trajectory.joint_trajectory.joint_names
        
        for point in moveit_trajectory.joint_trajectory.points:
            traj_point = JointTrajectoryPoint()
            traj_point.positions = point.positions
            traj_point.velocities = point.velocities if point.velocities else []
            traj_point.accelerations = point.accelerations if point.accelerations else []
            traj_point.time_from_start = point.time_from_start
            joint_trajectory.points.append(traj_point)
        
        return joint_trajectory    
    def error_code_to_string(self, error_code):
        """错误代码转可读字符串"""
        codes = {
            1: "成功",
            -1: "规划失败",
            -2: "无效运动规划",
            -3: "运动规划因环境变化失效",
            -4: "控制失败",
            -5: "无法获取传感器数据",
            -6: "超时",
            -7: "被抢占",
            -9: "起始状态碰撞",
            -10: "起始状态违反路径约束",
            -11: "目标碰撞",
            -12: "目标违反路径约束",
            -13: "目标约束违反",
            -14: "无效组名",
            -15: "无效目标约束",
            -16: "无效机器人状态",
            -25: "通信失败",
            99999: "通用失败"
        }
        return codes.get(error_code, f"未知错误({error_code})")
    
    def destroy(self):
        """清理资源"""
        self.get_logger().info("MoveIt ROS2客户端关闭")
        super().destroy_node()


# 测试函数
def test_client():
    """测试客户端"""
    import rclpy
    
    print("测试MoveIt ROS2客户端...")
    
    rclpy.init()
    client = None
    
    try:
        client = MoveItROS2Client()
        
        # 等待一下确保连接建立
        time.sleep(0.5)
        
        if client.is_available():
            print("✅ MoveIt服务可用")
        else:
            print("❌ MoveIt服务不可用")
            return False
        
        # 测试关节规划
        print("\n测试关节规划...")
        test_joints = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        
        result = client.plan_to_joints(
            test_joints, 
            group_name="panda_arm",
            planning_time=3.0
        )
        
        print(f"规划结果: 成功={result.get('success', False)}")
        print(f"错误代码: {result.get('error_code', 'N/A')}")
        print(f"错误信息: {result.get('error_message', 'N/A')}")
        print(f"规划时间: {result.get('planning_time', 0):.2f}s")
        
        if result.get('success', False):
            print(f"轨迹点数: {result.get('point_count', 0)}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client:
            client.destroy()
        rclpy.shutdown()


if __name__ == "__main__":
    try:
        success = test_client()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被中断")
        exit(130)
    except Exception as e:
        print(f"测试异常: {e}")
        exit(1)