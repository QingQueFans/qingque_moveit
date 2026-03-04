planning_scene/
└── unified_tools/                      # 统一工具层
    ├── src/
    │   └── ps_tools/                   # 综合工具包
    │       ├── __init__.py
    │       ├── cli/                    # CLI核心
    │       │   ├── __init__.py
    │       │   ├── main_cli.py         # 主CLI入口
    │       │   ├── interactive.py      # 交互模式
    │       │   ├── command_router.py   # 命令路由
    │       │   └── argument_parser.py  # 智能参数解析
    │       ├── engine/                 # 执行引擎
    │       │   ├── __init__.py
    │       │   ├── script_runner.py    # 脚本运行器
    │       │   ├── module_manager.py   # 模块管理器
    │       │   └── result_handler.py   # 结果处理器
    │       ├── config/                 # 配置系统
    │       │   ├── __init__.py
    │       │   ├── script_registry.py  # 脚本注册表
    │       │   ├── interaction_config.py # 交互配置
    │       │   └── default_configs.py  # 默认配置
    │       ├── interactive/            # 交互界面
    │       │   ├── __init__.py
    │       │   ├── form_builder.py     # 表单构建器
    │       │   ├── menu_system.py      # 菜单系统
    │       │   ├── wizard_engine.py    # 向导引擎
    │       │   └── input_handlers.py   # 输入处理器
    │       ├── utils/                  # 工具函数
    │       │   ├── __init__.py
    │       │   ├── file_utils.py
    │       │   ├── display_utils.py
    │       │   └── validation_utils.py
    │       └── plugins/                # 插件系统
    │           ├── __init__.py
    │           └── base_plugin.py      # 插件基类
    ├── scripts/
    │   ├── pstool                      # 主入口脚本
    │   └── pstool.bat                  # Windows支持
    ├── config/
    │   ├── scripts/                    # 各脚本配置文件
    │   │   ├── ps-add-object.json
    │   │   ├── ps-check-collision.json
    │   │   └── ...
    │   ├── menus/                      # 菜单配置
    │   │   ├── main_menu.json
    │   │   ├── object_menu.json
    │   │   └── ...
    │   └── themes/                     # 主题配置
    │       └── default.json
    ├── templates/                      # 模板文件
    │   ├── scripts/                    # 脚本模板
    │   │   ├── basic_script.py.j2
    │   │   └── form_script.py.j2
    │   └── forms/                      # 表单模板
    │       └── object_form.json.j2
    ├── storage/                        # 数据存储
    │   ├── history/                    # 命令历史
    │   ├── cache/                      # 缓存
    │   └── sessions/                   # 会话数据
    └── examples/
        ├── basic_usage.py
        ├── custom_plugin.py
        └── advanced_config.py