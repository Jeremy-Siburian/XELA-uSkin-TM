#!/usr/bin/env python

#Import all necessary libraries

from multiprocessing.connection import wait
import os, sys

from sklearn.metrics import recall_score
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from SensorUtils.xelamiddleware import *

from turtle import position, width
import numpy as np
import time
import re
import msvcrt
import threading
from GripperControl.robotiq_library import *
import socket

#Import techmanpy driver for robot control
from RobotControl import techmanpy
import asyncio

class MyData(object):
    def __init__(self):
        self.__data = {}
    def newdata(self,data):
        self.__data = data
        #print("New data: {}".format(data))
    def getdata(self):
        return self.__data

mydata = MyData()
message_no = 0
global rec
global loop_flag
#initiate settings object before starting the server and client
settings = XELA_Settings(client_port= 5001, server_port=5002)#client_ip="192.168.0.111", server_ip = "192.168.0.111", #IPs can be left out when you use "Iam" functions

#demo of the functions of XELA_Settings
print(settings.get_client())#print current client IP and Port

#Client will be self
settings.iamclient() # will automatically detect your IP Address
client = XELA_Client(settings,mydata.newdata)#pass in XELA_Settings object for IP and Port, second function must be the one which handles incoming data (storage), alternatively you can set request to client.getData() from your function to get latest info (safer)

global uSkin_data

def split_data(message): # For accessing JSON data
    out = []
    if len(message) > 0:
        #out = message[u"1"][u"data"].split(",") #originally to access the raw sensor data
        out = message[u"data"] #to access high level data
    #for i in range(0, len(out)):
    #    out[i] = int(out[i], 16)
    #    np.array(out)       
    return out

kill_threads = False

def keyboard_input(name): # a thread for receiving keyboard input
    global key_input
    #global taxel_no
    key_input = ""
    while(True):
        key_input = msvcrt.getch()     
        #print(key_input)
        if kill_threads:
            break  

keyboard_thread = threading.Thread(target= keyboard_input , args=(1,))
keyboard_thread.start()

#Core thread for receiving sensor data from middleware

def thread_function(name):
    global uSkin_data
    
    while True:    #your core method here to keep the app running. Once it ends, the program will close
        try:
            #data = client.getData() #use this to see the original data with time stamps 

            uSkin_data = split_data(client.getData())
            #data format: [number of clusters],[[cluster_n_centroid_x, cluster_n_centroid_y, [....]]    

            time.sleep(0.001)
        except:
            print("Error")
        if kill_threads:
            break

#Global variable declarations

kill_loop = False
global speed_value
global force_value

#Slip related variables
global x_baseline #Update the shear change baseline
global slip_threshold 
force_sensing_flag = False

#Sensor force data (x,y,z force)
X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
AXIS_SEL = X_AXIS

#Main thread for slip detection

def slip_detection_thread(name):
    global uSkin_data
    global kill_loop
    global force_sensing_flag
    kill_loop = False
    global x_baseline

    x_baseline = float(uSkin_data[2][AXIS_SEL])

    while force_sensing_flag: #Only detecting slip while object is being grasped
        #print("Force sensing...")
        time.sleep(0.1)

        if(len(uSkin_data) > 1):
            present_data = float(uSkin_data[2][AXIS_SEL])
            delta_digit =  present_data - x_baseline    #Change in shear force
            delta_digit_abs = abs(delta_digit) 

            if delta_digit_abs > slip_threshold: #Increase force if slip is detected
                print("Slip detected.")
                gripper.move(FULLY_CLOSED, 100, 1)
                time.sleep(0.1)
                gripper.stop()
                #slip_counter +=1

        #Update new shear baseline
        x_baseline = present_data

        if kill_loop:
            break

#Main function for set force grasping with uSkin sensors

def adaptive_grasping_uSkin():
    if(len(uSkin_data) > 0):
        #close the gripper
        global rec
        global x_baseline
        global z_baseline
        global slip_threshold
        global speed_value
        global force_value
        global force_sensing_flag

        print("Grasping...")
        position_value = FULLY_CLOSED
        speed_value = 5  # Set the desired speed
        force_value = 1  # Set the desired force
        gripper.move(position_value, speed_value, force_value)
        z_threshold = 800   #Change grasping force here
        slip_threshold = 50  #Change slip threshold here

        while(True): #grasp an object
            #print(uSkin_data) #use time.sleep instead if you don't want to print
            time.sleep(0.001)
            if(len(uSkin_data) > 1):
                if float(uSkin_data[2][2]) > z_threshold: #stop when z axis is over than the threshold
                    gripper.stop()
                    x_baseline = float(uSkin_data[2][AXIS_SEL])
                    z_baseline = float(uSkin_data[2][2])
                    time.sleep(0.1)

                    break                    

        print("Touch detected") 
        time.sleep(1)

        force_sensing_flag = True   #Start slip detection
        #with open(os.path.join(trial_results_path, "success_rate.txt"), "a") as success_rate:
        #    success_rate.write("\nTrial No.{}\n".format(trial_counter))
        #    success_rate.write("Initial grasping force: {}\n".format(z_baseline))

        print("Initial grasping force: ", z_baseline)
        print("Force sensing...")
        print(x_baseline)
        release_thread = threading.Thread(target=slip_detection_thread, args=(1,)) #A thread for continuously checking slip
        release_thread.start()

    else:
        print("No data. Please check the middleware")  


uSkin_thread = threading.Thread(target=thread_function, args=(1,)) #A thread for accessing uSkin data from the middleware
uSkin_thread.start()

debug_mode = 0 # set this to 1 if the gripper is not connected

if debug_mode != 1:
    try:
        print ('Opening Port...')
        gripper = Robotiq()
        gripper.__init__(port = 'COM3') #must be auto detect / drop down menu
        time.sleep(1)
        gripper.reset() # is it dangerous with uSkin installed?
        time.sleep(1)
        gripper.home()
        print('Port is opened')
        
    except:
        print("Gripper cannot be found!")

time.sleep(2)

#################################################################


#MAIN ROBOT MOVEMENT THREAD STARTS HERE

robot_ip = '192.168.5.20'
robot_port = 5890
connection_timeout = 5  # Timeout value in seconds
retry_delay = 0  # Delay between connection attempts in seconds
pick_finish_flag = False
release_finish_flag = False

#Flag message from TMflow
start_pick_flag = "$TMSCT,9,0,Listen1,*4C"
start_release_flag = "$TMSCT,9,0,Listen2,*4F"

# Asynchronous function to attempt the connection and return True if successful
async def try_connect():
    global pick_finish_flag
    global release_finish_flag
    global force_sensing_flag

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.settimeout(connection_timeout)
        client_socket.connect((robot_ip, robot_port))
        print("Connection established successfully!")
        
        while True:
            # Receive the response from the server
            response = client_socket.recv(1024)
            response_str = response.decode().strip()

            if start_pick_flag in response_str:
                print("Received grasping flag.")
                adaptive_grasping_uSkin()
                pick_finish_flag = True
                return True  # Return True on successful gripper movement

            elif start_release_flag in response_str:
                print("Received release flag.")
                try:
                    force_sensing_flag = False
                    time.sleep(1)
                    gripper.move(FULLY_OPEN, 5, 1)
                    time.sleep(0.5)
                    release_finish_flag = True
                    #force_sensing_flag = False
                    return True  # Return True on successful gripper movement
                    

                except:
                    print("Gripper cannot be found!")
                    return False

            else:
                print("Received response from server:", response_str)
                return False
            
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception as e:
        print(f"An error occurred while trying to establish a connection: {e}")
        return False
    finally:
        client_socket.close()

async def exit_listen_sequence():
    global pick_finish_flag
    global release_finish_flag
    if pick_finish_flag or release_finish_flag:
        try:
            async with techmanpy.connect_sct(robot_ip='192.168.5.20') as conn:
                await conn.exit_listen()
            pick_finish_flag = False
        except Exception as e:
            print(f"Error in exit_listen_sequence: {e}")


async def main():
    while True:
        if await try_connect():
            #time.sleep(0.1)
            await exit_listen_sequence()
        else:
            print("Waiting for connection. Retrying in {} seconds...".format(retry_delay))
            await asyncio.sleep(retry_delay)

# Run the main loop asynchronously
loop = asyncio.get_event_loop()
loop.run_until_complete(main())