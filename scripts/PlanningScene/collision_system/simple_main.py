#!/usr/bin/env python3
"""
简化主程序 - 带调试信息
"""
import rclpy
import sys
import os

print("=" * 50)
print("碰撞检测系统启动")
print("=" * 50)

# ========== 添加详细的路径调试 ==========
current_file = __file__
current_dir = os.path.dirname(os.path.abspath(current_file))
working_dir = os.getcwd()

print(f"[DEBUG] 脚本文件: {current_file}")
print(f"[DEBUG] 脚本目录: {current_dir}")
print(f"[DEBUG] 工作目录: {working_dir}")
print(f"[DEBUG] 两个目录是否相同: {current_dir == working_dir}")

# 添加路径
print(f"\n[DEBUG] 添加路径前 sys.path:")
for p in sys.path[:3]:
    print(f"  - {p}")

sys.path.insert(0, current_dir)  # 使用 insert 而不是 append

print(f"\n[DEBUG] 添加路径后 sys.path:")
for p in sys.path[:3]:
    print(f"  - {p}")

# ========== 检查文件是否存在 ==========
print("\n[DEBUG] 检查必要的文件:")
utils_dir = os.path.join(current_dir, "utils")
core_dir = os.path.join(current_dir, "core")

print(f"  utils目录: {utils_dir} - 存在: {os.path.exists(utils_dir)}")
print(f"  core目录: {core_dir} - 存在: {os.path.exists(core_dir)}")

config_loader_path = os.path.join(utils_dir, "config_loader.py")
print(f"  config_loader.py: {config_loader_path} - 存在: {os.path.exists(config_loader_path)}")

collision_checker_path = os.path.join(core_dir, "collision_checker.py")
print(f"  collision_checker.py: {collision_checker_path} - 存在: {os.path.exists(collision_checker_path)}")

# ========== 尝试导入 ==========
print("\n[DEBUG] 尝试导入模块...")
try:
    from utils.config_loader import SimpleConfigLoader
    print("✅ utils.config_loader 导入成功!")
except ImportError as e:
    print(f"❌ utils.config_loader 导入失败: {e}")
    print("\n[DEBUG] 尝试直接导入 utils 模块...")
    try:
        import utils
        print(f"  utils模块位置: {utils.__file__}")
        print(f"  utils模块内容: {dir(utils)}")
        
        import utils.config_loader
        print(f"  config_loader模块位置: {utils.config_loader.__file__}")
        print(f"  config_loader模块内容: {dir(utils.config_loader)}")
    except Exception as e2:
        print(f"  详细错误: {e2}")
    sys.exit(1)

try:
    from core.collision_checker import CollisionChecker, demo_all_functions
    print("✅ core.collision_checker 导入成功!")
except ImportError as e:
    print(f"❌ core.collision_checker 导入失败: {e}")
    sys.exit(1)

print("\n[DEBUG] 所有导入成功!")
print("=" * 50)

from typing import Dict, Any


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='碰撞检测系统')
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='配置文件路径'
    )
    parser.add_argument(
        '-d', '--demo',
        action='store_true',
        help='运行演示'
    )
    
    args = parser.parse_args()
    
    print(f"\n[DEBUG] 命令行参数: demo={args.demo}, config={args.config}")
    
    if args.demo:
        print("[DEBUG] 开始运行演示...")
        # 直接运行演示
        demo_all_functions()
    else:
        print("[DEBUG] 启动系统节点...")
        # 运行系统
        config = SimpleConfigLoader.load_config(args.config)
        print(f"[DEBUG] 配置加载成功: {list(config.keys())}")
        
        rclpy.init()
        checker = CollisionChecker(config)
        
        try:
            print("碰撞检测系统运行中...")
            rclpy.spin(checker)
        except KeyboardInterrupt:
            print("\n系统关闭")
        finally:
            checker.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
    print("\n[DEBUG] 程序结束")