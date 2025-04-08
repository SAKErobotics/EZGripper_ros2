# EZGripper ROS2 Integration Guide

## Purpose and Scope

This document serves as a comprehensive reference for integrating the [EZGripper module](https://sakerobotics.com/) from SAKE Robotics into ROS2 systems. It is designed to be a structured resource that provides all the necessary information for both human developers and Large Language Models (LLMs) to successfully integrate and use the EZGripper.

The guide covers:

- Complete system architecture of the EZGripper ROS2 components
- Detailed naming conventions for joints, frames, and parameters
- Comprehensive interface specifications including topics, services, and action servers
- Launch file configurations for different gripper setups
- Step-by-step integration examples with code samples
- Troubleshooting common issues

Whether you're integrating the EZGripper into a new robot system, debugging an existing setup, or using an LLM to assist with development, this guide aims to provide all the necessary information in a clear, structured format that's easy to parse and understand.

## Table of Contents
- [System Architecture](#system-architecture)
- [Naming Conventions](#naming-conventions)
- [Interface Specifications](#interface-specifications)
- [Launch Files](#launch-files)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

## System Architecture

The EZGripper ROS2 system consists of the following main components:

1. **Hardware Driver**: Communicates with the physical gripper hardware via serial or TCP.
2. **Joint State Publisher**: Publishes the joint states for the gripper.
3. **Static TF Publisher**: Publishes static transforms for fixed joints.
4. **Robot State Publisher**: Converts joint states to TF transforms.
5. **Control Interface**: Provides action and topic interfaces for controlling the gripper.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Joint State    │    │  Static TF      │    │  Robot State    │
│  Publisher      │───►│  Publisher      │───►│  Publisher      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                                              │
        │                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│  Hardware       │                          │  TF Tree        │
│  Driver         │                          │  Visualization  │
└─────────────────┘                          └─────────────────┘
        ▲
        │
┌─────────────────┐
│  Control        │
│  Interface      │
└─────────────────┘
```

## Naming Conventions

### Joint Names

The EZGripper uses a consistent naming convention for joints:

```
{prefix}_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}
```

Where:
- `prefix`: Arm name (e.g., "left_arm", "right_arm") - uniquely identifies each gripper instance
- `unit_num`: Gripper unit number (e.g., "1", "2", "3" for triple gripper)
- `finger_num`: Finger number (e.g., "1", "2")

**Important Update for Triple Grippers**: Triple gripper configurations now use fixed unit numbers:
- Unit 1: Left gripper
- Unit 2: Center gripper
- Unit 3: Right gripper

This fixed numbering simplifies configuration and avoids conflicts. See the [Triple Gripper Guide](../ezgripper_description/TRIPLE_GRIPPER_GUIDE.md) for more details.

Example: `left_arm_1_ezgripper_knuckle_palm_L1_1`

### TF Frame Names

The TF frames follow a similar naming convention:

```
{prefix}_{unit_num}_ezgripper_{link_name}
```

Where:
- `prefix`: Arm name (e.g., "left_arm", "right_arm")
- `unit_num`: Gripper unit number (e.g., "1", "2", "3" for triple gripper)
- `link_name`: Link name (e.g., "palm_link", "finger_L1_1", "finger_L2_1", "finger_pad_1")

Example: `left_arm_1_ezgripper_palm_link`

## Interface Specifications

### Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/ezgripper/joint_states` | `sensor_msgs/JointState` | Joint states for all gripper joints |
| `/{prefix}_{unit_num}_ezgripper/command` | `std_msgs/Float64` | Command to control gripper position (0-100 range) |
| `/tf` | `tf2_msgs/TFMessage` | Dynamic transforms for actuated joints |
| `/tf_static` | `tf2_msgs/TFMessage` | Static transforms for fixed joints |

### Action Servers

| Action Server | Type | Description |
|---------------|------|-------------|
| `/{robot_ns}/{action_name}` | `control_msgs/GripperCommand` | Action server for controlling the gripper |

### Parameters

#### Joint Publisher Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | String | `"left_arm"` | Arm name prefix for the gripper assembly |
| `use_sim_time` | Boolean | `false` | Use simulation time |

#### Static TF Publisher Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | String | `"left_arm"` | Arm name prefix for the gripper assembly |
| `use_sim_time` | Boolean | `false` | Use simulation time |

#### Hardware Driver Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | String | `"/dev/ttyUSB0"` | Serial device or TCP endpoint |
| `baudrate` | Integer | `57600` | Baud rate for serial device |
| `no_of_grippers` | Integer | `1` | Number of grippers to control |
| `gripper_X.action_name` | String | `"gripper_cmd"` | Name of the action server |
| `gripper_X.servo_ids` | List | `[1]` | List of servo IDs to control |
| `gripper_X.module_type` | String | `"dual_gen2_single_mount"` | Type of gripper module |
| `gripper_X.robot_ns` | String | `"main"` | Robot namespace |

## Launch Files

### Single Gripper

```bash
ros2 launch ezgripper_description ezgripper_single_description.launch.py prefix:=left_arm unit_num:=1 rviz:=true
```

### Triple Gripper

```bash
ros2 launch ezgripper_description ezgripper_triple_description.launch.py prefix:=left_arm rviz:=true
```

### Hardware Control

```bash
ros2 launch ezgripper_driver joy.launch.py
```

## Integration Examples

### 1. Adding a Triple Gripper to a Robot Arm

```python
# In your robot's launch file
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the package directory
    ezgripper_pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Include the triple gripper launch file
    triple_gripper_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ezgripper_pkg_dir, 'launch', 'ezgripper_triple_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'prefix': 'left_arm',  # Adjust as needed
            'launch_joint_publisher': 'true',
            'launch_static_tf_publisher': 'true',
            'launch_robot_state_publisher': 'true'
        }.items()
    )
    
    return LaunchDescription([
        # Your robot's other components
        # ...
        
        # Add the triple gripper
        triple_gripper_include
    ])
```

### 2. Controlling the Gripper

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class GripperController(Node):
    def __init__(self):
        super().__init__('gripper_controller')
        
        # Create publishers for each gripper
        self.gripper1_pub = self.create_publisher(
            Float64, 'left_arm_1_ezgripper/command', 10)
        self.gripper2_pub = self.create_publisher(
            Float64, 'left_arm_2_ezgripper/command', 10)
        self.gripper3_pub = self.create_publisher(
            Float64, 'left_arm_3_ezgripper/command', 10)
    
    def open_all_grippers(self):
        # Open position (100 = fully open)
        msg = Float64()
        msg.data = 100.0
        
        self.gripper1_pub.publish(msg)
        self.gripper2_pub.publish(msg)
        self.gripper3_pub.publish(msg)
    
    def close_all_grippers(self):
        # Closed position (0 = fully closed)
        msg = Float64()
        msg.data = 0.0
        
        self.gripper1_pub.publish(msg)
        self.gripper2_pub.publish(msg)
        self.gripper3_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    controller = GripperController()
    
    # Example usage
    controller.open_all_grippers()
    rclpy.spin_once(controller, timeout_sec=1.0)
    
    controller.close_all_grippers()
    rclpy.spin_once(controller, timeout_sec=1.0)
    
    controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Troubleshooting

### Common Issues

1. **Fingers Not Attached to Palm (Visualization Issues)**
   - **Always specify a prefix parameter**: The prefix is crucial for proper joint naming
   - Verify that joint names in the URDF match exactly with those in the joint publisher
   - For triple grippers, ensure you're using the fixed unit numbers (1, 2, 3)
   - Check the TF tree using `ros2 run tf2_tools view_frames` to verify all frames are connected
   - Inspect the joint states topic (`ros2 topic echo /ezgripper/joint_states`) to confirm correct joint names

2. **Missing TF Connections**
   - Ensure the joint state publisher is publishing the correct joint names
   - Verify that the joint names in the URDF match the joint names published by the joint state publisher
   - Check that both the static TF publisher and robot state publisher are running

3. **Gripper Not Moving**
   - Verify that the correct servo IDs are configured
   - Check serial/TCP connection parameters
   - Ensure the hardware driver is receiving commands

4. **Multiple Grippers Not Working**
   - For triple grippers, ensure all three grippers have joint states published
   - Verify that each gripper has the correct unit number in its joint names (1, 2, 3 for triple configuration)
   - Make sure the prefix parameter is unique for each gripper instance

### Debugging Commands

```bash
# Check joint states
ros2 topic echo /ezgripper/joint_states

# View TF tree
ros2 run tf2_tools view_frames

# Check TF transforms
ros2 topic echo /tf
ros2 topic echo /tf_static

# List all nodes
ros2 node list

# List all topics
ros2 topic list

# Check node parameters
ros2 param list
```
