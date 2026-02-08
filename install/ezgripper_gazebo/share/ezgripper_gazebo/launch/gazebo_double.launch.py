import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch.event_handlers import OnProcessExit
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # 1. Get Package Paths
    pkg_ezgripper_description = get_package_share_directory('ezgripper_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # ========================================================================
    # STEP 0: FIX THE MESH PATHS (The "Export" Fix)
    # ========================================================================
    # Gazebo needs to know where the 'ezgripper_description' package lives.
    # We point GZ_SIM_RESOURCE_PATH to the parent folder of the package share.
    
    # This finds ".../install/ezgripper_description/share"
    install_share_path = pkg_ezgripper_description
    
    # We need to go one level up to include the folder CONTAINING the package
    # (So Gazebo can find "package://ezgripper_description")
    gz_resource_path = os.path.dirname(install_share_path)

    # If you have other models in ~/.gazebo/models, keep them too
    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        gz_resource_path += ':' + os.environ['GZ_SIM_RESOURCE_PATH']

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH', 
        value=gz_resource_path
    )
    # ========================================================================

    # 2. Load URDF (Double Mount Standalone)
    xacro_file = os.path.join(pkg_ezgripper_description, 'urdf', 'ezgripper_double_with_mount_standalone.urdf.xacro')
    
    robot_description_content = ParameterValue(
        Command(
            [PathJoinSubstitution([FindExecutable(name="xacro")]), " ", xacro_file]
        ),
        value_type=str
    )
    
    robot_description = {'robot_description': robot_description_content}

    # 3. Start Gazebo Harmonic
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 4. Spawn Robot
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'ezgripper_double',
            '-z', '0.1'
        ],
        output='screen',
    )

    # 5. Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    # 6. The Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        output='screen'
    )

    # 7. Spawn Controllers
    load_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    load_gripper1_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["ezgripper_controller1"], 
        output="screen",
    )

    load_gripper2_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["ezgripper_controller2"], 
        output="screen",
    )

    return LaunchDescription([
        set_gz_resource_path,  # <--- THIS APPLIES THE FIX
        gz_sim,
        node_robot_state_publisher,
        spawn_entity,
        bridge,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_jsb, load_gripper1_ctrl, load_gripper2_ctrl],
            )
        ),
    ])
