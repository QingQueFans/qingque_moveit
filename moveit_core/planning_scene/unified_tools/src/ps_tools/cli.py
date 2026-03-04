#!/usr/bin/env python3
"""
统一工具层 - 主CLI
使用配置文件，正确路径处理
"""
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# 导入分离的模块
from .config import ConfigManager
from .runner import ScriptRunner
from .wizard import WizardEngine
class PSToolCLI:
    def __init__(self):
        # 确定基础目录
        self.base_dir = self._determine_base_dir()
        
        # 初始化各模块
        self.config_manager = ConfigManager(self.base_dir)
        self.script_runner = ScriptRunner(self.base_dir)
        self.wizard_engine = WizardEngine(self.script_runner, self.base_dir)
        
        # 加载配置
        self.scripts = self.config_manager.load_all_configs()
    def _determine_base_dir(self) -> Path:
        """确定项目根目录"""
        # 获取当前脚本路径
        script_path = Path(__file__).resolve()
        
        # 如果是通过 pstool 脚本运行
        if 'unified_tools' in str(script_path):
            # 找到包含 unified_tools 的目录（即 planning_scene）
            current = script_path
            while current.name != 'planning_scene' and current.parent != current:
                current = current.parent
            
            if current.name == 'planning_scene':
                return current
        
        # 备用方案：使用当前工作目录
        current_dir = Path.cwd()
        
        # 检查当前目录是否是 planning_scene
        if current_dir.name == 'planning_scene':
            return current_dir
        
        # 检查当前目录下是否有 planning_scene
        if (current_dir / 'planning_scene').exists():
            return current_dir / 'planning_scene'
        
        # 如果都找不到，返回当前目录
        print("⚠️  警告：未找到 planning_scene 目录，使用当前目录")
        return current_dir
    
    def _validate_structure(self) -> bool:
        """验证目录结构"""
        required = [
            self.base_dir / "unified_tools",
            self.base_dir / "collision_objects",
            self.base_dir / "collision_detection"
        ]
        
        for path in required:
            if not path.exists():
                print(f"❌ 缺失: {path}")
                return False
        
        print("✅ 目录结构验证通过")
        return True
    

    def run(self):
        """运行主循环"""
        print("=" * 60)
        print("🤖 机器人规划场景统一工具")
        print("=" * 60)
        
        while True:
            choice = self._show_main_menu()
            
            if choice == '0':
                print("再见！")
                return 0
            elif choice == '1':
                self._run_add_object()
            elif choice == '2':
                self._run_remove_object()
            elif choice == '3':
                self._run_list_objects()
            elif choice == '4':  # 新增：修改物体
                self._run_modify_object()
            elif choice == '5':
                self._run_collision_check()  # 待实现
            elif choice == '6':
                self._run_visualization()    # 待实现
            elif choice == '7':
                self._run_direct_command()
            elif choice == '8':
                self._run_config_wizard()
            else:
                print("无效选择")
    def _show_main_menu(self) -> str:
        """显示主菜单"""
        print("\n" + "=" * 40)
        print("主菜单")
        print("=" * 40)
        print("1. ➕ 添加物体")
        print("2. 🗑️  移除物体")
        print("3. 📋 列出物体")
        print("4. 🔧 修改物体")  # 新增
        print("5. 💥 碰撞检测")   # 预留
        print("6. 👁️  可视化")    # 预留
        print("7. 🖥️  直接命令模式")
        print("8. ⚙️  配置向导")
        print("0. 🚪 退出")
        print("=" * 40)
        return input("\n请选择 [0-8]: ").strip()    
    
    
    def _run_add_object(self):
        """运行添加物体向导（基于配置文件）"""
        print("\n" + "=" * 60)
        print("➕ 添加物体向导")
        print("=" * 60)
        
        config = self.scripts.get('ps-add-object')
        if not config:
            print("❌ 未找到 ps-add-object 的配置")
            print("正在创建默认配置...")
            config = self._create_default_add_object_config()
            self.scripts['ps-add-object'] = config        # 获取脚本路径
        script_path = self.config_manager.get_script_path(config)
        if not script_path:
            return
        
        # 运行向导收集参数
        params = self.wizard_engine.run_wizard(config)
        if params is None:  # 用户取消
            return
        # 构建并执行命令
        self.script_runner.execute_command(script_path, params, config.get('description', '添加物体'))
    def _run_remove_object(self):
            """运行移除物体向导"""
            print("\n" + "=" * 50)
            print("🗑️  移除物体")
            print("=" * 50)
            print("⚠️  警告：移除操作不可恢复！")
            print("-" * 50)
            
            config = self.scripts.get('ps-remove-object')
            if not config:
                print("❌ 未找到移除物体的配置")
                return
            
            # 检查是否是直接命令模式
            if config.get('interaction_type') == 'direct_only':
                print("此命令只能通过直接命令模式使用")
                print("请返回主菜单选择 '4. 🖥️  直接命令模式'")
                input("\n按回车键返回...")
                return
            
            # 运行向导（如果支持）
            script_path = self.config_manager.get_script_path(config)
            if not script_path:
                return
            
            params = self.wizard_engine.run_wizard(config)
            if params is None:
                return
            
            # 对于移除操作，增加额外确认
            print("\n" + "=" * 50)
            print("🚨 最后确认")
            print("=" * 50)
            print("你将要执行移除操作，此操作不可撤销！")
            
            # 特别检查是否是 --all 模式2
            if any(arg in ['--all', '-a'] for arg in params):
                print("⚠️  你选择了移除所有物体！")
                confirm = input("请输入 'CONFIRM-REMOVE-ALL' 以确认: ").strip()
                if confirm != 'CONFIRM-REMOVE-ALL':
                    print("操作取消")
                    return
            
            self.script_runner.execute_command(script_path, params, config.get('description', '移除物体')) 
    def _run_list_objects(self):
        """运行列出物体向导"""
        print("\n" + "=" * 50)
        print("📋 列出物体")
        print("=" * 50)
        
        # 加载配置
        config = self.scripts.get('ps-list-objects')
        if not config:
            print("❌ 未找到 ps-list-objects 的配置")
            # 如果没有配置，使用默认命令
            script_path = self.script_runner.find_script('ps-list-objects')
            if script_path:
                self.script_runner.execute_command(script_path, [], "列出物体")
            return
        
        # 获取脚本路径
        script_path = self.config_manager.get_script_path(config)
        if not script_path:
            print("❌ 未找到 ps-list-objects 脚本")
            return
        
        # 运行向导收集参数
        params = self.wizard_engine.run_wizard(config)
        if params is None:  # 用户取消
            return
        
        # 执行命令
        self.script_runner.execute_command(script_path, params, config.get('description', '列出物体'))    
    def _run_modify_object(self):
        """运行修改物体向导"""
        print("\n" + "=" * 50)
        print("🔧 修改物体")
        print("=" * 50)
        
        # 加载配置
        config = self.scripts.get('ps-modify-object')
        if not config:
            print("❌ 未找到 ps-modify-object 的配置")
            # 如果没有配置，使用默认命令
            script_path = self.script_runner.find_script('ps-modify-object')
            if script_path:
                print("直接运行修改物体命令")
                print("用法: ps-modify-object [物体ID] [操作] [参数]")
            return
        
        # 获取脚本路径
        script_path = self.config_manager.get_script_path(config)
        if not script_path:
            print("❌ 未找到 ps-modify-object 脚本")
            return
        
        # 运行向导收集参数
        params = self.wizard_engine.run_wizard(config)
        if params is None:  # 用户取消
            return
        
        # 执行命令
        self.script_runner.execute_command(script_path, params, config.get('description', '修改物体'))        
    
    



    def _process_step(self, params: List[str], step: Dict, collected_values: Dict):
        """处理单个步骤"""
        step_type = step.get('type', 'input')
        
        if step_type == 'multi_input':
            # 特殊处理：显示现有物体
            show_existing = step.get('show_existing', False)
            allow_select = step.get('allow_select', False)
            value = self.wizard_engine.ask_multi_input(
                step['prompt'],
                step.get('required', True),
                show_existing,
                allow_select
            )
        else:
            # 其他类型正常询问
            value = self.wizard_engine.ask_step(step)
        
        if value is None:
            return
        
        collected_values[step['name']] = value
        
        # 添加到参数列表
        self.wizard_engine.add_param_to_list(params, step, value)          
    
    def _add_step_to_params(self, params: List[str], step: Dict, value: Any):
        """将步骤添加到参数列表 - 统一处理逻辑"""
        # 🎯 处理 param_format
        param_format = step.get('param_format')
        if param_format:
            param_str = param_format.format(value=value)
            params.extend(param_str.split())
            return
        
        # 处理 flag 类型（confirm）
        if step.get('flag', False):
            if value:  # 只有为 True 时才添加
                params.append(step.get('short', f"--{step['name']}"))
            return
        
        # 处理 choice 类型
        if step.get('type') == 'choice':
            # 特殊处理：object_ids 模式不添加参数
            if step.get('name') == 'removal_mode' and value == 'object_ids':
                return
            # 其他 choice 直接添加值
            params.append(value)
            return
        
        # 默认处理：添加参数名和值
        if step.get('required', False) or value != '':
            param_name = step.get('short', f"--{step['name']}")
            params.append(param_name)
            if value != '':
                params.append(str(value))    



    
    
    def _run_direct_command(self):
        """直接命令模式"""
        print("\n" + "=" * 50)
        print("🖥️  直接命令模式")
        print("=" * 50)
        print("输入 'exit' 返回菜单，'list' 查看可用命令")
        print("-" * 50)
        
        while True:
            cmd = input("\n命令> ").strip()
            
            if not cmd:
                continue
            
            if cmd.lower() in ['exit', 'quit']:
                break
            
            if cmd.lower() == 'list':
                self._show_available_commands()
                continue            # 执行命令
            self._execute_direct_command(cmd)
    
    def _show_available_commands(self):
        """显示可用命令"""
        print("\n📚 可用命令:")
        print("-" * 30)
        for name, config in self.scripts.items():
            desc = config.get('description', '')
            print(f"  {name}: {desc}")
    
    def _execute_direct_command(self, cmd: str):
        """执行直接命令"""
        parts = cmd.split()
        if not parts:
            return
        
        script_name = parts[0]
        args = parts[1:]
        
        # 查找脚本
        script_path = None
        for config in self.scripts.values():
            if config.get('name') == script_name or config.get('script_name') == script_name:
                script_path = self.config_manager.get_script_path(config)
                break
        
        if not script_path:
            # 尝试直接查找
            for module in ["collision_objects", "collision_detection", "visualization", 
                         "acm_management", "state_validation", "core_functions"]:
                test_path = self.base_dir / module / "scripts" / script_name
                if test_path.exists():
                    script_path = test_path
                    break
        
        if not script_path:
            print(f"❌ 未找到命令: {script_name}")
            return
        
        self.script_runner.execute_command(script_path, args, f"执行 {script_name}")
    
    def _run_config_wizard(self):
        """配置向导"""
        print("\n" + "=" * 50)
        print("⚙️  配置向导")
        print("=" * 50)
        print("1. 重新加载配置")
        print("2. 查看当前配置")
        print("3. 创建新配置")
        print("0. 返回")
        
        choice = input("\n选择 [0-3]: ").strip()
        
        if choice == '1':
            self.scripts = self._load_scripts()
            print("✅ 配置已重新加载")
        elif choice == '2':
            self._show_current_configs()
        elif choice == '3':
            self._create_new_config()
    
    def _show_current_configs(self):
        """显示当前配置"""
        print("\n📄 当前配置:")
        print("-" * 30)
        for name, config in self.scripts.items():
            module = config.get('module', '未知')
            desc = config.get('description', '')
            print(f"  {name} ({module}): {desc}")
    
    def _create_new_config(self):
        """创建新配置"""
        print("\n创建新配置...")        # 简化的配置创建
        # 可以根据需要扩展
    
    def _create_default_add_object_config(self) -> Dict:
        """创建默认的添加物体配置"""
        return {
            "name": "ps-add-object",
            "description": "添加物体到规划场景",
            "module": "collision_objects",
            "script_name": "ps-add-object",
            "interaction_type": "wizard",
            "steps": [
                {
                    "type": "choice",
                    "name": "shape",
                    "prompt": "选择物体形状",
                    "required": True,
                    "options": [
                        {"value": "--box", "label": "立方体"},
                        {"value": "--sphere", "label": "球体"},
                        {"value": "--cylinder", "label": "圆柱体"},
                        {"value": "--cone", "label": "圆锥体"},
                        {"value": "--table", "label": "桌子"},
                        {"value": "--obstacle", "label": "障碍物"}
                    ],
                    "default": "--box"
                },
                {
                    "type": "input",
                    "name": "name",
                    "prompt": "物体名称",
                    "required": False
                },
                {
                    "type": "coordinates",
                    "name": "position",
                    "prompt": "位置坐标 (x,y,z)",
                    "default": "0,0,0.5",
                    "required": False
                },
                {
                    "type": "confirm",
                    "name": "validate",
                    "prompt": "添加前验证",
                    "default": False,
                    "flag": True,
                    "short": "-v"
                },
                {
                    "type": "confirm", 
                    "name": "yes",
                    "prompt": "跳过确认提示",
                    "default": False,
                    "flag": True,
                    "short": "-y"
                }
            ]
        }




def main():
    """主函数"""
    try:
        cli = PSToolCLI()
        return cli.run()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
        return 0
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())