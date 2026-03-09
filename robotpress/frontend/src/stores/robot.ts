// frontend/src/stores/robot.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRobotStore = defineStore('robot', () => {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const objects = ref<string[]>([])
  const taskStatus = ref('idle')
  const lastResult = ref<any>(null)
  const lastPose = ref<any>(null)
  const lastDimensions = ref<any>(null)
  // 连接 WebSocket
  const connect = () => {
    ws.value = new WebSocket('ws://localhost:8765')
    
    ws.value.onopen = () => {
      connected.value = true
      console.log('✅ 已连接到 RobotPress 后端')
      sendMessage({ type: 'list_objects' })
    }
    
    ws.value.onclose = () => {
      connected.value = false
      console.log('❌ 连接断开')
    }
    
    ws.value.onmessage = (e) => {
      const data = JSON.parse(e.data)
      handleMessage(data)
    }
  }

  // 处理消息
// 处理消息
  const handleMessage = (data: any) => {
    console.log('📩 收到消息:', data)
    console.log('📩 收到原始消息:', JSON.stringify(data))  // 先打印原始消息
    console.log('📩 收到消息:', data)    
    switch (data.type) {
      case 'object_list':
        objects.value = data.objects
        break
      case 'grasp_result':
        lastResult.value = data
        taskStatus.value = data.success ? 'success' : 'failed'
        sendMessage({ type: 'list_objects' })
        break
      case 'move_result':
        lastResult.value = data
        taskStatus.value = data.success ? 'success' : 'failed'
        break
      case 'add_result':  // 加上这个分支！
        if (data.success) {
          console.log('✅ 物体添加成功:', data.object_id)
          sendMessage({ type: 'list_objects' })  // 刷新列表
        } else {
          console.error('❌ 物体添加失败:', data.message)
        }
        break
      case 'move_object_result':
        lastResult.value = data
        taskStatus.value = data.success ? 'success' : 'failed'
        if (data.success) {
          console.log('✅ 物体移动成功:', data.object_id)
          sendMessage({ type: 'list_objects' })  // 刷新列表
        } else {
          console.error('❌ 物体移动失败:', data.message)
        }
        break  
      case 'object_pose':
        console.log('📍 物体位姿:', data.pose)
        lastPose.value = data  // 存到专门的变量
        // lastResult.value = data  // 可以注释掉这行
        break

      case 'object_dimensions':
        console.log('📏 物体尺寸:', data.dimensions)
        lastDimensions.value = data  // 存到专门的变量
        // lastResult.value = data  // 可以注释掉这行
        break  
      case 'error':
        console.error('❌ 错误:', data.message)
        break
    }
  }

  // 发送消息
  const sendMessage = (msg: any) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(msg))
    }
  }

  // 抓取物体
  const graspObject = (objectId: string, width?: number) => {
    taskStatus.value = 'running'
    sendMessage({
      type: 'grasp',
      object_id: objectId,
      width: width
    })
  }

  // 移动到位姿
  const moveToPose = (pose: number[]) => {
    taskStatus.value = 'running'
    sendMessage({
      type: 'move_to_pose',
      pose: pose
    })
  }
  // ========== 添加物体 ==========
  const addObject = (params: {
  type: 'add_object',  // 消息类型固定为 'add_object'
  shape: 'box' | 'sphere' | 'cylinder',
  object_id: string,
  position: [number, number, number],
  size?: [number, number, number],
  radius?: number,
  height?: number
}) => {
  sendMessage(params)  // 直接发整个 params
}
  // ========== 移除物体 ==========
  const removeObject = (objectId: string) => {
    sendMessage({
      type: 'remove_object',
      object_id: objectId
    })
  }
  // ========== 移动物体 ==========
  const moveObject = (objectId: string, position: number[], orientation?: number[]) => {
    taskStatus.value = 'running'
    sendMessage({
      type: 'move_object',
      object_id: objectId,
      position: position,
      orientation: orientation || [0, 0, 0, 1]
    })
  }
  // ========== 获取物体位姿 ==========
const getObjectPose = (objectId: string) => {
  sendMessage({
    type: 'get_object_pose',
    object_id: objectId
  })
}

// ========== 获取物体尺寸 ==========
const getObjectDimensions = (objectId: string) => {
  sendMessage({
    type: 'get_object_dimensions',
    object_id: objectId
  })
}
  return {
    connected,
    objects,
    taskStatus,
    lastResult,
    lastPose,        
    lastDimensions, 
    connect,
    graspObject,
    moveToPose,
    addObject,
    removeObject,
    moveObject,
    getObjectPose,      
    getObjectDimensions  
  }
})