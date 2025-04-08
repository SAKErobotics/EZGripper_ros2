#!/usr/bin/env python3
"""
Spawn Triple EZGripper - Description Component
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent, GroupAction
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PythonExpression
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.descriptions import ParameterValue as PV
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node, PushRosNamespace
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Path to the URDF file
    urdf_file = os.path.join(pkg_dir, 'urdf', 'ezgripper_triple_with_mount_standalone.urdf.xacro')
    
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time: "true" or "false"'
    )
    
    enable_hardware_arg = DeclareLaunchArgument(
        'enable_hardware',
        default_value='false',
        description='Enable hardware: "true" or "false"'
    )
    
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='ezgripper',
        description='Namespace for the gripper'
    )
    
    launch_joint_publisher_arg = DeclareLaunchArgument(
        'launch_joint_publisher',
        default_value='true',
        description='Whether to launch the gripper joint publisher'
    )
    
    launch_robot_state_publisher_arg = DeclareLaunchArgument(
        'launch_robot_state_publisher',
        default_value='true',
        description='Whether to launch robot state publisher'
    )
    
    launch_static_tf_publisher_arg = DeclareLaunchArgument(
        'launch_static_tf_publisher',
        default_value='true',
        description='Whether to launch the static TF publisher'
    )
    
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Whether to launch RViz'
    )
    
    # We don't need the single joint publisher for triple gripper
    # We'll use only the triple joint publisher below
    
    # For a triple gripper, we need a special joint publisher that can handle all three grippers
    # We'll use a modified version of the joint publisher with fixed unit numbers (1,2,3)
    joint_publisher_triple = Node(
        package='ezgripper_description',
        executable='gripper_joint_publisher',
        name='gripper_joint_publisher',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'prefix': LaunchConfiguration('prefix'),
                # Use fixed unit numbers 1,2,3 for the triple gripper
                'unit_nums_str': '1,2,3',
            }
        ],
        remappings=[
            ('/joint_states', '/ezgripper/joint_states')
        ],
        condition=IfCondition(LaunchConfiguration('launch_joint_publisher'))
    )
    
    # Include gripper static TF publisher launch file
    static_tf_publisher_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'gripper_static_tf_publisher.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'prefix': LaunchConfiguration('prefix')  # CRITICAL: This must be passed correctly as empty string when needed
        }.items(),
        condition=IfCondition(LaunchConfiguration('launch_static_tf_publisher'))
    )
    
    # Legacy unit number parameter (kept for backward compatibility)
    unit_num_arg = DeclareLaunchArgument(
        'unit_num',
        default_value='1',
        description='Legacy parameter - kept for backward compatibility'
    )
    
    # Add a prefix argument
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='gripper',
        description='Arm name for the gripper assembly (e.g., left_arm, right_arm)'
    )
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=LaunchConfiguration('namespace'),
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': ParameterValue(
                    Command(['xacro', ' ', urdf_file, 
                            ' unit_num:=', LaunchConfiguration('unit_num'),
                            ' prefix:=', LaunchConfiguration('prefix')]),
                    value_type=str),
                'publish_frequency': 50.0,
                'ignore_timestamp': True
            }
        ],
        # Use the joint states directly from the joint publisher
        remappings=[
            ('/joint_states', '/ezgripper/joint_states')
        ],
        condition=IfCondition(LaunchConfiguration('launch_robot_state_publisher'))
    )
    
    # Define RViz configuration path
    rviz_config_path = os.path.join(get_package_share_directory('ezgripper_description'), 'rviz', 'urdf.rviz')
    
    # Create RViz node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )
    
    # Event handler for robot state publisher
    robot_state_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=robot_state_publisher,
            on_exit=[
                LogInfo(msg=['Robot state publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Robot state publisher exited'))
            ]
        )
    )
    
    # Event handler for RViz
    rviz_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                LogInfo(msg=['RViz exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='RViz exited'))
            ]
        ),
        condition=IfCondition(LaunchConfiguration('rviz'))
    )
    
    # Global shutdown handler to ensure all processes are terminated
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Shutting down EZGripper Triple description']),
                # Execute a cleanup command to kill any lingering processes
                Node(
                    package='ezgripper_description',
                    executable='cleanup_ezgripper_processes.py',
                    name='cleanup_ezgripper_processes',
                    output='screen'
                )
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        enable_hardware_arg,
        namespace_arg,
        launch_joint_publisher_arg,
        launch_robot_state_publisher_arg,
        launch_static_tf_publisher_arg,
        rviz_arg,
        unit_num_arg,
        prefix_arg,
        
        # Included launch files
        joint_publisher_triple,   # Use only the triple gripper joint publisher
        static_tf_publisher_include,
        
        # Nodes
        robot_state_publisher,
        
        # RViz visualization
        rviz_node,
        
        # Event handlers
        robot_state_publisher_exit_handler,
        rviz_exit_handler,
        shutdown_handler
    ])
