#!/usr/bin/env python3
"""
Spawn Single EZGripper in RViz - Fixed version without joint_state_publisher_gui
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown

def generate_launch_description():
    """
    Launch Function
    """
    pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value='urdf.rviz',
        description="RViz configuration file"
    )
    
    # Start RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', [os.path.join(pkg_dir, 'rviz/'), LaunchConfiguration("rviz_config")]],
    )
    
    # Include the fixed description launch file
    gripper_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_single_description_fixed.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )
    
    # Add event handler for proper cleanup when RViz exits
    rviz_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                Node(
                    package='ros2cli',
                    executable='ros2',
                    output='screen',
                    arguments=['topic', 'echo', '--once', '/joint_states'],
                ),
            ]
        )
    )
    
    # Add shutdown handler
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                Node(
                    package='ros2cli',
                    executable='ros2',
                    output='screen',
                    arguments=['topic', 'echo', '--once', '/joint_states'],
                ),
            ]
        )
    )
    
    return LaunchDescription([
        use_sim_time_arg,
        rviz_config_arg,
        rviz_node,
        gripper_description,
        rviz_exit_handler,
        shutdown_handler
    ])
