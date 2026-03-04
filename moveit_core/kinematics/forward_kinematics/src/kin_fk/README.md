📐 FK计算原理详解
核心思想
已知关节角度，求末端执行器的位置和姿态。

text
输入: 关节角度 [j1, j2, j3, j4, j5, j6, j7]
输出: 末端位姿 [x, y, z, qx, qy, qz, qw]
🏗️ 计算方法：DH参数法
1. 每个关节的变换矩阵
python
# 对于关节i，其变换矩阵为：
Ti = [
    [cosθ,  -sinθ*cosα,  sinθ*sinα,  a*cosθ],
    [sinθ,   cosθ*cosα, -cosθ*sinα,  a*sinθ],
    [0,           sinα,        cosα,       d],
    [0,              0,           0,       1]
]
2. Panda的DH参数
python
DH_PARAMS = [
    # 关节1
    {"a": 0.0, "alpha": 0.0,      "d": 0.333, "theta": 0.0},
    # 关节2  
    {"a": 0.0, "alpha": -1.5708,  "d": 0.0,   "theta": 0.0},
    # 关节3
    {"a": 0.0, "alpha": 1.5708,   "d": -0.316,"theta": 0.0},
    # 关节4
    {"a": 0.0825, "alpha": 1.5708, "d": 0.0,   "theta": 0.0},
    # 关节5
    {"a": -0.0825,"alpha": -1.5708,"d": 0.384, "theta": 0.0},
    # 关节6
    {"a": 0.0, "alpha": 1.5708,   "d": 0.0,   "theta": 0.0},
    # 关节7
    {"a": 0.088, "alpha": 1.5708, "d": 0.0,   "theta": 0.0},
]
3. 计算过程
python
def compute_fk(joint_angles):
    T = 单位矩阵  # 从基座开始
    
    for i, angle in enumerate(joint_angles):
        # 获取关节i的DH参数
        a = DH_PARAMS[i]["a"]
        alpha = DH_PARAMS[i]["alpha"]
        d = DH_PARAMS[i]["d"]
        theta0 = DH_PARAMS[i]["theta"]
        
        # 当前关节的总角度
        theta = angle + theta0
        
        # 计算当前关节的变换矩阵
        Ti = dh_transform(theta, d, a, alpha)
        
        # 累积变换
        T = T @ Ti
    
    # 应用末端工具变换
    T = T @ tool_transform
    
    return T  # 4x4变换矩阵
4. 从矩阵提取位姿
python
def matrix_to_pose(T):
    # 位置
    x, y, z = T[0,3], T[1,3], T[2,3]
    
    # 旋转矩阵 → 四元数
    R = T[:3, :3]
    qw = sqrt(1 + R[0,0] + R[1,1] + R[2,2]) / 2
    qx = (R[2,1] - R[1,2]) / (4*qw)
    qy = (R[0,2] - R[2,0]) / (4*qw)
    qz = (R[1,0] - R[0,1]) / (4*qw)
    
    return [x, y, z, qx, qy, qz, qw]
🎯 物理意义
每一步变换相当于：

绕Z轴旋转θ（关节转动）

沿Z轴平移d（连杆长度）

沿X轴平移a（连杆偏移）

绕X轴旋转α（连杆扭转）

最终得到末端在基坐标系中的位姿！

📚 FK三个文件使用指南
一、文件结构
text
kin_fk/
├── fk_solver.py          # 核心求解器（底层）
├── pose_computer.py      # 位姿计算器（中层接口）
└── transform_calculator.py # 变换计算器（工具）
二、一行调用接口
fk_solver.py - 核心求解器
python
from kin_fk.fk_solver import FKSolver

# 一行调用：计算正运动学
fk = FKSolver()
T = fk.compute([0, -0.785, 0, -2.356, 0, 1.571, 0.785])  # 返回4x4矩阵
pose = fk.compute_pose_list([0, -0.785, 0, -2.356, 0, 1.571, 0.785])  # 返回7元素列表
pose_computer.py - 位姿计算器（推荐）
python
from kin_fk.pose_computer import PoseComputer

# 一行调用：计算末端位姿（最常用）
pc = PoseComputer()
result = pc.compute_end_effector([0, -0.785, 0, -2.356, 0, 1.571, 0.785])

# 结果包含：
print(f"位置: {result['position']}")        # [x,y,z]
print(f"方向: {result['orientation']}")     # [qx,qy,qz,qw]
print(f"变换矩阵: {result['matrix']}")       # 4x4矩阵
transform_calculator.py - 变换计算器
python
from kin_fk.transform_calculator import TransformCalculator

# 一行调用：坐标系变换
tc = TransformCalculator()
pose_in_base = tc.transform_pose(object_pose, from_frame="camera", to_frame="base_link")
三、完整示例
python
# 最简单的使用方式
from kin_fk.pose_computer import PoseComputer

# 一行搞定！
pc = PoseComputer()
result = pc.compute_end_effector([0, -0.785, 0, -2.356, 0, 1.571, 0.785])

print(f"末端位置: {result['position']}")
四、便捷函数（全局）
python
# 在 __init__.py 中导出便捷函数
from .pose_computer import quick_fk

# 直接使用
pose = quick_fk([0, -0.785, 0, -2.356, 0, 1.571, 0.785])
