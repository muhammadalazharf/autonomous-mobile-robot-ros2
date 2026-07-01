cmake_minimum_required(VERSION 3.8)
project(amr_motor)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(stm32_bridge src/stm32_bridge.cpp)
ament_target_dependencies(stm32_bridge
  rclcpp std_msgs geometry_msgs sensor_msgs)

install(TARGETS stm32_bridge
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME})

ament_package()
