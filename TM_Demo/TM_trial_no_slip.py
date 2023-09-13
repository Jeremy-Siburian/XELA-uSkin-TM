import time
import asyncio
import csv

from multiprocessing.connection import wait
import os, sys

from sklearn.metrics import recall_score
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from SensorUtils.xelamiddleware import *
from RobotControl import techmanpy

from turtle import position, width
import numpy as np
import time
import re
import msvcrt
import threading
from GripperControl.robotiq_library import *

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

def thread_function(name):
    global uSkin_data
    
    while True:    #your core method here to keep the app running. Once it ends, the program will close
        try:
            data = client.getData() #use this to see the original data with time stamps 

            uSkin_data = split_data(data)
            #data format: [number of clusters],[[cluster_n_centroid_x, cluster_n_centroid_y, [....]]    

            time.sleep(0.001)
        except:
            print("Error")
        if kill_threads:
            break

kill_loop = False
global x_baseline
global slip_threshold
global speed_value
global force_value
object_lost_flag = False
object_lost_time = 0
global z_baseline

force_sensing_flag = False

trial_counter = 0
slip_counter = 0

slip_flag = False

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
AXIS_SEL = X_AXIS

def slip_detection_thread(name):
    global uSkin_data
    global kill_loop
    global object_lost_flag
    kill_loop = False
    global trial_counter
    global slip_counter
    global object_lost_time
    slip_counter = 0

    x_baseline = float(uSkin_data[2][AXIS_SEL])

    while force_sensing_flag:
            sensor_reading = open("sensor-reading" + "-" + str(trial_counter) + ".txt", "a")
            sensor_reading.write('{}\n'.format(uSkin_data))
            #print(uSkin_data) #use time.sleep instead if you don't want to print
            #time.sleep(0.001)

            if(len(uSkin_data) > 1):
                present_data = float(uSkin_data[2][AXIS_SEL])
                delta_digit =  present_data - x_baseline
                delta_digit_abs = abs(delta_digit)

                if delta_digit_abs > x_release_threshold:
                    print("Slip detected.")
                    slip_counter +=1
            
            else:
                if not object_lost_flag:
                    object_lost_time = time.time()
                    print("Object is lost!")
                    object_lost_flag = True
                    gripper.home()
                    success_rate = open("success_rate.txt", "a")
                    success_rate.write("Fail\n")
                kill_loop = True

            shear_delta = open("shear_delta" + "-" + str(trial_counter) + ".txt", "a")
            shear_delta.write('{}\n'.format(delta_digit))
            shear_delta_abs = open("shear_delta_abs" + "-" + str(trial_counter)+ ".txt", "a")
            shear_delta_abs.write('{}\n'.format(delta_digit_abs))
            
            x_baseline = present_data

            if kill_loop:               
                break

def adaptive_grasping_uSkin():
    if(len(uSkin_data) > 0):
        #close the gripper
        global rec
        global x_baseline
        global z_baseline
        global x_release_threshold
        global speed_value
        global force_value
        global force_sensing_flag

        print("Grasping...")
        position_value = FULLY_CLOSED
        speed_value = 5  # Set the desired speed
        force_value = 1  # Set the desired force
        gripper.move(position_value, speed_value, force_value)
        z_threshold = 500
        x_release_threshold = 200

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

        force_sensing_flag = True

        success_rate = open("success_rate.txt", "a")
        success_rate.write("\nTrial No.{}\n".format(trial_counter))

        print("Initial grasping force: ", z_baseline)
        success_rate.write("Initial grasping force: {}\n".format(z_baseline))
        print("Force sensing...")
        print(x_baseline)
        print(x_release_threshold)
        release_thread = threading.Thread(target=slip_detection_thread, args=(1,)) #A thread for accessing uSkin data from the middleware
        release_thread.start()


    else:
        print("No data. Please check the middleware")  

uSkin_thread = threading.Thread(target=thread_function, args=(1,)) #A thread for accessing uSkin data from the middleware
uSkin_thread.start()

#################################################################

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

async def grasping():
    print("Grasping with uSkin...")
    adaptive_grasping_uSkin()

async def placing(conn):
    global uSkin_data
    global force_sensing_flag
    global x_baseline
    global z_baseline
    global slip_counter
    global object_lost_flag
    force_sensing_flag = False

    success_rate = open("success_rate.txt", "a")
    if not object_lost_flag:
        success_rate.write("Success\n")
    success_rate.write("Slip Count: {}\n".format(slip_counter))

    print("Grasping is completed, force sensing is stopped.")
    gripper.move(FULLY_OPEN, 100, 1)
    await conn.set_queue_tag(3, wait_for_completion=True)

async def exit():
    os._exit(0)

async def initial_pos(conn):
    await asyncio.sleep(5)
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 0.70, 200)

async def pick_pos(conn):
    #await conn.move_to_joint_angles_ptp([12.633, 30.844, 108.238, -48.883, 88.581, 14.926], 0.70, 200)
    #brake hose coordinate
    await conn.move_to_joint_angles_ptp([12.633, 31.263, 108.309, -49.372, 88.583, 14.925], 0.70, 200)
    #metal part coordinate
    #await conn.move_to_joint_angles_ptp([12.633, 29.059, 107.871, -46.730, 88.574, 14.930], 0.70, 200)
    await conn.set_queue_tag(1, wait_for_completion=True)

async def waypoint_1(conn):
    #await conn.move_to_joint_angles_ptp([12.969, 14.555, 97.971, -22.319, 88.504, 15.313], 0.50, 200)
    #
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 0.70, 200)

async def waypoint_2(conn):
    await conn.move_to_joint_angles_ptp([-19.610, 20.141, 90.185, -21.389, 88.503, 15.283], 0.50, 200)

async def place_pos(conn):
    await conn.move_to_joint_angles_ptp([-19.610, 27.032, 97.442, -35.536, 88.540, 15.250], 0.50, 200)
    await conn.set_queue_tag(2, wait_for_completion=True)

async def waypoint_3(conn):
    await asyncio.sleep(1)
    await conn.move_to_joint_angles_ptp([-19.610, 20.141, 90.185, -21.389, 88.503, 15.283], 0.70, 200)

async def return_to_initial(conn):
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 0.70, 200)
    await conn.set_queue_tag(4, wait_for_completion=True)

async def object_dropped(conn):
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 0.70, 200)


#Main thread for robot movement

async def main():
    async with techmanpy.connect_sct(robot_ip='192.168.5.20') as conn:
        #Main sequence

        global trial_counter
        global object_lost_flag
        global object_lost_time
        trial_counter = 25

        await initial_pos(conn)
        while True:
            trial_counter += 1
            print("Starting trial No. ", trial_counter)
            start_time = time.time()
            await pick_pos(conn)
            await grasping()
            await waypoint_1(conn)
            await waypoint_2(conn)
            await place_pos(conn)
            await placing(conn)
            await waypoint_3(conn)
            await return_to_initial(conn)

            #Cycle time calculation
            end_time = time.time()
            cycle_time = end_time - start_time

            print("Cycle time (total): {:.2f} seconds".format(cycle_time))
            file1 = open("cycle-time.txt", "a")

            file1.write("\nTrial No.{}\n".format(trial_counter))
            file1.write('Total cycle time = {}\n'.format(cycle_time))

            if object_lost_flag:
                object_lost_time_in_cycle = object_lost_time - start_time
                print("Object lost time within cycle: {:.2f} seconds".format(object_lost_time_in_cycle))
                file1.write("Object lost time within cycle: {:.2f} seconds\n".format(object_lost_time_in_cycle))
                object_lost_flag = False
            
            file1.close()
            time.sleep(10)

            if trial_counter == 50:
                await(exit())
        
        #await exit()

asyncio.run(main())