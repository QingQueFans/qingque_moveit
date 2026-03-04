cd ~/qingfu_moveit/moveit_core/planning_scene/collision_objects/scripts/
python3 ps-add-object --box --name "qingque" --position "0.5,0.2,0.4" --orientation "0,0,0.707,0.707" --yes


cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution/scripts/
python3 ros-start-execution --plan --cache --object-id "qingque"

cd ~/qingfu_moveit/moveit_ros/grasping/capability_servers/scripts
python3  ps-grab grab qingque --auto

cd ~/qingfu_moveit/moveit_ros/move_group/trajectory_execution/scripts/
python3 ros-start-execution --plan --cache --object-id "qing_fu"