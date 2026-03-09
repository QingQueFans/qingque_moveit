cmake_minimum_required(VERSION 3.8)
project(robot_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/GraspObject.srv"
  "srv/MoveToPose.srv"
  "srv/AddObject.srv"
  "srv/RemoveObject.srv"
  "srv/ListObjects.srv"
)

ament_package()