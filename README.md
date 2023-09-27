# uSkin Tactile Sensor on Robotiq Gripper & TM Robot

This codebase was created as part of a 6-month internship at the Plant Automation Team of Daimler Trucks Asia.

Project Title: <br />
**uSkin Tactile Sensors for Adaptive Grasping & Bin Picking Solution**

The repository is for controlling a Robotiq gripper mounted on a TM Robot using uSkin tactile sensors.

## Hardware Requirements

The hardware requirements of this project are the following:
1. 4x6 uSkin tactile sensors from [XELA Robotics](https://www.xelarobotics.com/)
2. 2F-85 Robotiq Gripper
3. TM5-900 Collaborative Robot

## Software Requirements

Required Python modules:
1. numpy
2. matplotlib
3. scipy
4. scikit-learn
5. keyboard
6. dearpygui
7. msvrt (Win) / getch (Linux)
8. pyserial
9. crcmod
10. techmanpy


and some socket io modules as written in the [software manual](https://xela.lat-d5.com/latest.php).
- websocket-client
- websockets

Explanation of each folder in the repository:
- GripperControl --> Controlling Robotiq Gripper via COM PORT
- RobotControl --> Controlling robot movement using techmanpy driver
- TM_Demo --> Full demo on controlling gripper and robot based on uSkin feedback.
- TwoSensorControl --> Prototype for two sensor clustering model
- SensorUtils --> Clustering middleware and XELA Robotics utility programs