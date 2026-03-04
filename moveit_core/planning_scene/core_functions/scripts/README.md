## 脚本说明

### 1. ps-get-scene - 获取场景信息
```bash
# 显示场景摘要
ps-get-scene

# 只显示物体
ps-get-scene --objects

# 只显示机器人状态
ps-get-scene --state

# 显示完整信息
ps-get-scene --full

# 设置所有关节为零
ps-set-state --zero

# 设置关节值
ps-set-state --joints "0,0.5,0,1.2,0,0,0"


# 设置单个关节
ps-set-state --joint panda_joint1=1.0 --joint panda_joint2=0.5

# 干运行（只显示不执行）
ps-set-state --joints "0,0,0,0,0,0,0" --dry-run

# 交互式清空
ps-clear-scene

# 直接清空（跳过确认）
ps-clear-scene --yes

# 只清空物体
ps-clear-scene --objects-only

# 干运行
ps-clear-scene --dry-run
# JSON格式输出
ps-get-scene --json
chmod +x "$SCRIPTS_DIR/ps-get-scene"
chmod +x "$SCRIPTS_DIR/ps-set-state"
chmod +x "$SCRIPTS_DIR/ps-clear-scene"