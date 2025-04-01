#!/usr/bin/env python3
"""
Spawn Triple EZGripper - Description Component
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent, GroupAction
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
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
    
    # Include gripper joint publisher launch file
    joint_publisher_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'gripper_joint_publisher.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'output_topic': '/gripper_joint_states'
        }.items(),
        condition=IfCondition(LaunchConfiguration('launch_joint_publisher'))
    )
    
    # Include gripper static TF publisher launch file
    static_tf_publisher_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'gripper_static_tf_publisher.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace')
        }.items(),
        condition=IfCondition(LaunchConfiguration('launch_static_tf_publisher'))
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
                'robot_description': Command(['xacro', ' ', urdf_file])
            }
        ],
        remappings=[
            ('/joint_states', '/gripper_joint_states')
        ],
        condition=IfCondition(LaunchConfiguration('launch_robot_state_publisher'))
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
    
    # Joint state merger node (only needed for triple gripper setup)
    joint_state_merger = Node(
        package='ezgripper_description',
        executable='ezgripper_joint_merger.py',
        name='ezgripper_joint_merger',
        namespace=LaunchConfiguration('namespace'),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        remappings=[
            ('/ezgripper/joint_states', '/gripper_joint_states'),
            ('/joint_states', '/robot_joint_states'),
            ('/merged_joint_states', '/joint_states')
        ],
        output='screen',
        # Add environment variables to help with parameter handling
        additional_env={'PYTHONUNBUFFERED': '1'}
    )
    
    # Event handler for joint state merger
    joint_state_merger_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_merger,
            on_exit=[
                LogInfo(msg=['Joint state merger exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Joint state merger exited'))
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        launch_joint_publisher_arg,
        launch_robot_state_publisher_arg,
        launch_static_tf_publisher_arg,
        
        # Included launch files
        joint_publisher_include,
        static_tf_publisher_include,
        
        # Nodes
        robot_state_publisher,
        joint_state_merger,
        
        # Event handlers
        robot_state_publisher_exit_handler,
        joint_state_merger_exit_handler
    ])
