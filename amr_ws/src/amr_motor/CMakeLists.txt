cmake_minimum_required(VERSION 3.8)
project(amr_motor)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# stm32_bridge akan diisi di Modul 2
# add_executable(stm32_bridge src/stm32_bridge.cpp)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
