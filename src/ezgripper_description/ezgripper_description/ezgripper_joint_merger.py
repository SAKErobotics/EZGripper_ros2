#!/usr/bin/env python3
"""
EZGripper Joint State Merger Node
Merges gripper joint states with the main robot joint states
Following the Linorobot2 architecture guidelines
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import numpy as np
import yaml
import os
from ament_index_python.packages import get_package_share_directory

class EzgripperJointMerger(Node):
    def __init__(self):
        super().__init__('ezgripper_joint_merger')
        
        # Declare parameters
        # Check if parameter exists before declaring it to avoid ParameterAlreadyDeclaredException
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)
        
        # Load component configuration to get the correct topic names
        pkg_share = get_package_share_directory('ezgripper_description')
        components_yaml_path = os.path.join(pkg_share, 'config', 'robot_components.yaml')
        
        try:
            with open(components_yaml_path, 'r') as file:
                component_config = yaml.safe_load(file)
            
            # Get the ezgripper component configuration
            ezgripper_config = component_config['components']['ezgripper']
            gripper_joint_states_topic = ezgripper_config.get('joint_states_topic', '/ezgripper/joint_states')
            self.get_logger().info(f'Using joint states topic from config: {gripper_joint_states_topic}')
        except Exception as e:
            self.get_logger().warn(f'Failed to load component configuration: {str(e)}')
            self.get_logger().warn(f'Using default topic names')
            gripper_joint_states_topic = '/ezgripper/joint_states'
        
        # Get remapping from parameters if available
        robot_joint_states_topic = '/robot_joint_states'
        merged_joint_states_topic = '/joint_states'
        
        self.get_logger().info(f'Subscribing to gripper joint states: {gripper_joint_states_topic}')
        self.get_logger().info(f'Subscribing to robot joint states: {robot_joint_states_topic}')
        self.get_logger().info(f'Publishing merged joint states to: {merged_joint_states_topic}')
        
        # Create subscribers for both joint state topics
        self.gripper_sub = self.create_subscription(
            JointState,
            gripper_joint_states_topic,
            self.gripper_callback,
            10
        )
        
        self.robot_sub = self.create_subscription(
            JointState,
            robot_joint_states_topic,
            self.robot_callback,
            10
        )
        
        # Create publisher for merged joint states
        self.merged_pub = self.create_publisher(
            JointState,
            merged_joint_states_topic,
            10
        )
        
        self.gripper_state = None
        self.robot_state = None
        
    def gripper_callback(self, msg):
        self.gripper_state = msg
        self.merge_states()
        
    def robot_callback(self, msg):
        self.robot_state = msg
        self.merge_states()
        
    def merge_states(self):
        if self.gripper_state and self.robot_state:
            # Create new merged message
            merged_msg = JointState()
            
            # Merge time and frame_id
            merged_msg.header.stamp = self.get_clock().now().to_msg()
            merged_msg.header.frame_id = self.robot_state.header.frame_id
            
            # Merge names
            merged_msg.name = self.robot_state.name + self.gripper_state.name
            
            # Merge positions
            merged_msg.position = list(self.robot_state.position) + list(self.gripper_state.position)
            
            # Merge velocities if available
            if self.robot_state.velocity and self.gripper_state.velocity:
                merged_msg.velocity = list(self.robot_state.velocity) + list(self.gripper_state.velocity)
            
            # Merge efforts if available
            if self.robot_state.effort and self.gripper_state.effort:
                merged_msg.effort = list(self.robot_state.effort) + list(self.gripper_state.effort)
            
            # Publish merged state
            self.merged_pub.publish(merged_msg)

def main(args=None):
    rclpy.init(args=args)
    node = EzgripperJointMerger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception as e:
            # Ignore shutdown errors - this happens when shutdown is called multiple times
            # or when the context is already shutting down
            pass

if __name__ == '__main__':
    main()

# Updated to match SCARA arm conventions
# - Renamed class to EzgripperJointMerger
# - Updated node name to ezgripper_joint_merger
# - Maintained consistent topic naming
# - Kept same functionality but with better naming conventions
