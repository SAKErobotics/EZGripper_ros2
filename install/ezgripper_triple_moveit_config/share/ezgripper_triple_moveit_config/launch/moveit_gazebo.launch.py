import os
import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    
    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError: 
        return None

def generate_launch_description():
    # 1. Load Base MoveIt Config (with OMPL)
    moveit_config = (
        MoveItConfigsBuilder("ezgripper_triple_mount_instantiation", package_name="ezgripper_triple_moveit_config")
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    # 2. Manually Load Cartesian Limits (Fix for Pilz crash)
    cartesian_limits_content = load_yaml("ezgripper_triple_moveit_config", "config/pilz_cartesian_limits.yaml")
    robot_description_planning = {
        "robot_description_planning": cartesian_limits_content
    }

    # 3. Manually Load Controllers (Fix for "0 controllers found") <--- NEW FIX
    moveit_controllers = load_yaml("ezgripper_triple_moveit_config", "config/moveit_controllers.yaml")

    ld = LaunchDescription()

    # 4. FORCE Sim Time
    ld.add_action(DeclareLaunchArgument("use_sim_time", default_value="true"))

    # 5. Move Group Node
    ld.add_action(Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.trajectory_execution,
            moveit_config.planning_scene_monitor,
            moveit_config.joint_limits,
            robot_description_planning, # Cartesian limits
            moveit_controllers,         # <--- INJECT CONTROLLERS HERE
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    ))

    # 6. RViz Node
    rviz_config_file = PathJoinSubstitution([
        FindPackageShare("ezgripper_triple_moveit_config"),
        "config",
        "moveit.rviz",
    ])

    ld.add_action(Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    ))

    return ld
