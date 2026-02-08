#!/usr/bin/env python3
"""
EZGripper Joint State Merger Node
Merges gripper joint states with the main robot joint states
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import numpy as np

class EzgripperJointMerger(Node):
    def __init__(self):
        super().__init__('ezgripper_joint_merger')
        
        # Create subscribers for both joint state topics
        self.gripper_sub = self.create_subscription(
            JointState,
            '/gripper_joint_states',
            self.gripper_callback,
            10
        )
        
        self.robot_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.robot_callback,
            10
        )
        
        # Create publisher for merged joint states
        self.merged_pub = self.create_publisher(
            JointState,
            '/merged_joint_states',
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
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

# Updated to match SCARA arm conventions
# - Renamed class to EzgripperJointMerger
# - Updated node name to ezgripper_joint_merger
# - Maintained consistent topic naming
# - Kept same functionality but with better naming conventions
