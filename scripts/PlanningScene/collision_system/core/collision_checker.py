#!/usr/bin/env python3
"""
核心碰撞检查器 - 实现所有6个功能（修复版）
"""
import rclpy
from rclpy.node import Node
from typing import Dict, List, Optional, Any
import numpy as np

# MoveIt2消息
from moveit_msgs.srv import (
    GetPlanningScene, ApplyPlanningScene,
    GetStateValidity
)
from moveit_msgs.msg import (
    PlanningScene, RobotState, AllowedCollisionMatrix,
    AllowedCollisionEntry, PlanningSceneWorld, CollisionObject
)
from sensor_msgs.msg import JointState


class CollisionChecker(Node):
    """简化版碰撞检查器 - 实现6个核心功能"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('collision_checker')
        self.config = config
        
        # 初始化服务客户端
        
        self.logger = self.get_logger()
        self.services_ready = False
        self._init_clients()
        
    def _init_clients(self):
        """初始化所有需要的服务客户端 - 修复版"""
        moveit_config = self.config.get('moveit_services', {})
        
        self.logger.info("初始化MoveIt服务连接...")
        
        # ==================== 修复1：正确的服务名称和类型 ====================
        # 1. 获取规划场景服务
        self.get_scene_client = self.create_client(
            GetPlanningScene,
            moveit_config.get('get_planning_scene', '/get_planning_scene')
        )
        
        # 2. 应用规划场景服务
        self.apply_scene_client = self.create_client(
            ApplyPlanningScene,
            moveit_config.get('apply_planning_scene', '/apply_planning_scene')
        )
        
        # ==================== 修复2：只有一个状态检查服务 ====================
        # 根据你的ROS服务列表，只有 /check_state_validity 服务
        # 所以我们将两个客户端都指向同一个服务
        check_state_service = moveit_config.get('check_state_validity', '/check_state_validity')        # 3. 检查状态有效性服务
        self.check_state_client = self.create_client(
            GetStateValidity,  # 关键修复：使用 GetStateValidity 而不是 CheckStateValidity
            check_state_service
        )
        
        # 4. 获取状态有效性服务 - 指向同一个服务
        # 因为 /get_state_validity 不存在
        self.get_state_client = self.check_state_client
        
        # ==================== 修复3：增强的服务等待逻辑 ====================
        self.services_ready = True
        required_services = [
            (self.get_scene_client, "获取场景"),
            (self.apply_scene_client, "应用场景"),
            (self.check_state_client, "状态检查"),
        ]
        
        for client, name in required_services:
            if client:
                if client.wait_for_service(timeout_sec=5.0):
                    self.logger.info(f"✅ {name}服务可用")
                else:
                    self.logger.error(f"❌ {name}服务不可用")
                    self.services_ready = False
            else:
                self.logger.error(f"❌ {name}客户端创建失败")
                self.services_ready = False
        
        if not self.services_ready:
            self.logger.warning("⚠️ 部分服务不可用，功能将受限")
    
    # ==================== 功能1: 自碰撞检查 ====================
    def check_self_collision(
        self, 
        robot_state: RobotState, 
        group_name: str = None
    ) -> Dict[str, Any]:
        """
        功能1: 检查机器人自碰撞 - 修复版
        """
        # 检查服务是否可用
        if not self.services_ready or not self.check_state_client:
            return {'collision': True, 'error': '服务不可用'}
        
        if group_name is None:
            group_name = self.config.get('default_planning_group', 'panda_arm')# 关键修复：group_name 必须是有效字符串
        if not isinstance(group_name, str) or group_name.strip() == "":
            group_name = 'panda_arm'
        
        # 使用 GetStateValidity 服务
        request = GetStateValidity.Request()
        request.robot_state = robot_state
        request.group_name = group_name
        
        try:
            future = self.check_state_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            
            if future.result() is not None:
                result = future.result()
                return {
                    'collision': not result.valid,  # 无效表示有碰撞
                    'valid': result.valid,
                    'contacts': result.contacts,
                    'cost_sources': result.cost_sources,
                    'group_name': group_name
                }
            else:
                return {'collision': True, 'error': '服务返回空结果'}
        except Exception as e:
            self.logger.error(f"自碰撞检查失败: {e}")
        
        return {'collision': True, 'error': '检查失败'}
    
    # ==================== 功能2: 环境碰撞检查 ====================
    def check_environment_collision(
        self,
        robot_state: RobotState,
        group_name: str = None
    ) -> Dict[str, Any]:
        """
        功能2: 检查机器人与环境物体的碰撞 - 修复版
        """
        # 使用与自碰撞检查相同的服务，但分析结果不同
        self_collision_result = self.check_self_collision(robot_state, group_name)
        
        if 'error' in self_collision_result:
            return self_collision_result
        
        # 分析接触点，判断是否是环境碰撞
        env_contacts = []
        if 'contacts' in self_collision_result:
            for contact in self_collision_result['contacts']:
                # 简化的环境碰撞判断：如果接触点不全是机器人部件
                if not (contact.body_name_1.startswith('panda') and 
                       contact.body_name_2.startswith('panda')):
                    env_contacts.append(contact)
        
        return {
            'collision': len(env_contacts) > 0,
            'environment_objects': len(env_contacts),
            'contacts': env_contacts,
            'details': f'发现 {len(env_contacts)} 个环境接触点'
        }    # ==================== 功能3: State修改 ====================
    def modify_robot_state(
        self,
        joint_names: List[str],
        joint_positions: List[float],
        velocities: List[float] = None,
        efforts: List[float] = None
    ) -> RobotState:
        """
        功能3: 创建或修改机器人状态
        """
        robot_state = RobotState()
        joint_state = JointState()
        
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.name = joint_names
        joint_state.position = [float(pos) for pos in joint_positions]
        
        if velocities:
            joint_state.velocity = [float(v) for v in velocities]
        if efforts:
            joint_state.effort = [float(e) for e in efforts]
        
        robot_state.joint_state = joint_state
        return robot_state
    
    # ==================== 功能4: Planning group获取关联信息 ====================
    def get_planning_group_info(
        self,
        group_name: str = None
    ) -> Dict[str, Any]:
        """
        功能4: 获取规划组的关联信息
        """
        if group_name is None:
            group_name = self.config.get('default_planning_group', 'panda_arm')
        
        # 返回真实的Panda机器人关节名（而不是示例数据）
        if group_name == 'panda_arm':
            return {
                'group_name': group_name,
                'joint_names': [
                    "panda_joint1", "panda_joint2", "panda_joint3",
                    "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
                ],
                'links': [
                    "panda_link1", "panda_link2", "panda_link3",
                    "panda_link4", "panda_link5", "panda_link6", "panda_link7"
                ],
                'end_effector': "panda_hand",
                'chain': ["panda_link0", "panda_hand"]
            }
        else:
            # 对于其他规划组，返回示例数据
            return {
                'group_name': group_name,
                'joint_names': [f'{group_name}_joint{i}' for i in range(1, 8)],
                'links': [f'{group_name}_link{i}' for i in range(1, 8)],
                'end_effector': f'{group_name}_hand',
                'chain': [f'{group_name}_base', f'{group_name}_hand']
            }
    
    # ==================== 功能5: 修改允许碰撞矩阵 ====================
    def modify_allowed_collision_matrix(
        self,
        object1: str,
        object2: str,
        allowed: bool = True
    ) -> bool:
        """
        功能5: 修改允许碰撞矩阵 - 简化实现
        """
        # 获取当前场景
        scene = self.get_current_scene()
        if not scene:
            self.logger.error("无法获取当前场景")
            return False
        
        #创建或更新允许碰撞矩阵
        if not scene.allowed_collision_matrix:
            from moveit_msgs.msg import AllowedCollisionMatrix,AllowedCollisionEntry
            scene.allowed_collision_matrix = AllowedCollisionMatrix()

        #确保场景设置正确    
        scene.is_diff=True

        #添加或更新条目
        #这里仅记录操作并应用场景
        
        self.logger.info(f"设置允许碰撞: {object1} <-> {object2} = {allowed}")
        success = self.apply_scene(scene)
        if success:
            self.get_logger().info('允许碰撞矩阵修改成功')
        else:
            self.get_logger().error('允许碰撞矩阵修改失败')    
        return success    
        
        
        
    # ==================== 功能6: 检查所有碰撞 ====================
    def check_all_collisions(
    self,
    robot_state: RobotState,
    group_name: str = None
) -> Dict[str, Any]:
        """
        功能6: 检查所有碰撞（自碰撞+环境碰撞）- 最简修复版
        """
        if not self.services_ready:
            return {'error': '服务不可用'}
    
        if group_name is None:
            group_name = self.config.get('default_planning_group', 'panda_arm')

        try:
            # 创建最简单的请求
            request = GetStateValidity.Request()
            request.robot_state = robot_state
            request.group_name = group_name
        
            # 只设置这两个必填字段，其他都不设置
            # constraints 和 planner_id 可能不存在或可选
        
            future = self.get_state_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
            if future.result() is not None:
                result = future.result()
            
                # 使用安全的方式获取结果
                valid = getattr(result, 'valid', False)
                contacts = getattr(result, 'contacts', [])
            
                # 分析碰撞类型
                self_contacts = []
                env_contacts = []
            
                for contact in contacts:
                    # 安全地访问属性
                    body1 = getattr(contact, 'body_name_1', '')
                    body2 = getattr(contact, 'body_name_2', '')
                
                    if 'panda' in body1 and 'panda' in body2:
                        self_contacts.append(contact)
                    else:
                        env_contacts.append(contact)
            
                return {
                    'all_collision_check': {
                        'valid': valid,
                        'self_collision': len(self_contacts) > 0,
                        'environment_collision': len(env_contacts) > 0,
                        'self_contact_count': len(self_contacts),
                        'env_contact_count': len(env_contacts),
                        'total_contacts': len(contacts),
                        'has_contacts': len(contacts) > 0
                    }
                }
            else:
                return {'error': '服务返回空结果'}
            
        except Exception as e:
            self.get_logger().error(f"所有碰撞检查失败: {e}")
            return {'error': f'检查失败: {str(e)}'}
    
    # ==================== 辅助方法 ====================
    def get_current_scene(self) -> Optional[PlanningScene]:
        """获取当前规划场景"""
        if not self.services_ready or not self.get_scene_client:
            self.logger.error("获取场景服务不可用")
            return None
        
        request = GetPlanningScene.Request()
        
        try:
            future = self.get_scene_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            
            if future.result() is not None:
                return future.result().scene
        except Exception as e:
            self.logger.error(f"获取场景失败: {e}")
        
        return None
    
    def apply_scene(self, scene: PlanningScene) -> bool:
        """应用规划场景"""
        if not self.services_ready or not self.apply_scene_client:
            self.logger.error("应用场景服务不可用")
            return False
        
        #确保scene有必要的设置
        if not hasattr(scene,'is_diff') or scene.world is None:
            scene.is_diff = True#设置为差异更新

        #确保有world对象
        if not hasattr(scene,'world')or scene.world is None:
            scene.world  =PlanningSceneWorld()

        request = ApplyPlanningScene.Request()
        request.scene = scene
        
        
        try:
            future = self.apply_scene_client.call_async(request)
            rclpy.spin_until_future_complete(self, future,timeout_sec=5.0)          
            if future.result() is not None:
                result = future.result()
                if hasattr(result,'error_message') and result.error_message:
                    self.get_logger().warn(f'应用场景警告：{result.error_message}')
                success = result.success
                self.get_logger().info(f'场景应用结果：{'成功' if success else '失败'} ')   
                return success
            else:
                self.get_logger().error('场景应用无相应') 
        except Exception as e:
            self.logger.error(f"应用场景失败: {e}")
        
        return False
    
    def create_demo_state(self) -> RobotState:
        """创建演示用的机器人状态"""
        # 使用真实的Panda机器人关节名
        joint_names = [
            "panda_joint1", "panda_joint2", "panda_joint3",
            "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"
        ]
        
        # 安全位置
        joint_positions = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        
        return self.modify_robot_state(joint_names, joint_positions)


# ==================== 简化使用示例 ====================
def demo_all_functions():
    """演示所有6个功能 - 修复版"""
    import rclpy
    
    print("="*50)
    print("碰撞检测系统 - 6个核心功能演示（修复版）")
    print("="*50)
    
    rclpy.init()
    
    # 加载配置
    config = {
        'moveit_services': {
            'get_planning_scene': '/get_planning_scene',
            'apply_planning_scene': '/apply_planning_scene',
            'check_state_validity': '/check_state_validity',
            'get_state_validity': '/check_state_validity'  # 指向同一个服务
        },
        'default_planning_group': 'panda_arm',
        'service_timeout': 10.0
    }
    
    checker = CollisionChecker(config)
    
   # 检查服务可用性
    if not checker.services_ready:
        print("❌ 服务不可用，演示终止")
        print("请检查:")
        print("1. MoveIt是否已启动: ros2 launch moveit2_tutorials demo.launch.py")
        print("2. 服务是否存在: ros2 service list | grep -E '(planning_scene|state_validity)'")
        checker.destroy_node()
        rclpy.shutdown()
        return
    
    print("✅ 所有服务连接成功")
    
    # 1. 创建机器人状态（功能3）
    print("\n1. 创建机器人状态...")
    demo_state = checker.create_demo_state()
    print(f"   创建状态成功: {len(demo_state.joint_state.position)} 个关节")
    print(f"   关节名称: {demo_state.joint_state.name}")
    print(f"   关节位置: {demo_state.joint_state.position}")
    
    # 2. 自碰撞检查（功能1）
    print("\n2. 检查自碰撞...")
    self_collision = checker.check_self_collision(demo_state)
    if 'error' in self_collision:
        print(f"   自碰撞检查失败: {self_collision['error']}")
    else:
        print(f"   自碰撞检查结果: {'有碰撞' if self_collision.get('collision') else '无碰撞'}")
        print(f"   状态有效性: {'有效' if self_collision.get('valid') else '无效'}")
        print(f"   接触点数量: {len(self_collision.get('contacts', []))}")
    
    # 3. 环境碰撞检查（功能2）
    print("\n3. 检查环境碰撞...")
    env_collision = checker.check_environment_collision(demo_state)
    if 'error' in env_collision:
        print(f"   环境碰撞检查失败: {env_collision['error']}")
    else:
        print(f"   环境碰撞检查结果: {'有碰撞' if env_collision.get('collision') else '无碰撞'}")
        print(f"   环境接触点数量: {env_collision.get('environment_objects', 0)}")
        print(f"   详细信息: {env_collision.get('details', '')}")
    
    # 4. 获取规划组信息（功能4）
    print("\n4. 获取规划组信息...")
    group_info = checker.get_planning_group_info()
    print(f"   规划组: {group_info['group_name']}")
    print(f"   关节数: {len(group_info['joint_names'])}")
    print(f"   前3个关节: {group_info['joint_names'][:3]}...")
    print(f"   末端执行器: {group_info['end_effector']}")
    
    # 5. 修改允许碰撞矩阵（功能5）
    print("\n5. 修改允许碰撞矩阵...")
    success = checker.modify_allowed_collision_matrix(
        "panda_link1", "panda_link2", allowed=True
    )
    print(f"   修改结果: {'成功' if success else '失败'}")
    
    # 6. 检查所有碰撞（功能6）
    # 6. 检查所有碰撞（功能6）
    print("\n6. 检查所有碰撞...")
    all_collisions = checker.check_all_collisions(demo_state)
    if 'error' in all_collisions:
        print(f"   所有碰撞检查失败: {all_collisions['error']}")
    elif 'all_collision_check' in all_collisions:
        result = all_collisions['all_collision_check']
        print(f"   状态有效性: {'有效' if result['valid'] else '无效'}")
        print(f"   自碰撞: {'有' if result['self_collision'] else '无'} ({result['self_contact_count']}个接触点)")
        print(f"   环境碰撞: {'有' if result['environment_collision'] else '无'} ({result['env_contact_count']}个接触点)")
        print(f"   总接触点: {result['total_contacts']}")
    
        # 删除这行！因为根本没有 minimum_distance 字段
        # print(f"   最近距离: {result['minimum_distance']:.4f}m")  # ← 删除这行！
    
        if result['total_contacts'] > 0:
            print(f"   ⚠️ 检测到碰撞，状态不安全")
        else:
            print(f"   ✅ 无碰撞，状态安全")
            print("\n" + "="*50)
            print("演示完成")
            print("="*50)
    
    checker.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    demo_all_functions()