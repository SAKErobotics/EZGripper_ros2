#!/usr/bin/env python3
"""
EZGripper Joint Position Publisher
Publishes joint positions for the EZGripper based on arm_name and unit_num identification
"""
import os
import re
import yaml
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState
from ament_index_python.packages import get_package_share_directory

class GripperJointPublisher(Node):
    def __init__(self):
        super().__init__('gripper_joint_publisher')
        
        # Check for prefix parameter
        self.declare_parameter('prefix', '')
        
        # Check for unit_num parameter (for backward compatibility)
        self.declare_parameter('unit_num', '1')
        
        # Get the prefix parameter
        self.prefix = self.get_parameter('prefix').value
        
        # Get the unit_num parameter
        unit_num = self.get_parameter('unit_num').value
        
        # For triple gripper, we'll use a comma-separated string for unit numbers
        self.declare_parameter('unit_nums_str', '')
        unit_nums_str = self.get_parameter('unit_nums_str').value
        
        # Process unit numbers
        if unit_nums_str:
            # Split the comma-separated string into a list of unit numbers
            self.unit_nums = unit_nums_str.split(',')
            self.get_logger().info(f'Using multiple unit_nums: {self.unit_nums}')
        else:
            # Use the single unit_num for backward compatibility
            self.unit_nums = [unit_num]
            self.get_logger().info(f'Using single unit_num: {unit_num}')
            
        # For triple gripper, if we have exactly 3 unit numbers, assume they are the fixed 1,2,3
        if len(self.unit_nums) == 3 and unit_nums_str == '1,2,3':
            self.get_logger().info('Detected triple gripper with fixed unit numbers (1,2,3)')
        
        # Log warning if prefix is empty
        if not self.prefix:
            self.get_logger().warn('Prefix parameter is empty! This will cause incorrect joint naming.')
            self.get_logger().warn('Please specify a prefix (arm name) when launching the node.')
            # Use a default prefix to avoid frames starting with underscore
            self.prefix = 'default'
            self.get_logger().warn(f'Using "{self.prefix}" as default prefix')
        else:
            self.get_logger().info(f'Using prefix: {self.prefix}')
        
        # Load controller configuration to get joint names
        pkg_share = get_package_share_directory('ezgripper_description')
        controllers_yaml_path = os.path.join(pkg_share, 'config', 'ezgripper_controllers.yaml')
        
        self.get_logger().info(f'Loading controller configuration from {controllers_yaml_path}')
        with open(controllers_yaml_path, 'r') as file:
            controller_config = yaml.safe_load(file)

        # Extract joint names from configuration
        joint_names = []
        for controller, params in controller_config.items():
            if 'ros__parameters' in params and 'joint' in params['ros__parameters']:
                joint_name = params['ros__parameters']['joint']
                joint_names.append(joint_name)
                self.get_logger().info(f'Found joint from controller config: {joint_name}')
        
        # Create empty lists for the new joint names and positions
        new_joint_names = []
        new_joint_positions = []
        new_joint_velocities = []
        new_joint_efforts = []
        
        # Publisher for the joint states
        self.publisher = self.create_publisher(JointState, '/ezgripper/joint_states', 10)
        self.get_logger().info('Publisher created for /ezgripper/joint_states')

        # Create a dictionary to map joint names to their respective indexes
        self.joint_indexes = {name: i for i, name in enumerate(new_joint_names)}
        
        # Group joints by gripper (prefix + unit_num)
        self.grippers = set()  # Set of (prefix, unit_num) tuples
        self.gripper_to_joints = {}
        
        # Regular expression to extract components
        # Format: arm_name_unit_num_ezgripper_knuckle_palm_L1_finger_num
        # Example: left_arm_1_ezgripper_knuckle_palm_L1_1 (left arm, gripper 1, finger 1)
        pattern = r'([^_]+)_([^_]+)_ezgripper_knuckle_palm_L1_([^_]+)'
        
        # Alternative pattern for backward compatibility (no unit number)
        # Format: arm_name_ezgripper_knuckle_palm_L1_finger_num
        alt_pattern = r'([^_]+)_ezgripper_knuckle_palm_L1_([^_]+)'
        
        # Create a mapping from controller joint names to actual joint names with the correct prefix
        self.controller_to_actual_joint = {}
        
        # Create new joint names using the correct prefix
        new_joint_names = []
        new_joint_positions = []
        new_joint_velocities = []
        new_joint_efforts = []
        
        for joint_name in joint_names:
            # Try the main pattern first (with unit_num)
            match = re.match(pattern, joint_name)
            if match:
                original_arm_name = match.group(1)  # e.g., 'left_arm'
                unit_num = match.group(2)   # e.g., '1'
                finger_num = match.group(3) # e.g., '1' or '2' (finger identifier)
                
                # Create a new joint name with the correct prefix to match the URDF
                # Format should be: {prefix}_ezgripper_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}
                new_joint_name = f'{self.prefix}_ezgripper_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}'
                
                # Map the original joint name to the new joint name
                self.controller_to_actual_joint[joint_name] = new_joint_name
                
                # Add the new joint name to our lists
                new_joint_names.append(new_joint_name)
                new_joint_positions.append(0.0)
                new_joint_velocities.append(0.0)
                new_joint_efforts.append(0.0)
                
                # Create a unique gripper identifier using the prefix
                gripper_id = (self.prefix, unit_num)
                self.grippers.add(gripper_id)
                
                if gripper_id not in self.gripper_to_joints:
                    self.gripper_to_joints[gripper_id] = []
                
                self.gripper_to_joints[gripper_id].append(new_joint_name)
                self.get_logger().info(f'Added joint {new_joint_name} to gripper {gripper_id}')
            else:
                # Try the alternative pattern (without unit_num)
                match = re.match(alt_pattern, joint_name)
                if match:
                    original_arm_name = match.group(1)  # e.g., 'left_arm'
                    finger_num = match.group(2) # e.g., '1' or '2' (finger identifier)
                    
                    # For backward compatibility, use '1' as default unit_num
                    unit_num = '1'
                    
                    # Create a new joint name with the correct prefix to match the URDF
                    # Format should be: {prefix}_ezgripper_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}
                    new_joint_name = f'{self.prefix}_ezgripper_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}'
                    
                    # Map the original joint name to the new joint name
                    self.controller_to_actual_joint[joint_name] = new_joint_name
                    
                    # Add the new joint name to our lists
                    new_joint_names.append(new_joint_name)
                    new_joint_positions.append(0.0)
                    new_joint_velocities.append(0.0)
                    new_joint_efforts.append(0.0)
                    
                    # Create a unique gripper identifier using the prefix
                    gripper_id = (self.prefix, unit_num)
                    self.grippers.add(gripper_id)
                    
                    if gripper_id not in self.gripper_to_joints:
                        self.gripper_to_joints[gripper_id] = []
                    
                    self.gripper_to_joints[gripper_id].append(new_joint_name)
                    self.get_logger().info(f'Added joint {new_joint_name} to gripper {gripper_id} (using default unit_num)')
        
        # For a triple gripper setup, we need to ensure all three grippers have joint states
        # Check if we're in a triple gripper setup (based on the presence of unit_num=1)
        is_triple_gripper = any(unit_num == '1' for _, unit_num in self.grippers)
        
        # If this is a triple gripper, ensure we have joint states for all three grippers
        if is_triple_gripper:
            # Add joint states for grippers 2 and 3 if they don't exist
            for unit_num in ['2', '3']:
                gripper_id = (self.prefix, unit_num)
                if gripper_id not in self.gripper_to_joints:
                    # Create joint names for this gripper
                    for finger_num in ['1', '2']:
                        new_joint_name = f'{self.prefix}_ezgripper_{unit_num}_ezgripper_knuckle_palm_L1_{finger_num}'
                        if new_joint_name not in new_joint_names:
                            new_joint_names.append(new_joint_name)
                            new_joint_positions.append(0.0)
                            new_joint_velocities.append(0.0)
                            new_joint_efforts.append(0.0)
                            self.joint_indexes[new_joint_name] = len(new_joint_names) - 1
                            
                            # Add to gripper_to_joints mapping
                            if gripper_id not in self.gripper_to_joints:
                                self.gripper_to_joints[gripper_id] = []
                            self.gripper_to_joints[gripper_id].append(new_joint_name)
                            self.get_logger().info(f'Added joint {new_joint_name} for triple gripper setup')
        
        # Initialize joint state message with the new joint names
        self.joint_state = JointState()
        self.joint_state.name = new_joint_names
        self.joint_state.position = new_joint_positions
        self.joint_state.velocity = new_joint_velocities
        self.joint_state.effort = new_joint_efforts
        
        # Check if we have any grippers with empty prefixes and warn about it
        for gripper_id in list(self.grippers):
            prefix, unit_num = gripper_id
            if not prefix or prefix == '_':
                self.get_logger().warn(f'Found gripper with empty prefix: {gripper_id}')
                self.get_logger().warn('This will cause incorrect joint naming and control issues.')
                self.get_logger().warn('Please specify a prefix (arm name) when launching the node.')
        
        # Create one subscriber per gripper (prefix + unit_num)
        self.subscribers = []
        for gripper_id in self.gripper_to_joints:
            prefix, unit_num = gripper_id
            
            # Get all finger joints for this gripper
            finger_joints = self.gripper_to_joints[gripper_id]
            
            if finger_joints:
                # Topic name uses prefix and unit_num
                topic_name = f'{prefix}_{unit_num}_ezgripper/command'
                self.subscribers.append(
                    self.create_subscription(Float64, topic_name, 
                                            self.create_callback(gripper_id, finger_joints), 10)
                )
                self.get_logger().info(f'Created subscriber for {topic_name} controlling {finger_joints}')
        
        # Timer to publish joint states
        publish_frequency = 10.0  # Default 10Hz
        self.timer = self.create_timer(1.0/publish_frequency, self.publish_joint_states)

    def create_callback(self, gripper_id, finger_joints):
        def callback(msg):
            # Map the 0-100 range to the actual joint limits (-1.57075 to 0.27)
            # Where 0 is fully closed (0.27 radians) and 100 is fully open (-1.57075 radians)
            JOINT_LOWER_LIMIT = -1.57075  # Fully open position in radians
            JOINT_UPPER_LIMIT = 0.27     # Fully closed position in radians
            
            # Normalize the input value (0 to 100) to the joint limits
            # Invert the mapping since 0 should be closed (upper limit) and 100 should be open (lower limit)
            normalized_position = JOINT_UPPER_LIMIT - ((msg.data / 100.0) * (JOINT_UPPER_LIMIT - JOINT_LOWER_LIMIT))
            
            # Update all finger joints for this gripper with the same position
            prefix, unit_num = gripper_id
            for joint_name in finger_joints:
                if joint_name in self.joint_indexes:
                    index = self.joint_indexes[joint_name]
                    self.joint_state.position[index] = normalized_position
                    self.get_logger().info(f'Updated {joint_name} position to {normalized_position}')
                else:
                    self.get_logger().warn(f'Joint {joint_name} not found in joint_indexes')
        
        return callback

    def publish_joint_states(self):
        # Update timestamp
        self.joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Publish the joint state with the correct joint names
        self.publisher.publish(self.joint_state)
        self.get_logger().debug(f'Published joint states with names: {self.joint_state.name}')

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = GripperJointPublisher()
        rclpy.spin(node)
    except Exception as e:
        print(f'Exception in node: {str(e)}')
    finally:
        # Destroy the node explicitly
        rclpy.shutdown()

if __name__ == '__main__':
    main()
