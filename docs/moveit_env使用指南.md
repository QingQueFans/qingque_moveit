#!/usr/bin/env python3
"""使用环境验证模块的脚本"""

# 1. 导入验证模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moveit_env import get_env, ensure_module

# 2. 获取环境验证器
env = get_env()

# 3. 确保必需模块可用
env.ensure_module('core')      # ps_core
env.ensure_module('objects')   # ps_objects  
env.ensure_module('ik')        # IK求解器

# 4. 现在可以安全导入（有多种方式）

# 方式A：传统导入（现在一定成功）
from ps_objects.object_manager import create_box
from grasping.ik_solver import solve_for_object

# 方式B：使用验证器的动态导入
create_box = env.get_available_function('create_box')
solve_for_object = env.get_available_function('solve_for_object')

# 5. 使用
result = create_box("test", 0.5, 0.3, 0.4)
ik_result = solve_for_object("test")

#!/usr/bin/env python3
"""命令行工具示例"""

from moveit_env import setup_moveit_env

def main():
    # 详细检查环境
    env = setup_moveit_env(verbose=True)
    
    # 检查特定模块
    if not env.ensure_module('objects', exit_on_fail=False):
        print("⚠️  物体模块不可用，使用简化模式")
        # 降级处理...
    else:
        # 正常流程
        create_box = env.get_available_function('create_box')
        create_box("box", 0.5, 0.0, 0.3)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""环境测试脚本"""

from moveit_env import setup_moveit_env

# 详细测试所有模块
env = setup_moveit_env(verbose=True)

# 生成报告
summary = env.check_all_modules()

print("\n📋 详细报告:")
for module, result in summary['results'].items():
    print(f"\n{module}:")
    print(f"  可用: {result['available']}")
    print(f"  路径: {result['path']}")
    if result['imports_available']:
        print(f"  可用导入: {len(result['imports_available'])}个")
    if result['imports_failed']:
        print(f"  失败导入: {len(result['imports_failed'])}个")
        for fail in result['imports_failed'][:3]:  # 只显示前3个
            print(f"    - {fail}")

