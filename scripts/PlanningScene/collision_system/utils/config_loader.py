#!/usr/bin/env python3
"""
简化配置加载
"""
import yaml
import os


class SimpleConfigLoader:
    """简化配置加载器"""
    
    @staticmethod
    def load_config(config_path: str = None):
        """加载配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                print(f"[CONFIG] 从文件加载配置: {config_path}")
                return config
        else:
            # 返回默认配置 - 修复版
            print("[CONFIG] 使用默认配置")
            return {
                'moveit_services': {
                    'get_planning_scene': '/get_planning_scene',
                    'apply_planning_scene': '/apply_planning_scene',
                    'check_state_validity': '/check_state_validity',
                    # 关键修复：/get_state_validity 不存在，指向同一个服务
                    'get_state_validity': '/check_state_validity'  # ← 改为指向 /check_state_validity
                },
                'default_planning_group': 'panda_arm',
                'service_timeout': 10.0
            }