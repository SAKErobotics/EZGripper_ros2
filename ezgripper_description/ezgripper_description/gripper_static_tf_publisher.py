#!/usr/bin/env python3
"""Static TF Publisher for EZGripper
This node publishes static transforms for the EZGripper components that don't move.
For the underactuated EZGripper, only the palm to L1 joints are actuated.
The L1 to L2 joints and finger pad joints are fixed and published as static transforms.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster
import yaml
import os
import math
from ament_index_python.packages import get_package_share_directory

class GripperStaticTFPublisher(Node):
    def __init__(self):
        super().__init__('gripper_static_tf_publisher')
        
        # Create a static transform broadcaster
        self.static_broadcaster = StaticTransformBroadcaster(self)
        
        # Load the static transforms from the YAML configuration
        self.get_logger().info('Creating static transforms for EZGripper components')
        
        # Create static transforms for the EZGripper components
        self.create_static_transforms()
        
    def create_static_transforms(self):
        """Create static transforms for the EZGripper components"""
        # Create transforms for the single gripper
        self.create_finger_transforms('left')
        
        # Create transforms for the triple gripper
        for i in range(1, 4):
            self.create_finger_transforms(f'ezgripper_gripper{i}')
    
    def create_finger_transforms(self, prefix):
        """Create transforms for a gripper's fingers
        Note: For the underactuated EZGripper, only the palm to L1 joints are actuated.
        The L1 to L2 joints and finger pad joints are fixed and published as static transforms.
        """
        # The palm to L1 joints are actuated and handled by the joint_state_publisher
        # We only publish the fixed L1 to L2 and L2 to pad transforms
        
        # Create transform from finger L1_1 to finger L2_1 (fixed joint)
        self.publish_static_transform(
            parent_frame=f'{prefix}_ezgripper_finger_L1_1',
            child_frame=f'{prefix}_ezgripper_finger_L2_1',
            x=0.052, y=0.0, z=0.0,
            roll=0.0, pitch=0.0, yaw=0.0
        )
        
        # Create transform from finger L2_1 to finger pad 1 (fixed joint)
        self.publish_static_transform(
            parent_frame=f'{prefix}_ezgripper_finger_L2_1',
            child_frame=f'{prefix}_ezgripper_finger_pad_1',
            x=0.01849, y=0.0, z=0.0,
            roll=0.0, pitch=-0.23, yaw=0.0
        )
        
        # Create transform from finger L1_2 to finger L2_2 (fixed joint)
        self.publish_static_transform(
            parent_frame=f'{prefix}_ezgripper_finger_L1_2',
            child_frame=f'{prefix}_ezgripper_finger_L2_2',
            x=0.052, y=0.0, z=0.0,
            roll=0.0, pitch=0.0, yaw=0.0
        )
        
        # Create transform from finger L2_2 to finger pad 2 (fixed joint)
        self.publish_static_transform(
            parent_frame=f'{prefix}_ezgripper_finger_L2_2',
            child_frame=f'{prefix}_ezgripper_finger_pad_2',
            x=0.01849, y=0.0, z=0.0,
            roll=0.0, pitch=-0.23, yaw=0.0
        )
        
        self.get_logger().info(f'Created static transforms for {prefix} fingers')
        
    def publish_static_transform(self, parent_frame, child_frame, x, y, z, roll, pitch, yaw):
        """Publish a static transform
        
        Args:
            parent_frame: Parent frame ID
            child_frame: Child frame ID
            x, y, z: Translation
            roll, pitch, yaw: Rotation in radians
        """
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = parent_frame
        transform.child_frame_id = child_frame
        
        # Set translation
        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = z
        
        # Set rotation using quaternion
        # Simple conversion from Euler angles to quaternion
        # This is a simplified version, for more accuracy use tf_transformations
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        transform.transform.rotation.w = cy * cp * cr + sy * sp * sr
        transform.transform.rotation.x = cy * cp * sr - sy * sp * cr
        transform.transform.rotation.y = sy * cp * sr + cy * sp * cr
        transform.transform.rotation.z = sy * cp * cr - cy * sp * sr
        
        # Publish the transform
        self.static_broadcaster.sendTransform(transform)
        self.get_logger().info(f'Created static transform from {parent_frame} to {child_frame}')

def main(args=None):
    rclpy.init(args=args)
    node = GripperStaticTFPublisher()
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
