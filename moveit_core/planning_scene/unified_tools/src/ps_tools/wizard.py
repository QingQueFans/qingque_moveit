#!/usr/bin/env python3
"""
wizard.py - 向导引擎
负责交互式参数收集
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class WizardEngine:
    def __init__(self, runner, base_dir: Path):
        self.runner = runner  # 🎯 需要 runner 来获取物体列表
        self.base_dir = base_dir
    
    # 从这里开始复制函数...
    def run_wizard(self, config: Dict) -> Optional[List[str]]:
        """运行向导收集参数 - 支持不同脚本格式"""
        script_name = config.get('name')
        
        # 🎯 根据不同脚本使用不同逻辑
        if script_name == 'ps-add-object':
            return self.run_add_object_wizard(config)
        elif script_name == 'ps-remove-object':
            return self.run_remove_object_wizard(config)
        elif script_name == 'ps-modify-object':
            return self.run_modify_object_wizard(config)
        elif script_name == 'ps-list-objects':
            return self.run_list_objects_wizard(config)
        else:
            return self.run_generic_wizard(config)

    def run_add_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """添加物体的特殊逻辑"""
        params = []
        collected_values = {}
        
        # 1. 形状选择（直接添加 --box 等）
        shape_step = next((s for s in config.get('steps', []) if s['name'] == 'shape'), None)
        if shape_step:
            value = self.ask_step(shape_step)
            if value is None: return None
            params.append(value)  # --box
        
        # 2. 名称参数（--name 值）
        name_step = next((s for s in config.get('steps', []) if s['name'] == 'name'), None)
        if name_step:
            value = self.ask_step(name_step)
            if value is None: return None
            params.extend(['--name', value])
        
        # 3. 位置参数（--position 值）
        pos_step = next((s for s in config.get('steps', []) if s['name'] == 'position'), None)
        if pos_step:
            value = self.ask_step(pos_step)
            if value is None: return None
            params.extend(['--position', value])
        
        # 4. 条件参数（尺寸、半径等）
        shape = collected_values.get('shape')
        if shape in config.get('conditional_steps', {}):
            for step in config['conditional_steps'][shape]:
                value = self.ask_step(step)
                if value is None: return None
                param_name = step.get('short', f"--{step['name']}")
                params.extend([param_name, value])
        
        # 5. 高级选项
        for option in config.get('advanced_options', []):
            value = self.ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params

    def run_remove_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """移除物体的特殊逻辑 - 保持原有格式"""
        params = []
        collected_values = {}
        # 1. 移除模式选择
        mode_step = next((s for s in config.get('steps', []) if s['name'] == 'removal_mode'), None)
        if mode_step:
            value = self.ask_step(mode_step)
            if value is None: return None
            
            if value == 'object_ids':
                # 特殊处理：物体ID直接作为参数
                obj_step = next((s for s in config.get('conditional_steps', {}).get(value, []) 
                            if s['name'] == 'objects'), None)
                if obj_step:
                    obj_value = self.ask_step(obj_step)
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
                    value = self.ask_step(step)
                    if value is None: return None
                    params.append(value)
        
        # 3. 高级选项
        for option in config.get('advanced_options', []):
            value = self.ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params        
    def run_modify_object_wizard(self, config: Dict) -> Optional[List[str]]:
        """修改物体的特殊逻辑 - 物体ID是位置参数"""
        params = []
        collected_values = {}
        
        print(f"\n📝 {config.get('description', '配置向导')}")
        print("-" * 40)
        
        # 1. 🎯 关键：物体ID直接作为位置参数，不是--option
        object_step = next((s for s in config.get('steps', []) if s['name'] == 'object_ids'), None)
        if object_step:
            value = self.ask_step(object_step)
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
            value = self.ask_step(operation_step)
            if value is None: return None
            
            collected_values['operation'] = value
            params.append(value)  # 添加 --move-to
        
        # 3. 操作参数（坐标、尺寸等）
        operation = collected_values.get('operation')
        if operation in config.get('operation_parameters', {}):
            for step in config['operation_parameters'][operation]:
                value = self.ask_step(step)
                if value is None: return None
                params.append(value)  # 添加坐标值
        
        # 4. 高级选项（-y 等）
        for option in config.get('advanced_options', []):
            value = self.ask_step(option)
            if value is None: return None
            if value:
                params.append(option.get('short', f"--{option['name']}"))
        
        return params  
         
    def run_list_objects_wizard(self, config: Dict) -> Optional[List[str]]:
            """列出物体的向导逻辑"""
            print(f"\n📝 {config.get('description', '列出场景中的物体')}")
            print("-" * 40)
            
            # ps-list-objects 可能有可选参数，比如过滤条件
            params = []
            
            # 检查是否有可选参数步骤
            steps = config.get('steps', [])
            if steps:
                print("可选参数（直接按回车跳过）:")
                for step in steps:
                    value = self.ask_step(step)
                    if value is not None and value != '':
                        # 添加到参数列表
                        self.add_param_to_list(params, step, value)
            else:
                print("✅ 列出物体通常不需要额外参数")
            
            return params
    
    def run_generic_wizard(self, config: Dict) -> Optional[List[str]]:
        """通用向导逻辑"""
        print(f"\n📝 {config.get('description', '配置向导')}")
        print("-" * 40)
        
        params = []
        steps = config.get('steps', [])
        
        if not steps:
            print("⚠️  此配置没有定义步骤")
            return []
        
        for step in steps:
            value = self.ask_step(step)
            if value is None:  # 用户取消
                return None
            
            # 添加到参数列表
            self.add_param_to_list(params, step, value)
        
        # 处理条件步骤（如果有）
        conditional_steps = config.get('conditional_steps', {})
        # 这里可以根据 collected_values 处理条件步骤
        # 但需要先收集值，这里简化处理
        
        return params        
    
    def ask_step(self, step: Dict) -> Any:
        """询问单个步骤"""
        step_type = step.get('type', 'input')
        if step_type == 'multi_input':
            show_existing = step.get('show_existing', False)
            allow_select = step.get('allow_select', False)
            return self.ask_multi_input(
                step['prompt'], 
                step.get('required', True),
                show_existing,
                allow_select
            )
        prompt = step['prompt']
        default = step.get('default', '')
        required = step.get('required', False)
        
        if step_type == 'choice':
            return self.ask_choice(step)
        elif step_type == 'confirm':
            return self.ask_yes_no(prompt, bool(default))
        elif step_type == 'coordinates':
            return self.ask_coordinates(prompt, str(default))
        elif step_type == 'number':
            return self.ask_number(prompt, step)
        else:  # input
            return self.ask_input(prompt, str(default), required)
    
    def ask_choice(self, step: Dict) -> str:
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
    
    def ask_yes_no(self, prompt: str, default: bool) -> bool:
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
    
    def ask_coordinates(self, prompt: str, default: str) -> str:
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
    
    def ask_number(self, prompt: str, step: Dict) -> float:
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
    
    def ask_input(self, prompt: str, default: str, required: bool) -> str:
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

    def ask_multi_input(self, prompt: str, required: bool = True, 
                        show_existing: bool = False, allow_select: bool = False) -> List[str]:
        """询问多个输入值 - 修复版"""
        
        if show_existing:
            objects, display_map = self.runner.get_existing_objects_with_display()
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
                selected = self.parse_selection_with_map(user_input, display_map)
                if selected:
                    values.extend(selected)
                    print(f"  已添加: {', '.join(selected)}")
                    continue
            
            values.append(user_input)
        
        return values        

    def ask_file_input(self, prompt: str, file_types: List[str] = None, default: str = "") -> str:
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
                if not self.ask_yes_no("  是否继续？", False):
                    continue
            
            if file_types:
                ext = path_obj.suffix.lower()
                if ext not in file_types:
                    print(f"  ⚠️  文件类型应为: {', '.join(file_types)}")
                    if not self.ask_yes_no("  是否继续？", False):
                        continue
            
            return str(path_obj)        

    def parse_selection(self, selection: str, options: List[str]) -> List[str]:
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
    def parse_selection_with_map(self, selection: str, display_map: Dict[int, str]) -> List[str]:
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

    def evaluate_condition(self, condition: str, values: Dict) -> bool:
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
        
    def extract_object_id(self, display_line: str) -> Optional[str]:
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

    def add_param_to_list(self, params: List[str], step: Dict, value: Any):
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
        
