# diagnostic_controller.py
#!/usr/bin/env python3
"""
诊断脚本 - 测试插件导入
"""
import os
import sys
import importlib.util

def diagnose_plugin_import():
    print("=" * 60)
    print("插件导入诊断")
    print("=" * 60)
    
    # 基础路径
    base_path = "/home/diyuanqiongyu/qingfu_moveit"
    plugin_base = os.path.join(base_path, "moveit_plugins")
    
    # ========== 查找插件文件 ==========
    print("\n🔍 搜索插件文件...")
    
    # 可能的插件文件位置
    possible_files = [
        os.path.join(plugin_base, "moveit_controller_manager", "src", "moveit_controller_manager", "controller_manager.py"),
        os.path.join(plugin_base, "moveit_controller_manager", "src", "moveit_controller_manager.py"),
        os.path.join(plugin_base, "moveit_controller_manager", "src", "controller_manager.py"),
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            print(f"✅ 找到文件: {file_path}")
            print(f"   文件大小: {os.path.getsize(file_path)} 字节")
            
            # 查看文件前几行
            try:
                with open(file_path, 'r') as f:
                    first_lines = [next(f) for _ in range(5)]
                print(f"   文件开头: {''.join(first_lines).strip()}")
            except:
                print("   无法读取文件内容")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    # ========== 检查目录结构 ==========
    print("\n📁 检查目录结构...")
    plugin_dir = os.path.join(plugin_base, "moveit_controller_manager", "src")
    if os.path.exists(plugin_dir):
        print(f"插件src目录: {plugin_dir}")
        print("目录内容:")
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            if os.path.isdir(item_path):
                print(f"  📂 {item}/")
                # 列出子目录内容
                try:
                    sub_items = os.listdir(item_path)
                    for sub in sub_items[:5]:  # 只显示前5个
                        print(f"    - {sub}")
                    if len(sub_items) > 5:
                        print(f"    ... 还有 {len(sub_items)-5} 个文件")
                except:
                    print("    (无法访问)")
            else:
                print(f"  📄 {item}")
    else:
        print(f"❌ 目录不存在: {plugin_dir}")
    
    # ========== 尝试导入 ==========
    print("\n🔄 尝试导入...")
    
    # 添加插件路径到sys.path
    sys.path.insert(0, plugin_dir)
    print(f"已添加路径到sys.path: {plugin_dir}")
    
    # 尝试import moveit_controller_manager
    try:
        import moveit_controller_manager
        print(f"✅ import moveit_controller_manager 成功")
        print(f"   模块位置: {moveit_controller_manager.__file__}")
        print(f"   模块内容: {dir(moveit_controller_manager)}")
    except ImportError as e:
        print(f"❌ import moveit_controller_manager 失败: {e}")
    
    # 尝试从子目录导入
    try:
        from moveit_controller_manager import controller_manager
        print(f"✅ from moveit_controller_manager import controller_manager 成功")
    except ImportError as e:
        print(f"❌ 子模块导入失败: {e}")
    
    # ========== 尝试动态导入 ==========
    print("\n🔧 尝试动态导入...")
    
    # 查找实际的controller_manager.py
    actual_path = None
    for root, dirs, files in os.walk(os.path.join(plugin_base, "moveit_controller_manager")):
        if "controller_manager.py" in files:
            actual_path = os.path.join(root, "controller_manager.py")
            break
    
    if actual_path:
        print(f"找到controller_manager.py: {actual_path}")
        
        # 动态导入
        try:
            spec = importlib.util.spec_from_file_location("plugin_controller_manager", actual_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            print("✅ 动态导入成功")
            print(f"模块内容: {dir(module)}")
            
            # 检查是否有MoveItControllerManager类
            if hasattr(module, 'MoveItControllerManager'):
                print("🎉 找到 MoveItControllerManager 类!")
                print(f"类属性: {dir(module.MoveItControllerManager)}")
            else:
                print("⚠️ 模块中没有 MoveItControllerManager 类")
                
        except Exception as e:
            print(f"❌ 动态导入失败: {e}")
    else:
        print("❌ 未找到controller_manager.py文件")

if __name__ == "__main__":
    diagnose_plugin_import()