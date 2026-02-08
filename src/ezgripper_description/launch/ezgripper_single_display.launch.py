#!/usr/bin/env python3
"""
Spawn Single EZGripper in RViz - Top Level Launch File
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    """
    Launch Function for Single EZGripper Display
    """
    # Get package directories
    pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time: "true" or "false"'
    )
    
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value='urdf.rviz',
        description="RViz configuration file"
    )
    
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='ezgripper',
        description='Namespace for the gripper'
    )
    
    # Start RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', [os.path.join(pkg_dir, 'rviz/'), LaunchConfiguration("rviz_config")]],
    )
    
    # Include the description launch file
    gripper_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_single_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'launch_joint_publisher': 'true',
            'launch_robot_state_publisher': 'true'
        }.items(),
    )
    
    # Add event handler for proper cleanup when RViz exits
    rviz_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                LogInfo(msg=['RViz exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='RViz exited'))
            ]
        )
    )
    
    # Add shutdown handler
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Launch shutting down'])
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        rviz_config_arg,
        namespace_arg,
        
        # Nodes
        rviz_node,
        
        # Included launch files
        gripper_description,
        
        # Event handlers
        rviz_exit_handler,
        shutdown_handler
    ])
