#!/usr/bin/env python3
"""
验证五个箱子的碰撞效果
"""
import rclpy
import time
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

class CollisionVerifier(Node):
    def __init__(self):
        super().__init__('collision_verifier')
        self.scene_pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        time.sleep(1)
        print("📦 按教程搭建五个箱子")
        print("="*50)
    
    def create_tutorial_wall(self):
        """按教程创建五个箱子的墙"""
        scene = PlanningScene()
        scene.is_diff = True
        
        # 教程中的五个箱子位置（调整到Panda工作空间内）
        boxes = [
            {"id": "box1", "pos": (0.4, 0.0, 0.3), "size": (0.1, 0.1, 0.1)},
            {"id": "box2", "pos": (0.4, 0.0, 0.5), "size": (0.1, 0.1, 0.1)},
            {"id": "box3", "pos": (0.4, 0.0, 0.7), "size": (0.1, 0.1, 0.1)},
            {"id": "box4", "pos": (0.4, -0.15, 0.5), "size": (0.1, 0.1, 0.1)},
            {"id": "box5", "pos": (0.4, 0.15, 0.5), "size": (0.1, 0.1, 0.1)},
        ]
        
        for box in boxes:
            obj = CollisionObject()
            obj.id = box["id"]
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.ADD
            
            # 创建Box
            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.BOX
            primitive.dimensions = list(box["size"])
            
            # 设置位置
            pose = Pose()
            pose.position.x = box["pos"][0]
            pose.position.y = box["pos"][1]
            pose.position.z = box["pos"][2]
            pose.orientation.w = 1.0
            
            obj.primitives.append(primitive)
            obj.primitive_poses.append(pose)
            scene.world.collision_objects.append(box)
            
            print(f"  创建 {box['id']}: 位置{box['pos']}")
        
        self.scene_pub.publish(scene)
        print("✅ 教程墙已创建完成")
        return boxes
    
    def test_collision_scenarios(self):
        """测试三种碰撞场景"""
        print("\n🧪 碰撞测试场景")
        print("="*50)
        
        scenarios = [
            ("1. 直接碰撞测试", "尝试让机械臂末端直接穿过箱子"),
            ("2. 避障规划测试", "规划绕过箱子的路径"),
            ("3. 贴近测试", "让机械臂贴近但不碰撞箱子"),
        ]
        
        for name, instruction in scenarios:
            print(f"\n{name}")
            print(f"  操作: {instruction}")
            print(f"  观察: 查看MoveIt的碰撞反馈")
            input("  按回车继续测试...")
        
        print("\n✅ 所有场景测试完成")
    
    def measure_clearance(self):
        """测量箱子间距"""
        print("\n📏 测量箱子布局")
        print("="*50)
        
        # 箱子的理论位置
        positions = [
            (0.4, 0.0, 0.3),   # 底部
            (0.4, 0.0, 0.5),   # 中部
            (0.4, 0.0, 0.7),   # 顶部
            (0.4, -0.15, 0.5), # 左部
            (0.4, 0.15, 0.5),  # 右部
        ]
        
        print("箱子布局分析:")
        print(f"  垂直间距: {positions[2][2] - positions[0][2]:.2f}m (共3层)")
        print(f"  水平间距: {positions[4][1] - positions[3][1]:.2f}m (左右对称)")
        print(f"  箱子尺寸: 0.1x0.1x0.1m")
        print(f"  可通过间隙: 约0.05m (需要精确规划)")
        
        return positions
    
    def plan_around_wall(self):
        """规划绕墙路径的概念演示"""
        print("\n🎯 绕墙路径规划概念")
        print("="*50)
        
        print("规划策略:")
        print("  1. 从左侧绕过: Y轴负方向移动")
        print("  2. 从右侧绕过: Y轴正方向移动")  
        print("  3. 从上方绕过: Z轴正方向移动")
        print("  4. 从下方绕过: Z轴负方向移动")
        
        print("\n在RViz中尝试:")
        print("  1. 设置起点在墙左侧")
        print("  2. 设置终点在墙右侧")
        print("  3. 点击Plan，观察避障路径")
        
        input("\n按回车查看清理选项...")
    
    def cleanup_options(self):
        """清理选项"""
        print("\n🗑️ 清理选项")
        print("="*50)
        
        options = [
            ("1. 移除所有箱子", "从场景中完全删除"),
            ("2. 保留箱子", "继续其他实验"),
            ("3. 修改箱子", "调整位置或大小"),
            ("4. 添加更多障碍", "创建复杂环境"),
        ]
        
        for option, desc in options:
            print(f"  {option}: {desc}")
        
        try:
            choice = input("\n选择清理选项 (1-4, 默认2): ").strip()
            if choice == "1":
                self.remove_all_boxes()
                print("✅ 所有箱子已移除")
            elif choice == "" or choice == "2":
                print("✅ 箱子保留在场景中")
            elif choice == "3":
                print("ℹ️  需要运行修改脚本")
            elif choice == "4":
                print("ℹ️  可以运行 add_more_obstacles.py")
        except:
            print("✅ 箱子保留在场景中")
    
    def remove_all_boxes(self):
        """移除所有箱子"""
        scene = PlanningScene()
        scene.is_diff = True
        
        for i in range(1, 6):
            obj = CollisionObject()
            obj.id = f"box{i}"
            obj.header.frame_id = "world"
            obj.operation = CollisionObject.REMOVE
            scene.world.collision_objects.append(obj)
        
        self.scene_pub.publish(scene)
def main():
    rclpy.init()
    verifier = CollisionVerifier()
    
    try:
        # 1. 创建教程墙
        boxes = verifier.create_tutorial_wall()
        
        # 2. 等待用户查看
        print("\n" + "="*50)
        print("👀 请在RViz中查看五个箱子的布局")
        print("   它们应该形成一个'十字'形状的墙")
        input("按回车继续测试...")
        
        # 3. 测量布局
        positions = verifier.measure_clearance()
        
        # 4. 碰撞测试
        verifier.test_collision_scenarios()
        
        # 5. 规划演示
        verifier.plan_around_wall()
        
        # 6. 清理选项
        verifier.cleanup_options()
        
        print("\n" + "="*50)
        print("🎉 教程箱子验证完成!")
        print("="*50)
        print("\n下一步可以:")
        print("1. 实现真实避障路径规划")
        print("2. 添加动态障碍物")
        print("3. 实现抓取这五个箱子")
        print("4. 创建更复杂的环境")
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    finally:
        # 不清除，让用户决定
        verifier.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
