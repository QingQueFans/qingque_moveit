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
    """主CLI类 - 配置文件版本"""
    
    def __init__(self):
        # 确定根目录：总是以 unified_tools 的父目录为基准
        script_path = Path(__file__).resolve()
        
        # 找到包含 unified_tools 的目录（即 planning_scene）
        current = script_path
        while current.name != 'unified_tools' and current.parent != current:
            current = current.parent
        
        if current.name == 'unified_tools':
            self.base_dir = current.parent  # planning_scene 目录
        else:
            # 备用方案：当前目录
            self.base_dir = Path.cwd()
        
        print(f"📁 项目根目录: {self.base_dir}")
        
        # 验证目录结构
        if not self._validate_structure():
            print("❌ 目录结构不正确！")
            print(f"请确保在 planning_scene/ 或 unified_tools/ 目录下运行")
            sys.exit(1)
        
        self.config_dir = self.base_dir / "unified_tools" / "config"
        self.scripts = self._load_scripts()
    
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
    
    def _load_scripts(self) -> Dict[str, Dict]:
        """加载脚本配置"""
        scripts = {}
        
        if not self.config_dir.exists():
            print(f"⚠️  配置目录不存在: {self.config_dir}")
            return scripts
        
        print(f"📂 加载配置目录: {self.config_dir}")
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    script_name = config.get('name')
                    if script_name:
                        scripts[script_name] = config
                        print(f"📄 加载配置: {script_name}")
            except Exception as e:
                print(f"⚠️  加载 {config_file.name} 失败: {e}")
        
        return scripts
    
    def _get_script_path(self, config: Dict) -> Optional[Path]:
        """根据配置获取脚本路径"""
        module = config.get('module')
        script_name = config.get('script_name') or config.get('name')
        
        if not module or not script_name:
            print(f"❌ 配置缺少 module 或 script_name: {config.get('name')}")
            return None
        
        # 构建路径：base_dir / module / scripts / script_name
        script_path = self.base_dir / module / "scripts" / script_name
        
        if script_path.exists():
            print(f"✅ 找到脚本: {script_path}")
            return script_path
        else:
            print(f"❌ 脚本不存在: {script_path}")
            return None
    
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
        script_path = self._get_script_path(config)
        if not script_path:
            return
        
        # 运行向导收集参数
        params = self._run_wizard(config)
        if params is None:  # 用户取消
            return
        # 构建并执行命令
        self._execute_command(script_path, params, config.get('description', '添加物体'))
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
            script_path = self._get_script_path(config)
            if not script_path:
                return
            
            params = self._run_wizard(config)
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
            
            self._execute_command(script_path, params, config.get('description', '移除物体')) 
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
            script_path = self._find_script('ps-list-objects')
            if script_path:
                self._execute_command(script_path, [], "列出物体")
            return
        
        # 获取脚本路径
        script_path = self._get_script_path(config)
        if not script_path:
            print("❌ 未找到 ps-list-objects 脚本")
            return
        
        # 运行向导收集参数
        params = self._run_wizard(config)
        if params is None:  # 用户取消
            return
        
        # 执行命令
        self._execute_command(script_path, params, config.get('description', '列出物体'))    
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
            script_path = self._find_script('ps-modify-object')
            if script_path:
                print("直接运行修改物体命令")
                print("用法: ps-modify-object [物体ID] [操作] [参数]")
            return
        
        # 获取脚本路径
        script_path = self._get_script_path(config)
        if not script_path:
            print("❌ 未找到 ps-modify-object 脚本")
            return
        
        # 运行向导收集参数
        params = self._run_wizard(config)
        if params is None:  # 用户取消
            return
        
        # 执行命令
        self._execute_command(script_path, params, config.get('description', '修改物体'))        
    def _run_modify_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """修改物体的特殊逻辑 - 物体ID是位置参数"""
        params = []
        collected_values = {}
        
        print(f"\n📝 {config.get('description', '配置向导')}")
        print("-" * 40)
        
        # 1. 🎯 关键：物体ID直接作为位置参数，不是--option
        object_step = next((s for s in config.get('steps', []) if s['name'] == 'object_ids'), None)
        if object_step:
            value = self._ask_step(object_step)
            if value is None: return None
            
            # ❌ 不要这样：params.append('--object_ids')
            # ✅ 要这样：直接添加物体ID
            if isinstance(value, list):
                params.extend(value)  # ['fu'] → 直接添加 'fu'
            else:
                params.append(value)
        
        # 2. 修改操作（--move-to 等）
        operation_step = next((s for s in config.get('modification_options', []) 
                            if s['name'] == 'operation'), None)
        if operation_step:
            value = self._ask_step(operation_step)
            if value is None: return None
            
            collected_values['operation'] = value
            params.append(value)  # 添加 --move-to
        
        # 3. 操作参数（坐标、尺寸等）
        operation = collected_values.get('operation')
        if operation in config.get('operation_parameters', {}):
            for step in config['operation_parameters'][operation]:
                value = self._ask_step(step)
                if value is None: return None
                params.append(value)  # 添加坐标值
        
        # 4. 高级选项（-y 等）
        for option in config.get('advanced_options', []):
            value = self._ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params           
    
    def _parse_selection(self, selection: str, options: List[str]) -> List[str]:
        """解析用户的选择输入"""
        selection = selection.strip()
        
        if selection.lower() == 'all':
            return options.copy()
        
        # 尝试解析数字选择（如 "1 3 5" 或 "1-5"）
        selected = []
        
        # 处理范围（如 "1-5"）
        if '-' in selection and selection.count('-') == 1:
            try:
                start_str, end_str = selection.split('-')
                start = int(start_str.strip()) - 1
                end = int(end_str.strip())
                
                if 0 <= start < len(options) and 0 < end <= len(options) and start < end:
                    selected.extend(options[start:end])
                    return selected
            except:
                pass
        
        # 处理多个数字（如 "1 3 5"）
        try:
            indices = [int(idx.strip()) - 1 for idx in selection.split()]
            for idx in indices:
                if 0 <= idx < len(options):
                    selected.append(options[idx])
            return selected
        except:
            pass
        
        # 如果不是数字选择，返回空列表让上层处理
        return []

    

    def _ask_file_input(self, prompt: str, file_types: List[str] = None, default: str = "") -> str:
        """询问文件路径"""
        while True:
            path = input(f"{prompt}: ").strip()
            if not path and default:
                path = default
            
            if not path:
                print("  文件路径不能为空")
                continue
            
            path_obj = Path(path)
            if not path_obj.exists():
                print(f"  ⚠️  文件不存在: {path}")
                if not self._ask_yes_no("  是否继续？", False):
                    continue
            
            if file_types:
                ext = path_obj.suffix.lower()
                if ext not in file_types:
                    print(f"  ⚠️  文件类型应为: {', '.join(file_types)}")
                    if not self._ask_yes_no("  是否继续？", False):
                        continue
            
            return str(path_obj)
    def _run_wizard(self, config: Dict) -> Optional[List[str]]:
        """运行向导收集参数 - 支持不同脚本格式"""
        script_name = config.get('name')
        
        # 🎯 根据不同脚本使用不同逻辑
        if script_name == 'ps-add-object':
            return self._run_add_object_wizard(config)
        elif script_name == 'ps-remove-object':
            return self._run_remove_object_wizard(config)
        elif script_name == 'ps-modify-object':
            return self._run_modify_object_wizard(config)
        elif script_name == 'ps-list-objects':
            return self._run_list_objects_wizard(config)
        else:
            return self._run_generic_wizard(config)

    def _run_add_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """添加物体的特殊逻辑"""
        params = []
        collected_values = {}
        
        # 1. 形状选择（直接添加 --box 等）
        shape_step = next((s for s in config.get('steps', []) if s['name'] == 'shape'), None)
        if shape_step:
            value = self._ask_step(shape_step)
            if value is None: return None
            params.append(value)  # --box
        
        # 2. 名称参数（--name 值）
        name_step = next((s for s in config.get('steps', []) if s['name'] == 'name'), None)
        if name_step:
            value = self._ask_step(name_step)
            if value is None: return None
            params.extend(['--name', value])
        
        # 3. 位置参数（--position 值）
        pos_step = next((s for s in config.get('steps', []) if s['name'] == 'position'), None)
        if pos_step:
            value = self._ask_step(pos_step)
            if value is None: return None
            params.extend(['--position', value])
        
        # 4. 条件参数（尺寸、半径等）
        shape = collected_values.get('shape')
        if shape in config.get('conditional_steps', {}):
            for step in config['conditional_steps'][shape]:
                value = self._ask_step(step)
                if value is None: return None
                param_name = step.get('short', f"--{step['name']}")
                params.extend([param_name, value])
        
        # 5. 高级选项
        for option in config.get('advanced_options', []):
            value = self._ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params

    def _run_remove_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """移除物体的特殊逻辑 - 保持原有格式"""
        params = []
        collected_values = {}
        # 1. 移除模式选择
        mode_step = next((s for s in config.get('steps', []) if s['name'] == 'removal_mode'), None)
        if mode_step:
            value = self._ask_step(mode_step)
            if value is None: return None
            
            if value == 'object_ids':
                # 特殊处理：物体ID直接作为参数
                obj_step = next((s for s in config.get('conditional_steps', {}).get(value, []) 
                            if s['name'] == 'objects'), None)
                if obj_step:
                    obj_value = self._ask_step(obj_step)
                    if obj_value is None: return None
                    
                    if isinstance(obj_value, list):
                        params.extend(obj_value)  # 直接添加物体ID
                    else:
                        params.append(obj_value)
            else:
                # 其他模式：--all、--pattern 等
                params.append(value)
        
        # 2. 模式参数（如 --pattern 的值）
        mode = collected_values.get('removal_mode')
        if mode in config.get('conditional_steps', {}):
            for step in config['conditional_steps'][mode]:
                if step['name'] != 'objects':  # objects已处理
                    value = self._ask_step(step)
                    if value is None: return None
                    params.append(value)
        
        # 3. 高级选项
        for option in config.get('advanced_options', []):
            value = self._ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params        
    
   
    def _process_step(self, params: List[str], step: Dict, collected_values: Dict):
        """处理单个步骤"""
        step_type = step.get('type', 'input')
        
        if step_type == 'multi_input':
            # 特殊处理：显示现有物体
            show_existing = step.get('show_existing', False)
            allow_select = step.get('allow_select', False)
            value = self._ask_multi_input(
                step['prompt'],
                step.get('required', True),
                show_existing,
                allow_select
            )
        else:
            # 其他类型正常询问
            value = self._ask_step(step)
        
        if value is None:
            return
        
        collected_values[step['name']] = value
        
        # 添加到参数列表
        self._add_param_to_list(params, step, value)          
    
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
    def _add_param_to_list(self, params: List[str], step: Dict, value: Any):
        """将参数添加到列表"""
        if step.get('type') == 'choice':
            params.append(value)
        elif step.get('flag'):
            if value:
                params.append(step.get('short', f"--{step['name']}"))
        else:
            if step.get('required', False) or value != '':
                param_name = step.get('short', f"--{step['name']}")
                params.append(param_name)
                if value != '':
                    params.append(str(value))
    
    def _ask_step(self, step: Dict) -> Any:
        """询问单个步骤"""
        step_type = step.get('type', 'input')
        if step_type == 'multi_input':
            show_existing = step.get('show_existing', False)
            allow_select = step.get('allow_select', False)
            return self._ask_multi_input(
                step['prompt'], 
                step.get('required', True),
                show_existing,
                allow_select
            )
        prompt = step['prompt']
        default = step.get('default', '')
        required = step.get('required', False)
        
        if step_type == 'choice':
            return self._ask_choice(step)
        elif step_type == 'confirm':
            return self._ask_yes_no(prompt, bool(default))
        elif step_type == 'coordinates':
            return self._ask_coordinates(prompt, str(default))
        elif step_type == 'number':
            return self._ask_number(prompt, step)
        else:  # input
            return self._ask_input(prompt, str(default), required)
    
    def _ask_choice(self, step: Dict) -> str:
        """询问选择"""
        options = step.get('options', [])
        if not options:
            return ''
        
        print("\n选项:")
        for i, opt in enumerate(options, 1):
            label = opt.get('label', opt.get('value', ''))
            desc = opt.get('description', '')
            print(f"  {i}. {label}")
            if desc:
                print(f"     {desc}")
        
        while True:
            choice = input(f"\n选择 [1-{len(options)}]: ").strip()
            if not choice and 'default' in step:
                return step['default']
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]['value']
            
            print("无效选择，请重试")
    
    def _ask_yes_no(self, prompt: str, default: bool) -> bool:
        """询问是/否"""
        default_str = "Y/n" if default else "y/N"
        while True:
            answer = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not answer:
                return default
            if answer in ['y', 'yes']:
                return True
            if answer in ['n', 'no']:
                return False
            print("请输入 y 或 n")
    
    def _ask_coordinates(self, prompt: str, default: str) -> str:
        """询问坐标"""
        while True:
            value = input(f"{prompt} (默认: {default}): ").strip()
            if not value:
                return default            # 简单验证
            parts = value.split(',')
            if len(parts) != 3:
                print("格式错误，应为 x,y,z")
                continue
            
            try:
                [float(p.strip()) for p in parts]
                return value
            except:
                print("坐标必须是数字")
    
    def _ask_number(self, prompt: str, step: Dict) -> float:
        """询问数字"""
        default = step.get('default', 0)
        min_val = step.get('min')
        max_val = step.get('max')
        
        while True:
            value = input(f"{prompt} (默认: {default}): ").strip()
            if not value:
                return float(default)
            
            try:
                num = float(value)
                if min_val is not None and num < min_val:
                    print(f"最小值是 {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"最大值是 {max_val}")
                    continue
                return num
            except:
                print("请输入数字")
    
    def _ask_input(self, prompt: str, default: str, required: bool) -> str:
        """询问输入"""
        while True:
            value = input(f"{prompt} (默认: {default}): ").strip()
            if not value:
                if default:
                    return default
                if required:
                    print("此字段必填")
                    continue
                return ''
            return value
    
    def _evaluate_condition(self, condition: str, values: Dict) -> bool:
        """评估条件"""
        try:
            # 简单的条件评估
            if ' in ' in condition:
                var, check = condition.split(' in ')
                var = var.strip()
                check = check.strip("'[] ")
                return values.get(var) in check.split(',')
            return True
        except:
            return True
    
    def _execute_command(self, script_path: Path, params: List[str], description: str):
        """执行命令"""
        command = [str(script_path)] + params
        
        print("\n" + "=" * 50)
        print(f"📋 {description}")
        print("=" * 50)
        print("生成的命令:")
        print(f"  {' '.join(command)}")
        print("=" * 50)
        
        confirm = input("\n确认执行？(Y/n): ").strip().lower()
        if confirm in ['n', 'no']:
            print("操作取消")

            return
        
        print("\n🚀 执行中...\n")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print("-" * 50)
            print("执行结果:")
            print("-" * 50)
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("\n错误输出（其实不一定错了，观察退出码，若为0就没错):")
                print(result.stderr)
            
            print(f"\n退出码: {result.returncode}")
            print("-" * 50)
            
        except subprocess.TimeoutExpired:
            print("⏰ 命令执行超时")
        except Exception as e:
            print(f"❌ 执行错误: {e}")
    

    
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
                script_path = self._get_script_path(config)
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
        
        self._execute_command(script_path, args, f"执行 {script_name}")
    
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
    def _find_script(self, script_name: str) -> Optional[Path]:
        """查找脚本文件"""
        # 1. 先在当前模块的scripts目录查找
        modules = [
            "collision_objects",
            "collision_detection", 
            "visualization",
            "acm_management",
            "state_validation",
            "core_functions"
        ]
        
        for module in modules:
            script_path = self.base_dir / module / "scripts" / script_name
            if script_path.exists():
                return script_path
        
        # 2. 尝试直接在当前目录查找
        script_path = self.base_dir / script_name
        if script_path.exists():
            return script_path
        
        return None
    def _get_existing_objects(self) -> List[str]:
        """获取当前场景中的物体ID列表 - 改进版"""
        # 使用安静模式运行 ps-list-objects
        list_script = self._find_script('ps-list-objects')
        if not list_script:
            return []
        
        try:
            # 使用 --quiet 模式获取物体ID列表
            result = subprocess.run(
                [str(list_script), '--quiet'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # 解析输出，每行一个物体ID
                objects = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        objects.append(line.strip())
                return objects
                
        except Exception as e:
            print(f"⚠️  获取物体列表失败: {e}")
        
        return []   
    
    def _get_existing_objects_with_display(self) -> Tuple[List[Tuple[int, str]], Dict[int, str]]:
        """获取物体ID列表和显示映射 - 过滤缓存日志"""
        list_script = self._find_script('ps-list-objects')
        if not list_script:
            return [], {}
        
        try:
            result = subprocess.run(
                [str(list_script)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                objects = []
                display_map = {}
                
                lines = result.stdout.split('\n')
                index = 1
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                # 在第24行左右（for line in lines:循环内）添加：

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 🚨 添加这行过滤错误日志
                    if 'Failed init_port' in line or 'fastrtps_port' in line:
                        continue  # 跳过错误日志行
                        
                    # 🚫 过滤掉缓存日志行
                    if '[缓存]' in line or '缓存文件:' in line or '已加载' in line:
                        continue
                    
                    # 过滤掉统计行
                    if '当前场景中有' in line or '个物体' in line:
                        continue
                    
                    # 提取真实物体ID
                    obj_id = line
                    
                    # 清理格式
                    if '. ' in line:
                        # 处理 "1. [缓存] xxx" 或 "1. qing"
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            obj_id = parts[1]
                    
                    # 移除中括号内容
                    if '[' in obj_id and ']' in obj_id:
                        obj_id = re.sub(r'\[.*?\]\s*', '', obj_id)
                    
                    # 清理空格
                    obj_id = obj_id.strip()
                    
                    if obj_id:  # 确保不是空字符串
                        objects.append((index, obj_id))
                        display_map[index] = obj_id
                        index += 1
                
                return objects, display_map
        
        except Exception as e:
            print(f"⚠️  获取物体列表失败: {e}")
        
        return [], {}   
    def _extract_object_id(self, display_line: str) -> Optional[str]:
        """从显示行中提取真实的物体ID - 增强过滤"""
        line = display_line.strip()
        
        # 🚫 过滤各种错误日志和系统信息
        filter_keywords = [
            '[缓存]', '缓存文件:', '已加载', '个物体的缓存',
            '当前场景中有', '个物体',
            'Failed init_port', 'fastrtps_port', 'open_and_lock_file',
            'Function open_port_internal', 'ERROR', 'Error', 'WARNING'
        ]
        
        if any(keyword in line for keyword in filter_keywords):
            return None
        
        # 移除序号
        if re.match(r'^\d+\.\s+', line):
            line = re.sub(r'^\d+\.\s+', '', line)
        
        # 移除括号内容
        line = re.sub(r'\s*\([^)]*\)', '', line)
        
        # 移除中括号内容
        line = re.sub(r'\[.*?\]\s*', '', line)
        
        # 清理
        line = line.strip('"').strip("'").strip()
        
        return line if line else None    

    def _ask_multi_input(self, prompt: str, required: bool = True, 
                        show_existing: bool = False, allow_select: bool = False) -> List[str]:
        """询问多个输入值 - 修复版"""
        
        if show_existing:
            objects, display_map = self._get_existing_objects_with_display()
            if objects and display_map:
                print(f"\n📋 当前场景中的物体 ({len(objects)} 个):")
                print("-" * 40)
                for i, obj_id in objects:
                    display_line = f"  {i}. {obj_id}"
                    print(display_line)
                print("-" * 40)
                
                if allow_select:
                    print("\n可选操作:")
                    print("  1. 输入数字选择（如: 1 3 5 或 1-5）")
                    print("  2. 直接输入物体ID")
                    print("  3. 输入 'all' 选择所有物体")
                    print("  4. 空行结束输入")
            
            existing_objects = objects  # 真实ID列表
        else:
            existing_objects = []
            display_map = {}
        
        print(f"\n{prompt}")
        
        values = []
        while True:
            if show_existing and allow_select and existing_objects:
                user_input = input(f"选择或输入（当前已选 {len(values)} 个）: ").strip()
            else:
                user_input = input(f"  第{len(values)+1}个（空行结束）: ").strip()
            
            if not user_input:
                if len(values) == 0 and required:
                    print("  至少需要一个值")
                    continue
                break
            
            # 处理选择模式
            if show_existing and allow_select and existing_objects:
                # 使用display_map来映射选择
                selected = self._parse_selection_with_map(user_input, display_map)
                if selected:
                    values.extend(selected)
                    print(f"  已添加: {', '.join(selected)}")
                    continue
            
            values.append(user_input)
        
        return values
    def _parse_selection_with_map(self, selection: str, display_map: Dict[int, str]) -> List[str]:
        """使用显示映射解析用户选择 - 确保ID干净"""
        selection = selection.strip().lower()
        
        if selection == 'all':
            return list(display_map.values())
        
        selected = []
        
        # 处理范围选择
        if '-' in selection and selection.count('-') == 1:
            try:
                start_str, end_str = selection.split('-')
                start = int(start_str.strip())
                end = int(end_str.strip())
                
                for i in range(start, end + 1):
                    if i in display_map:
                        # 🆕 确保提取干净的ID
                        obj_id = display_map[i]
                        if ' (' in obj_id:
                            obj_id = obj_id.split(' (')[0].strip()
                        selected.append(obj_id)
                return selected
            except:
                pass
        
        # 处理多个数字选择
        try:
            indices = [int(idx.strip()) for idx in selection.split()]
            for idx in indices:
                if idx in display_map:
                    obj_id = display_map[idx]
                    if ' (' in obj_id:
                        obj_id = obj_id.split(' (')[0].strip()
                    selected.append(obj_id)
            return selected
        except:
            pass
        
        return []
    
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