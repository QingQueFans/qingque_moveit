📚 MoveGroup接口模块使用指南
一、模块概述
move_group_interface 是三级模块的核心，提供运动规划、抓取任务、轨迹执行的一站式接口。完全基于你的一行调用接口构建，无需任何底层实现。

二、三种使用方式
方式1：规划上下文（抓取专用） 🔥 最常用
python
from planning_interface.move_group_interface.src.move_group_interface import get_planning_context

# 获取单例
ctx = get_planning_context()

# 抓取场景中已存在的物体
result = ctx.grasp_object("qingque", strategy="top_grasp")
result = ctx.grasp_object("test_cube", strategy="side_grasp", width_mm=45)

# 抓取指定位姿（视觉引导）
pose = [0.5, 0.0, 0.3, 0, 0, 0, 1]
result = ctx.grasp_pose(pose, "vision_target", width_mm=50)

# 批量抓取
result = ctx.batch_grasp(["part1", "part2", "part3"], strategy="top_grasp")

# 查询当前任务状态
status = ctx.get_current_task_info()
print(f"当前物体: {status['current_object']}")
print(f"状态: {status['status']}")
print(f"缓存命中: {status['cache_hit']}")
适用场景：

✅ 日常抓取任务

✅ 视觉引导抓取

✅ 批量流水线作业

✅ 任务状态监控

方式2：MoveGroup类（运动+抓取） 🚀 通用接口
python
from planning_interface.move_group_interface.src.move_group_interface import MoveGroup

# 创建MoveGroup实例
arm = MoveGroup("panda_arm")  # 指定规划组

# ----- 运动控制 -----
# 移动到指定位姿
result = arm.move_to_pose([0.5, 0.0, 0.3, 0, 0, 0, 1])

# 移动到指定关节位置
result = arm.move_to_joints([0, -0.5, 0, -1.5, 0, 1.5, 0])

# 移动到物体位置（自动IK）
result = arm.move_to_object("qingque", use_cache=True)

# ----- 抓取任务 -----
# 抓取物体（委托给规划上下文）
result = arm.grasp("test_cube", strategy="top_grasp", width_mm=45)
result = arm.grasp_pose([0.5, 0.0, 0.3, 0, 0, 0, 1], "target")

# ----- 状态查询 -----
status = arm.get_status()
适用场景：

✅ 需要同时进行运动控制和抓取

✅ 调试机械臂运动

✅ 自定义运动序列

✅ 与MoveGroup语义一致的接口

方式3：轨迹执行（纯移动） ⚡ 轻量级
python
from planning_interface.move_group_interface.src.move_group_interface import (
    execute_trajectory,
    move_to_pose,
    move_to_joints,
    get_execution_stats,
    clear_trajectory_cache
)

# 通过物体ID执行（自动IK+规划）
result = execute_trajectory("qingque", use_cache=True, timeout=5.0)

# 通过位姿执行（IK+规划）
result = execute_trajectory([0.5, 0.0, 0.3, 0, 0, 0, 1])

# 通过关节执行（直接规划）
result = execute_trajectory({"joints": [0, -0.5, 0, -1.5, 0, 1.5, 0]})

# 快速函数
result = move_to_pose(0.5, 0.0, 0.3)  # 默认方向
result = move_to_joints([0, -0.5, 0, -1.5, 0, 1.5, 0])

# 系统管理
stats = get_execution_stats()
print(f"缓存命中率: {stats.get('hit_rate_percent', 0):.1f}%")
clear_trajectory_cache()  # 清空缓存
适用场景：

✅ 纯移动任务，不需要抓取

✅ 快速测试

✅ 命令行工具后端

✅ 性能测试

三、参数说明
grasp_object() 参数
参数	类型	说明	默认值
object_id	str	场景中已存在的物体ID	必填
strategy	str	抓取策略：top_grasp/side_grasp	"top_grasp"
width_mm	int/float	手动指定夹爪宽度(mm)	None（自动计算）
execute_trajectory() 参数
参数	类型	说明	默认值
target	str/list/dict	物体ID/位姿/关节	必填
use_cache	bool	是否使用缓存	True
timeout	float	规划超时时间(秒)	5.0
strategy	str	规划算法	"rrt_connect"
wait	bool	是否等待执行完成	True
四、返回值格式
所有方法返回统一格式的字典：

python
{
    "success": True/False,           # 是否成功
    "object_id": "qingque",          # 物体ID
    "grasp_width_mm": 50.0,          # 抓取宽度(mm)
    "grasp_strategy": "top_grasp",   # 抓取策略
    "ik_joints": [0.1, -0.5, ...],   # 关节解
    "execution_time": 2.35,           # 执行时间(秒)
    "cache_hit": True,                # 缓存是否命中
    "timestamp": "2026-02-12 15:30",  # 时间戳
    "message": "✅ 成功抓取物体 qingque",
    
    # 失败时包含
    "error": "移动失败",              # 错误信息
    "original_error": "timeout"       # 原始错误
}
五、完整示例
示例1：完整抓取-放置流程
python
from planning_interface.move_group_interface.src.move_group_interface import (
    get_planning_context,
    MoveGroup,
    execute_trajectory
)

def pick_and_place_demo():
    """抓取-放置演示"""
    
    # 1. 使用规划上下文抓取
    ctx = get_planning_context()
    grasp_result = ctx.grasp_object("qingque", strategy="top_grasp")
    
    if not grasp_result["success"]:
        print(f"❌ 抓取失败: {grasp_result['error']}")
        return False
    
    print(f"✅ 抓取成功，耗时: {grasp_result['execution_time']:.2f}s")
    
    # 2. 使用MoveGroup移动到放置位置
    arm = MoveGroup("panda_arm")
    place_pose = [0.6, 0.2, 0.4, 0, 0, 0, 1]
    move_result = arm.move_to_pose(place_pose)
    
    if not move_result["success"]:
        print(f"❌ 移动失败: {move_result['error']}")
        return False
    
    # 3. 释放物体（抓取服务器功能）
    from grasping.pick_action_server import release_object
    release_result = release_object("qingque")
    
    print(f"✅ 放置完成！")
    return True
示例2：批量流水线作业
python
from planning_interface.move_group_interface.src.move_group_interface import get_planning_context

def batch_assembly_line():
    """流水线批量抓取"""
    
    ctx = get_planning_context()
    
    # 待抓取物体列表
    parts = ["part_a_001", "part_b_002", "part_c_003", "part_d_004"]
    
    results = []
    for part_id in parts:
        print(f"\n🔄 处理: {part_id}")
        
        # 抓取
        result = ctx.grasp_object(part_id, strategy="top_grasp")
        
        if result["success"]:
            print(f"   ✅ 成功 | 宽度: {result['grasp_width_mm']:.1f}mm | 缓存: {'命中' if result['cache_hit'] else '未命中'}")
        else:
            print(f"   ❌ 失败 | 错误: {result.get('error', '未知')}")
        
        results.append({
            "part": part_id,
            "success": result["success"],
            "result": result
        })
    
    # 统计
    success_count = sum(1 for r in results if r["success"])
    print(f"\n📊 统计: {success_count}/{len(parts)} 成功")
    
    return results
六、最佳实践
1. 预加载常用物体
python
# 程序启动时预热缓存
def warmup_cache():
    ctx = get_planning_context()
    common_objects = ["qingque", "test_cube", "box", "cylinder"]
    
    for obj in common_objects:
        # 只计算IK，不执行
        from kin_ik.ik_solver import solve_for_object
        solve_for_object(obj)
    
    print("✅ 缓存预热完成")
2. 错误处理
python
def safe_grasp(object_id):
    ctx = get_planning_context()
    result = ctx.grasp_object(object_id)
    
    if result["success"]:
        return result
    
    # 错误分类处理
    error = result.get("error", "")
    if "IK求解失败" in error:
        # 尝试其他策略
        return ctx.grasp_object(object_id, strategy="side_grasp")
    elif "移动失败" in error:
        # 增加超时时间
        arm = MoveGroup("panda_arm")
        return arm.move_to_object(object_id, timeout=10.0)
    elif "抓取失败" in error:
        # 检查夹爪状态
        from grasping.pick_action_server import get_grasp_status
        status = get_grasp_status()
        print(f"夹爪状态: {status}")
        return result
    
    return result
七、选择建议
使用方式	适合场景	复杂度
规划上下文	日常抓取任务	⭐ 简单
MoveGroup类	运动控制+抓取混合	⭐⭐ 中等
轨迹执行	纯移动、快速测试	⭐ 最简单
八、一句话总结
需求	一行代码
抓取场景中的物体	ctx.grasp_object("qingque")
移动到指定位姿	arm.move_to_pose([0.5,0,0.3,0,0,0,1])
纯轨迹执行	execute_trajectory("qingque")
三种方式，各司其职，覆盖所有使用场景！ 🚀