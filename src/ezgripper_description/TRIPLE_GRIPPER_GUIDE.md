# EZGripper Triple Configuration Guide

## Overview

This document provides detailed information about the triple EZGripper configuration, including the fixed unit numbering system, joint naming conventions, and troubleshooting tips for common issues.

## Fixed Unit Numbering

The triple EZGripper configuration uses fixed unit numbers (1, 2, 3) for the left, center, and right grippers respectively. This simplifies configuration and avoids conflicts when multiple grippers are used in the same robot.

### Key Points:

- Unit 1: Left gripper
- Unit 2: Center gripper
- Unit 3: Right gripper

## Joint Naming Convention

Joint names follow this pattern:
```
{prefix}_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}
```

Where:
- `prefix`: Uniquely identifies the gripper instance (e.g., "left_arm", "right_arm")
- `unit_num`: Fixed unit number (1, 2, or 3)
- `finger_num`: Finger identifier (1 or 2)

Example: `left_arm_1_ezgripper_knuckle_palm_L1_1`

## Important Configuration Requirements

1. **Always specify a prefix parameter**: 
   - The prefix parameter is crucial for proper joint naming and control
   - If not specified, a default prefix "default" will be used, but this may cause issues in multi-gripper setups
   - The prefix should uniquely identify each gripper instance in your robot

2. **Controller Configuration**:
   - Joint names in the controller configuration must match the URDF joint names
   - The controller configuration is located at `ezgripper_description/config/ezgripper_controllers.yaml`

## Common Issues and Solutions

### Fingers Not Attached to Palm

If the fingers appear detached from the palm in visualization:

1. **Check Joint Names**:
   - Ensure the joint names in the URDF match the names expected by the joint publisher
   - Verify that the prefix and unit numbers are consistent across all files

2. **Verify Joint Publisher Output**:
   - Check that the joint publisher is correctly mapping the joint names
   - Look for any warnings about empty prefixes or mismatched joint names

3. **Inspect TF Tree**:
   - Use `ros2 run tf2_tools view_frames` to visualize the TF tree
   - Verify that all the necessary frames are being published

4. **Parameter Consistency**:
   - Ensure the same prefix is used across all launch files and nodes
   - Confirm that the fixed unit numbers (1, 2, 3) are correctly specified in the URDF

## Launch File Usage

To launch the triple gripper with proper configuration:

```bash
# Launch with a specific prefix (recommended)
ros2 launch ezgripper_description ezgripper_triple_standalone.launch.py prefix:=my_robot

# Check the joint states being published
ros2 topic echo /ezgripper/joint_states
```

## Integration with Robot Systems

When integrating the triple gripper with your robot:

1. Include the triple gripper description in your robot's launch file
2. Provide a unique prefix that identifies this gripper instance
3. Use the fixed unit numbers (1, 2, 3) for the triple configuration
4. Subscribe to the appropriate command topics for controlling each gripper:
   - `{prefix}_1_ezgripper/command` (left gripper)
   - `{prefix}_2_ezgripper/command` (center gripper)
   - `{prefix}_3_ezgripper/command` (right gripper)
