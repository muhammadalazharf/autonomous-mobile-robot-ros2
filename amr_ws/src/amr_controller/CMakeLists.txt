cmake_minimum_required(VERSION 3.8)
project(amr_controller)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(stm32_bridge src/stm32_bridge.cpp)

ament_target_dependencies(stm32_bridge
  rclcpp
  geometry_msgs
  sensor_msgs
)

install(TARGETS
  stm32_bridge
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()