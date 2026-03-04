import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(MODULE_ROOT)

PERCEPTION_SRC = os.path.join(PROJECT_ROOT, 'perception', 'object_detection', 'src')
sys.path.insert(0, PERCEPTION_SRC)

from object_detection.object_detector import PureObjectDetector

# 测试
print("=== 测试 PureObjectDetector 模式设置 ===")

detector = PureObjectDetector(None, None)
print(f"1. 初始模式: {detector.mode}")

detector.set_mode("cache_only")
print(f"2. 设置后模式: {detector.mode}")

print(f"3. 检测器属性: {dir(detector)}")
