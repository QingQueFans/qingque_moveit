#!/usr/bin/env python3
"""
MoveIt环境验证模块
放在项目根目录，所有文件都从这里导入
"""

import sys
import os
import importlib
from typing import List, Dict, Tuple, Optional

# ========== 配置区 ==========
MOVEIT_CORE_ROOT = "/home/diyuanqiongyu/qingfu_moveit/moveit_core"

# 所有可能的模块定义
MODULE_DEFINITIONS = {
    'core': {
        'path': f"{MOVEIT_CORE_ROOT}/planning_scene/core_functions/src",
        'imports': [
            ('ps_core.scene_client', ['PlanningSceneClient']),
            ('ps_core.scene_manager', ['PlanningSceneManager']),
        ],
        'essential': True  # 是否必需
    },
    
    'cache': {
        'path': f"{MOVEIT_CORE_ROOT}/cache_manager/src",
        'imports': [
            ('ps_cache.object_cache', ['ObjectCache']),
            ('ps_cache.cache_manager', ['CachePathTools']),
        ],
        'essential': False
    },
    
    'objects': {
        'path': f"{MOVEIT_CORE_ROOT}/planning_scene/collision_objects/src",
        'imports': [
            ('ps_objects.object_manager', [
                'ObjectManager',
                'create_box',           # 一行调用函数
                'add_object',
                'remove_object',
                'list_objects',
                'clear_all_objects'
            ]),
            ('ps_objects.shape_generator', ['ShapeGenerator']),
        ],
        'essential': True
    },
    
    'ik': {
        'path': f"{MOVEIT_CORE_ROOT}/kinematics/inverse_kinematics/src",
        'imports': [
            ('kin_ik.ik_solver', [
                'IKSolver',
                'solve_ik',             # 一行调用函数
                'solve_for_object',
                'solve_pose'
            ]),
        ],
        'essential': True
    },
    
    'grasping': {
        'path': f"{MOVEIT_CORE_ROOT}/planning_scene/unified_tools/src",
        'imports': [
            ('grasping.gripper_controller', ['calculate_gripper']),
            ('grasping.grasp_planner', ['GraspPlanner']),
        ],
        'essential': False
    }
}

# ========== 核心验证类 ==========

class MoveItEnvValidator:
    """MoveIt环境验证器"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = {}
        self.available_modules = set()
        
    def check_module(self, module_name: str) -> Dict:
        """检查单个模块"""
        if module_name not in MODULE_DEFINITIONS:
            return {"available": False, "error": f"未知模块: {module_name}"}
        
        module_def = MODULE_DEFINITIONS[module_name]
        result = {
            "module": module_name,
            "path": module_def['path'],
            "essential": module_def['essential'],
            "path_exists": False,
            "imports_available": [],
            "imports_failed": [],
            "available": False
        }
        
        # 1. 检查路径
        path_exists = os.path.exists(module_def['path'])
        result["path_exists"] = path_exists
        
        if not path_exists:
            result["error"] = f"路径不存在: {module_def['path']}"
            return result
        
        # 2. 添加到sys.path（如果不在）
        if module_def['path'] not in sys.path:
            sys.path.insert(0, module_def['path'])
        
        # 3. 检查导入
        for import_path, items in module_def['imports']:
            for item in items:
                try:                    # 尝试导入
                    module = importlib.import_module(import_path)
                    if hasattr(module, item):
                        result["imports_available"].append(f"{import_path}.{item}")
                    else:
                        result["imports_failed"].append(f"{import_path}.{item} - 属性不存在")
                except ImportError as e:
                    result["imports_failed"].append(f"{import_path}.{item} - {e}")
        
        # 4. 判断是否可用
        if path_exists and len(result["imports_failed"]) == 0:
            result["available"] = True
            self.available_modules.add(module_name)
        
        return result
    
    def check_all_modules(self) -> Dict:
        """检查所有模块"""
        if self.verbose:
            print("🔍 检查MoveIt环境...")
        
        for module_name in MODULE_DEFINITIONS:
            result = self.check_module(module_name)
            self.results[module_name] = result
            
            if self.verbose:
                status = "✅" if result["available"] else "❌"
                print(f"  {status} {module_name}: {result['path']}")
                if not result["available"] and result.get("error"):
                    print(f"    错误: {result['error']}")
        
        # 总结
        available = [m for m, r in self.results.items() if r["available"]]
        essential_missing = [m for m, r in self.results.items() 
                           if r["essential"] and not r["available"]]
        
        summary = {
            "total_modules": len(MODULE_DEFINITIONS),
            "available_modules": available,
            "available_count": len(available),
            "essential_missing": essential_missing,
            "all_essential_available": len(essential_missing) == 0,
            "results": self.results
        }
        
        if self.verbose:
            print(f"\n📊 总结:")
            print(f"  总模块数: {summary['total_modules']}")
            print(f"  可用模块: {summary['available_count']}")
            print(f"  缺失必需模块: {summary['essential_missing']}")
            print(f"  环境{'✅ 就绪' if summary['all_essential_available'] else '❌ 不完整'}")
        
        return summary
    
    def ensure_module(self, module_name: str, exit_on_fail=True) -> bool:
        """确保模块可用，否则退出"""
        if module_name not in self.results:
            self.check_module(module_name)
        
        result = self.results[module_name]
        
        if not result["available"]:
            print(f"\n❌ 错误: 模块 '{module_name}' 不可用")
            print(f"   路径: {result['path']}")
            print(f"   路径存在: {result['path_exists']}")
            if result.get("error"):
                print(f"   错误: {result['error']}")
            if result["imports_failed"]:
                print(f"   导入失败:")
                for fail in result["imports_failed"]:
                    print(f"     - {fail}")
            
            if exit_on_fail:
                sys.exit(1)
            
            return False
        
        return True
    
    def get_available_function(self, function_name: str):
        """动态获取可用的函数"""        # 在所有模块中查找函数
        for module_name, module_def in MODULE_DEFINITIONS.items():
            if module_name not in self.available_modules:
                continue
            
            for import_path, items in module_def['imports']:
                if function_name in items:
                    try:
                        module = importlib.import_module(import_path)
                        return getattr(module, function_name)
                    except:
                        continue
        
        raise AttributeError(f"函数 '{function_name}' 在所有可用模块中均未找到")

# ========== 便捷函数 ==========

def setup_moveit_env(modules=None, verbose=True) -> MoveItEnvValidator:
    """
    设置MoveIt环境
    
    Args:
        modules: 指定要检查的模块列表，None则检查所有
        verbose: 是否输出详细信息
    
    Returns:
        MoveItEnvValidator 实例
    """
    validator = MoveItEnvValidator(verbose=verbose)
    
    if modules is None:
        validator.check_all_modules()
    else:
        for module in modules:
            validator.check_module(module)
    
    return validator

def quick_import(module_name: str, item_name: str):
    """快速导入并返回"""
    validator = MoveItEnvValidator(verbose=False)
    validator.check_module(module_name.split('.')[0])
    
    try:
        module = importlib.import_module(module_name)
        return getattr(module, item_name)
    except Exception as e:
        raise ImportError(f"无法导入 {module_name}.{item_name}: {e}")

# ========== 全局实例（单例模式） ==========
_env_validator = None

def get_env() -> MoveItEnvValidator:
    """获取全局环境验证器实例"""
    global _env_validator
    if _env_validator is None:
        _env_validator = setup_moveit_env(verbose=True)
    return _env_validator

# ========== 自动初始化 ==========
# 当此模块被导入时，自动检查核心模块
if __name__ != "__main__":
    # 静默初始化，只检查必需模块
    _env_validator = MoveItEnvValidator(verbose=False)
    for module_name, module_def in MODULE_DEFINITIONS.items():
        if module_def['essential']:
            _env_validator.check_module(module_name)