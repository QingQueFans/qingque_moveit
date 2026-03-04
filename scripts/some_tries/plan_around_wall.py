#!/usr/bin/env python3
"""
避障规划脚本 - 修复版
确保先运行：
1. ros2 launch moveit_resources_panda_moveit_config demo.launch.py
2. python3 create_wall_only.py
"""
import rclpy
import sys
import time
from rclpy.node import Node
from moveit_commander import MoveGroupCommander, PlanningSceneInterface, RobotCommander

class WallObstaclePlanner(Node):
    def __init__(self):
        super().__init__('wall_obstacle_planner')
        
        # 等待 MoveGroup 启动
        time.sleep(2)
        
        # 初始化 MoveIt Commander
        self.robot = RobotCommander()
        self.move_group = MoveGroupCommander("panda_arm")
        self.scene = PlanningSceneInterface()
        
        self.get_logger().info("="*60)
        self.get_logger().info("🧱 有墙环境下的避障规划测试")
        self.get_logger().info("="*60)
        
        # 设置规划参数
        self.move_group.set_planning_time(5.0)  # 规划时间
        self.move_group.set_num_planning_attempts(10)  # 尝试次数
        self.move_group.set_max_velocity_scaling_factor(0.5)  # 速度限制
        self.move_group.set_max_acceleration_scaling_factor(0.5)  # 加速度限制
        
    def check_environment(self):
        """检查环境和墙"""
        # 检查机器人模型
        model_frame = self.robot.get_planning_frame()
        self.get_logger().info(f"规划框架: {model_frame}")
        
        # 检查当前关节状态
        joint_values = self.move_group.get_current_joint_values()
        self.get_logger().info(f"当前关节值: {[round(v, 3) for v in joint_values]}")
        
        # 检查墙是否已创建
        known_objects = self.scene.get_known_object_names()
        wall_objects = [obj for obj in known_objects if "wall_box" in obj]
        
        if wall_objects:
            self.get_logger().info(f"✅ 检测到 {len(wall_objects)} 个墙的组成部分")
            for obj in wall_objects:
                self.get_logger().info(f"  - {obj}")
            return True
        else:
            self.get_logger().warning("⚠️  未检测到墙！请先运行 create_wall_only.py")
            return False
    
    def plan_and_move(self, target_name, joint_target):
        """规划并移动到目标位置"""
        self.get_logger().info(f"\n🎯 尝试移动到: {target_name}")
        self.get_logger().info(f"目标关节: {[round(v, 3) for v in joint_target]}")
        
        # 设置目标
        self.move_group.set_joint_value_target(joint_target)
        
        # 规划路径
        self.get_logger().info("🤔 正在规划路径...")
        plan = self.move_group.plan()
        
        if plan[0]:  # plan 返回 (success, trajectory, planning_time, error_code)
            self.get_logger().info(f"✅ 规划成功！用时: {plan[2]:.2f}秒")
            
            # 显示轨迹信息
            trajectory = plan[1]
            num_points = len(trajectory.joint_trajectory.points)
            self.get_logger().info(f"轨迹点数: {num_points}")
            
            if num_points > 0:
                # 显示第一个和最后一个点
                first_point = trajectory.joint_trajectory.points[0].positions
                last_point = trajectory.joint_trajectory.points[-1].positions
                self.get_logger().info(f"起点: {[round(v, 3) for v in first_point]}")
                self.get_logger().info(f"终点: {[round(v, 3) for v in last_point]}")
            
            # 询问是否执行
            response = input("执行这个轨迹吗？ (y/n): ")
            if response.lower() == 'y':
                self.get_logger().info("🚀 执行轨迹...")
                self.move_group.execute(trajectory, wait=True)
                self.get_logger().info("🎉 执行完成！")
                return True
            else:
                self.get_logger().info("⏸️ 跳过执行")
                return True
        else:
            error_code = plan[3]
            self.get_logger().error(f"❌ 规划失败！错误码: {error_code}")
            return False 
    def test_obstacle_avoidance(self):
        """测试避障功能"""
        # 定义测试序列
        test_sequence = [
            ("安全位置_远离墙", [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]),
            ("向前_靠近墙", [0.8, 0.0, 0.0, -1.5, 0.0, 1.5, 0.0]),
            ("尝试绕过墙", [1.0, -0.5, 0.3, -1.2, 0.2, 1.3, 0.6]),
            ("回到初始位置", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ]
        
        results = []
        for name, joints in test_sequence:
            success = self.plan_and_move(name, joints)
            results.append((name, success))
            time.sleep(1)  # 等待一下
        
        # 总结结果
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("📊 测试结果总结")
        self.get_logger().info("="*60)
        
        for name, success in results:
            status = "✅ 成功" if success else "❌ 失败"
            self.get_logger().info(f"{name:20} {status}")
        
        # 统计
        total = len(results)
        successful = sum(1 for _, success in results if success)
        self.get_logger().info(f"\n成功率: {successful}/{total} ({successful/total*100:.1f}%)")
    
    def visualize_current_pose(self):
        """显示当前末端位姿"""
        current_pose = self.move_group.get_current_pose().pose
        self.get_logger().info("\n🔍 当前末端执行器位姿:")
        self.get_logger().info(f"  位置: x={current_pose.position.x:.3f}, "
                             f"y={current_pose.position.y:.3f}, "
                             f"z={current_pose.position.z:.3f}")
        self.get_logger().info(f"  朝向: w={current_pose.orientation.w:.3f}")

def main():
    rclpy.init()
    
    planner = WallObstaclePlanner()
    
    try:
        # 1. 检查环境
        if not planner.check_environment():
            planner.get_logger().error("环境检查失败，退出")
            return
        
        # 2. 显示当前状态
        planner.visualize_current_pose()
        
        # 3. 询问用户开始测试
        print("\n" + "="*60)
        print("是否开始避障规划测试？")
        print("提示：在 RViz 中观察轨迹如何绕过墙")
        print("="*60)
        
        response = input("开始测试？ (y/n): ")
        if response.lower() != 'y':
            planner.get_logger().info("测试取消")
            return
        
        # 4. 执行测试
        planner.test_obstacle_avoidance()
        
        planner.get_logger().info("\n🎉 测试完成！")
        planner.get_logger().info("在 RViz 中观察轨迹，看机械臂如何避开墙")
        
    except KeyboardInterrupt:
        planner.get_logger().info("\n🛑 用户中断")
    except Exception as e:
        planner.get_logger().error(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        planner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()