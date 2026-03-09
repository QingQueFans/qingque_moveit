"""
RobotPress WebSocket 桥接服务器
连接 Vue 前端和你的 planning_interface
"""

import asyncio
import websockets  # pyright: ignore[reportMissingImports]
import json
import sys
import os
from typing import Dict, Any

# ========== 添加你的项目路径 ==========
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit")
sys.path.insert(0, "/home/diyuanqiongyu/qingfu_moveit/moveit_ros/planning_interface/src")
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/install/pymoveit2/lib/python3.10/site-packages')

# ========== 导入快捷函数 ==========
from planning_interface import (
    grasp_object,
    move_to_pose,
    add_box,
    add_sphere,
    add_cylinder,
    remove_object,
    move_object
)
from planning_interface.knowledge.objects.cache import ObjectCache


class RobotPressBridge:
    """WebSocket 桥接器"""
    
    def __init__(self):
        self.object_cache = ObjectCache()
        self.clients = set()
        print("[RobotPress] 桥接器初始化完成")
    
    async def handle_client(self, websocket):
        """处理单个客户端连接"""
        self.clients.add(websocket)
        print(f"[RobotPress] 新客户端连接，当前连接数: {len(self.clients)}")
        
        try:
            # 发送欢迎消息
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "已连接到 RobotPress 后端"
            }))
            
            # 发送物体列表
            await self._send_objects(websocket)
            
            # 处理客户端消息
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            print("[RobotPress] 客户端断开连接")
        finally:
            self.clients.remove(websocket)
    
    async def _handle_message(self, websocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "grasp":
                await self._handle_grasp(websocket, data)
            elif msg_type == "list_objects":
                await self._send_objects(websocket)
            elif msg_type == "get_object":
                await self._handle_get_object(websocket, data)
            elif msg_type == "move_to_pose":
                await self._handle_move(websocket, data)
            elif msg_type == "add_object":
                await self._handle_add_object(websocket, data)
            elif msg_type == "remove_object":
                await self._handle_remove_object(websocket, data)
            elif msg_type == "move_object":
                await self._handle_move_object(websocket, data)
            elif msg_type == "get_object_pose":
                await self._handle_get_object_pose(websocket, data)    
            elif msg_type == "get_object_dimensions":
                await self._handle_get_object_dimensions(websocket, data)      
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"未知消息类型: {msg_type}"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "无效的 JSON 格式"
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def _handle_grasp(self, websocket, data):
        """处理抓取请求"""
        object_id = data.get("object_id")
        width = data.get("width")
        strategy = data.get("strategy", "auto")
        
        print(f"[RobotPress] 收到抓取请求: {object_id}")
        
        # ✅ 用快捷函数
        result = grasp_object(object_id, width_mm=width, strategy=strategy)
        
        await websocket.send(json.dumps({
            "type": "grasp_result",
            "success": result.get("success", False),
            "object_id": object_id,
            "message": f"抓取 {'成功' if result.get('success') else '失败'}",
            "details": result
        }))
    
    async def _handle_move(self, websocket, data):
        """处理移动请求"""
        pose = data.get("pose")
        if not pose or len(pose) < 3:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "需要提供位置 [x,y,z]"
            }))
            return
        
        print(f"[RobotPress] 收到移动请求: {pose[:3]}")
        
        # ✅ 用快捷函数
        result = move_to_pose(pose)
        
        await websocket.send(json.dumps({
            "type": "move_result",
            "success": result.get("success", False),
            "pose": pose[:3],
            "message": f"移动 {'成功' if result.get('success') else '失败'}"
        }))
    
    async def _handle_get_object(self, websocket, data):
        """获取单个物体信息"""
        object_id = data.get("object_id")
        if not object_id:
            return
        
        # 从缓存获取物体信息
        obj_info = self.object_cache.get_object_info(object_id)
        
        await websocket.send(json.dumps({
            "type": "object_info",
            "object_id": object_id,
            "data": obj_info
        }))
    
    async def _send_objects(self, websocket):
        """发送物体列表"""
        # 从缓存获取所有物体
        objects = self.object_cache.get_all_objects()
        object_list = [obj.get("id") for obj in objects if obj.get("id")]
        
        await websocket.send(json.dumps({
            "type": "object_list",
            "objects": object_list,
            "count": len(object_list)
        }))
    async def _handle_get_object_pose(self, websocket, data):
        """处理获取物体位姿请求"""
        object_id = data.get("object_id")
        print(f"[RobotPress] 获取物体位姿: {object_id}")
        
        try:
            # 从缓存获取位姿
            pose = self.object_cache.get_pose(object_id)
            print(f"[RobotPress] get_pose 返回: {pose}")  # 加这行
            if pose:
                pose = [float(x) for x in pose]  # 加这行！
                await websocket.send(json.dumps({
                    "type": "object_pose",
                    "object_id": object_id,
                    "pose": pose  # 7个数 [x,y,z,qx,qy,qz,qw]
                    
                }))
                print(f"[RobotPress] 位姿发送成功: {pose}")  # 加日志
                
            else:
                await websocket.send(json.dumps({
                    "type": "object_pose",
                    "object_id": object_id,
                    "pose": None,
                    "error": "未找到物体位姿"
                }))
                
        except Exception as e:
            print(f"[RobotPress] 获取位姿异常: {e}")
            await websocket.send(json.dumps({
                "type": "object_pose",
                "object_id": object_id,
                "error": str(e)
            }))    
    async def _handle_get_object_dimensions(self, websocket, data):
        """处理获取物体尺寸请求"""
        object_id = data.get("object_id")
        print(f"[RobotPress] 获取物体尺寸: {object_id}")
        
        try:
            # 从缓存获取尺寸
            dimensions = self.object_cache.get_dimensions(object_id)
            
            if dimensions:
                await websocket.send(json.dumps({
                    "type": "object_dimensions",
                    "object_id": object_id,
                    "dimensions": dimensions
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "object_dimensions",
                    "object_id": object_id,
                    "dimensions": None,
                    "error": "未找到物体尺寸信息"
                }))
                
        except Exception as e:
            print(f"[RobotPress] 获取尺寸异常: {e}")
            await websocket.send(json.dumps({
                "type": "object_dimensions",
                "object_id": object_id,
                "error": str(e)
            }))            
    async def broadcast(self, message: str):
        """向所有客户端广播消息"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )
    
    async def _handle_add_object(self, websocket, data):
        """处理添加物体请求"""
        print(f"[RobotPress] 添加物体: {data}")
        
        obj_type = data.get("shape")
        object_id = data.get("object_id")
        position = data.get("position")
        
        try:
            # ✅ 根据类型用不同的快捷函数
            if obj_type == "box":
                size = data.get("size")
                result = add_box(object_id, position, size)
            elif obj_type == "sphere":
                radius = data.get("radius")
                result = add_sphere(object_id, position, radius)
            elif obj_type == "cylinder":
                radius = data.get("radius")
                height = data.get("height")
                result = add_cylinder(object_id, position, radius, height)
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"未知物体类型: {obj_type}"
                }))
                return
            
            # 返回结果
            await websocket.send(json.dumps({
                "type": "add_result",
                "success": result.get("success", False),
                "object_id": object_id,
                "message": f"添加 {'成功' if result.get('success') else '失败'}"
            }))
            
            # 添加成功后自动推送新列表
            await self._send_objects(websocket)
            
        except Exception as e:
            print(f"[RobotPress] 添加物体异常: {e}")
            await websocket.send(json.dumps({
                "type": "add_result",
                "success": False,
                "object_id": object_id,
                "message": str(e)
            }))
    
    async def _handle_remove_object(self, websocket, data):
        """处理移除物体请求"""
        object_id = data.get("object_id")
        print(f"[RobotPress] 移除物体: {object_id}")
        
        try:
            # ✅ 用快捷函数
            result = remove_object(object_id)
            
            await websocket.send(json.dumps({
                "type": "remove_result",
                "success": result.get("success", False),
                "object_id": object_id,
                "message": f"移除 {'成功' if result.get('success') else '失败'}"
            }))
            
            await self._send_objects(websocket)
            
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "remove_result",
                "success": False,
                "object_id": object_id,
                "message": str(e)
            }))
    
    async def _handle_move_object(self, websocket, data):
        """处理移动物体请求"""
        object_id = data.get("object_id")
        new_position = data.get("position")
        new_orientation = data.get("orientation", [0, 0, 0, 1])
        
        print(f"[RobotPress] 移动物体: {object_id} -> {new_position}")
        
        try:
            # ✅ 用快捷函数
            result = move_object(object_id, new_position, new_orientation)
            
            await websocket.send(json.dumps({
                "type": "move_object_result",
                "success": result.get("success", False),
                "object_id": object_id,
                "message": result.get("message", "")
            }))
            
            # 移动成功后刷新物体列表
            if result.get("success"):
                await self._send_objects(websocket)
                
        except Exception as e:
            print(f"[RobotPress] 移动物体异常: {e}")
            await websocket.send(json.dumps({
                "type": "move_object_result",
                "success": False,
                "object_id": object_id,
                "message": str(e)
            }))


async def main():
    """主函数"""
    bridge = RobotPressBridge()
    
    async with websockets.serve(
        bridge.handle_client,
        "0.0.0.0",  # 允许所有 IP 访问
        8765,       # WebSocket 端口
        ping_interval=20,
        ping_timeout=60
    ):
        print("=" * 50)
        print("🚀 RobotPress WebSocket 服务器启动")
        print(f"📡 监听地址: ws://0.0.0.0:8765")
        print("=" * 50)
        await asyncio.Future()  # 一直运行


if __name__ == "__main__":
    asyncio.run(main())