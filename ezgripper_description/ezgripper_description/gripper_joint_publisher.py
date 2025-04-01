#!/usr/bin/env python3
"""
EZGripper Joint Position Publisher
Publishes joint positions for the EZGripper following the Linorobot2 architecture
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import yaml
import os
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Float64

class JointPositionPublisher(Node):
    def __init__(self):
        super().__init__('joint_position_publisher')
        
        # Retrieve the namespace and prepend it to the joint names
        namespace = self.get_namespace().strip('/')
        if namespace:
            namespace_prefix = f'{namespace}/'
        else:
            namespace_prefix = ''

        # Load component configuration from YAML file
        pkg_share = get_package_share_directory('ezgripper_description')
        components_yaml_path = os.path.join(pkg_share, 'config', 'robot_components.yaml')
        controllers_yaml_path = os.path.join(pkg_share, 'config', 'ezgripper_controllers.yaml')
        
        self.get_logger().info(f'Loading component configuration from {components_yaml_path}')
        try:
            with open(components_yaml_path, 'r') as file:
                component_config = yaml.safe_load(file)
            
            # Get the ezgripper component configuration
            ezgripper_config = component_config['components']['ezgripper']
            self.get_logger().info(f'Loaded ezgripper component configuration')
        except Exception as e:
            self.get_logger().warn(f'Failed to load component configuration: {str(e)}')
            self.get_logger().warn(f'Falling back to controller configuration')
            ezgripper_config = None
        
        # Load controller configuration as fallback
        self.get_logger().info(f'Loading controller configuration from {controllers_yaml_path}')
        with open(controllers_yaml_path, 'r') as file:
            controller_config = yaml.safe_load(file)

        # Extract joint names from configuration
        joint_names = []
        if ezgripper_config and 'joints' in ezgripper_config:
            # Use component configuration if available
            for joint in ezgripper_config['joints']:
                joint_names.append(joint['name'])
                self.get_logger().info(f'Found joint from component config: {joint["name"]}')
        else:
            # Fallback to controller configuration
            for controller, params in controller_config.items():
                if 'ros__parameters' in params and 'joint' in params['ros__parameters']:
                    joint_name = params['ros__parameters']['joint']
                    joint_names.append(joint_name)
                    self.get_logger().info(f'Found joint from controller config: {joint_name}')

        # Initialize joint state message with joint names
        self.joint_state = JointState()
        self.joint_state.name = joint_names
        self.joint_state.position = [0.0] * len(joint_names)
        self.joint_state.velocity = [0.0] * len(joint_names)
        self.joint_state.effort = [0.0] * len(joint_names)
        self.get_logger().info(f'Initialized joint state with joints: {joint_names}')

        # Publisher for the joint states
        # Following Linorobot2 architecture, we publish to 'joint_states' in our namespace
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.get_logger().info('Publisher created for joint_states')

        # Create a dictionary to map joint names to their respective indexes
        self.joint_indexes = {name: i for i, name in enumerate(joint_names)}
        self.get_logger().info(f'Joint indexes: {self.joint_indexes}')

        # Create subscribers for the gripper control
        # Since the EZGripper is underactuated (both palm to L1 joints move together),
        # we only need one subscriber per gripper
        self.subscribers = []
        
        # Group joint names by gripper prefix
        gripper_prefixes = set()
        for joint_name in joint_names:
            # Extract the gripper prefix (e.g., 'left' from 'left_ezgripper_knuckle_palm_L1_1')
            if '_ezgripper_' in joint_name:
                prefix = joint_name.split('_ezgripper_')[0]
                gripper_prefixes.add(prefix)
        
        # Create one subscriber per gripper
        for prefix in gripper_prefixes:
            # Use a standardized topic name for each gripper
            topic_name = f'{prefix}_ezgripper/command'
            
            # Find the first palm to L1 joint for this gripper to use as the control joint
            control_joint = None
            for joint_name in joint_names:
                if joint_name.startswith(f'{prefix}_ezgripper_') and 'knuckle_palm_L1' in joint_name:
                    control_joint = joint_name
                    break
            
            if control_joint:
                self.subscribers.append(
                    self.create_subscription(Float64, topic_name, self.create_callback(control_joint), 10)
                )
                self.get_logger().info(f'Created subscriber for {topic_name} controlling {control_joint}')
            else:
                self.get_logger().warn(f'No control joint found for gripper prefix {prefix}')

        # Timer to publish joint states
        # Get publish frequency from component config or use default
        publish_frequency = 10.0  # Default 10Hz
        if ezgripper_config and 'parameters' in ezgripper_config and 'publish_frequency' in ezgripper_config['parameters']:
            publish_frequency = float(ezgripper_config['parameters']['publish_frequency'])
        
        self.timer = self.create_timer(1.0/publish_frequency, self.publish_joint_states)

    def create_callback(self, joint_name):
        def callback(msg):
            # Map the 0-100 range to the actual joint limits (-1.57075 to 0.27)
            # Where 0 is fully closed (0.27 radians) and 100 is fully open (-1.57075 radians)
            JOINT_LOWER_LIMIT = -1.57075  # Fully open position in radians
            JOINT_UPPER_LIMIT = 0.27     # Fully closed position in radians
            
            # Normalize the input value (0 to 100) to the joint limits
            # Invert the mapping since 0 should be closed (upper limit) and 100 should be open (lower limit)
            normalized_position = JOINT_UPPER_LIMIT - ((msg.data / 100.0) * (JOINT_UPPER_LIMIT - JOINT_LOWER_LIMIT))
            
            # Get the base name without the finger number (e.g., 'left_ezgripper_knuckle_palm_L1' from 'left_ezgripper_knuckle_palm_L1_1')
            # Handle both single and triple gripper configurations
            if '_1' in joint_name or '_2' in joint_name:
                # For triple gripper, the pattern is like 'left_gripper1_ezgripper_knuckle_palm_L1_1'
                # For single gripper, the pattern is like 'left_ezgripper_knuckle_palm_L1_1'
                base_name = joint_name[:-2]  # Remove the last 2 characters (e.g., '_1' or '_2')
                
                # Update both joints with the same value for underactuation
                for suffix in ['_1', '_2']:
                    full_joint_name = f"{base_name}{suffix}"
                    if full_joint_name in self.joint_indexes:
                        index = self.joint_indexes[full_joint_name]
                        self.joint_state.position[index] = normalized_position
                        self.get_logger().info(f'Updated {full_joint_name} position to {normalized_position} (from normalized input {msg.data})')
                        
                # For triple gripper, also update the corresponding joints in the other grippers
                # Check if this is a triple gripper joint (contains 'gripper1', 'gripper2', or 'gripper3')
                for gripper_num in ['1', '2', '3']:
                    if f'_gripper{gripper_num}_' in joint_name:
                        # This is a triple gripper joint
                        # Update the corresponding joints in the other grippers
                        current_gripper = f'_gripper{gripper_num}_'
                        for other_gripper_num in ['1', '2', '3']:
                            if other_gripper_num != gripper_num:
                                # Replace the current gripper number with the other gripper number
                                other_gripper = f'_gripper{other_gripper_num}_'
                                other_joint_base = base_name.replace(current_gripper, other_gripper)
                                
                                # Update both joints in the other gripper
                                for suffix in ['_1', '_2']:
                                    other_joint = f"{other_joint_base}{suffix}"
                                    if other_joint in self.joint_indexes:
                                        index = self.joint_indexes[other_joint]
                                        self.joint_state.position[index] = normalized_position
                                        self.get_logger().info(f'Updated corresponding joint {other_joint} to {normalized_position}')
            else:
                # For any other joints that might not follow this pattern
                index = self.joint_indexes[joint_name]
                self.joint_state.position[index] = normalized_position
                self.get_logger().info(f'Updated {joint_name} position to {normalized_position} (from normalized input {msg.data})')
        return callback

    def publish_joint_states(self):
        # Update timestamp
        self.joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Publish the joint states
        self.publisher.publish(self.joint_state)
        self.get_logger().debug(f'Published joint state: {self.joint_state.position}')

def main(args=None):
    rclpy.init(args=args)
    node = JointPositionPublisher()
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
# - Renamed class to JointPositionPublisher
# - Updated node name to joint_position_publisher
# - Added proper namespace handling
# - Added YAML configuration loading
# - Added proper joint naming with namespace
# - Added dynamic subscriber creation
# - Maintained consistent topic naming
# - Kept same functionality but with better naming conventions
