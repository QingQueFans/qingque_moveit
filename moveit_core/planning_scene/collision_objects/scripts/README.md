# ps-add-object 命令行一览
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1"
python3 ps-add-object --box --name "my_box" --position "0.5,0,0.5" --size "0.1,0.1,0.1"
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --orientation "0,0,0.707,0.707"
python3 ps-add-object --sphere --position "0.3,0.3,0.3" --radius 0.1
python3 ps-add-object --sphere --name "my_sphere" --position "0.3,0.3,0.3" --radius 0.1
python3 ps-add-object --sphere --position "0.3,0.3,0.3" --radius 0.1 --orientation "0,0.707,0,0.707"
python3 ps-add-object --cylinder --position "0.7,0,0.3" --radius 0.05 --height 0.4
python3 ps-add-object --cylinder --name "my_cylinder" --position "0.7,0,0.3" --radius 0.05 --height 0.4
python3 ps-add-object --cylinder --position "0.7,0,0.3" --radius 0.05 --height 0.4 --orientation "0.707,0,0,0.707"
python3 ps-add-object --cone --position "0.4,0.4,0.3" --radius 0.1 --height 0.5
python3 ps-add-object --cone --name "my_cone" --position "0.4,0.4,0.3" --radius 0.1 --height 0.5
python3 ps-add-object --cone --position "0.4,0.4,0.3" --radius 0.1 --height 0.5 --orientation "0,0.707,0.707,0"
python3 ps-add-object --table --position "0.5,0,0.05" --size "1.0,1.0,0.1"
python3 ps-add-object --table --name "worktable" --position "0.5,0,0.05" --size "1.0,1.0,0.1"
python3 ps-add-object --obstacle --position "0.2,0.2,0.2" --size "0.15,0.15,0.4"
python3 ps-add-object --obstacle --name "wall" --position "0.2,0.2,0.2" --size "0.15,0.15,0.4"
python3 ps-add-object --from-file objects.json
python3 ps-add-object --from-file /path/to/object_config.json
python3 ps-add-object --composite --config table_config.json
python3 ps-add-object --composite --config table_config.json --name "dining_table"
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --validate
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --dry-run
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --yes
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --validate --dry-run
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --validate --yes
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --dry-run --yes
python3 ps-add-object --box --position "0.5,0,0.5" --size "0.1,0.1,0.1" --validate --dry-run --yes
好的，我来分析一下之前提供的ps-add-object脚本支持的所有命令行参数：

# ps-add-object 所有命令行参数

基础形状创建（互斥，只能选一个）

```bash
# 创建立方体
python3 ps-add-object --box
python3 ps-add-object --box --name "my_box"

# 创建球体
python3 ps-add-object --sphere
python3 ps-add-object --sphere --name "my_sphere"

# 创建圆柱体
python3 ps-add-object --cylinder
python3 ps-add-object --cylinder --name "my_cylinder"

# 创建圆锥体
python3 ps-add-object --cone
python3 ps-add-object --cone --name "my_cone"

# 创建桌子（立方体）
python3 ps-add-object --table
python3 ps-add-object --table --name "my_table"

# 创建障碍物（立方体）
python3 ps-add-object --obstacle
python3 ps-add-object --obstacle --name "my_obstacle"
```

通用形状参数

```bash
# 指定位置（默认: "0,0,0.5"）
python3 ps-add-object --box --position "0.5,0.3,0.4"
python3 ps-add-object --box -p "0.5,0.3,0.4"

# 指定尺寸（对于立方体，默认: "0.1,0.1,0.1"）
python3 ps-add-object --box --size "0.2,0.3,0.1"
python3 ps-add-object --box -s "0.2,0.3,0.1"

# 指定半径（对于球体/圆柱体/圆锥体，默认: 0.1）
python3 ps-add-object --sphere --radius 0.15
python3 ps-add-object --sphere -r 0.15

# 指定高度（对于圆柱体/圆锥体，默认: 0.2）
python3 ps-add-object --cylinder --height 0.3
python3 ps-add-object --cylinder --radius 0.05 --height 0.3

# 指定姿态四元数
python3 ps-add-object --box --orientation "0,0,0.707,0.707"
python3 ps-add-object --box -o "0,0,0.707,0.707"
```

高级创建方式（互斥）

```bash
# 从JSON文件加载
python3 ps-add-object --from-file objects.json
python3 ps-add-object -f objects.json

# 创建复合物体
python3 ps-add-object --composite --config composite_config.json
python3 ps-add-object -c --config composite_config.json
```

高级选项（可以组合）

```bash
# 添加前验证物体
python3 ps-add-object --box --validate
python3 ps-add-object --box -v

# 干运行模式（只验证不添加）
python3 ps-add-object --box --dry-run
python3 ps-add-object --box -d

# 跳过确认提示
python3 ps-add-object --box --yes
python3 ps-add-object --box -y
```

名称参数（可选）

```bash
# 指定物体名称
python3 ps-add-object --box --name "my_custom_box"
python3 ps-add-object --box -n "my_custom_box"

# 如果不指定名称，会根据形状类型自动生成：
# --box → "box"
# --sphere → "sphere" 
# --cylinder → "cylinder"
# --cone → "cone"
# --table → "table"
# --obstacle → "obstacle"
# --from-file → 使用文件中的name字段或"from_file"
# --composite → "composite"
```

组合使用示例

```bash
# 示例1：创建立方体，指定所有参数，添加前验证
python3 ps-add-object --box --name "custom_box" --position "0.5,0.2,0.4" --size "0.2,0.1,0.15" --orientation "0,0,0.707,0.707" --validate --yes
python3 ps-add-object --box --name "custom_box2" --position "0.4,0.2,0.4" --size "0.1,0.1,0.15" --orientation "0,0,0.707,0.707" --validate --yes

# 示例2：创建球体，干运行查看效果
python3 ps-add-object --sphere --name "big_ball" --position "0.3,0.3,0.3" --radius 0.2 --dry-run

# 示例3：从文件创建，跳过确认
python3 ps-add-object --from-file table_config.json -y

# 示例4：创建复合物体
python3 ps-add-object --composite --config robot_parts.json --name "robot_assembly"


参数缩写总结

· -n = --name
· -p = --position
· -s = --size
· -r = --radius
· -o = --orientation
· -f = --from-file
· -c = --composite
· -v = --validate
· -d = --dry-run
· -y = --yes

```

# ps-remove-object 所有命令行参数

基础用法

```bash
# 移除单个物体
python3 ps-remove-object "my_box"

# 移除多个物体（空格分隔）
python3 ps-remove-object "my_box" "my_sphere" "my_cylinder"
```

移除模式选项（互斥，只能选一个）

```bash
# 移除所有物体
python3 ps-remove-object --all
python3 ps-remove-object -a

# 使用通配符模式匹配
python3 ps-remove-object --pattern "obstacle_*"
python3 ps-remove-object -p "box*"

# 交互式选择要移除的物体
python3 ps-remove-object --interactive
python3 ps-remove-object -i

# 从文件读取物体ID列表（每行一个）
python3 ps-remove-object --from-file objects_to_remove.txt
python3 ps-remove-object -f objects.txt
```

高级选项（可以组合使用）

```bash
# 干运行模式（只显示，不实际移除）
python3 ps-remove-object "my_box" --dry-run
python3 ps-remove-object --all --dry-run -d

# 跳过确认提示
python3 ps-remove-object "my_box" --yes
python3 ps-remove-object --all -y

# 强制模式（即使物体不存在也不报错）
python3 ps-remove-object "not_exist" --force

# 静默模式（不显示详细信息）
python3 ps-remove-object "my_box" --silent
python3 ps-remove-object --all -s

# 组合使用示例
python3 ps-remove-object --pattern "temp_*" --dry-run --yes
python3 ps-remove-object --from-file list.txt --force --silent
```

完整示例

```bash
# 示例1：交互式选择并跳过确认
python3 ps-remove-object --interactive --yes

# 示例2：移除所有匹配前缀的物体，干运行查看效果
python3 ps-remove-object --pattern "test_*" --dry-run

# 示例3：从文件读取要移除的列表，强制模式
python3 ps-remove-object --from-file remove_list.txt --force

# 示例4：移除特定物体，静默模式
python3 ps-remove-object "box1" "box2" "sphere1" --silent --yes


参数缩写总结

· -a = --all
· -p = --pattern
· -i = --interactive
· -f = --from-file
· -d = --dry-run
· -y = --yes
· -s = --silent
```

# 移除单个物体并清除缓存（默认行为）
ps-remove-object "my_box"

# 移除多个物体并清除缓存
ps-remove-object "box1" "sphere1" "cylinder1"

# 移除所有物体并清除整个缓存
ps-remove-object --all --clear-all-cache

# 只移除场景物体，保留缓存
ps-remove-object "my_box" --keep-cache

# 只清除缓存，不移除场景物体
ps-remove-object "my_box" --cache-only

# 清除整个缓存，不移除场景物体
ps-remove-object --cache-only --clear-all-cache

# 从文件读取物体列表并移除
ps-remove-object --from-file objects.txt

# 使用通配符
ps-remove-object --pattern "temp_*"

# 交互式选择
ps-remove-object --interactive
# ps-list-objects 所有命令行参数

```bash
# 简洁模式（默认）
python3 ps-list-objects

# 显示详细信息
python3 ps-list-objects --details
python3 ps-list-objects -d

# 显示数量统计
python3 ps-list-objects --count
python3 ps-list-objects -c

# JSON格式输出
python3 ps-list-objects --json
python3 ps-list-objects -j

# 详细模式（包括空场景信息）
python3 ps-list-objects --verbose
python3 ps-list-objects -v

# 安静模式（只输出物体ID）
python3 ps-list-objects --quiet
python3 ps-list-objects -q
# 按名称排序
python3 ps-list-objects --sort name
python3 ps-list-objects -s name

# 按类型排序
python3 ps-list-objects --sort type
python3 ps-list-objects -s type

# 不排序（默认）
python3 ps-list-objects --sort none
# 导出到JSON文件
python3 ps-list-objects --export objects.json
python3 ps-list-objects -e objects.json

# 指定导出格式
python3 ps-list-objects --export objects.csv --format csv
python3 ps-list-objects --export objects.txt --format txt

# 组合使用
python3 ps-list-objects --details --json --export scene_data.json
# 列出详细信息并按名称排序
python3 ps-list-objects --details --sort name

# 筛选并导出
python3 ps-list-objects --filter "test_*" --json --export test_objects.json

# 获取统计信息
python3 ps-list-objects --count --type composite

# 安静模式导出ID列表
python3 ps-list-objects --quiet --export id_list.txt
```

# ps-modify-object 所有命令行参数
```bash
# 移动物体
python3 ps-modify-object "my_box" --move-to "0.5,0.2,0.3"
python3 ps-modify-object "custom_box" --move-to "0.5,0.2,0.3"
python3 ps-modify-object "my_box" -m "0.5,0.2,0.3"

# 调整尺寸
python3 ps-modify-object "my_box" --resize "0.2,0.3,0.1"
python3 ps-modify-object "my_box" -r "0.2,0.3,0.1"

# 旋转物体
python3 ps-modify-object "my_box" --rotate "0,0,0.707,0.707"
python3 ps-modify-object "my_box" -o "0,0,0.707,0.707"

# 重命名物体
python3 ps-modify-object "old_name" --rename "new_name"
python3 ps-modify-object "old_name" -n "new_name"

# 复制物体
python3 ps-modify-object "source" --copy-to "destination"
python3 ps-modify-object "source" -c "destination"

# 批量移动匹配的物体
python3 ps-modify-object --pattern "obstacle_*" --move-to "0,0,0.5"
python3 ps-modify-object -p "box*" -m "0.5,0,0.5"

# 从配置文件批量修改
python3 ps-modify-object --from-file modify_config.json
python3 ps-modify-object -f config.json

# 修改后验证
python3 ps-modify-object "my_box" --move-to "0.5,0,0.5" --validate
python3 ps-modify-object "my_box" -m "0.5,0,0.5" -v

# 干运行（只显示计划）
python3 ps-modify-object "my_box" --move-to "0.5,0,0.5" --dry-run
python3 ps-modify-object "my_box" -m "0.5,0,0.5" -d

# 跳过确认提示
python3 ps-modify-object "my_box" --rename "new_box" --yes
python3 ps-modify-object "my_box" -n "new_box" -y

# 复制时保留原物体
python3 ps-modify-object "source" --copy-to "copy" --keep-original
python3 ps-modify-object "source" -c "copy" -k
```

## 