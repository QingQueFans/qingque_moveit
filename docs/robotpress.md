cd ~/qingfu_moveit/robotpress/frontend
npm run dev
cd ~/qingfu_moveit/robotpress/backend
./run.sh
ros2 launch moveit_resources_panda_moveit_config demo.launch.py

✅ 前端启动方法总结
你现在前端已经开了，用的是：

bash
cd ~/qingfu_moveit/robotpress/frontend
npm run dev

🎯 保持这个开着，不要关！
你会看到：

text
VITE v7.3.1  ready in 449 ms
➜ Local: http://localhost:5173
📊 前端相关的几个命令
命令	作用	什么时候用
npm run dev	开发模式（你现在用的）	写代码时，热重载
npm run build	构建生产版本	要部署时
npm run preview	预览构建后的版本	构建后测试
Ctrl + C	停止	用完关掉

✅ 后端启动方法（WebSocket 服务器）
🎯 在新终端中运行
bash
cd ~/qingfu_moveit/robotpress/backend
./run.sh
你会看到：

text
==================================================
🚀 RobotPress WebSocket 服务器启动
📡 监听地址: ws://0.0.0.0:8765
==================================================
📊 后端相关命令
命令	作用	说明
./run.sh	启动后端	会激活虚拟环境并运行 bridge.py
python3 bridge.py	直接启动（不推荐）	需要自己先 source qingque_env
Ctrl + C	停止后端	优雅关闭服务器
✅ 前后端配合
服务	终端	地址	作用
前端	终端1	http://localhost:5173	显示界面
后端	终端2	ws://localhost:8765	接收指令、控制机器人
🎯 现在你的状态
终端1：前端 (npm run dev) ✅ 已开

终端2：后端 (./run.sh) ❌ 还没开

新开一个终端，把后端跑起来，然后刷新前端页面，就能连上了！

关键问题就一个： watch 的源类型错误！

错误原因：
你用了：

typescript
const { lastPose, lastDimensions } = store
watch(lastPose, ...)  // ❌ lastPose 可能是个 Proxy，不是 ref
但 store.lastPose 是从 Pinia 返回的，它已经是响应式的，但不能直接解构后当 watch 源。

正确做法：
typescript
// ✅ 方法1：用函数返回
watch(() => store.lastPose, ...)

// ✅ 方法2：不解构，直接用
watch(store.lastPose, ...)  // 注意：这里 store.lastPose 是 ref
你最后用的是：

typescript
watch(() => store.lastPose, (newVal) => {
  // ...
}, { immediate: true, deep: true })
这样 watch 就能正确追踪到变化了。

教训：
Pinia store 的结构要小心处理

watch 的源可以是 ref、reactive 或 getter 函数

解构可能会丢失响应性