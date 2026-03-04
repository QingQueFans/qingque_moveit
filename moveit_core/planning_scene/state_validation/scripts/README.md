状态验证模块 - 命令行大全

快速参考

1. 状态验证 (ps-validate-state)

```bash
# 基本验证
ps-validate-state --current
ps-validate-state --state-file state.json
ps-validate-state --joint-state "[0,0,0,0,0,0]"
ps-validate-state --pose "[0.5,0.3,0.2,0,0,0,1]"

# 检查选项
ps-validate-state --current --check-collision
ps-validate-state --current --check-joint-limits
ps-validate-state --current --check-reachability
ps-validate-state --current --check-singularity
ps-validate-state --current --check-constraints
ps-validate-state --current --check-all

# 配置和输出
ps-validate-state --state-file state.json --joint-limits-file limits.json
ps-validate-state --current --json
ps-validate-state --current --verbose
ps-validate-state --current --quiet
```

2. 约束检查 (ps-check-constraints)

```bash
# 从文件检查
ps-check-constraints --constraints constraints.json --current
ps-check-constraints --state-file state.json --constraints constraints.json

# 单个约束
ps-check-constraints --joint-state "[0,0,0,0,0,0]" --joint-constraint "[0.1,0,0,0,0,0]"
ps-check-constraints --position "[0.5,0,0.5]" --position-constraint "[0.5,0,0.5]"
ps-check-constraints --current --distance-constraint "robot" "obstacle1"

# 参数调整
ps-check-constraints --constraints constraints.json --tolerance 0.02
ps-check-constraints --distance-constraint obj1 obj2 --min-distance 0.1 --max-distance 1.0
ps-check-constraints --constraints constraints.json --severity high

# 输出选项
ps-check-constraints --constraints constraints.json --json
ps-check-constraints --constraints constraints.json --verbose
ps-check-constraints --constraints constraints.json --quiet
```

3. 轨迹验证 (ps-validate-trajectory)

```bash
# 轨迹文件
ps-validate-trajectory --trajectory-file trajectory.json
ps-validate-trajectory --waypoints-file waypoints.json
ps-validate-trajectory --joint-trajectory "[[0,0,0,0,0,0],[0.1,0,0,0,0,0]]"

# 检查选项
ps-validate-trajectory --trajectory-file path.json --check-collision
ps-validate-trajectory --trajectory-file path.json --check-joint-limits
ps-validate-trajectory --trajectory-file path.json --check-velocity
ps-validate-trajectory --trajectory-file path.json --check-acceleration
ps-validate-trajectory --trajectory-file path.json --check-continuity
ps-validate-trajectory --trajectory-file path.json --check-smoothness
ps-validate-trajectory --trajectory-file path.json --check-timing
ps-validate-trajectory --trajectory-file path.json --check-all

# 参数调整
ps-validate-trajectory --trajectory-file path.json --max-velocity 0.5
ps-validate-trajectory --trajectory-file path.json --max-acceleration 1.0
ps-validate-trajectory --trajectory-file path.json --max-position-error 0.01
ps-validate-trajectory --trajectory-file path.json --time-resolution 0.01

# 输出选项
ps-validate-trajectory --trajectory-file trajectory.json --json
ps-validate-trajectory --trajectory-file trajectory.json --verbose
ps-validate-trajectory --trajectory-file trajectory.json --quiet
```

4. 违规分析 (ps-get-violations)

```bash
# 单个文件分析
ps-get-violations --results-file validation_results.json
ps-get-violations --results-file results.json --type collision
ps-get-violations --results-file results.json --severity high
ps-get-violations --results-file results.json --check-type joint_limits

# 批量分析
ps-get-violations --results-files result1.json result2.json result3.json
ps-get-violations --results-files *.json

# 标准输入
cat results.json | ps-get-violations --stdin

# 分析模式
ps-get-violations --results-file results.json --stats-only
ps-get-violations --results-file results.json --generate-report
ps-get-violations --results-file results.json --min-violation 0.1

# 输出选项
ps-get-violations --results-file results.json --json
ps-get-violations --results-file results.json --verbose
ps-get-violations --results-file results.json --quiet
```

常用组合命令

状态验证流水线

```bash
# 验证状态并分析违规
ps-validate-state --state-file state.json --check-all --json > state_result.json
ps-get-violations --results-file state_result.json --severity high

# 验证轨迹并生成报告
ps-validate-trajectory --trajectory-file trajectory.json --check-all --json > traj_result.json
ps-get-violations --results-file traj_result.json --generate-report
```

批量处理

```bash
# 批量验证多个状态文件
for file in states/*.json; do
    ps-validate-state --state-file "$file" --quiet && echo "✅ $file" || echo "❌ $file"
done

# 收集所有违规
ps-get-violations --results-files results/*.json --json > all_violations.json
```

集成到脚本中

```bash
# 在脚本中使用退出码
if ps-validate-state --current --check-collision --quiet; then
    echo "状态安全，可以继续"
else
    echo "发现碰撞，停止执行"
    exit 1
fi

# 获取JSON结果并解析
result=$(ps-validate-state --current --json)
valid=$(echo "$result" | jq '.valid')
if [ "$valid" = "true" ]; then
    echo "验证通过"
fi
```

环境变量支持（可选）

```bash
# 设置默认参数
export PS_VALIDATION_TIMEOUT=10  # 超时时间
export PS_JSON_OUTPUT=true       # 默认JSON输出

# 使用环境变量
ps-validate-state --current  # 会自动使用环境变量
```

帮助命令

```bash
# 查看详细帮助
ps-validate-state --help
ps-check-constraints --help
ps-validate-trajectory --help
ps-get-violations --help

# 查看版本信息（如果实现）
ps-validate-state --version
```

快捷别名（建议添加到 ~/.bashrc）

```bash
alias vs='ps-validate-state --current --check-collision'
alias vst='ps-validate-trajectory --check-all'
alias vc='ps-check-constraints --current'
alias gv='ps-get-violations'
```

调试模式

```bash
# 增加调试输出
PS_DEBUG=1 ps-validate-state --current --verbose

# 查看缓存状态
ls -la ~/.planning_scene_cache/
cat ~/.planning_scene_cache/objects.json | jq '. | length'
```
```
记住：所有命令都支持 --help 查看详细用法！
状态验证模块 (state_validation) 指令详解

模块目的

这个模块用于验证机器人状态和轨迹的有效性，确保它们在实际执行前是安全、可行的。

四个核心指令及其用途

1. ps-validate-state - 验证单个状态

作用：检查单个机器人状态是否有效

使用场景：

· 规划前验证目标状态
· 检查当前机器人状态是否安全
· 验证手动输入的状态配置

能检查什么：

```bash
# 检查碰撞（机器人与环境物体）
ps-validate-state --current --check-collision

# 检查关节限位（关节角度是否超限）
ps-validate-state --current --check-joint-limits

# 检查可达性（末端位置是否在工作空间内）
ps-validate-state --current --check-reachability

# 检查奇异点（机器人是否处于奇异构型）
ps-validate-state --current --check-singularity

# 综合检查
ps-validate-state --current --check-all
```

实际例子：

```bash
# 验证关节状态 [0,0,0,0,0,0] 是否有效
ps-validate-state --joint-state "[0,0,0,0,0,0]" --check-all

# 验证机器人位姿 [x,y,z, qx,qy,qz,qw]
ps-validate-state --pose "[0.5,0.3,0.2,0,0,0,1]" --check-collision
```

2. ps-check-constraints - 检查约束条件

作用：验证状态是否满足各种约束条件

约束类型：

· 位置约束：末端必须在特定位置范围内
· 姿态约束：末端姿态必须满足要求
· 距离约束：与特定物体保持安全距离
· 工作空间约束：必须在指定工作区域内

使用场景：

· 装配任务（精确位置要求）
· 避障任务（安全距离要求）
· 协作任务（工作区域限制）

例子：

```bash
# 检查末端是否在 [0.5,0,0.5] ± 0.01m 范围内
ps-check-constraints --position "[0.5,0,0.5]" --position-constraint "[0.5,0,0.5]" --tolerance 0.01

# 检查与障碍物的距离（0.1m - 1.0m）
ps-check-constraints --current --distance-constraint "robot" "obstacle1" --min-distance 0.1 --max-distance 1.0

# 从文件加载复杂约束
ps-check-constraints --state-file state.json --constraints constraints.json
```

3. ps-validate-trajectory - 验证轨迹

作用：检查整个运动轨迹是否可行

能检查什么：

· 连续性：轨迹点之间是否跳跃太大
· 碰撞：整个轨迹是否与物体碰撞
· 速度/加速度：是否超过机器人能力
· 平滑性：轨迹是否足够平滑
· 关节限位：整个轨迹是否都在关节限位内

使用场景：

· 规划完成后验证轨迹
· 优化轨迹前评估质量
· 安全检查（特别是高速运动）

例子：

```bash
# 验证轨迹文件
ps-validate-trajectory --trajectory-file trajectory.json

# 只检查碰撞和速度
ps-validate-trajectory --trajectory-file path.json --check-collision --check-velocity

# 调整验证参数（降低速度限制）
ps-validate-trajectory --trajectory-file path.json --max-velocity 0.5 --max-acceleration 1.0
```

4. ps-get-violations - 分析违规信息

作用：从验证结果中提取和分析问题

能做什么：

· 统计违规类型和数量
· 按严重程度分类
· 生成修复建议
· 批量分析多个验证结果

使用场景：

· 调试规划失败原因
· 生成问题报告
· 优化前的诊断

例子：

```bash
# 分析单个验证结果
ps-validate-state --current --check-all --json > result.json
ps-get-violations --results-file result.json

# 只显示高严重度问题
ps-get-violations --results-file result.json --severity high

# 生成修复报告
ps-get-violations --results-file result.json --generate-report

# 批量分析
ps-get-violations --results-files result1.json result2.json result3.json
```

实际工作流程示例

场景1：规划一个拾取动作

```bash
# 1. 验证目标位置是否可达且安全
ps-validate-state --pose "[0.3,0.2,0.1,0,0,0,1]" --check-reachability --check-collision

# 2. 检查是否满足精确位置约束
ps-check-constraints --position "[0.3,0.2,0.1]" --position-constraint "[0.3,0.2,0.1]" --tolerance 0.005

# 3. 生成轨迹后验证
ps-validate-trajectory --trajectory-file pick_trajectory.json --check-all

# 4. 如果有问题，分析原因
ps-get-violations --results-file validation_result.json --generate-report
```

场景2：安全检查

```bash
# 检查当前状态是否安全
ps-validate-state --current --check-all

# 检查与所有障碍物的距离
ps-check-constraints --current --distance-constraint "robot" "obstacle_1" --min-distance 0.2
ps-check-constraints --current --distance-constraint "robot" "obstacle_2" --min-distance 0.2

# 批量安全检查脚本
for obstacle in obstacle_1 obstacle_2 obstacle_3; do
    ps-check-constraints --current --distance-constraint "robot" "$obstacle" --min-distance 0.2 --quiet && \
    echo "✅ 与 $obstacle 安全" || echo "❌ 与 $obstacle 太近"
done
```

场景3：轨迹优化

```bash
# 验证原始轨迹
ps-validate-trajectory --trajectory-file original.json --json > original_validation.json

# 分析问题
ps-get-violations --results-file original_validation.json --type collision

# 优化后验证
ps-validate-trajectory --trajectory-file optimized.json --json > optimized_validation.json

# 对比结果
ps-get-violations --results-files original_validation.json optimized_validation.json
```

与物体管理模块的关系

```
物体管理模块 (collision_objects)       状态验证模块 (state_validation)
      ↓                                      ↓
创建/管理场景物体                     ↓ 使用这些物体进行验证
      ↓                              检查机器人与物体的关系
      ↓                                      ↓
[物体存在] → → → → → → [状态验证] → → → [轨迹验证]
```

数据流：

1. collision_objects 创建和管理物体
2. 物体信息保存到缓存 ~/.planning_scene_cache/objects.json
3. state_validation 读取缓存，验证状态/轨迹
4. 验证结果可用于调试和优化

总结

什么时候用哪个命令？

问题 使用命令
"这个位置能到达吗？" ps-validate-state --check-reachability
"会撞到东西吗？" ps-validate-state --check-collision
"关节角度超限了吗？" ps-validate-state --check-joint-limits
"精确位置要求满足吗？" ps-check-constraints --position-constraint
"安全距离够吗？" ps-check-constraints --distance-constraint
"整个轨迹安全吗？" ps-validate-trajectory --check-all
"轨迹速度太快吗？" ps-validate-trajectory --check-velocity
"验证结果有什么问题？" ps-get-violations
"怎么修复这些问题？" ps-get-violations --generate-report

核心价值：

1. 安全保障：提前发现问题，避免实际碰撞
2. 质量保证：确保满足任务要求（精度、速度等）
3. 调试帮助：快速定位问题原因
4. 优化指导：提供具体的改进建议

这些工具让你能在仿真中就发现问题，而不是在实际执行中才遇到问题，大大提高了机器人的安全性和可靠性。