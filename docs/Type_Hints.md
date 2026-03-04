这些是 Python类型注解（Type Hints），用于提高代码的可读性和可维护性。让我详细解释每个的作用：

1. Dict - 字典类型注解

```python
from typing import Dict

# 普通写法（无类型提示）
def process_data(data):
    for key, value in data.items():
        print(f"{key}: {value}")

# 类型注解写法
def process_data(data: Dict[str, int]) -> None:
    """
    参数data必须是：键为字符串，值为整数的字典
    返回值：None（无返回值）
    """
    for key, value in data.items():
        print(f"{key}: {value}")

# 使用示例
process_data({"age": 25, "score": 95})  # ✅ 正确
process_data({"name": "Alice", "age": "25"})  # ❌ 错误：age应该是int
```

更复杂的Dict类型：

```python
from typing import Dict, List, Tuple

# 复杂字典类型
config: Dict[str, Dict[str, List[str]]] = {
    "robot1": {
        "joints": ["joint1", "joint2", "joint3"],
        "sensors": ["camera", "lidar"]
    },
    "robot2": {
        "joints": ["joint_a", "joint_b"],
        "sensors": ["imu", "gps"]
    }
}

# 函数中使用
def get_robot_config(robots: Dict[str, Dict]) -> List[str]:
    return list(robots.keys())
```

2. List - 列表类型注解

```python
from typing import List

# 普通列表
names: List[str] = ["Alice", "Bob", "Charlie"]

# 嵌套列表
matrix: List[List[float]] = [
    [1.0, 2.0, 3.0],
    [4.0, 5.0, 6.0]
]

# 在函数中使用
def filter_positive(numbers: List[float]) -> List[float]:
    """返回正数列表"""
    return [n for n in numbers if n > 0]

# 在ROS中的实际应用
from sensor_msgs.msg import JointState
from typing import List

def get_joint_positions(joint_state: JointState) -> List[float]:
    """从JointState消息中提取位置"""
    return list(joint_state.position)  # 明确返回float列表
```

3. Optional - 可空类型注解

```python
from typing import Optional

def find_robot_by_name(name: str, robots: List[Robot]) -> Optional[Robot]:
    """
    根据名称查找机器人
    可能找到，也可能找不到（返回None）
    """
    for robot in robots:
        if robot.name == name:
            return robot
    return None  # 允许返回None

# 使用时需要检查None
robot = find_robot_by_name("panda", robot_list)
if robot is not None:  # 必须检查
    robot.move_to_position([0.5, 0, 0.3])
else:
    print("机器人不存在")

# 对比：非Optional类型
def get_robot_name(robot: Robot) -> str:
    """这个函数总是返回字符串，不能返回None"""
    return robot.name
```

4. Any - 任意类型注解

```python
from typing import Any

def debug_print(value: Any) -> None:
    """
    接受任何类型的参数
    通常用于：
    1. 调试函数
    2. 包装器函数
    3. 动态类型处理
    """
    print(f"类型: {type(value)}, 值: {value}")

# 各种类型都可以传入
debug_print(42)           # int
debug_print("Hello")      # str  
debug_print([1, 2, 3])    # list
debug_print({"a": 1})     # dict
debug_print(None)         # None

# 谨慎使用！失去类型安全性
# 尽量使用具体类型，除非必要
```
在ROS 2中的实际应用

示例1：MoveIt服务封装

```python
from typing import Dict, List, Optional, Any
import rclpy
from moveit_msgs.srv import GetPlanningScene
from geometry_msgs.msg import Pose

class MoveItWrapper:
    def __init__(self):
        self.robot_config: Dict[str, Any] = {}
        self.joint_names: List[str] = []
        
    def get_current_pose(self, link_name: str) -> Optional[Pose]:
        """
        获取当前末端位姿
        返回：Pose对象或None（如果失败）
        """
        try:
            # 调用MoveIt服务
            response = self._call_service(link_name)
            if response.success:
                return response.pose
            return None
        except Exception as e:
            self.get_logger().error(f"获取位姿失败: {e}")
            return None
    
    def plan_path(self, 
                  waypoints: List[Pose],
                  constraints: Optional[Dict[str, Any]] = None
                 ) -> Optional[List[Pose]]:
        """
        规划路径
        waypoints: 必须的路径点列表
        constraints: 可选的约束条件字典
        """
        if constraints is None:
            constraints = {}
        # 规划逻辑...
```

示例2：配置管理

```python
from typing import Dict, List, Optional, Any
import yaml

class ConfigManager:
    def __init__(self, config_path: str):
        self.config: Dict[str, Any] = self._load_config(config_path)
        
    def _load_config(self, path: str) -> Dict[str, Any]:
        """加载YAML配置"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_moveit_services(self) -> Dict[str, str]:
        """获取MoveIt服务配置"""
        services = self.config.get('moveit_services', {})
        return {
            'get_scene': services.get('get_planning_scene', '/get_planning_scene'),
            'apply_scene': services.get('apply_planning_scene', '/apply_planning_scene')
        }
    
    def get_joint_limits(self, joint_name: str) -> Optional[List[float]]:
        """获取关节限位"""
        limits = self.config.get('joint_limits', {})
        return limits.get(joint_name)  # [min, max]
```

为什么使用类型注解？

好处：

```python
# 1. 提高可读性
def process(data):  # ❌ data是什么类型？返回什么？
    pass

def process(data: Dict[str, int]) -> List[str]:  # ✅ 一目了然
    pass

# 2. 静态类型检查（使用mypy）
# pip install mypy
# mypy your_script.py  # 检查类型错误

# 3. IDE智能提示
# VS Code/PyCharm能提供更好的代码补全

# 4. 文档化
# 类型注解本身就是文档
```

Python 3.9+ 的简化语法

```python
# Python 3.9+ 可以使用内置类型
# 不再需要 typing 模块
list[str]           # 代替 List[str]
dict[str, int]      # 代替 Dict[str, int]
tuple[int, int]     # 代替 Tuple[int, int]

# 但 Optional 和 Any 仍然需要 typing
from typing import Optional, Any
```

在ROS 2项目中的最佳实践

```python
from typing import Dict, List, Optional, Any, Union
import rclpy
from moveit_msgs.msg import RobotState
from geometry_msgs.msg import Pose, Point

class RobotController:
    def __init__(self, 
                 config: Dict[str, Any],
                 joint_names: Optional[List[str]] = None):
        """
        初始化机器人控制器
        
        Args:
            config: 配置字典
            joint_names: 可选的关节名列表，为None时使用默认
        """
        self.config = config
        self.joint_names = joint_names or self._get_default_joints()
        
    def move_to_positions(self,
                         positions: Union[List[float], Dict[str, float]],
                         timeout: float = 10.0
                        ) -> bool:
        """
        移动到指定位置
        
        Args:
            positions: 可以是位置列表或字典
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        # 实现...
        pass
```

总结

类型 作用 使用场景
Dict[K, V] 指定字典键值类型 配置数据、参数传递
List[T] 指定列表元素类型 关节位置、路径点列表
Optional[T] 可能为None的类型 可能失败的操作返回值
Any 任意类型 动态数据、包装器函数

简单记忆：

· Dict：当你想说"这是个字典，键是X，值是Y"
· List：当你想说"这是个列表，里面都是T类型"
· Optional：当你想说"可能返回T，也可能返回None"
· Any：当你想说"什么类型都可以"（谨慎使用）