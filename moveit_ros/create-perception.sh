#!/bin/bash
# 创建感知模块完整目录结构（最小化版本）

# 基础路径（根据您的实际情况调整）
BASE_DIR="perception"

echo "=== 创建感知模块目录结构 ==="
echo "基础路径: $BASE_DIR"

# ========== 创建所有目录 ==========
mkdir -p "$BASE_DIR"

# 1. 点云处理子模块
mkdir -p "$BASE_DIR/point_cloud_processing/src/point_cloud_processing"
mkdir -p "$BASE_DIR/point_cloud_processing/scripts"
mkdir -p "$BASE_DIR/point_cloud_processing/examples"

# 2. 物体检测子模块
mkdir -p "$BASE_DIR/object_detection/src/object_detection"
mkdir -p "$BASE_DIR/object_detection/scripts"
mkdir -p "$BASE_DIR/object_detection/examples"

# 3. 深度图像处理子模块
mkdir -p "$BASE_DIR/depth_image_processing/src/depth_image_processing"
mkdir -p "$BASE_DIR/depth_image_processing/scripts"
mkdir -p "$BASE_DIR/depth_image_processing/examples"

# 4. Octomap集成子模块
mkdir -p "$BASE_DIR/octomap_integration/src/octomap_integration"
mkdir -p "$BASE_DIR/octomap_integration/scripts"
mkdir -p "$BASE_DIR/octomap_integration/examples"

# 5. 传感器集成子模块
mkdir -p "$BASE_DIR/sensor_integration/src/sensor_integration"
mkdir -p "$BASE_DIR/sensor_integration/scripts"
mkdir -p "$BASE_DIR/sensor_integration/examples"

echo "✓ 目录结构创建完成"

# ========== 创建最简单的 __init__.py 文件 ==========
echo "=== 创建基础文件 ==="

# 为每个src目录创建 __init__.py
for module in point_cloud_processing object_detection depth_image_processing octomap_integration sensor_integration; do
    cat > "$BASE_DIR/$module/src/$module/__init__.py" << 'EOF'
"""
${module} 模块
"""
EOF
    echo "✓ 创建 $module/__init__.py"
done

# ========== 创建最简单的脚本文件 ==========
# 点云处理脚本
cat > "$BASE_DIR/point_cloud_processing/scripts/ros-process-pointcloud" << 'EOF'
#!/usr/bin/env python3
print("点云处理工具")
EOF

# 物体检测脚本
cat > "$BASE_DIR/object_detection/scripts/ros-detect-objects" << 'EOF'
#!/usr/bin/env python3
print("物体检测工具")
EOF

# 深度图像处理脚本
cat > "$BASE_DIR/depth_image_processing/scripts/ros-process-depth-image" << 'EOF'
#!/usr/bin/env python3
print("深度图像处理工具")
EOF

# Octomap脚本
cat > "$BASE_DIR/octomap_integration/scripts/ros-generate-octomap" << 'EOF'
#!/usr/bin/env python3
print("Octomap生成工具")
EOF

# 传感器集成脚本
cat > "$BASE_DIR/sensor_integration/scripts/ros-manage-sensors" << 'EOF'
#!/usr/bin/env python3
print("传感器管理工具")
EOF

# 设置脚本可执行权限
chmod +x "$BASE_DIR"/*/scripts/* 2>/dev/null

echo "✓ 脚本文件创建完成"

# ========== 创建最简单的示例文件 ==========
for module in point_cloud_processing object_detection depth_image_processing octomap_integration sensor_integration; do
    cat > "$BASE_DIR/$module/examples/${module}_demo.py" << 'EOF'
#!/usr/bin/env python3
"""
${module} 示例
"""
print("${module} 示例程序")
EOF
    echo "✓ 创建 $module 示例文件"
done

# ========== 创建 README 文件 ==========
cat > "$BASE_DIR/README.md" << 'EOF'
# 感知模块

## 目录结构
