Autonomous RF Signal Detection Drone

This repository contains the software and documentation for my Autonomous RF Signal Detection Drone project.

The goal of the project was to develop a quadcopter capable of autonomously searching an area for an unknown RF transmitter using RSSI (Received Signal Strength Indicator) measurements. The drone communicates with a Pixhawk flight controller through MAVLink, follows a predefined search pattern, detects when the RF signal exceeds a threshold, collects additional RSSI measurements around the detected area, estimates the transmitter location, and then returns to its starting position.

The system integrates:

Pixhawk 2.4.8 running ArduCopter for flight control
Raspberry Pi 4 as the onboard mission computer
Heltec WiFi LoRa 32 V3 modules for RF transmission and RSSI measurements
Python and MAVLink for autonomous flight commands and mission logic
A custom RSSI based location estimation method using measurements collected around the detected signal area
Repository Contents

The repository contains the main autonomous drone programs as well as the LoRa sender and receiver programs used for RF signal testing and detection.

The code is separated into different files and functions to handle tasks such as:

Establishing MAVLink communication
Switching the drone into GUIDED mode
Arming and autonomous takeoff
Executing the zigzag search pattern
Monitoring RSSI values
Performing the circular signal measurement pattern
Estimating the RF transmitter location
Returning to the original starting position
Landing

Project Report: 

For the best understanding of the project, I recommend reading the project report alongside the source code.
The report explains the hardware architecture, system design, MAVLink communication, autonomous search logic, RF detection method, location estimation approach, testing process, challenges encountered, and possible future improvements.
The code shows how these concepts were implemented in practice.
Reading the report and code together provides the clearest picture of the complete system flow and the reasoning behind the implementation.

Overall Mission Flow : 

Initialize System → Connect to Pixhawk → Enter GUIDED Mode → Arm → Take Off → Execute Zigzag Search → Detect RF Signal → Perform Circular RSSI Sampling → Estimate Transmitter Location → Return Home → Land
This project was developed as a hands-on exploration of avionics, embedded systems, autonomous UAVs, RF communication, and MAVLink-based flight control.
