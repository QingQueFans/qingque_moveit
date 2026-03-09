<!-- frontend/src/views/Dashboard.vue -->
<template>
  <div class="dashboard qingque-theme">
    <!-- 顶端栏 - 太卜司卷轴风格 -->
    <header class="qingque-header p-4 text-white">
      <div class="container mx-auto flex justify-between items-center">
        <div class="flex items-center gap-3">
          <h1 class="qingque-title text-2xl font-bold">🎐 青雀·摸鱼控制台</h1>
          <span class="text-sm bg-white/20 px-3 py-1 rounded-full">v2.0 雀神版</span>
        </div>
        <div class="flex items-center gap-6">
          <!-- 连接状态 - 占卜风格 -->
          <div class="flex items-center gap-2">
            <div class="qingque-status" 
                 :class="connected ? 'status-running' : 'status-idle'">
              {{ connected ? '⚡' : '○' }}
            </div>
            <span>{{ connected ? '在线' : '离线' }}</span>
          </div>
          
          <!-- 任务状态 - 青雀表情 -->
          <div class="flex items-center gap-2">
            <div class="qingque-status" :class="'status-' + taskStatus">
              {{ statusEmoji }}
            </div>
            <span>{{ statusText }}</span>
          </div>
          
          <button @click="connect" 
                  class="qingque-btn px-4 py-2">
            {{ connected ? '已连接' : '连接' }}
            <span class="btn-face">🀫</span>
          </button>
        </div>
      </div>
      
      <!-- 摸鱼语录 - 随机显示 -->
      <div class="container mx-auto mt-2 text-sm text-white/70 italic">
        "{{ currentQuote }}"
      </div>
    </header>

    <!-- 主内容区域 - 四列牌桌 -->
    <div class="container mx-auto p-6 grid grid-cols-4 gap-6">
      
      <!-- 列1：物体列表 + 快捷抓取 + 快捷任务 -->
      <div class="col-span-1 space-y-6">
        <!-- 物体列表卡 - 麻将牌 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🀄</span> 桌上牌面
            <span class="text-xs text-gray-400 ml-auto">共 {{ store.objects.length }} 张</span>
          </h2>
          
          <div v-if="store.objects.length === 0" class="text-gray-400 text-center py-8 text-sm">
            牌桌空空，去添加几张吧
          </div>
          
          <div v-else class="space-y-2 max-h-60 overflow-auto mahjong-scroll">
            <div v-for="obj in store.objects" :key="obj"   
                class="p-2 border rounded-lg transition tile-item relative group"
                :class="{ 'selected-tile': selectedObject === obj }"
                @click="selectedObject = obj">
              
              <!-- 物体ID - 点击查看详情 -->
              <div class="flex items-center gap-2 cursor-pointer" @click="showObjectDetails(obj)">
                <span class="text-[#1f8a7c]">🀫</span>
                <span class="hover:text-[#1f8a7c] transition">{{ obj }}</span>
              </div>
              
              <!-- 移除按钮 -->
              <button @click.stop="store.removeObject(obj)" 
                      class="absolute right-2 top-1/2 -translate-y-1/2 text-red-400 hover:text-red-600 px-2 text-lg opacity-0 group-hover:opacity-100 transition"
                      title="移除物体">
                ✕
              </button>
            </div>
          </div>
        </div>

        <!-- 物体详情弹窗 - 青雀风格 -->
        <div v-if="showDetailsModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click="showDetailsModal = false">
          <div class="qingque-card p-6 max-w-md w-full mx-4 transform transition-all" @click.stop>
            <!-- 标题 -->
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-xl font-bold flex items-center gap-2">
                <span class="text-[#1f8a7c]">🀫</span>
                物体详情 · {{ currentObject?.id }}
              </h3>
              <button @click="showDetailsModal = false" class="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            
            <!-- 加载状态 -->
            <div v-if="loadingDetails" class="text-center py-8">
              <div class="text-[#1f8a7c] animate-spin text-4xl mb-2">⚡</div>
              <p class="text-gray-500">占卜中...</p>
            </div>
            
            <!-- 信息展示 -->
            <div v-else class="space-y-4">
              <!-- 位姿信息 -->
              <div class="bg-[#e8f0f5] p-4 rounded-lg">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-[#1f8a7c] font-bold">📍 位姿</span>
                  <span class="text-xs text-gray-400">7维 [x y z qx qy qz qw]</span>
                </div>
                <div class="grid grid-cols-7 gap-1 text-center">
                  <div v-for="(val, idx) in currentPose" :key="idx" 
                      class="bg-white p-2 rounded text-sm font-mono">
                    {{ val.toFixed(3) }}
                  </div>
                </div>
              </div>
              
              <!-- 尺寸信息 -->
              <div class="bg-[#e8f0f5] p-4 rounded-lg">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-[#1f8a7c] font-bold">📏 尺寸</span>
                  <span class="text-xs text-gray-400">{{ currentDimensions?.type || '未知' }}</span>
                </div>
                
                <!-- 根据类型显示不同格式 -->
                <div v-if="currentDimensions?.type === 'box'" class="grid grid-cols-3 gap-2">
                  <div v-for="(dim, idx) in currentDimensions.size" :key="idx" 
                      class="bg-white p-2 rounded text-center">
                    <div class="text-xs text-gray-400">{{ ['长', '宽', '高'][idx] }}</div>
                    <div class="font-mono">{{ dim.toFixed(3) }}</div>
                  </div>
                </div>
                
                <div v-else-if="currentDimensions?.type === 'sphere'" class="bg-white p-2 rounded text-center">
                  <div class="text-xs text-gray-400">半径</div>
                  <div class="font-mono">{{ currentDimensions.radius.toFixed(3) }}</div>
                </div>
                
                <div v-else-if="currentDimensions?.type === 'cylinder'" class="grid grid-cols-2 gap-2">
                  <div class="bg-white p-2 rounded text-center">
                    <div class="text-xs text-gray-400">半径</div>
                    <div class="font-mono">{{ currentDimensions.radius.toFixed(3) }}</div>
                  </div>
                  <div class="bg-white p-2 rounded text-center">
                    <div class="text-xs text-gray-400">高度</div>
                    <div class="font-mono">{{ currentDimensions.height.toFixed(3) }}</div>
                  </div>
                </div>
              </div>
              
              <!-- 关闭按钮 -->
              <button @click="showDetailsModal = false" 
                      class="w-full qingque-btn py-3 mt-2">
                收到！
                <span class="btn-face">🀫</span>
              </button>
            </div>
          </div>
        </div>
        <!-- 快捷抓取卡片 - 青雀手气 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🎲</span> 今日手气
          </h2>
          <div class="grid grid-cols-2 gap-2">
            <button v-for="(preset, id) in presets" :key="id"
                    @click="quickGrasp(id)"
                    class="qingque-btn-small p-2 rounded-lg text-center">
              <div class="text-2xl mb-1">{{ preset.emoji }}</div>
              <div class="text-xs">{{ preset.name }}</div>
              <span class="btn-face-mini">{{ preset.width }}mm</span>
            </button>
          </div>
          <!-- 摸鱼提示 -->
          <div class="mt-2 text-xs text-gray-400 text-center">
            ⏳ 今日摸鱼指数 {{ Math.floor(Math.random() * 30 + 70) }}%
          </div>
        </div>

        <!-- 快捷任务卡片 - 四象牌 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🎯</span> 四象牌
          </h2>
          <div class="grid grid-cols-2 gap-2">
            <div @click="runTask('pick')" 
                 class="qingque-btn-small p-3 rounded-lg text-center cursor-pointer tile-action">
              <span class="text-2xl block mb-1">🤏</span>
              <span class="text-xs">抓取</span>
              <span class="tile-mark">發</span>
            </div>
            <div @click="runTask('place')" 
                 class="qingque-btn-small p-3 rounded-lg text-center cursor-pointer tile-action">
              <span class="text-2xl block mb-1">📦</span>
              <span class="text-xs">放置</span>
              <span class="tile-mark">中</span>
            </div>
            <div @click="runTask('home')" 
                 class="qingque-btn-small p-3 rounded-lg text-center cursor-pointer tile-action">
              <span class="text-2xl block mb-1">🏠</span>
              <span class="text-xs">归位</span>
              <span class="tile-mark">白</span>
            </div>
            <div @click="runTask('scan')" 
                 class="qingque-btn-small p-3 rounded-lg text-center cursor-pointer tile-action">
              <span class="text-2xl block mb-1">🔄</span>
              <span class="text-xs">巡视</span>
              <span class="tile-mark">板</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 列2：3D模型 + 坐标控制 - 青雀的占卜盘 -->
      <div class="col-span-1 space-y-6">
        <!-- 3D 数字孪生卡片 - 卜卦盘 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">☯</span> 卜卦·机械臂
          </h2>
          <div class="aspect-square bg-gradient-to-br from-[#2c3e4e] to-[#1a2a35] rounded-lg relative overflow-hidden">
            <!-- 模拟机械臂的简易图形 -->
            <div class="absolute inset-0 flex items-end justify-center pb-4">
              <div class="relative w-32">
                <!-- 基座 - 牌桌 -->
                <div class="w-32 h-4 bg-[#d4af37] rounded-full mx-auto opacity-30"></div>
                <!-- 关节1 -->
                <div class="w-2 h-20 bg-gradient-to-t from-[#1f8a7c] to-[#64b5a6] mx-auto origin-bottom" 
                     :style="{ transform: `rotate(${jointAngles[0]}deg)` }">
                  <div class="w-4 h-4 bg-[#d4af37] rounded-full absolute -top-2 -left-1 animate-pulse"></div>
                </div>
                <!-- 关节2 -->
                <div class="w-2 h-16 bg-gradient-to-t from-[#64b5a6] to-[#1f8a7c] mx-auto origin-bottom" 
                     :style="{ transform: `rotate(${jointAngles[1]}deg)` }">
                  <div class="w-4 h-4 bg-[#f5e6b3] rounded-full absolute -top-2 -left-1"></div>
                </div>
                <!-- 末端 - 青雀的小麻雀 -->
                <div class="w-6 h-6 bg-[#d4af37] rounded-full mx-auto mt-2 flex items-center justify-center text-xs">
                  🐦
                </div>
              </div>
            </div>
            <!-- 占卜网格 -->
            <svg class="absolute inset-0 w-full h-full opacity-10">
              <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#d4af37" stroke-width="1" stroke-dasharray="5,5"/>
              <line x1="50%" y1="0" x2="50%" y2="100%" stroke="#d4af37" stroke-width="1" stroke-dasharray="5,5"/>
              <circle cx="50%" cy="50%" r="30" fill="none" stroke="#1f8a7c" stroke-width="1" stroke-dasharray="3,3"/>
            </svg>
          </div>
        </div>

        <!-- 移动控制卡片 - 罗盘（带高级宽度） -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🧭</span> 摸鱼罗盘
            <span class="text-xs text-gray-400 ml-auto">可控制位置/宽度</span>
          </h2>
          
          <!-- XYZ 位置控制（一直显示） -->
          <div class="space-y-3">
            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="text-xs text-gray-500">坎·X</label>
                <input v-model.number="movePose.x" type="number" step="0.1" 
                      class="w-full p-2 border rounded-lg focus:border-[#1f8a7c] bg-white/50">
              </div>
              <div>
                <label class="text-xs text-gray-500">离·Y</label>
                <input v-model.number="movePose.y" type="number" step="0.1" 
                      class="w-full p-2 border rounded-lg focus:border-[#1f8a7c] bg-white/50">
              </div>
              <div>
                <label class="text-xs text-gray-500">坤·Z</label>
                <input v-model.number="movePose.z" type="number" step="0.1" 
                      class="w-full p-2 border rounded-lg focus:border-[#1f8a7c] bg-white/50">
              </div>
            </div>
            
            <!-- 移形按钮 + 高级开关 -->
            <div class="flex gap-2">
              <button @click="handleMove" 
                      class="flex-1 qingque-btn py-3">
                🚀 占卜·移形
                <span class="btn-face">坎离坤</span>
              </button>
              <button @click="showWidth = !showWidth" 
                      class="w-10 h-10 rounded-lg border border-[#1f8a7c] text-[#1f8a7c] hover:bg-[#1f8a7c] hover:text-white transition flex items-center justify-center"
                      :title="showWidth ? '隐藏宽度设置' : '设置抓取宽度'">
                <span class="text-xl">{{ showWidth ? '⚡' : '⚙️' }}</span>
              </button>
            </div>

            <!-- 宽度设置（默认隐藏，点击齿轮展开） -->
            <div v-if="showWidth" class="mt-3 pt-3 border-t border-[#1f8a7c]/20">
              <div class="flex items-center gap-3">
                <label class="text-sm text-gray-600 w-16">抓取宽度</label>
                <input v-model.number="graspWidth" type="number" 
                      placeholder="自动" 
                      class="flex-1 p-2 border rounded-lg focus:border-[#1f8a7c]">
                <span class="text-xs text-gray-400">mm</span>
                <button @click="graspWidth = 0" 
                        class="text-sm text-gray-400 hover:text-[#1f8a7c]">
                  重置
                </button>
              </div>
              <p class="text-xs text-gray-400 mt-1 ml-16">
                ⚡ 留空则使用智能计算宽度
              </p>
            </div>

            <!-- 直接抓取输入（放这里也顺） -->
            <div class="mt-2 flex gap-2">
              <input v-model="directObjectId" 
                    placeholder="输入物体ID" 
                    class="flex-1 p-2 border rounded-lg focus:border-[#1f8a7c]">
              <button @click="graspDirect" 
                      class="bg-[#1f8a7c] text-white px-4 py-2 rounded-lg hover:bg-[#0f6a5c]">
                抓
              </button>
            </div>
          </div>
        </div>
      <!-- 列3：关节监控 + IO面板 - 青雀的牌局记录 -->
      <div class="col-span-1 space-y-6">
        <!-- 关节状态监控 - 牌面点数 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🀁</span> 七索·关节
          </h2>
          <div class="space-y-3">
            <div v-for="i in 7" :key="i" class="flex items-center gap-2">
              <span class="w-8 text-sm font-medium" :class="'tile-j' + i">J{{i}}:</span>
              <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-[#1f8a7c] to-[#d4af37] rounded-full" 
                     :style="{width: jointPositions[i-1] + '%'}"></div>
              </div>
              <span class="text-xs w-12 text-right">{{jointAngles[i-1]?.toFixed(1)}}°</span>
            </div>
          </div>
        </div>

        <!-- IO 监控面板 - 牌局状态 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">🀂</span> 牌局·I/O
          </h2>
          <div class="grid grid-cols-4 gap-2">
            <div v-for="pin in ioPins" :key="pin.name" 
                 class="p-2 border rounded-lg text-center tile-io"
                 :class="pin.value ? 'bg-[#e8f0f5] border-[#1f8a7c]' : 'bg-gray-50'">
              <div class="text-xs text-gray-500">{{pin.name}}</div>
              <div class="text-2xl" :class="pin.value ? 'text-[#1f8a7c]' : 'text-gray-400'">
                {{pin.value ? '●' : '○'}}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div> 

      <!-- 列4：任务状态 + 结果 + 日志 - 青雀的账本 -->
      <div class="col-span-1 space-y-6">
        <!-- 任务状态卡片 - 卦象 -->
        <div class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">☯</span> 今日卦象
          </h2>
          <div class="text-center py-4">
            <div class="text-7xl mb-2 animate-pulse status-symbol" 
                 :class="'status-' + taskStatus">
              {{ statusSymbol }}
            </div>
            <div class="text-xl font-bold">{{ statusText }}</div>
            <div class="text-xs text-gray-400 mt-2">{{ guaMessage }}</div>
          </div>
        </div>

        <!-- 最新结果卡片 - 牌局记录 -->
        <div v-if="lastResult" class="qingque-card p-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">📋</span> 上局牌面
          </h2>
          <pre class="text-xs bg-[#e8f0f5] p-3 rounded-lg overflow-auto max-h-32 border border-[#1f8a7c]/20">
{{ JSON.stringify(lastResult, null, 2) }}
          </pre>
        </div>

        <!-- 操作日志卡片 - 青雀的流水账 -->
        <div class="qingque-card p-4 bg-gradient-to-b from-[#1f8a7c]/5 to-white">
          <div class="flex justify-between items-center mb-3">
            <h3 class="text-lg font-bold flex items-center gap-2">
              <span class="text-[#1f8a7c]">📜</span> 流水账
            </h3>
            <button @click="logs = []" class="text-xs text-gray-400 hover:text-[#1f8a7c] transition">
              清账
            </button>
          </div>
          <div class="h-48 overflow-auto font-mono text-sm bg-white/80 rounded-lg p-3 border border-[#1f8a7c]/20">
            <div v-for="(log, i) in logs" :key="i" 
                 class="border-b border-[#1f8a7c]/10 py-1 last:border-0"
                 :class="{
                   'text-green-600': log.type === 'success',
                   'text-red-600': log.type === 'error',
                   'text-yellow-600': log.type === 'action',
                   'text-gray-600': log.type === 'info'
                 }">
              <span class="text-gray-400">[{{ log.time }}]</span> {{ log.msg }}
            </div>
            <div v-if="logs.length === 0" class="text-gray-400 text-center py-4">
              今日无事，摸鱼中...
            </div>
          </div>
          <!-- 青雀印章 -->
          <div class="text-right mt-1 text-xs text-gray-400">
            🕊️ 青雀印
          </div>
        </div>
        <!-- 添加物体卡片 -->
        <div class="qingque-card p-4 mt-4">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-[#1f8a7c]">➕</span> 添加物体
          </h2>
          
          <!-- 形状选择 -->
          <div class="flex gap-2 mb-3">
            <button @click="newObject.type='box'" 
                    class="flex-1 p-2 rounded border"
                    :class="newObject.type==='box' ? 'bg-[#1f8a7c] text-white' : 'bg-white'">
              立方体
            </button>
            <button @click="newObject.type='sphere'"
                    class="flex-1 p-2 rounded border"
                    :class="newObject.type==='sphere' ? 'bg-[#1f8a7c] text-white' : 'bg-white'">
              球体
            </button>
            <button @click="newObject.type='cylinder'"
                    class="flex-1 p-2 rounded border"
                    :class="newObject.type==='cylinder' ? 'bg-[#1f8a7c] text-white' : 'bg-white'">
              圆柱
            </button>
          </div>
          
          <!-- 物体ID -->
          <input v-model="newObject.id" placeholder="物体ID" 
                class="w-full p-2 border rounded mb-3">
          
          <!-- 位置 -->
          <div class="grid grid-cols-3 gap-2 mb-3">
            <input v-model.number="newObject.x" placeholder="X" class="p-2 border rounded">
            <input v-model.number="newObject.y" placeholder="Y" class="p-2 border rounded">
            <input v-model.number="newObject.z" placeholder="Z" class="p-2 border rounded">
          </div>
          
          <!-- 立方体参数 -->
          <div v-if="newObject.type === 'box'" class="grid grid-cols-3 gap-2 mb-3">
            <input v-model.number="newObject.sizeX" placeholder="长" class="p-2 border rounded">
            <input v-model.number="newObject.sizeY" placeholder="宽" class="p-2 border rounded">
            <input v-model.number="newObject.sizeZ" placeholder="高" class="p-2 border rounded">
          </div>
          
          <!-- 球体/圆柱参数 -->
          <div v-else class="grid grid-cols-2 gap-2 mb-3">
            <input v-model.number="newObject.radius" placeholder="半径" class="p-2 border rounded">
            <input v-if="newObject.type === 'cylinder'" v-model.number="newObject.height" 
                  placeholder="高度" class="p-2 border rounded">
          </div>
          
          <button @click="addNewObject" 
                  class="w-full bg-[#1f8a7c] text-white p-2 rounded hover:bg-[#0f6a5c]">
            添加物体
          </button>
        </div>        
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRobotStore } from '../stores/robot'

const store = useRobotStore()
console.log('store内容:', store)
console.log('addObject是否存在:', store.addObject)
const selectedObject = ref('')
const graspWidth = ref(40)
const movePose = ref({ x: 0.5, y: 0, z: 0.3 })
// 直接输入物体ID
const showWidth = ref(false)  // ← 就加这
const directObjectId = ref('')
const { connected, objects, taskStatus, lastResult, connect, graspObject, moveToPose } = store

// ========== 青雀语录 ==========
const quotes = [
  "工作不算争取价值，那叫劳动交换酬劳",
  "今日不宜工作，宜摸鱼",
  "摸鱼一时爽，一直摸鱼一直爽",
  "牌桌之上，自有天道",
  "占卜说今天适合偷懒",
  "人生苦短，我用摸鱼",
  "工作是不可能工作的",
  "摸鱼是一种生活态度",
  "让我看看谁还在认真工作",
  "牌运来了，挡都挡不住"
]

const currentQuote = ref(quotes[0])

// 每小时换一句
setInterval(() => {
  currentQuote.value = quotes[Math.floor(Math.random() * quotes.length)]
}, 3600000)

// ========== 状态文字和符号 ==========
const statusText = computed(() => {
  const status = taskStatus.value
  if (status === 'running') return '卦动·执行'
  if (status === 'success') return '上上签'
  if (status === 'failed') return '下下签'
  return '静卦·待机'
})

const statusEmoji = computed(() => {
  const status = taskStatus.value
  if (status === 'running') return '⚡'
  if (status === 'success') return '✅'
  if (status === 'failed') return '❌'
  return '○'
})

const statusSymbol = computed(() => {
  const status = taskStatus.value
  if (status === 'running') return '⚡'
  if (status === 'success') return '☯'
  if (status === 'failed') return '⚠️'
  return '○'
})

const guaMessage = computed(() => {
  const status = taskStatus.value
  if (status === 'running') return '卦象未定，静待结果'
  if (status === 'success') return '大吉大利，今晚吃鸡'
  if (status === 'failed') return '凶，建议摸鱼避祸'
  return '无事卦，宜摸鱼'
})

// ========== 模拟关节数据 ==========
const jointAngles = ref([0, -45, 0, -90, 0, 90, 45])
const jointPositions = computed(() => {
  return jointAngles.value.map(a => (a + 90) / 180 * 100)
})

// ========== 模拟 IO 数据 ==========
const ioPins = ref([
  { name: 'DI1', value: true },
  { name: 'DI2', value: false },
  { name: 'DO1', value: true },
  { name: 'DO2', value: false },
  { name: 'AI1', value: false },
  { name: 'AI2', value: true },
  { name: 'AO1', value: true },
  { name: 'AO2', value: false },
])

// ========== 日志系统 ==========
type LogType = 'info' | 'success' | 'error' | 'action'
const logs = ref<{ time: string; msg: string; type?: LogType }[]>([])

const addLog = (msg: string, type: LogType = 'info') => {
  logs.value.unshift({
    time: new Date().toLocaleTimeString(),
    msg,
    type
  })
  if (logs.value.length > 50) logs.value.pop()
}
// ========== 添加物体表单 ==========
const newObject = ref({
  type: 'box' as 'box' | 'sphere' | 'cylinder',
  id: '',
  x: 0.5,
  y: 0,
  z: 0.3,
  sizeX: 0.1,
  sizeY: 0.1,
  sizeZ: 0.1,
  radius: 0.05,
  height: 0.1
})

const addNewObject = () => {
  console.log('✅ addNewObject 被点击了')
  
  // 把 type 改名为 shape，并且单独发 add_object
  const params: any = {
    shape: newObject.value.type,        // 原来是 type，现在改 shape
    object_id: newObject.value.id,
    position: [newObject.value.x, newObject.value.y, newObject.value.z]
  }
  
  if (newObject.value.type === 'box') {
    params.size = [newObject.value.sizeX, newObject.value.sizeY, newObject.value.sizeZ]
  } else {
    params.radius = newObject.value.radius
    if (newObject.value.type === 'cylinder') {
      params.height = newObject.value.height
    }
  }
  
  // 发送消息时 type 固定为 'add_object'
  store.addObject({
    type: 'add_object',  // 消息类型
    ...params
  })
  
  addLog(`📦 添加物体: ${newObject.value.id}`, 'action')
  newObject.value.id = ''
}
// ========== 物体详情弹窗 ==========
const showDetailsModal = ref(false)
const loadingDetails = ref(false)
const currentObject = ref<{ id: string } | null>(null)
const currentPose = ref<number[]>([])
const currentDimensions = ref<any>(null)

// 显示物体详情
// 显示物体详情
const showObjectDetails = async (objectId: string) => {
  currentObject.value = { id: objectId }
  currentPose.value = []
  currentDimensions.value = null
  loadingDetails.value = true
  showDetailsModal.value = true
  
  // 同时请求位姿和尺寸
  store.getObjectPose(objectId)
  store.getObjectDimensions(objectId)
}
// 直接用 store.lastPose 和 store.lastDimensions
watch(() => store.lastPose, (newVal) => {
  console.log('🎯 监听到位姿:', newVal)
  if (newVal && newVal.object_id === currentObject.value?.id) {
    currentPose.value = newVal.pose || []
    // 强制更新视图
    currentPose.value = [...currentPose.value]
  }
}, { immediate: true, deep: true })

watch(() => store.lastDimensions, (newVal) => {
  console.log('🎯 监听到尺寸:', newVal)
  if (newVal && newVal.object_id === currentObject.value?.id) {
    currentDimensions.value = newVal.dimensions
  }
}, { immediate: true, deep: true })

// 当两者都到位时关闭加载
watch([() => currentPose.value, () => currentDimensions.value], () => {
  if (currentPose.value.length > 0 && currentDimensions.value) {
    console.log('✅ 关闭加载')
    loadingDetails.value = false
  }
}, { immediate: true })
// ========== 快捷抓取预设 ==========
const presets = {
  'train_1': { width: 40, name: '火车', emoji: '🚂' },
  'test_cube': { width: 50, name: '方块', emoji: '📦' },
  'coke_can': { width: 65, name: '可乐罐', emoji: '🥤' }
} as const

const quickGrasp = (objId: keyof typeof presets) => {
  selectedObject.value = objId
  graspWidth.value = presets[objId].width
  handleGrasp()
}

// ========== 快捷任务 ==========
const runTask = (task: string) => {
  addLog(`🎯 执行任务: ${task}`, 'action')
  if (task === 'home') {
    addLog('🏠 归位', 'info')
  }
}

// ========== 操作函数 ==========
const handleGrasp = () => {
  if (!selectedObject.value) return
  addLog(`🔄 摸牌: ${selectedObject.value}`, 'action')
  graspObject(selectedObject.value, graspWidth.value)
}
const graspDirect = () => {
  if (!directObjectId.value.trim()) {
    addLog('❌ 请输入物体ID', 'error')
    return
  }
  selectedObject.value = directObjectId.value
  handleGrasp()
  directObjectId.value = ''
}
const handleMove = () => {
  addLog(`🎯 移形: [${movePose.value.x.toFixed(2)}, ${movePose.value.y.toFixed(2)}, ${movePose.value.z.toFixed(2)}]`, 'action')
  moveToPose([movePose.value.x, movePose.value.y, movePose.value.z, 0, 0, 0, 1])
}

// ========== 模拟关节更新 ==========
let interval: ReturnType<typeof setInterval>
onMounted(() => {
  interval = setInterval(() => {
    jointAngles.value = jointAngles.value.map(a => a + (Math.random() - 0.5) * 2)
  }, 2000)
})

onUnmounted(() => {
  clearInterval(interval)
})

// ========== 监听结果 ==========

watch(lastResult, (newVal) => {
  if (newVal) {
    if (newVal.success) {
      addLog(`✅ 和牌: ${newVal.object_id || '操作'}`, 'success')
    } else {
      addLog(`❌ 诈和: ${newVal.error || '未知错误'}`, 'error')
    }
  }
})

onMounted(() => {
  connect()
  addLog('🎐 青雀驾到，开始摸鱼', 'info')
})
</script>

<style scoped>
/* 青雀主题全局样式 */

/* 青雀主题变量 */
.qingque-theme {
  --qingque-primary: #1f8a7c;
  --qingque-secondary: #64b5a6;
  --qingque-accent: #d4af37;
  --qingque-dark: #2c3e4e;
  --qingque-light: #e8f0f5;
  --qingque-gold: #f5e6b3;
}

/* 卡片样式 - 麻将牌 */
.qingque-card {
  background: white;
  border-radius: 16px 16px 8px 8px;
  box-shadow: 0 10px 20px rgba(31, 138, 124, 0.1),
              inset 0 -2px 0 var(--qingque-primary);
  border-left: 4px solid var(--qingque-primary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.qingque-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 30px rgba(31, 138, 124, 0.2),
              inset 0 -2px 0 var(--qingque-accent);
  border-left-color: var(--qingque-accent);
}

.qingque-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(45deg, 
      rgba(31, 138, 124, 0.02) 25%, 
      transparent 25%,
      transparent 50%,
      rgba(31, 138, 124, 0.02) 50%,
      rgba(31, 138, 124, 0.02) 75%,
      transparent 75%,
      transparent
    );
  background-size: 20px 20px;
  pointer-events: none;
}

/* 标题栏 - 卷轴 */
.qingque-header {
  background: linear-gradient(135deg, var(--qingque-dark) 0%, #1a2a35 100%);
  border-bottom: 3px solid var(--qingque-primary);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  position: relative;
}

.qingque-header::before,
.qingque-header::after {
  content: "";
  position: absolute;
  bottom: -3px;
  width: 30px;
  height: 10px;
  background: var(--qingque-primary);
  border-radius: 0 0 10px 10px;
}
.qingque-header::before { left: 20px; }
.qingque-header::after { right: 20px; }

/* 标题文字 */
.qingque-title {
  font-weight: 500;
  letter-spacing: 2px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  position: relative;
  display: inline-block;
}
.qingque-title::before,
.qingque-title::after {
  content: "●";
  font-size: 8px;
  color: var(--qingque-accent);
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}
.qingque-title::before { left: -15px; }
.qingque-title::after { right: -15px; }

/* 按钮样式 - 麻将牌 */
.qingque-btn {
  background: linear-gradient(145deg, #ffffff, #f0f0f0);
  border: 2px solid var(--qingque-primary);
  border-radius: 8px;
  color: var(--qingque-dark);
  font-weight: 600;
  position: relative;
  overflow: hidden;
  transition: all 0.2s;
  box-shadow: 0 4px 0 var(--qingque-primary);
}

.qingque-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 0 var(--qingque-accent);
  border-color: var(--qingque-accent);
}

.qingque-btn:active {
  transform: translateY(2px);
  box-shadow: 0 2px 0 var(--qingque-primary);
}

.qingque-btn-small {
  background: white;
  border: 1px solid var(--qingque-primary);
  border-radius: 8px;
  color: var(--qingque-dark);
  position: relative;
  overflow: hidden;
  transition: all 0.2s;
}

.qingque-btn-small:hover {
  background: var(--qingque-light);
  border-color: var(--qingque-accent);
}

/* 按钮上的小牌面 */
.btn-face {
  position: absolute;
  bottom: 2px;
  right: 5px;
  font-size: 12px;
  opacity: 0.2;
  color: var(--qingque-primary);
}

.btn-face-mini {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 8px;
  opacity: 0.3;
}

/* 状态指示器 - 占卜盘 */
.qingque-status {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: white;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 0 15px currentColor;
}

.status-idle { border-color: #95a5a6; color: #7f8c8d; }
.status-running { border-color: #f39c12; color: #e67e22; animation: divination-spin 2s infinite; }
.status-success { border-color: var(--qingque-primary); color: var(--qingque-primary); }
.status-failed { border-color: #e74c3c; color: #c0392b; }

/* 状态大符号 */
.status-symbol {
  filter: drop-shadow(0 0 10px currentColor);
}
.status-symbol.status-running { color: #f39c12; }
.status-symbol.status-success { color: var(--qingque-primary); }
.status-symbol.status-failed { color: #e74c3c; }

@keyframes divination-spin {
  0% { transform: rotate(0deg); }
  25% { transform: rotate(10deg); }
  75% { transform: rotate(-10deg); }
  100% { transform: rotate(0deg); }
}

/* 云纹装饰 */
.cloud-pattern {
  background-image: radial-gradient(circle at 20px 20px, rgba(31, 138, 124, 0.1) 2px, transparent 2px);
  background-size: 40px 40px;
}

/* 水波纹 */
.wave-border {
  border-bottom: 2px solid var(--qingque-primary);
  position: relative;
}
.wave-border::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 6px;
  background: repeating-linear-gradient(
    45deg,
    var(--qingque-primary) 0px,
    var(--qingque-primary) 4px,
    transparent 4px,
    transparent 8px
  );
  opacity: 0.3;
}

/* 麻将字符元素 */
.mahjong-character {
  position: relative;
}
.mahjong-character::after {
  content: "發";
  position: absolute;
  bottom: 2px;
  right: 5px;
  font-size: 20px;
  font-weight: bold;
  color: var(--qingque-accent);
  opacity: 0.1;
  transform: rotate(-10deg);
  font-family: "KaiTi", "楷体", serif;
}

/* 牌面列表项 */
.tile-item {
  border-color: rgba(31, 138, 124, 0.3);
  transition: all 0.2s;
}
.tile-item:hover {
  background: var(--qingque-light);
  border-color: var(--qingque-primary);
}
.selected-tile {
  background: var(--qingque-light);
  border-color: var(--qingque-accent);
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
}

/* 动作卡片 */
.tile-action {
  background: white;
  border: 1px solid rgba(31, 138, 124, 0.3);
  position: relative;
}
.tile-action:hover {
  background: var(--qingque-light);
  border-color: var(--qingque-accent);
}
.tile-mark {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 10px;
  opacity: 0.3;
  font-family: "KaiTi", serif;
}

/* IO 面板的牌格 */
.tile-io {
  transition: all 0.2s;
}
.tile-io:hover {
  transform: scale(1.05);
  border-color: var(--qingque-primary);
}

/* 关节标识 */
.tile-j1::before { content: "🀇"; margin-right: 4px; opacity: 0.3; }
.tile-j2::before { content: "🀈"; margin-right: 4px; opacity: 0.3; }
.tile-j3::before { content: "🀉"; margin-right: 4px; opacity: 0.3; }
.tile-j4::before { content: "🀊"; margin-right: 4px; opacity: 0.3; }
.tile-j5::before { content: "🀋"; margin-right: 4px; opacity: 0.3; }
.tile-j6::before { content: "🀌"; margin-right: 4px; opacity: 0.3; }
.tile-j7::before { content: "🀍"; margin-right: 4px; opacity: 0.3; }

/* 自定义滚动条 - 麻将风格 */
.mahjong-scroll::-webkit-scrollbar {
  width: 6px;
}
.mahjong-scroll::-webkit-scrollbar-track {
  background: var(--qingque-light);
  border-radius: 3px;
}
.mahjong-scroll::-webkit-scrollbar-thumb {
  background: var(--qingque-primary);
  border-radius: 3px;
}
.mahjong-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--qingque-accent);
}
</style>