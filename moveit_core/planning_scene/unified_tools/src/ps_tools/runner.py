#!/usr/bin/env python3
"""
runner.py - 脚本执行器
"""
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

class ScriptRunner:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    # 从这里开始复制函数...
    def execute_command(self, script_path: Path, params: List[str], description: str):
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
    
    def find_script(self, script_name: str) -> Optional[Path]:
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
    def get_existing_objects(self) -> List[str]:
        """获取当前场景中的物体ID列表 - 改进版"""
        # 使用安静模式运行 ps-list-objects
        list_script = self.find_script('ps-list-objects')
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
    
    def get_existing_objects_with_display(self) -> Tuple[List[Tuple[int, str]], Dict[int, str]]:
        """获取物体ID列表和显示映射 - 过滤缓存日志"""
        list_script = self.find_script('ps-list-objects')
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