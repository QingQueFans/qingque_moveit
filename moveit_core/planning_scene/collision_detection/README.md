# 1. 检查碰撞
python3 ps-check-collision --objects "box1" "box2"
python3 ps-check-collision --all

# 2. 检查自碰撞
python3 ps-check-self-collision "robot_arm"

# 3. 计算距离
python3 ps-compute-distance --objects "box1" "sphere1"
python3 ps-compute-distance --nearest "target" --count 3
python3 ps-compute-distance --nearest "x1" --count 3

# 4. 分析接触
python3 ps-get-contacts --objects "gripper" "object"
python3 ps-get-contacts --grasp "gripper" "target"

# 5. 运行演示
python3 collision_checking_demo.py
python3 distance_computation.py