#!/usr/bin/env python3
"""
config.py - 配置管理器
负责加载和验证配置文件
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_dir = base_dir / "unified_tools" / "config"  # 🎯 注意路径
        self.cache = {}  # 配置缓存
        
    # 从这里开始复制函数...
    def load_all_configs(self) -> Dict[str, Dict]:
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
    
    def get_script_path(self, config: Dict) -> Optional[Path]:
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
        