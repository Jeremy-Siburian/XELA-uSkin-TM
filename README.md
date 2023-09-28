# uSkin Tactile Sensors on Robotiq Gripper & Omron TM Robot

Project Owner: Jeremy Siburian <br>
Last Updated: **September 28, 2023**

## Table of Contents

Contents of this documentation are the following:
1. [Overview](#1-overview)
2. [Hardware & Software Requirements](#2-hardware--software-requirements)
3. [Folder Navigation & Program Explanation](#3-folder-navigation--program-explanation)
4. [How to Run Programs](#4-how-to-run-programs)
5. [Robot Setup (Listen Node)]()
6. [Sensor Setup]()
5. [Related Links]()

Note: <br>
**Documentation is still under construction, some contents may be missing.**

Future Updates: <br>
1. Move detailed documentation into GitHub Wiki, README only contains high-level information.

## 1. Overview

The repository is for controlling a Robotiq gripper mounted on an Omron TM Robot using uSkin tactile sensors.

This codebase was created as part of a 6-month internship at the Plant Automation Team, Vehicle Manufacturing Engineering Japan, Daimler Trucks Asia.

Project Title: <br />
**uSkin Tactile Sensors for Adaptive Grasping & Bin Picking Solution**

For the full documentation of the project, please follow [link]() here.

## 2. Hardware & Software Requirements

The hardware requirements of this project are the following:
1. 4x6 uSkin tactile sensors from [XELA Robotics](https://www.xelarobotics.com/)
2. 2F-85 Robotiq Gripper
3. TM5-900 Collaborative Robot

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


and some socket io modules as written in the [XELA Robotics software manual](https://xela.lat-d5.com/latest.php).
- websocket-client
- websockets

## 3. Folder Navigation & Program Explanation

Explanation of each folder in the repository:
- **GripperControl** --> Controlling Robotiq Gripper via COM PORT.
- **RobotControl** --> Controlling robot movement using techmanpy communication driver.
- **TM_Demo** --> Demo programs on controlling gripper and TM robot based on uSkin feedback.
- **TwoSensorControl** --> Prototype for two sensor clustering model.
- **SensorUtils** --> Clustering middleware and XELA Robotics utility programs

## 4. How to Run Programs

To combine sensor feedback, gripper control, and robot movement together, two main control architectures are used as a prototype:
1. **Python-Only Control** (TMflow in Listen Node)
2. **Python + TMflow** (Robot movement is controlled in TMflow)

### Python-Only Control (TMflow in Listen Node)

In this control architecture, the robot movements are fully controlled in a Python script. **The TMflow is left in Listen Node only.**

Main demo program(s): <br>
1. **TM_trial_no_slip.py**
2. **TM_trial_slip.py**

To run the demo/trial program, the steps are the following:
1. In the TMflow software, a **Listen Node** must be active in order to receive robot commands from the Python script. 
2. In Visual Studio Code, **"clustering_middleware.py"** must be run at all times to access high-level data from the middleware.
3. After Listen Node is active and the clustering middleware is run, the main demo/trial programs can be executed.

### Python + TMflow (Robot movement is controlled in TMflow)

In this control architecture, the robot movement is fully done within TMflow. The main purpose of this control architecture is to develop a protototype of picking using TM Robot's built-in vision features.

Main demo program(s):
1. TM_socket_test.py

## 5. Robot Setup (Listen Node)

For more detailed explanation on how to prepare the robot, please visit the [Listen Node] and [techmanpy](https://github.com/jvdtoorn/techmanpy/tree/master) documentations.

## 6. Sensor Setup

For more detailed explanation on how to set up the sensors, please refer to the official documentation from [XELA Robotics](https://www.xelarobotics.com/) website.

## 7. Related Links

Below are a compilation of useful links related to the project.

### 1. Robot Related Links
|Related Link|Description|
|:---|:---|
|[techmanpy](https://github.com/jvdtoorn/techmanpy/tree/master)| Python communication driver for Techman Robots. |
|Listen Node ([Manual](https://assets.omron.eu/downloads/manual/en/v1/i848_tm_expression_editor_and_listen_node_reference_manual_en.pdf)) | Official documentation on Listen Node (How to activate, how to send external scripts, etc.) |
| [TM Robot TCP/IP](https://www.youtube.com/watch?v=dG73qZ8iPCM) | Youtube tutorial video on how to set up TCP/IP connection for TM robots.|

### 2. Sensor Related Links
|Related Link|Description|
|:---|:---|
| [XELA Sensors & Software Introduction](https://www.youtube.com/watch?v=kBmtRZjPg_Q) | Youtube tutorial covering the setup of the sensors, use of the software, ways to integrate software in 3rd party one and general troubleshooting. |

### 3. Gripper Control Related Links