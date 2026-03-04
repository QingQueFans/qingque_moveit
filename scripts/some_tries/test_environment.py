#!/usr/bin/env python3
"""
环境测试工具
"""
import subprocess
import sys

def run_command(cmd, capture=True):
    """运行命令并返回结果"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr, result.returncode
        else:
            subprocess.run(cmd, shell=True)
            return None, None, 0
    except Exception as e:
        return None, str(e), 1

def check_ros2():
    """检查ROS 2环境"""
    print("="*60)
    print("检查ROS 2环境")
    print("="*60)
    
    # 检查ROS_DISTRO
    import os
    ros_distro = os.environ.get('ROS_DISTRO', '未设置')
    print(f"ROS_DISTRO: {ros_distro}")
    
    if ros_distro in ['humble', 'jazzy']:
        print("✅ ROS 2 版本正确")
    elif ros_distro == 'noetic':
        print("❌ 这是ROS 1，请切换到ROS 2")
        return False
    else:
        print("⚠️  未识别版本，继续检查...")
    
    # 检查ros2命令
    stdout, stderr, code = run_command("ros2 --version")
    if code == 0:
        print("✅ ros2 命令可用")
        print(f"  版本: {stdout.strip()}")
    else:
        print("❌ ros2 命令不可用")
        return False
    
    return True

def check_moveit():
    """检查MoveIt 2环境"""
    print("\n" + "="*60)
    print("检查MoveIt 2环境")
    print("="*60)
    
    # 检查MoveIt相关包
    stdout, stderr, code = run_command("ros2 pkg list | grep -i moveit | head -10")
    
    if stdout and 'moveit' in stdout:
        print("✅ 找到MoveIt相关包")
        packages = [pkg.strip() for pkg in stdout.split('\n') if pkg.strip()]
        print(f"前{len(packages)}个包:")
        for pkg in packages:
            print(f"  - {pkg}")
    else:
        print("⚠️  未找到MoveIt包")
        print("可能需要安装: sudo apt install ros-${ROS_DISTRO}-moveit")
    
    # 检查Panda包
    stdout, stderr, code = run_command("ros2 pkg list | grep panda")
    if stdout and 'panda' in stdout:
        print("✅ 找到Panda相关包")
    else:
        print("⚠️  未找到Panda包")
    
    return True

def check_running_demo():
    """检查演示是否在运行"""
    print("\n" + "="*60)
    print("检查演示运行状态")
    print("="*60)
    
    # 检查话题
    stdout, stderr, code = run_command("ros2 topic list | head -20")
    
    if stdout:
        topics = stdout.strip().split('\n')
        moveit_topics = [t for t in topics if any(word in t.lower() for word in ['move', 'joint', 'panda'])]
        
        if moveit_topics:
            print("✅ 发现机械臂相关话题")
            print(f"共发现 {len(moveit_topics)} 个相关话题")
            for topic in moveit_topics[:5]:
                print(f"  - {topic}")
            return True
        else:
            print("❌ 未发现机械臂话题，演示可能未运行")
            return False
    else:
        print("❌ 无法获取话题列表")
        return False

def main():
    print("🔧 ROS 2 + MoveIt 2 环境诊断工具")
    print("="*60)
    
    all_checks = []
    
    # 运行检查
    all_checks.append(check_ros2())
    all_checks.append(check_moveit())
    all_checks.append(check_running_demo())
    
    print("\n" + "="*60)
    
    if all(all_checks):
        print("🎉 所有检查通过！环境正常。")
        print("\n下一步:")
        print("1. 运行控制脚本: python3 scripts/basic_control.py")
        print("2. 查看项目文档: docs/ 目录")
    else:
        print("⚠️  部分检查未通过")
        print("\n常见问题解决:")
        print("1. 激活ROS 2环境: source /opt/ros/humble/setup.bash")
        print("2. 启动Panda演示: ros2 launch moveit_resources_panda_moveit_config demo.launch.py")
        print("3. 安装缺失的包: sudo apt install ros-humble-moveit ros-humble-moveit-resources-panda-moveit-config")
    
    print("="*60)

if __name__ == "__main__":
    main()
