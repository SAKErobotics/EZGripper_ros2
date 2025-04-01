cmake_minimum_required(VERSION 3.5)
project(ezgripper_description)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Install directories
install(
  DIRECTORY 
    urdf 
    meshes 
    rviz 
    launch
    config
  DESTINATION share/${PROJECT_NAME}
)

# Auto-detect and install Python executables from both scripts/ and package directories
file(GLOB PYTHON_SCRIPTS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.py")
file(GLOB PYTHON_PACKAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME}/*.py")

# Create a list of all Python files from both locations
set(ALL_PYTHON_FILES ${PYTHON_SCRIPTS_DIR} ${PYTHON_PACKAGE_DIR})

# Iterate over each Python file and install them as executables
foreach(python_file ${ALL_PYTHON_FILES})
    get_filename_component(script_name ${python_file} NAME_WE)
    install(PROGRAMS
        ${python_file}
        DESTINATION lib/${PROJECT_NAME}
        RENAME ${script_name}
    )
endforeach()

# Install scripts directory
install(
  DIRECTORY scripts/
  DESTINATION lib/${PROJECT_NAME}
  FILES_MATCHING PATTERN "*.py"
  PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)

# No longer using ament_python_install_package since we removed setup.py

# Make sure the scripts are executable
install(
  PROGRAMS 
    scripts/ezgripper_joint_merger.py
    ${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME}/gripper_joint_publisher.py
    ${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME}/ezgripper_joint_merger.py
    ${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME}/gripper_static_tf_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
