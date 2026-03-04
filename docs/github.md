doken密钥：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
整个发送过程（从本地到 GitHub）完整介绍：
1. 准备工作
bash
# 进入你的工作空间
cd ~/qingfu_moveit

# 创建 .gitignore（告诉 Git 哪些文件不用管）
cat > .gitignore << EOF
__pycache__/
*.pyc
ml_env/
qingque_env/
.vscode/
build/
install/
log/
EOF
2. 初始化本地仓库
bash
git init                    # 创建本地仓库（只做一次）
git add .                   # 添加所有文件（除了 .gitignore 里的）
git commit -m "第一次提交"   # 提交到本地仓库
3. 在 GitHub 创建空仓库
打开 https://github.com

点 "+" → New repository

填仓库名 qingque_moveit

不要勾选 "Add README"

点 "Create repository"

4. 连接本地和远程
bash
# 添加远程地址
git remote add origin https://github.com/QingQueFans/qingque_moveit.git
5. 设置身份（第一次用 Git 需要）
bash
git config --global user.email "2222070426@qq.com"
git config --global user.name "QingQueFans"
6. 生成 GitHub Token
打开 https://github.com/settings/tokens

Generate new token

勾选 repo 权限

复制生成的 token

7. 推送代码
bash
git branch -M main          # 确保用 main 分支
git push -u origin main     # 推送到 GitHub
# 用户名: QingQueFans
# 密码: 粘贴刚才的 token
8. 验证成功
text
枚举对象中: 432, 完成.
写入对象中: 100% (432/432), 537.37 KiB, 完成.
To https://github.com/QingQueFans/qingque_moveit.git
 * [new branch]      main -> main
9. 后续更新
bash
# 修改代码后
git add .
git commit -m "修改了xxx"
git push
关键点：
✅ .gitignore 过滤垃圾文件

✅ Token 代替密码

✅ 仓库名要一致

✅ 一次配置，永久使用

现在要再加新文件或修改，按这个流程：
1. 先查看当前状态
bash
git status
# 会看到：
# - M 修改过的文件
# - U 新建的文件
2. 添加修改/新文件
bash
# 添加所有修改和新文件
git add .

# 或者只添加特定的
git add 文件名
3. 提交到本地
bash
git commit -m "描述你改了啥"
# 例如：git commit -m "添加了抓取功能"
4. 推送到 GitHub
bash
git push
# 不需要再输用户名密码，已经记住了
完整示例：
bash
# 假设你修改了 ros2_moveit_client.py，又新建了 test.py

git status
# 看到：
# modified:   src/ompl_planner/ros2_moveit_client.py  (M)
# untracked:  test.py                                  (U)

git add .
git commit -m "优化规划器，添加测试文件"
git push
如果只想提交部分：
bash
git add src/ompl_planner/ros2_moveit_client.py  # 只加这个
git commit -m "只修改了规划器"
git push
就这么简单！