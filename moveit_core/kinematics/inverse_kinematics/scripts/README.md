🚀 MoveIt Core IK 工具箱完整使用指南

📋 目录

1. 工具箱概览
2. 快速开始
3. 命令参考手册
4. 典型工作流程
5. 高级使用技巧
6. 故障排除

---

1. 🔍 工具箱概览

架构关系图

```
kin-ik (核心) ──┬── kin-ik-multiple (多解)
                ├── kin-ik-constrained (约束)
                ├── kin-ik-seed (种子管理)
                ├── kin-ik-optimize (优化)
                └── kin-ik-benchmark (性能测试)
```

功能定位表

脚本 核心功能 适用场景
kin-ik 基础逆运动学求解 单点IK计算、快速验证
kin-ik-multiple 获取多个IK解 路径规划、避障选择
kin-ik-constrained 带约束IK求解 特定姿态要求、避障
kin-ik-seed 种子管理求解 连续运动、特定配置
kin-ik-optimize 优化IK解质量 高质量运动、能耗优化
kin-ik-benchmark 性能测试评估 系统验证、参数调优

数据流

```
场景位姿 → kin-ik (基础解) → kin-ik-optimize (优化) → 执行
                     ↓
              kin-ik-constrained (约束) → 避障规划
                     ↓
              kin-ik-multiple (多解) → 路径选择
                     ↓
              kin-ik-seed (连续) → 轨迹生成
```

---

2. 🚀 快速开始

安装与准备

```bash
# 确保在脚本目录
cd /home/diyuanqiongyu/qingfu_moveit/moveit_core/kinematics/inverse_kinematics/scripts

# 测试环境
python3 kin-ik --help
```

最简单的示例

```bash
# 1. 基础IK求解
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1"

# 2. 查看所有脚本
ls kin-ik* | xargs -I {} echo "可用脚本: {}"
```

---

3. 📚 命令参考手册

3.1 通用参数（所有脚本都支持）

参数 说明 格式 默认值
--pose 目标位姿 "x y z qx qy qz qw" 必选
--pose-file 位姿JSON文件 path/to/file.json -
--json JSON格式输出 无参数 关
--verbose, -v 详细输出级别 -v, -vv, -vvv 0

3.2 专用参数速查表

kin-ik (基础求解)

```bash
--seed "j1 j2 j3 j4 j5 j6"        # 初始关节角度
--check-collision                  # 碰撞检查
--robot-model model.json          # 自定义机器人模型
```

kin-ik-multiple (多解)

```bash
--num 8                           # 需要多少个解 (默认: 5)
--check-collision                  # 检查碰撞
```

kin-ik-constrained (约束)

```bash
--horizontal                      # 末端保持水平
--vertical                        # 末端保持垂直
--joint-limit 2 -1.5 1.5         # 关节限制: 关节ID 最小值 最大值
--avoid-obstacle 0.3 0.2 0.1 0.05 # 避障: X Y Z 半径
```

kin-ik-seed (种子管理)

```bash
--seed "0 0 0 0 0 0"             # 直接指定种子
--seed-file seeds.json           # 从文件读取种子
--sample-workspace 10            # 工作空间采样种子数
--sample-near "0.1 0.2 0.3 0.4 0.5 0.6" 0.05  # 在解附近采样
```

kin-ik-optimize (优化)

```bash
--method gradient_descent         # 优化方法: gradient_descent/random_search/simulated_annealing
--iterations 50                   # 最大迭代次数
--weight-movement 0.3             # 关节运动最小化权重
--weight-manipulability 0.3       # 可操作性最大化权重
--weight-singularity 0.2          # 奇异性避免权重
--weight-preference 0.1           # 关节偏好权重
--weight-energy 0.1               # 能量最小化权重
--solution "0.1 0.2 0.3 0.4 0.5 0.6"  # 初始解
--solution-file solution.json     # 初始解文件
```

kin-ik-benchmark (性能测试)

```bash
--basic                           # 基本IK测试
--constrained                     # 带约束IK测试
--optimization                    # 优化IK测试
--all                             # 全部测试
--poses 10                        # 测试位姿数量
--iterations 3                    # 每个位姿重复次数
--pose-file test_poses.json       # 测试位姿文件
--output results.json             # 结果输出文件
```

3.3 参数组合限制

· ❌ 不要同时使用 --pose 和 --pose-file
· ❌ kin-ik-seed 的种子参数是互斥的
· ✅ 可以组合 --json 和 --verbose 获取详细JSON输出

---

4. 🔄 典型工作流程

4.1 场景1：简单抓取规划

```bash
# 1. 基础IK求解
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --json > base_solution.json

# 2. 验证约束可行性（水平抓取）
python3 kin-ik-constrained --pose "0.5 0.0 0.3 0 0 0 1" --horizontal --json > constrained_solution.json

# 3. 获取多个备选方案
python3 kin-ik-multiple --pose "0.5 0.0 0.3 0 0 0 1" --num 5 --json > multiple_solutions.json

# 4. 选择最佳解并优化
python3 kin-ik-optimize --pose "0.5 0.0 0.3 0 0 0 1" \
  --solution-file constrained_solution.json \
  --json > optimized_solution.json
```

4.2 场景2：连续轨迹生成

```bash
#!/bin/bash
# 生成从A到B的轨迹点

start_pose="0.3 0.2 0.4 0 0 0 1"
end_pose="0.6 -0.1 0.3 0 0 0.707 0.707"

# 计算起点解
python3 kin-ik --pose "$start_pose" --json > start.json

# 用起点作为种子计算终点（保证连续性）
start_joints=$(python3 -c "import json; d=json.load(open('start.json')); print(' '.join(str(x) for x in d['solution']))")
python3 kin-ik-seed --pose "$end_pose" --seed "$start_joints" --json > end.json
# 生成中间点
for i in {1..9}; do
  alpha=$(echo "scale=2; $i/10" | bc)
  
  # 插值位姿
  python3 -c "
import numpy as np
import json

with open('start.json') as f:
    start = json.load(f)
with open('end.json') as f:
    end = json.load(f)

pose_start = np.array(start['pose'] if 'pose' in start else start['target_pose'])
pose_end = np.array(end['pose'] if 'pose' in end else end['target_pose'])

pose_interp = pose_start * (1-$alpha) + pose_end * $alpha
print(' '.join(str(x) for x in pose_interp))
" > temp_pose.txt
  
  pose=$(cat temp_pose.txt)
  python3 kin-ik --pose "$pose" --json >> trajectory.json
done
```

4.3 场景3：系统性能评估

```bash
# 全面性能测试
python3 kin-ik-benchmark --all --poses 20 --iterations 5 --json > benchmark_results.json

# 分析结果
python3 -c "
import json
with open('benchmark_results.json') as f:
    data = json.load(f)

print('性能测试报告')
print('='*40)
for mode, result in data['results'].items():
    print(f'{mode}:')
    print(f'  成功率: {result[\"overall_success_rate\"]*100:.1f}%')
    print(f'  平均时间: {result[\"avg_time_ms\"]:.1f}ms')
    if result['avg_error']:
        print(f'  平均误差: {result[\"avg_error\"]:.6f}')
"
```
4.4 场景4：避障约束规划

```bash
# 1. 基础解（可能碰撞）
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --json > free_solution.json

# 2. 添加障碍物约束
python3 kin-ik-constrained --pose "0.5 0.0 0.3 0 0 0 1" \
  --horizontal \
  --avoid-obstacle 0.4 0.0 0.2 0.1 \
  --avoid-obstacle 0.6 0.1 0.3 0.08 \
  --json > constrained_solution.json

# 3. 验证约束满足
python3 -c "
import json
with open('constrained_solution.json') as f:
    data = json.load(f)

if data['success'] and data.get('constraints_satisfied', False):
    print('✓ 约束满足，关节角度:', data['solution'])
else:
    print('✗ 约束不满足，尝试多解搜索...')
"
```

---

5. 🎯 高级使用技巧

5.1 输出处理技巧

提取关键信息

```bash
# 提取关节角度
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(' '.join(str(x) for x in d['solution']))"

# 批量处理JSON结果
for file in *.json; do
  quality=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('quality', 0))")
  echo "$file: $quality"
done | sort -k2 -nr  # 按质量排序
```

可视化输出

```python
#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt

# 加载多个解的结果
solutions = []
for i in range(5):
    with open(f'solution_{i}.json') as f:
        data = json.load(f)
        if data['success']:
            solutions.append({
                'joints': data['solution'],
                'quality': data['quality'],
                'error': data['error']
            })

# 绘制质量对比
qualities = [s['quality'] for s in solutions]
plt.bar(range(len(qualities)), qualities)
plt.title('IK解质量对比')
plt.show()
```

5.2 参数调优指南

基于场景的参数选择

场景 推荐参数 说明
实时控制 --iterations 30 --method gradient_descent 快速响应
精密装配 --iterations 100 --weight-manipulability 0.4 高精度
连续运动 kin-ik-seed + --sample-near 连续性保证
避障规划 kin-ik-constrained + --avoid-obstacle 安全第一

性能优化组合

```bash
# 高性能配置
python3 kin-ik-optimize \
  --pose "0.5 0.0 0.3 0 0 0 1" \
  --method gradient_descent \
  --iterations 40 \
  --weight-manipulability 0.4 \
  --weight-singularity 0.3 \
  --weight-energy 0.3
```
5.3 脚本组合模式

模式A：探索-优化-选择

```bash
# 1. 探索多种可能性
python3 kin-ik-multiple --pose "$target" --num 8 --json > exploration.json

# 2. 对每个解进行优化
python3 -c "
import json
with open('exploration.json') as f:
    data = json.load(f)

for i, sol in enumerate(data['solutions'][:3]):  # 取前3个
    with open(f'temp_solution_{i}.json', 'w') as f:
        json.dump({'solution': sol['solution']}, f)
    
    # 调用优化脚本
    import subprocess
    subprocess.run([
        'python3', 'kin-ik-optimize',
        '--pose', ' '.join(str(x) for x in data['target_pose']),
        '--solution-file', f'temp_solution_{i}.json',
        '--json'
    ])
"
```

模式B：约束递进求解

```bash
# 先松后紧的约束策略
# 1. 无约束求解
python3 kin-ik --pose "$target" --json > stage1.json

# 2. 添加软约束
python3 kin-ik-constrained --pose "$target" --horizontal --json > stage2.json

# 3. 添加硬约束
python3 kin-ik-constrained --pose "$target" \
  --horizontal \
  --joint-limit 2 -1.0 0.5 \
  --json > stage3.json
```

5.4 自动化工作流示例

```python
#!/usr/bin/env python3
"""
自动化IK工作流
"""
import subprocess
import json
import os

class IKWorkflow:
    def __init__(self):
        self.results = {}
    
    def solve_with_fallback(self, target_pose, constraints=None):
        """带回退机制的IK求解"""
        
        # 尝试1: 基础求解
        result = self.run_script('kin-ik', target_pose)
        if result['success']:
            return result
        
        # 尝试2: 多解搜索
        result = self.run_script('kin-ik-multiple', target_pose, num=10)
        if result['success']:
            # 选择质量最高的解
            best = max(result['solutions'], key=lambda x: x['quality'])
            return best
        
        # 尝试3: 放宽约束
        if constraints:
            # 移除一些约束重新尝试
            pass
        
        return None
    
    def run_script(self, script, target_pose, **kwargs):
        """运行IK脚本"""
        cmd = ['python3', script, '--pose', ' '.join(str(x) for x in target_pose)]
        
        for key, value in kwargs.items():
            if isinstance(value, bool) and value:
                cmd.append(f'--{key.replace("_", "-")}')
            elif value is not None:
                cmd.extend([f'--{key.replace("_", "-")}', str(value)])
        
        cmd.append('--json')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {'success': False, 'error': result.stderr}

# 使用示例
workflow = IKWorkflow()
result = workflow.solve_with_fallback(
    [0.5, 0.0, 0.3, 0, 0, 0, 1],
    constraints={'horizontal': True}
)
```

---

6. ⚠️ 故障排除

6.1 常见错误及解决

错误1：导入依赖失败

```
[警告] 导入依赖失败: No module named 'ps_core'
```

解决方案：

```bash
# 确保在正确目录
cd /home/diyuanqiongyu/qingfu_moveit/moveit_core/kinematics/inverse_kinematics/scripts

# 检查路径设置
python3 -c "import sys; print(sys.path)"
```

错误2：参数格式错误

```
错误: 位姿必须是7个数字
```

解决方案：

```bash
# 确保四元数格式正确
# 错误：只有6个数字
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0.1"

# 正确：7个数字（四元数）
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1"
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0.707 0.707"
```

错误3：无解或成功率低

诊断步骤：

```bash
# 1. 检查工作空间
python3 kin-ik-benchmark --basic --poses 5 --iterations 3

# 2. 尝试不同种子
python3 kin-ik-seed --pose "0.5 0.0 0.3 0 0 0 1" --sample-workspace 10

# 3. 放宽约束
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1"  # 先无约束
```

6.2 性能优化建议

问题：求解速度慢

```bash
# 诊断
python3 kin-ik-benchmark --basic --poses 1 --iterations 10

# 优化
python3 kin-ik-optimize --method gradient_descent --iterations 30
```

问题：解质量差

```bash
# 增加探索
python3 kin-ik-multiple --pose "$target" --num 12

# 使用优化
python3 kin-ik-optimize --weight-manipulability 0.4 --weight-singularity 0.3
```

6.3 调试模式

```bash
# 启用详细输出
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" -vvv

# 结合JSON输出
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --json -v 2>&1 | python3 -m json.tool

# 输出到文件并查看
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --json > debug.json
cat debug.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"
```

---

7. 📈 最佳实践总结

7.1 工作流建议

1. 先测试后应用：使用 kin-ik-benchmark 验证系统性能
2. 渐进式约束：从无约束开始，逐步添加约束
3. 种子连续性：连续运动时使用前一个解作为种子
4. 多解选择：重要任务使用 kin-ik-multiple 获取备选方案
5. 质量优化：关键应用使用 kin-ik-optimize 提升解质量

7.2 参数配置黄金法则

· 实时控制：迭代次数 < 50，优先速度
· 精密任务：迭代次数 > 100，优先精度
· 连续运动：必用种子机制保证平滑性
· 复杂环境：必用约束避免碰撞

7.3 输出管理

```bash
# 建立标准输出结构
mkdir -p results/{raw,processed,reports}
python3 kin-ik --pose "$target" --json > results/raw/base_ik.json
python3 kin-ik-multiple --pose "$target" --num 5 --json > results/raw/multiple.json
python3 kin-ik-benchmark --all --poses 10 --output results/reports/benchmark.json
```

---

🎉 开始使用吧！

你的逆运动学工具箱现在已经准备就绪。根据不同的应用场景，选择合适的脚本组合：

· 快速验证：kin-ik
· 路径规划：kin-ik-seed + kin-ik-multiple
· 安全避障：kin-ik-constrained
· 最优控制：kin-ik-optimize
· 系统评估：kin-ik-benchmark

每个脚本都可以独立使用，也可以灵活组合，构建复杂的机器人运动规划系统。祝你使用愉快！🚀

kin-ik-constrained --pose "0.5 0.0 0.3 0 0 0 1" --horizontal --json > grasp.json

# 3. 测试
cd ~/qingfu_moveit/moveit_core/kinematics/inverse_kinematics/scripts
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --save-to-cache
# 基础求解
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1"

# 带物体ID的求解（新功能）
python3 kin-ik --pose "0.6 0.1 0.2 0 0 0 1" --object-id "coke_can_01" --save-to-cache
python3 kin-ik --pose "0.6 0.1 0.2 0 1 1 1" --object-id "qing_fu" --save-to-cache

# 检查碰撞并保存缓存
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --object-id "blue_box" --save-to-cache --check-collision

# 详细输出
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --object-id "tool_001" --save-to-cache --verbose

# JSON格式输出
python3 kin-ik --pose "0.5 0.0 0.3 0 0 0 1" --object-id "red_sphere" --save-to-cache --json


# 单个物体
python3 kin-ik-object --object-id "box"

# 多个物体
python3 kin-ik-object --objects "box,coke_can_01,test_cube"

# 指定抓取策略
python3 kin-ik-object --object-id "coke_can_01" --grasp-strategy "side" --offset 0.03