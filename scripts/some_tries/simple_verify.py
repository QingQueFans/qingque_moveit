#!/usr/bin/env python3
"""
简化验证脚本 - 避免导入问题
"""
import rclpy
from rclpy.node import Node
import time

class SimpleVerifier(Node):
    def __init__(self):
        super().__init__('simple_verifier')
    
    def verify_wall(self):
        """验证墙是否存在"""
        print("🧐 验证墙的效果")
        print("="*50)
        
        print("请在RViz中手动测试:")
        print("\n1. 视觉确认:")
        print("   - 看到五个半透明的立方体吗？")
        print("   - 位置在 (0.4, 0.0, 0.3/0.5/0.7) 和 (0.4, ±0.1, 0.5)")
        
        print("\n2. 碰撞测试:")
        print("   - 拖动白色机械臂到墙的位置")
        print("   - 观察路径线是否变红（碰撞）")
        print("   - 尝试规划，观察是否失败")
        
        print("\n3. 绕墙测试:")
        print("   - 设置起点在墙左侧")
        print("   - 设置终点在墙右侧") 
        print("   - 点击Plan，观察是否绕开")
        
        input("\n按回车继续查看清理选项...")
    
    def show_options(self):
        """显示后续选项"""
        print("\n📋 后续操作选项")
        print("="*50)
        
        options = [
            ("继续使用墙", "进行更多实验"),
            ("手动清除墙", "运行清除脚本"),
            ("修改墙", "调整位置或大小"),
            ("结束", "墙保留在场景中"),
        ]
        
        for i, (name, desc) in enumerate(options, 1):
            print(f"{i}. {name}: {desc}")
        
        print("\n💡 提示: 墙会一直存在，直到被明确清除")

def main():
    rclpy.init()
    verifier = SimpleVerifier()
    
    try:
        print("🔍 五个箱子墙验证")
        print("如果看不到墙，请先运行 create_wall_only.py")
        print("="*50)
        
        # 验证
        verifier.verify_wall()
        
        # 显示选项
        verifier.show_options()
        
        print("\n" + "="*50)
        print("✅ 验证完成")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    finally:
        verifier.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
