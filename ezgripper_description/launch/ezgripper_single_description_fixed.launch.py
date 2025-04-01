#!/usr/bin/env python3
"""
Spawn Single EZGripper in RViz - Fixed version without joint_state_publisher_gui
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch_ros.actions import Node, PushRosNamespace
from launch.conditions import UnlessCondition
from launch.substitutions import LaunchConfiguration, Command
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('ezgripper_description')

    # Path to the URDF file
    urdf_file = os.path.join(pkg_dir, 'urdf', 'ezgripper_single_with_mount_standalone.urdf.xacro')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'namespace',
            default_value='ezgripper',
            description='Namespace for the gripper'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time: "true" or "false"'
        ),

        # Group actions under the namespace
        GroupAction([
            PushRosNamespace(LaunchConfiguration('namespace')),

            # Custom joint state publisher for gripper
            Node(
                package='ezgripper_description',
                executable='gripper_joint_publisher.py',
                name='gripper_joint_publisher',
                parameters=[
                    {'use_sim_time': LaunchConfiguration('use_sim_time')}
                ],
                remappings=[
                    ('/joint_states', '/gripper_joint_states')
                ],
                output='screen'
            ),

            # Joint state merger node
            Node(
                package='ezgripper_description',
                executable='ezgripper_joint_merger.py',
                name='ezgripper_joint_merger',
                parameters=[
                    {'use_sim_time': LaunchConfiguration('use_sim_time')}
                ],
                remappings=[
                    ('/ezgripper/joint_states', '/gripper_joint_states'),
                    ('/joint_states', '/robot_joint_states'),
                    ('/merged_joint_states', '/joint_states')
                ],
                output='screen'
            ),
            
            # Static TF publisher for fixed joints in the gripper
            Node(
                package='linorobot2_description',
                executable='gripper_static_tf_publisher',
                name='gripper_static_tf_publisher',
                parameters=[
                    {'use_sim_time': LaunchConfiguration('use_sim_time')}
                ],
                output='screen'
            ),

            # Robot state publisher
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='ezgripper_robot_state_publisher',
                parameters=[
                    {
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                        'robot_description': Command(['xacro', ' ', urdf_file])
                    }
                ],
                output='screen',
                condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
            )
        ])
    ])
