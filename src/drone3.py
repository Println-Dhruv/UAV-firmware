# For more information on MAVlink command and it's parameters visit the mavlink.io -> Pymavlink(in Languages at top right) -> Command protocal (under microservices) and clicking the relavent command type.
# can also watch the video series from youtube to help guide and understand the parameters and functions.(https://www.youtube.com/watch?v=6M7e7DDLTQc) 



from pymavlink import mavutil  #importing the mavutil module form the pymavlink which we downloaded. 
from zigzag3 import Location   # importing the Location class form the zigzag3 file.  
import time

#Creating drone class
class Drone:  
    
    # Requests a specific MAVLink message from the Pixhawk at a specified update frequency
    def request_message_interval(self, message_id, frequency_hz):
        
        # MAV_CMD_SET_MESSAGE_INTERVAL requires the time between each message in microseconds instead of the number of messages per second. 1 second = 1,000,000 microseconds.
        # We divide 1,000,000 by the frequency we want.
    
        # Example:
        # 5 Hz  -> 1,000,000 / 5  = 200,000 microseconds between messages
        # 10 Hz -> 1,000,000 / 10 = 100,000 microseconds between messages.
        interval_microseconds = int(
            1_000_000 / frequency_hz
        )

        self.connection.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, # MAVLink command used to tell the Pixhawk how often we want a particular MAVLink message to be sent.
            0, # Confirmation value
            message_id, # Param 1: ID of the MAVLink message that we want the Pixhawk to send
            interval_microseconds, # Param 2: Time between each message in microseconds
            0, # All the parameters below and including this are unused. 
            0,
            0,
            0,
            0 # Param 7: use the flight-stack default response target
        )

    def __init__(self):
        self.connection = mavutil.mavlink_connection(   # Initiating the connection between the Raspberry Pi and the Pixhawk flight controller.
            "/dev/serial0",  # The port name 
            baud=57600   # The baud rate for data transfer 
        )

        print("Waiting for heartbeat...")   

        self.connection.wait_heartbeat()  # Waiting for the heartbeat form the Pixhawk before we move forward. 

        print("Heartbeat received")

        self.request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, # Request GLOBAL_POSITION_INT from the Pixhawk at 5 Hz(5 messages every second). This message gives us information such as the drone's GPS latitude, longitude and altitude.
            5
        )

        self.request_message_interval(   
            mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, # Request LOCAL_POSITION_NED from the Pixhawk at 10 Hz (10 messages every second). This gives us the drone's localx, y, z position and velocity, which we use for movement and checking whether the drone has reached a target.
            10
        )

        print("Position messages requested")

        self.pattern_start = Location()  # self.pattern_start is a variable which contains an instance of Location class

        self.pattern_start.get_current_location(  # Sending the connection variable to the function called get_current_location to get the initail starting position so we know the home location. 
            self.connection
        )
        
        # Saving the home GPS location so we can come back and land

        self.home_lat = self.pattern_start.latitudeH  # latitude for GPS 
        self.home_lon = self.pattern_start.longitudeH # longitude for GPS
    
    time.sleep(10)   # Give EKF/GPS additional time to settle before flight commands. 
                
    def Guided(self):   # This makes sure the drone gets into GUIDED mode so that it can run the manual script for automation we have written rather than Stabilize mode. 
        guided_mode = (
            self.connection.mode_mapping()["GUIDED"]
        )

        self.connection.mav.set_mode_send(
            self.connection.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            guided_mode
        )

        while True:
            message = self.connection.recv_match(
                type="HEARTBEAT",
                blocking=True
            )

            if message.custom_mode == guided_mode:
                print("GUIDED mode")
                break

     
    # this function sends a MAVlink Command to arm the drone
    def Arm(self):  
        self.connection.mav.command_long_send(      
            self.connection.target_system,   # ID of the Pixhawk/autopilot we are sending the command to
            self.connection.target_component, # ID of the specific component inside that system
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # MAVLink command used to arm or disarm the drone 
            0, # confirmation value; 0 means this is the first command request
            1, # parameter 1: 1 = arm, 0 = disarm
            0, # parameter 2: normal arming (not forcing the safety checks)
            0, # parameters 3-7 are unused for this command
            0,
            0,
            0,
            0
        )
        
        
        print("Arming")
        while True:
            message = self.connection.recv_match(   # Trying to receive the heartbeat message that contains the information about the current state of the drone.
                type="HEARTBEAT",
                blocking=True
            )

            armed = (                   # Checks the safety armed flag 
                message.base_mode  
                & mavutil.mavlink
                .MAV_MODE_FLAG_SAFETY_ARMED
            )
            
            # Continue once the armed flag is set 
            if armed:  
                print("Armed")
                break
            
    
    # this function sends a MAVlink Command to take off the drone      
    def TakeOff(self):  
        self.connection.mav.command_long_send(   
            self.connection.target_system,  # ID of the Pixhawk/autopilot we are sending the command to
            self.connection.target_component, # ID of the specific component inside that system
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, # MAVLink command used for take off
            0,  # parameter not used
            0,  # param1: Controls the pitch but since we are a drone and not a plane we don't need it so we put 0
            0,  # parameter not used
            0,  # parameter not used
            0,  # yaw not used
            0,  # param5: latitude of 0 meanse we use the current latitude starting postion we are at
            0,  # param6: longitude of 0 meanse we use the current longitude starting postion we are at.
            3 # This is the height we want to reach at take off which is 3 meters. 
        )


       
        while True:
            message = self.connection.recv_match(    # The recv_match means reciving the message that has the type GLOBAL_POSTION_INT and save it inside the message variable. 
                type="GLOBAL_POSITION_INT",
                blocking=True  
            )

            altitude = (  
                message.relative_alt / 1000  # Message variable contains all the details about GLOBAL_POSTION_INT such as longitude, latitude etc, but we only want altitude so we do message.relative_alt.altitude comes back multiplied by 1000 so we divide by 1000 to get it in meters.
            )

            print(  
                f"Altitude: {altitude:.1f} m"   
            )

            if altitude >= 2.8:  # Once we reach the height of around 3 we exit the loop and print take off completed.
                print("Takeoff completed")
                break  # Break out of the loop.

    # Starts the autonomous RF search sequence implemented by the Location class. 
    def Search(self):
        self.pattern_start.zigzag( # We are activating the zigzag function from the Location class and sending the self.connection which holds the connection port and the baud rate information we set earlier. 
            self.connection
        )

    # After completing the search we need to head back to the saved home location. 
    def Home(self):
        self.connection.mav.send(       
            mavutil.mavlink.MAVLink_set_position_target_global_int_message(
                10, # time boot 
                self.connection.target_system,  # ID of the Pixhawk/autopilot we are sending the command to.
                self.connection.target_component, # ID of the specific component inside that system.
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # MAVLink coordinate frame. 
                0b110111111000, # Type mask: use position (latitude, longitude and altitude), while ignoring velocity, acceleration, yaw and yaw-rate fields.
                self.home_lat, # The saved home latitude form earlier inside the init function. 
                self.home_lon, # The saved home longitude form earlier inside the init function.
                3, # Going to the GPS location while maintaining 3 meters above the ground similar to take off and throughout the mission.
                0, # Velocity values — ignored by the type mask.
                0, # Velocity values — ignored by the type mask.
                0, # Velocity values — ignored by the type mask.
                0, # Acceleration values — ignored by the type mask.
                0, # Acceleration values — ignored by the type mask.
                0, # Acceleration values — ignored by the type mask.
                0, # Yaw — ignored
                0 # Yaw rate — ignored.
            )
        )

        print("Going home")

        # Continuously receives the drone's current GPS position from the Pixhawk
        while True:
            message = self.connection.recv_match(
                type="GLOBAL_POSITION_INT",
                blocking=True
            )
           
            # Calculates the difference between the drone's current GPS position and the saved home position.
            
             
            latitude_difference = abs(
                message.lat - self.home_lat
            )

            longitude_difference = abs(
                message.lon - self.home_lon
            )
            
            # both GPS differences are within certain range that means we have reached home

            if (
                latitude_difference < 100
                and longitude_difference < 100
            ):
                print("Home reached")
                break


       
    def Land(self):
        self.connection.mav.command_long_send(
            self.connection.target_system, # ID of the Pixhawk/autopilot we are sending the command to.
            self.connection.target_component,  # ID of the specific component inside that system.
            mavutil.mavlink.MAV_CMD_NAV_LAND,  # MAVLink navigation command telling the drone to land.
            0, # confirmation value : first command request
            0, # default behaviour. 
            0, # normal landing; precision landing disabled
            0, # unused
            0, # yaw value
            0, # latitude.
            0, # longitude.
            0, # landing altitude
        )

        print("Landing")

        # Waits for disarming and prints the message once disarmed. 
        while True:
            message = self.connection.recv_match(
                type="HEARTBEAT",
                blocking=True
            )

            armed = (
                message.base_mode
                & mavutil.mavlink
                .MAV_MODE_FLAG_SAFETY_ARMED
            )

            if not armed:
                print("Landed and disarmed")
                break
