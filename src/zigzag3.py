import serial  #importing serial for the seiral communication between the esp32 and the raspberry pi. 
import time   #importing time for adding some delays 
import math   #importing math for the clauclation of the location of the source. 

from pymavlink import mavutil  # importing the module mavutil. 

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout = 1.0) # This is the port that connects to the Heltec esp 32 for the rssi information with the baud rate. Also with timeout we wait for 1 second when trying to read the serial data.
time.sleep(3)  # Waiting for 3 seconds to initialize the connection. 
ser.reset_input_buffer() # Clearing the old serial data that is in the input buffer
print("Serial OK")



        
     

class Location:   # Creating the class called location

    def __init__(self):   
        self.latitudeH = 0  # latitude is set to 0 first 
        self.longitudeH = 0 # longitude is set to 0t

    def get_current_location(self, the_connection):   # When we pass the connection and active the function in the drone file we run the following code. 
        self.connection = the_connection   # Creating a variable to save the connection information

        message = self.connection.recv_match(  # Reciving the message and saving it to the variable called message which contains the GLOBAL POSTION INT and setting blocking to true means we don't stop the program if we don't recieve anything
            type="GLOBAL_POSITION_INT",
            blocking=True, # Wait for the requested message instead of immediately continuing.
            timeout = 10  # Stop waiting if no message is received within 10 seconds.
        )
        
        # Messgae variable contains lots of information such as latitude, longitude,altitude etc.
        # To access them seperately we make use of the following code.

        self.latitudeH = message.lat # message.lat takes the latitude only form the saved message inside the message variable
        self.longitudeH = message.lon # message.lon takes the longitude only form the saved message inside the message variable
        
        # This changes the global varaible to the current location aka the home location and we can access it in the drone file directly and save it to a new variable
        # which will represent the saved home location where we can come back and land. 

        print("Home location saved")
        
        
    # Wait until the drone reaches the current point on the circle before sending the next point. Without this check, Python would send the following target
    # immediately while the drone was still travelling toward the current target.
    
    def wait_until_reached(self, the_connection, target_x, target_y, measurments):  # we are passing the parameters here 
      
      # This will run unitil we have reached the target x and y postion
      while True:
             position = the_connection.recv_match(type="LOCAL_POSITION_NED", blocking=True)   # we keep getting the current location

             # we find the difference between the current and the taraget location. 
             x_difference = abs(position.x - target_x)  

             y_difference = abs(position.y - target_y)
    

             x = position.x
             y = position.y
             time.sleep(0.01)
             
             if ser.in_waiting > 0: # Check whether there are bytes available in the serial input buffer. if there is greater than 0 available to read execute the next line.
                 rssi = int(ser.readline().decode("utf-8").strip()) # Read one RSSI value, convert the received bytes to text, remove whitespace/newline characters, and convert the result to an integer.
                 measurments.append([x,y,rssi])  # We save the current postion with the rssi value we get and add it to the 2d list of measurements that we created below. 
                 
             
             # Once we reach the target postion we break
             if (x_difference < 1 and y_difference < 1):
                print("Position reached")
                return # This reutrns nothing but it is used to get out of the Search function and after this will will run the Home function inside the drone file taking us home.
            
                 
        
    # This function makes the drone stop at the current location  
    def stop(self):

        print("Stopping drone")

        while True:

            self.connection.mav.send(
                mavutil.mavlink.MAVLink_set_position_target_local_ned_message(  
                    0,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    0b110111000111,  # We are changing the type mask here which ignores x,y and z and uses the velocity filed instead. 
                    0,
                    0,
                    0,
                    0, # vx  these velocity are set to 0 so that the drone can stop and running this loop makes sure that we don't continue the code of circle mode after setting the velocity to 0 as it will take time to slow down the drone. 
                    0, # vy 
                    0, # vz 
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )
            
            position = self.connection.recv_match(
            type="LOCAL_POSITION_NED",
            blocking=True
            )

            if abs(position.vx) < 0.2 and abs(position.vy) < 0.2: # If the velocity in x and y is less than 0.2 run the code below 
                print("Drone stopped")
                return position # Since the velocity is almost 0 we can retrun that postion which will be used to start the circle mode.


       


    def left_circle(self, x, y, the_connection):  # This the circle code that runs when we are at the certian rssi value. 
          
        radius = 2  # The radius of the circle 
        center_x = x # The x stays the same as we are moving sideways not up.
        center_y = y - 2  # Going to left is negative y so this -1 gives us a center a little bit away from where we have stopped 
        measurments = [] # We create this empty list here to save rssi values. 
        self.connection = the_connection # saving the connection
    
        print("start x=", x, "y=", y, "center_x=", center_x, "center_y=", center_y)
        
        
        for angle in range(90, 451, 15):  # Going from 90 to 451 actually more like < 451 so techinically 450. and add up by +15 degrees. 
         
            angle_radians = math.radians(angle) # Converting from radians to degree.
            
            # We get the value based on the radius times cosin of an angle gives us the length x or y value then we need to add the centre to get the correct location in the x and y plane
            # as the centre is not at 0,0 rather at some other place where we stop then we put centre as + or - 1 based on +x/y or -x/y. 
        
            target_x = center_x + radius*math.cos(angle_radians)  # each time the target will change based on the anlge we are going to. 
            target_y = center_y + radius*math.sin(angle_radians)  
            
             # We are using local postion ned meaning we are using the x and y coordinate and where we start is the 0,0 postion so the entire map is in x and y coordinate.
             # this is different than the local offset here we use the x and y coorinate to make our circling easier. Thinking of it as an actualy 2d plane with x and y layed out. 
             
            self.connection.mav.send(     # This is the same idea as the local offset but instead we are actaly going to the targer x and target y in the 2d grid. 
                    mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    0b110111111000,
                    target_x,
                    target_y,
                    -3, # Height is +3 meters but in this up is considered to be negative. 
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )
            
            print("angle=", angle, "target=(", target_x, ",", target_y, ")")
            
            
            self.wait_until_reached(self.connection, target_x, target_y, measurments)  # We need to use this similar idea as below to make sure we giong to locations step by step and not synchronously which causes problem. 
            
        self.estimate_location(measurments, self.connection) # Once we collected all the info in the 2d measurements list we send it to the function called estimate_location which takes in the connection and the measurement list as parameters to determine the estimate GPS location of source. 
            
            
            
            
    # Similar idea as left circle.     
    def right_circle(self, x, y, the_connection):
          
        radius = - 2
        center_x = x 
        center_y = y + 2   
        measurments = []
        self.connection = the_connection
        print("start x=", x, "y=", y, "center_x=", center_x, "center_y=", center_y)
        
        
        for angle in range(90, 451, 15):
            angle_radians = math.radians(angle)
        
            target_x = center_x + radius*math.cos(angle_radians)
            target_y = center_y + radius*math.sin(angle_radians)
            
            self.connection.mav.send(
                    mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    0b110111111000,
                    target_x,
                    target_y,
                    -3,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )
            
            print("angle=", angle, "target=(", target_x, ",", target_y, ")")
            
            
            self.wait_until_reached(self.connection, target_x, target_y, measurments)
            
        self.estimate_location(measurments, self.connection)
        
     
    # Similar idea as left circle 
    def front_circle(self, x, y, the_connection):
          
        radius = - 2
        center_x = x + 2
        center_y = y     
        measurments = []
        self.connection = the_connection
        print("start x=", x, "y=", y, "center_x=", center_x, "center_y=", center_y)
        
        
        for angle in range(0, 361, 15):
            angle_radians = math.radians(angle)
        
            target_x = center_x + radius*math.cos(angle_radians)
            target_y = center_y + radius*math.sin(angle_radians)
            
            self.connection.mav.send(
                    mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    0b110111111000,
                    target_x,
                    target_y,
                    -3,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )
            
            print("angle=", angle, "target=(", target_x, ",", target_y, ")")
            
            
            self.wait_until_reached(self.connection, target_x, target_y, measurments)
            
        self.estimate_location(measurments, self.connection)
         
         
         
   
    def estimate_location(self, measurments, the_connection ):  # This takes in the 2d measurments list as parameter along side the connection.  
       max_dbm = measurments[0][2] # We consider the first rssi value to be the max as we know the 2d layout is ([x1,y1,rssi], [x2,y2,rssi]....)
       sum_weight = 0  
       numerator_x = 0
       numerator_y = 0
       self.connection = the_connection
       
        
        
       for z in range(len(measurments)): # Finding max dbm we keep checking if the current value is greater than the current max if it is change the max to the current value. 
            if measurments[z][2] > max_dbm: 
                max_dbm = measurments[z][2]

       for i in range(len(measurments)): # Replacing dbm with the weights. 
            dbm = measurments[i][2]  # The i keeps changing and the index of 2 is constant as rssi is the third postion in the 2d list.
            weight = pow(10,((dbm - max_dbm)/10)) # Calculating the weight. 
            measurments[i][2] = weight  # Changing the current rssi value to the weight we calculated above.
            
       for a in range(len(measurments)):  # The sum of weights
           sum_weight += measurments[a][2]
           
       for b in range(len(measurments)):  # The numerator is x1 times weight1 then add it to the next set. 
           numerator_x += measurments[b][0] * measurments[b][2]
           
       for c in range(len(measurments)):  # The numerator is y1 times weight1 then add it to the next set. 
           numerator_y  += measurments[c][1] * measurments[c][2]
           
           
       # Based on the numerator divide by the sum of the weight we get the x and y estimate.  
       x_estimate = numerator_x / sum_weight    
       y_estimate = numerator_y / sum_weight
       
       
       current_postion = self.connection.recv_match(type="LOCAL_POSITION_NED", blocking=True)  
       
       # After the circle is completed we get the detla x and y buy doing the following calculation.
       delta_x = x_estimate - current_postion.x  
       delta_y = y_estimate - current_postion.y
       
       radius_earth = 6378137  # Radius of earth in meters
       
       current_GPS = self.connection.recv_match(type="GLOBAL_POSITION_INT",blocking=True)
       
       delta_latitude = (delta_x/radius_earth)*(180/math.pi)  # Calculating the delta latitude.
       
       delta_longitude = (delta_y/(radius_earth * math.cos(math.radians(current_GPS.lat/pow(10,7)))))*(180/math.pi) # Calculating the delta longitude by using the current latitude not delta latitude. 
       
       
       
       # Calculating the estimated gps location of the rssi source with delta latitude and longitude.
       estimated_latitude = (current_GPS.lat/pow(10,7)) + delta_latitude     
       estimated_longitude = (current_GPS.lon/pow(10,7)) + delta_longitude
       
       print(estimated_latitude)
       print(estimated_longitude)
       
       
    def set_ground_speed(self, speed):  # Setting the grown speed by using the speed paramater and using it in the function below as a paramater. 
        self.connection.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
            0,
            1,       # Ground speed
            speed,   # Speed in metres per second 
            0,
            0,
            0,
            0,
            0
        )

        print(f"Ground speed set to {speed} m/s") 


    def zigzag(self, the_connection):
        self.connection = the_connection

        left = 2 
        up = 2
        right = 2
        
        self.set_ground_speed(0.7)  # Passing the parameter of 0.7 to the function to set the ground speed as 0.7 m/s.


        # LOCAL_POSITION_NED uses a fixed local coordinate system and anything regarding local means we are using the x and y coordinate system. North direction is +x, South direction is -x, West direction is -y, East direction is +y that is how ardupilot firmware is designed.
        # We are using local offset here meaning when we stop and change direction we move 2 meters in +/-x or +/-y from that postion we are stopped at and not from the (0,0) postion that is the postion of the home or start. 

        for i in range(1):  # For testing purposes we are only running the pattern one time. 

            # ---------------- LEFT ----------------

            starting_position = self.connection.recv_match(   # Reciving the location postion in 2d the x and y coordinate and saving that message into the variable called starting_postion. 
                type="LOCAL_POSITION_NED",
                blocking=True
            )

            target_x = starting_position.x  # We are not moving in the x direction so we the starting postion is the target x postion. 
            target_y = starting_position.y + left  # Here going to the left is considered to be going in the negative y direction as that is the layout of the coorinate system in arudpilot.


            self.connection.mav.send(     # Sending a commange
                mavutil.mavlink.MAVLink_set_position_target_local_ned_message(    # Sending a local offset command.
                    10, # time boot
                    self.connection.target_system,   # ID of the Pixhawk/autopilot we are sending the command to
                    self.connection.target_component,  # ID of the specific component inside that system
                    mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED, # MavLink command used for local offset frame. 
                    0b110111111000, # Type mask: use position (x, y and altitude), while ignoring velocity, acceleration, yaw and yaw-rate fields.
                    0,
                    left,  # Going + 2 meters to the left side. 
                    0,  # Altitude of 0 here menas that we want to stay at the same height and from earlier codes we see that we will maintin a hegit of 3 meters. 
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )

            print("left")
            
            # Sending a MAVLink position target does not wait for the drone to physically reach that position. Python continues executing immediately to the next movement command
            # before the current movement has physically completed, causing the new target to replace the previous one.

            # To keep the zigzag movement sequential, the current LOCAL_POSITION_NED position is continuously compared with target_x and target_y. The program
            # only continues to the next movement once the drone is within the specified range of the current target. 
            
            
            while True: 
            
                time.sleep(0.01)
                if ser.in_waiting > 0: # Check whether there are bytes available in the serial input buffer. 
                 rssi = int(ser.readline().decode("utf-8").strip()) # Read one RSSI value, convert the received bytes to text, remove whitespace/newline characters, and convert the result to an integer. 
                 print(rssi)
                    
                position = the_connection.recv_match(type="LOCAL_POSITION_NED", blocking=True) 

                x_difference = abs(position.x - target_x)

                y_difference = abs(position.y - target_y)
                
                if(rssi > -60): # Here we keep checking the rssi value each time the while loop runs and once it goes above the threshold it means that we need to go to circle mode to get the estimate location of the rssi source. 
                    print("Circle mode")
                    stopped_position = self.stop()  # Stoping the drone first using the stop function or else it will keep moving forward until the left_circle function runs making the drone come back to start the circle mode so to fix that back and forth movement we stop the drone first. 

                    self.left_circle(  # After stopping we run the left circle function 
                        stopped_position.x,  # The stop function returns the postion and using the .x and .y we get the x and y postion and we use that as a starting point of the circle. 
                        stopped_position.y,
                        self.connection # Passing the connection as a paramater.
                    )
                    return  # After the circle is completed we retrun nothing and after this it goes to the function of Home inside the drone file.

                if (x_difference < 0.2 and y_difference < 0.2): # Once the difference is less than 0.5 that means we are very close to target location hence reached. 
                    print("Position reached")
                    break  # Breaking so we move on to the code below.
            
            self.stop() # Stopping the drone. 
            time.sleep(2) # Waiting for 2 seconds to give drone time to settle in before changing the direction. 
            
            
            

            # ---------------- UP ---------------- (Similar idea as left)

            starting_position = self.connection.recv_match(
                type="LOCAL_POSITION_NED",
                blocking=True
            )

            target_x = starting_position.x + up
            target_y = starting_position.y

            self.connection.mav.send(
                mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
                    0b110111111000,
                    up,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )

            print("up")

            
            while True:
            
                time.sleep(0.01)
                if ser.in_waiting > 0:
                 rssi = int(ser.readline().decode("utf-8").strip())
                 print(rssi)
                    
                position = the_connection.recv_match(type="LOCAL_POSITION_NED", blocking=True)

                x_difference = abs(position.x - target_x)

                y_difference = abs(position.y - target_y)
                
                if(rssi > -60):
                    print("Circle mode")
                    stopped_position = self.stop()

                    self.front_circle(
                        stopped_position.x,
                        stopped_position.y,
                        self.connection
                    )
                    return

                if (x_difference < 0.2 and y_difference < 0.2):
                    print("Position reached")
                    break
                
            self.stop()
            time.sleep(2)                

            # ---------------- RIGHT ----------------(Similar idea as left)

            starting_position = self.connection.recv_match(
                type="LOCAL_POSITION_NED",
                blocking=True
            )

            target_x = starting_position.x
            target_y = starting_position.y + right

            self.connection.mav.send(
                mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
                    0b110111111000,
                    0,
                    right,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )

            print("right")
            
            while True:
            
                time.sleep(0.01)
                if ser.in_waiting > 0:
                 rssi = int(ser.readline().decode("utf-8").strip())
                 print(rssi)
                    
                position = the_connection.recv_match(type="LOCAL_POSITION_NED", blocking=True)

                x_difference = abs(position.x - target_x)

                y_difference = abs(position.y - target_y)
                
                if(rssi > -60):
                    print("Circle mode")
                    stopped_position = self.stop()

                    self.right_circle(
                        stopped_position.x,
                        stopped_position.y,
                        self.connection
                    )
                    return

                if (x_difference < 0.2 and y_difference < 0.2):
                    print("Position reached")
                    break

            self.stop()
            time.sleep(2)        
        
            # ---------------- UP ----------------(Similar idea as left)

            starting_position = self.connection.recv_match(
                type="LOCAL_POSITION_NED",
                blocking=True
            )

            target_x = starting_position.x + up
            target_y = starting_position.y

            self.connection.mav.send(
                mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                    10,
                    self.connection.target_system,
                    self.connection.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
                    0b110111111000,
                    up,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            )

            print("up")
            
            
            
            while True:
            
                time.sleep(0.01)
                if ser.in_waiting > 0:
                 rssi = int(ser.readline().decode("utf-8").strip())
                 print(rssi)
                    
                position = the_connection.recv_match(type="LOCAL_POSITION_NED", blocking=True)

                x_difference = abs(position.x - target_x)

                y_difference = abs(position.y - target_y)
                
                if(rssi > -60):
                    print("Circle mode")
                    stopped_position = self.stop()

                    self.front_circle(
                        stopped_position.x,
                        stopped_position.y,
                        self.connection
                    )
                    return

                if (x_difference < 0.2 and y_difference < 0.2):
                    print("Position reached")
                    self.stop()
                    time.sleep(2)
                    return  # Returning at the end makes the program ends the serach function and continue to the Home function. 
                
                       
            
        
        print("Zigzag completed")