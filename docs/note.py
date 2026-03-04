import sys
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/collision_objects/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/core_functions/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_plugins/moveit_controller_manager/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/collision_detection/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/planning_scene/unified_tools/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/cache_manager/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/move_group/trajectory_execution/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_core/kinematics/inverse_kinematics/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/grasping/capability_servers/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_planners/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/perception/object_detection/src')
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit/moveit_ros/grasping/grasp_execution/src')
from ps_objects.object_manager import(
    create_box,
    add_object
)
result = create_box("my_box", 0.5, 0.3, 0.4)
from kin_ik.ik_solver import solve_ik
from trajectory_execution.trajectory_execution_manager import execute_trajectory
execute_trajectory("my_box")