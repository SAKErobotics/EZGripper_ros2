# EZGripper Launch File Testing

This document describes the automated testing framework for EZGripper launch files, which enables easy validation of functionality without requiring a graphical interface.

## Testing Script Overview

The `test_ezgripper_launch_files.py` script provides a comprehensive testing solution for all EZGripper launch files. It runs each launch file in headless mode (without visualization), collects diagnostic information, and verifies proper cleanup after termination.

### Key Features

- **Headless Testing**: Tests run without any UI components, making them faster and more efficient
- **Comprehensive Diagnostics**: Collects detailed information about nodes, topics, parameters, and processes
- **Automatic Cleanup**: Verifies that all processes terminate properly and cleans up any lingering processes
- **Detailed Reporting**: Generates individual test reports with timestamps and diagnostic information
- **Progress Monitoring**: Provides real-time updates on test progress with clear status indicators

## Running the Tests

To run the tests, follow these steps:

1. Make sure you're in your ROS2 workspace:
   ```bash
   cd /home/sake/linorobot2_ws
   ```

2. Source your ROS2 environment:
   ```bash
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ```

3. Run the test script:
   ```bash
   /home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/ezgripper_description/test_ezgripper_launch_files.py
   ```

## Test Results

The script creates a directory at `~/ezgripper_test_results` where it stores individual test result files. Each file contains:

- Test metadata (name, command, timestamp)
- Output from the launch file execution
- Diagnostic information:
  - Running processes
  - ROS2 node list
  - ROS2 topic list
  - ROS2 parameter list
  - Node information for key components
  - Topic data samples
  - TF tree information
  - Cleanup verification

## Available Tests

The script tests the following launch files:

1. Single EZGripper Description
2. Double EZGripper Description
3. Triple EZGripper Description
4. Single EZGripper Integration
5. Double EZGripper Integration
6. Triple EZGripper Integration
7. Single EZGripper Standalone
8. Double EZGripper Standalone
9. Triple EZGripper Standalone

## Benefits for AI Development

This testing framework is particularly valuable for AI systems working with the EZGripper for several reasons:

1. **Validation Without Visualization**: AI systems can verify functionality without requiring graphical interfaces
2. **Reproducible Testing**: Provides consistent, reproducible test results for validation
3. **Diagnostic Data Collection**: Automatically gathers comprehensive diagnostic information for analysis
4. **Process Verification**: Ensures proper cleanup and resource management
5. **Integration Testing**: Validates that all components work together correctly

## Extending the Tests

To add new tests, simply update the `TESTS` list in the script with additional test configurations:

```python
{
    "name": "new_test_name",
    "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description new_launch_file.launch.py",
    "description": "Description of the new test"
}
```
