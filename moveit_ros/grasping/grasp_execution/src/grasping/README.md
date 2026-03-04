
二、使用方式

1. 一行调用（推荐）

```python
# 在任何文件中
from grasping.gripper_controller import calculate_gripper

result = calculate_gripper("test_cube")
result = calculate_gripper("box") 
result = calculate_gripper([0.05, 0.05, 0.05], type="box")
```

2. 快速获取参数

```python
from grasping.gripper_controller import get_gripper_width, get_gripper_params

# 只要宽度
width_mm = get_gripper_width("test_cube")

# 要全部参数
width, force, strategy = get_gripper_params("test_cube")
```

3. 类方式调用

```python
from grasping.gripper_controller import GripperCalculator

result = GripperCalculator.calculate("test_cube")
```

三、测试代码

在文件末尾添加测试：

```python
# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== 夹爪计算器简化接口测试 ===")
    
    # 测试1: 物体ID模式
    print("\n测试1: 物体ID模式")
    result1 = calculate_gripper("test_cube")
    print(f"  成功: {result1['success']}, 宽度: {result1.get('gripper_width', 0)*1000:.1f}mm")
    
    # 测试2: 尺寸列表模式
    print("\n测试2: 尺寸列表模式")
    result2 = calculate_gripper([0.05, 0.05, 0.05], type="box")
    print(f"  成功: {result2['success']}, 宽度: {result2.get('gripper_width', 0)*1000:.1f}mm")
    
    # 测试3: 快速函数
    print("\n测试3: 快速函数")
    width_mm = get_gripper_width([0.1, 0.1, 0.1], type="box")
    print(f"  夹爪宽度: {width_mm:.1f}mm")
    
    # 测试4: 多参数获取
    print("\n测试4: 多参数获取")                                                                      
    width, force, strategy = get_gripper_params([0.03, 0.03, 0.03], type="box")
    print(f"  宽度: {width:.1f}mm, 力: {force:.1f}N, 策略: {strategy}")
```

四、优势

1. 向后兼容：不破坏现有代码
2. 简单易用：一行调用解决
3. 多种输入：支持物体ID、尺寸列表、完整字典
4. 智能解析：自动判断输入类型
5. 错误处理：内置异常捕获

这样你就在不修改原有逻辑的基础上，添加了最简单的一行调用接口！