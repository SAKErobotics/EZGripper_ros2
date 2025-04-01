#!/usr/bin/env python3
"""
EZGripper Integration - Launch File for Integration with Other Components
This launch file is designed to integrate the EZGripper with other robot components
following the Linorobot2 architecture guidelines.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('ezgripper_description')
    
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
    
    launch_static_tf_publisher_arg = DeclareLaunchArgument(
        'launch_static_tf_publisher',
        default_value='true',
        description='Whether to launch the static TF publisher'
    )
    
    launch_robot_state_publisher_arg = DeclareLaunchArgument(
        'launch_robot_state_publisher',
        default_value='false',
        description='Whether to launch robot state publisher (should be false when integrated)'
    )
    
    # Include the base component launch file
    component_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'launch_joint_publisher': LaunchConfiguration('launch_joint_publisher'),
            'launch_static_tf_publisher': LaunchConfiguration('launch_static_tf_publisher')
        }.items()
    )
    
    # Joint state merger node for integration
    joint_state_merger = Node(
        package='ezgripper_description',
        executable='ezgripper_joint_merger.py',
        name='ezgripper_joint_merger',
        namespace=LaunchConfiguration('namespace'),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        remappings=[
            ('/ezgripper/joint_states', '/ezgripper/joint_states'),
            ('/joint_states', '/robot_joint_states'),
            ('/merged_joint_states', '/joint_states')
        ],
        output='screen'
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
        launch_static_tf_publisher_arg,
        launch_robot_state_publisher_arg,
        
        # Include component launch
        component_launch,
        
        # Nodes
        joint_state_merger,
        
        # Event handlers
        joint_state_merger_exit_handler
    ])
