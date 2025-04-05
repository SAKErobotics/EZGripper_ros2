#!/usr/bin/env python3
"""
EZGripper Process Cleanup Script
This script is used to clean up any lingering EZGripper processes
when the launch file is shut down.
"""

import os
import signal
import subprocess
import sys
import rclpy
from rclpy.node import Node

class CleanupEzgripperProcesses(Node):
    def __init__(self):
        super().__init__('cleanup_ezgripper_processes')
        self.get_logger().info('Starting EZGripper process cleanup')
        self.cleanup()
        
    def cleanup(self):
        """Clean up any lingering EZGripper processes"""
        self.get_logger().info('Cleaning up EZGripper processes')
        
        # Process patterns to look for
        patterns = [
            "gripper_joint_publisher",
            "gripper_static_tf_publisher"
        ]
        
        # Build the pkill command
        pkill_pattern = "|".join(patterns)
        pkill_cmd = f"pkill -f '{pkill_pattern}' || true"
        
        # Execute the pkill command
        try:
            self.get_logger().info(f'Executing: {pkill_cmd}')
            subprocess.run(pkill_cmd, shell=True, check=False)
            self.get_logger().info('Cleanup completed successfully')
        except Exception as e:
            self.get_logger().error(f'Error during cleanup: {str(e)}')
        
        # Exit after cleanup
        sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = CleanupEzgripperProcesses()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
