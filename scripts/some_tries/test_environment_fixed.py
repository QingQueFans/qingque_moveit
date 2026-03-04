#!/usr/bin/env python3
"""
修正版环境测试 - 解决ros2命令语法问题
"""
import os
import sys
import subprocess

def run_cmd(cmd, timeout=3):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "命令超时", 1
    except Exception as e:
        return None, str(e), 1

def check_ros_activation():
    """检查ROS环境是否激活"""
    print("="*60)
    print("检查ROS 2环境激活状态")
    print("="*60)
    
    # 检查环境变量
    ros_distro = os.environ.get('ROS_DISTRO', '')
    print(f"ROS_DISTRO环境变量: {ros_distro if ros_distro else '❌ 未设置'}")
    
    if not ros_distro:
        print("\n❌ ROS环境未激活")
        print("请运行: source /opt/ros/humble/setup.bash")
        return False
    
    if ros_distro not in ['humble', 'jazzy']:
        print(f"\n⚠️  非标准ROS 2版本: {ros_distro}")
    
    # 检查ros2命令是否存在
    stdout, stderr, code = run_cmd("which ros2")
    if code == 0:
        print(f"✅ ros2命令位置: {stdout.strip()}")
    else:
        print("❌ ros2命令未找到")
        return False
    
    # 检查ros2版本（新语法）
    stdout, stderr, code = run_cmd("ros2 version")
    if code == 0 and "humble" in stdout.lower():
        print("✅ ros2版本检查通过")
        print(f"  输出: {stdout.strip()[:50]}...")
        return True
    else:
        # 尝试其他方法
        stdout, stderr, code = run_cmd("ros2 -h 2>&1 | head -2")
        if code == 0:
            print("✅ ros2命令可用")
            print(f"  帮助信息: {stdout.strip()}")
            return True
        else:
            print("❌ ros2命令有问题")
            return False

def check_moveit():
    """检查MoveIt安装"""
    print("\n" + "="*60)
    print("检查MoveIt安装")
    print("="*60)
    
    # 检查包
    stdout, stderr, code = run_cmd("ros2 pkg list | grep -i moveit | wc -l")
    if code == 0 and stdout.strip().isdigit():
        count = int(stdout.strip())
        print(f"✅ 找到 {count} 个MoveIt相关包")
        
        # 列出前几个
        stdout, stderr, code = run_cmd("ros2 pkg list | grep -i moveit | head -5")
        if code == 0:
            print("示例包:")
            for pkg in stdout.strip().split('\n'):
                if pkg:
                    print(f"  - {pkg}")
    else:
        print("❌ 未找到MoveIt包")
    
    # 检查Panda包
    stdout, stderr, code = run_cmd("ros2 pkg list | grep -i panda")
    if code == 0 and stdout.strip():
        print("✅ 找到Panda相关包")
        for pkg in stdout.strip().split('\n')[:3]:
            if pkg:
                print(f"  - {pkg}")
    else:
        print("⚠️  未找到Panda包")

def check_demo_running():
    """检查演示是否运行"""
    print("\n" + "="*60)
    print("检查演示运行状态")
    print("="*60)
    
    # 简单快速的检查
    stdout, stderr, code = run_cmd("ros2 topic list 2>/dev/null | wc -l", timeout=2)
    
    if code != 0:
        print("❌ 无法获取话题列表")
        print("可能原因:")
        print("  1. ROS环境未激活")
        print("  2. 演示未启动")
        print("  3. ROS核心未运行")
        return False
    
    topic_count = int(stdout.strip()) if stdout.strip().isdigit() else 0
    
    if topic_count == 0:
        print("❌ 没有发现任何ROS话题")
        print("请启动Panda演示:")
        print("  ros2 launch moveit_resources_panda_moveit_config demo.launch.py")
        return False
    
    print(f"✅ 发现 {topic_count} 个ROS话题")
    
    # 检查机械臂相关话题
    stdout, stderr, code = run_cmd("ros2 topic list 2>/dev/null | grep -E '(joint|panda|move)' | head -5")
    if code == 0 and stdout.strip():
        print("✅ 发现机械臂相关话题:")
        for topic in stdout.strip().split('\n'):
            if topic:
                print(f"  - {topic}")
        return True
    else:
        print("⚠️  未发现机械臂特定话题")
        print("Panda演示可能未完全启动")
        return Falsedef provide_instructions():
    """提供操作指导"""
    print("\n" + "="*60)
    print("操作指导")
    print("="*60)
    
    print("📋 推荐工作流程:")
    print("")
    print("终端1 - 激活环境并启动演示:")
    print("  source /opt/ros/humble/setup.bash")
    print("  ros2 launch moveit_resources_panda_moveit_config demo.launch.py")
    print("")
    print("终端2 - 激活环境并运行控制:")
    print("  source /opt/ros/humble/setup.bash")
    print("  cd ~/qingfu_moveit")
    print("  python3 scripts/basic_control.py")
    print("")
    print("💡 提示: 每个新终端都需要先激活ROS环境!")

def main():
    print("🔧 ROS 2环境诊断工具 (修正版)")
    print("="*60)
    
    # 运行检查
    ros_ok = check_ros_activation()
    
    if ros_ok:
        check_moveit()
        demo_ok = check_demo_running()
        
        print("\n" + "="*60)
        if demo_ok:
            print("🎉 所有检查通过！可以开始控制机械臂了。")
            print("\n运行控制脚本:")
            print("  python3 scripts/basic_control.py")
        else:
            print("⚠️  基础环境OK，但演示未运行")
            provide_instructions()
    else:
        print("\n❌ ROS环境有问题")
        provide_instructions()
    
    print("="*60)

if __name__ == "__main__":
    main()
