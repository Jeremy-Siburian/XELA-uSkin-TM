#!/usr/bin/env python3
from multiprocessing.connection import wait
import os, sys
import keyboard
from sklearn.metrics import recall_score
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from SensorUtils.xelamiddleware import *

from turtle import position, width
import numpy as np
import time
import re

if os.name == 'posix': #Linux OS
    import getch as user_input
    portname = '/dev/ttyUSB0'
else:
    import msvcrt as user_input #Windows OS
    portname = 'COM4' #must be auto detect / drop down menu

import dearpygui.dearpygui as dpg
import threading
from robotiq_library import *

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
        key_input = user_input.getch() #this will pause the program in Linux. not ideal
        print(key_input)
        if kill_threads:
            break  
        #name.wait(0.1)
        #time.sleep(0.1)

keyboard_thread = threading.Thread(target= keyboard_input , args=(1,))
if os.name != 'posix':
    keyboard_thread.start()   #only run this in windows for now

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

kill_loop = False
global x_baseline
global x_release_threshold
global speed_value
global force_value

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
AXIS_SEL = X_AXIS

def slip_detection_thread(name):
    global uSkin_data
    global kill_loop
    kill_loop = False
    x_baseline = float(uSkin_data[2][AXIS_SEL])

    while True:
            #print(uSkin_data) #use time.sleep instead if you don't want to print
            time.sleep(0.001)
            
            if(len(uSkin_data) > 1):
                present_data = float(uSkin_data[2][AXIS_SEL])
                delta_digit =  present_data - x_baseline

                if abs(delta_digit) > x_release_threshold:
                    print("Slip detected.")
                    gripper.move(FULLY_CLOSED, speed_value, force_value)
                    time.sleep(0.1)
                    gripper.stop()
            
            else:
                print("Object is lost!")
                gripper.home()
                    #asyncio.run(object_drop())
                kill_loop = True

            x_baseline = present_data

            if kill_loop:               
                break

def force_sensing_thread(name):
    global uSkin_data
    global kill_loop
    kill_loop = False
    x_baseline = float(uSkin_data[2][AXIS_SEL])
    while True: #
            print(uSkin_data) #use time.sleep instead if you don't want to print
            #time.sleep(0.001)
            if(len(uSkin_data) > 1):
                if  x_baseline > 0:
                    if float(uSkin_data[2][AXIS_SEL]) - x_baseline > x_release_threshold: #stop when z axis is over than the threshold
                        #gripper.home()
                        gripper.move(FULLY_CLOSED, speed_value, force_value)
                        time.sleep(0.5)
                        gripper.stop()
                        print('break the loop')
                elif x_baseline < 0:
                    if float(uSkin_data[2][AXIS_SEL]) + x_baseline > x_release_threshold: #stop when z axis is over than the threshold
                        #gripper.home()
                        gripper.move(FULLY_CLOSED, speed_value, force_value)
                        time.sleep(0.5)
                        gripper.stop()
                        print('break the loop')
                        break
            if kill_loop:
                break

def force_sensing_thread_reversed(name):
    global uSkin_data
    global kill_loop
    kill_loop = False
    past_data = 0
    counter = 0
    gripper_flag = 0
    while True: #
            #pos = gripper.POSITION 
            #print(pos) #use time.sleep instead if you don't want to print
            time.sleep(0.001)
            
            if(len(uSkin_data) > 1):
                present_data = float(uSkin_data[2][AXIS_SEL])
                delta_digit =  present_data - past_data

                if delta_digit > x_release_threshold:
                    gripper.move(FULLY_CLOSED, speed_value, force_value)
                    time.sleep(0.5)
                    gripper.stop()
                    gripper_flag = 1    
                    
                #elif -x_release_threshold < delta_digit < x_release_threshold:
                #    print('no motion')
                #else:
                    #gripper.move(gripper.POSITION - 5,1,1)
                    #print('standby')

                #x_baseline = float(uSkin_data[2][0])
                
                print(delta_digit)
            
            else:
                gripper.home()
                kill_loop = 1

            past_data = present_data

            if kill_loop:               
                break

def slip_detection_thread(name):
    global uSkin_data
    global kill_loop
    kill_loop = False
    x_baseline = float(uSkin_data[2][AXIS_SEL])
    while True: #
            print(uSkin_data) #use time.sleep instead if you don't want to print
            #time.sleep(0.001)
            if(len(uSkin_data) > 1):
                if  x_baseline > 0:
                    if float(uSkin_data[2][AXIS_SEL]) - x_baseline > x_release_threshold: #stop when z axis is over than the threshold
                        #gripper.home()
                        gripper.move(FULLY_CLOSED, speed_value, force_value)
                        print('break the loop')
                        break
                elif x_baseline < 0:
                    if float(uSkin_data[2][AXIS_SEL]) + x_baseline > x_release_threshold: #stop when z axis is over than the threshold
                        #gripper.home()
                        gripper.move(FULLY_CLOSED, speed_value, force_value)
                        print('break the loop')
                        break
            if kill_loop:
                break


uSkin_thread = threading.Thread(target=thread_function, args=(1,)) #A thread for accessing uSkin data from the middleware
uSkin_thread.start()

#################################################################
debug_mode = 0 # set this to 1 if the gripper is not connected

if debug_mode != 1:
    try:
        print ('Opening Port...')
        gripper = Robotiq()
        gripper.__init__(port = 'COM3') 
        time.sleep(1)
        gripper.reset() # is it dangerous with uSkin installed?
        time.sleep(1)
        gripper.home()
        print('Port is opened')
        gripper.initialize_status_thread()

        
    except:
        print("Gripper cannot be found!")
########################### GUI Part here #####################    

def pos_callback():
    data = gripper.position()
    print(data)

def home_callback():
    global kill_loop
    kill_loop = True
    print("Home Position")
    gripper.home()

def move_callback():
    print("Moving...")
    position_value = int(dpg.get_value(slider_position))
    speed_value = int(dpg.get_value(slider_speed))
    force_value = int(dpg.get_value(slider_force))
    gripper.move(position_value, speed_value, force_value)

def stop_callback():
    #gripper.position()
    gripper.stop()

def read_position_callback(): # under development
    gripper.position()
    time.sleep(0.1)
    pos = rec
    print(pos)

def grip_uskin_callback():
    if(len(uSkin_data) > 0):
        print("Moving...")
        #position_value = int(dpg.get_value(slider_position))
        position_value = FULLY_CLOSED
        speed_value = int(dpg.get_value(slider_speed))
        force_value = int(dpg.get_value(slider_force))
        gripper.move(position_value, speed_value, force_value)
        
        while(True):
            #print(uSkin_data)
            time.sleep(0.1)
            if(len(uSkin_data) > 0):
                if int(uSkin_data[0]) > 0: #stop as soon as a touch is detected
                    gripper.stop()
                    break
            else:
                print("No data")
                break
            
    else:
        print("No data. Please check the middleware")

def release_demo_callback():
    if(len(uSkin_data) > 0):
        #close the gripper
        global rec
        global x_baseline   
        global x_release_threshold
        global speed_value
        global force_value
        
        print("Grasping...")
        position_value = FULLY_CLOSED
        speed_value = int(dpg.get_value(slider_speed))
        force_value = int(dpg.get_value(slider_force))
        gripper.move(position_value, speed_value, force_value)
        z_threshold = int(dpg.get_value(slider_z))
        x_release_threshold = int(dpg.get_value(slider_x))

        while(True): #grasp an object
            #print(uSkin_data) #use time.sleep instead if you don't want to print
            time.sleep(0.001)
            if(len(uSkin_data) > 1):
                if float(uSkin_data[2][2]) > z_threshold: #stop when z axis is over than the threshold
                    gripper.stop()
                    time.sleep(0.1)
                    break                    

        print("Touch detected") 
        #while(rec != b'ERR MOVE 07\n'): #wait until the gripper is ready
        print('wait')
        time.sleep(1)

        print("Force sensing...")
        #print(x_baseline)
        print(x_release_threshold)
        release_thread = threading.Thread(target=slip_detection_thread, args=(1,)) #A thread for accessing uSkin data from the middleware
        release_thread.start()
        
    else:
        print("No data. Please check the middleware")         
            
def increase_force_demo_callback():
    if(len(uSkin_data) > 0):
        #close the gripper
        global key_input
        global x_baseline   
        global x_release_threshold
        global speed_value
        global force_value

        print("Grasping...")
        position_value = FULLY_CLOSED
        speed_value = int(dpg.get_value(slider_speed))
        force_value = int(dpg.get_value(slider_force))
        gripper.move(position_value, speed_value, force_value)
        z_threshold = int(dpg.get_value(slider_z))
        x_release_threshold = int(dpg.get_value(slider_x))

        while(True): #grasp an object
            #print(uSkin_data) #use time.sleep instead if you don't want to print
            time.sleep(0.001)
            if(len(uSkin_data) > 1):
                if float(uSkin_data[2][2]) > z_threshold: #stop when z axis is over than the threshold
                    gripper.stop()
                    x_baseline = float(uSkin_data[2][AXIS_SEL])
                    time.sleep(0.1)
                    break                    

        print("Touch detected") 
        print('wait')
        time.sleep(1)

        print("Force sensing...")
        increase_force_thread = threading.Thread(target=force_sensing_thread_reversed, args=(1,)) #A thread for accessing uSkin data from the middleware
        increase_force_thread.start()  

#def check_message(name): # a thread for receiving socket messages
#    global rec
#    rec = ""
#    while(True):
#        if kill_threads:
#            break
#        rec = gripper.sock.recv(buffer_size)
#        if len(rec) > 0:
#            print(rec)        

#socket_thread = threading.Thread(target= check_message , args=(1,))
#socket_thread.start()

dpg.create_context()
dpg.create_viewport(width = 500, height = 400)
dpg.setup_dearpygui()

with dpg.window(label="Robotiq Gripper", width=500, height=400):
    dpg.add_button(label="Home", callback=home_callback)
    slider_position = dpg.add_slider_float(label="Position",default_value=40, min_value = 0, max_value=255)
    slider_speed = dpg.add_slider_float(label="Speed",default_value=5, min_value = 0, max_value=255)
    slider_force = dpg.add_slider_float(label="Force",default_value=1, min_value = 0, max_value=255)
    dpg.add_button(label="Pos", callback=pos_callback)
    dpg.add_button(label="Move", callback=move_callback)
    dpg.add_button(label="Stop", callback=stop_callback) 
    dpg.add_button(label="Grasp with uSkin", callback=grip_uskin_callback)
    dpg.add_button(label="Release Object Demo", callback=release_demo_callback)
    dpg.add_button(label="Increase Force Demo",callback=increase_force_demo_callback)
    slider_z = dpg.add_slider_int(label="Z threshold",default_value=300, min_value = 1, max_value=1000)
    slider_x = dpg.add_slider_int(label="X threshold",default_value=10, min_value = 1, max_value=5000)

dpg.show_viewport()
dpg.start_dearpygui()

#during closing app
gripper.home()

kill_threads = True

dpg.destroy_context()
sys.exit()