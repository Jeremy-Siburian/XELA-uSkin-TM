#!/usr/bin/env python3
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from xelamiddleware import *
import sys
import numpy as np
import time

#example data container
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

#initiate settings object before starting the server and client
settings = XELA_Settings(client_port= 5001, server_port=5002)#client_ip="192.168.0.111", server_ip = "192.168.0.111", #IPs can be left out when you use "Iam" functions

#demo of the functions of XELA_Settings
print(settings.get_client())#print current client IP and Port


#Client will be self
settings.iamclient() # will automatically detect your IP Address
client = XELA_Client(settings,mydata.newdata)#pass in XELA_Settings object for IP and Port, second function must be the one which handles incoming data (storage), alternatively you can set request to client.getData() from your function to get latest info (safer)

# uSkin related
uSkin_data = []

#loc = []


def split_data(message): # For accessing JSON data
    out = []
    if len(message) > 0:
        #out = message[u"1"][u"data"].split(",") #originally to access the raw sensor data
        out = message[u"data"] #to access high level data
    #for i in range(0, len(out)):
    #    out[i] = int(out[i], 16)
    #    np.array(out)       
    return out

while True:    #your core method here to keep the app running. Once it ends, the program will close
    try:
        #data = client.getData() #use this to see the original data with time stamps 

        data = split_data(client.getData())
        #data format: [number of clusters],[[cluster_n_centroid_x, cluster_n_centroid_y, [....]]    
        print(data)

        time.sleep(0.001)
    except KeyboardInterrupt:
        break #break on KeyboardInterrupt

#turn all off
client.close()

time.sleep(5) #safe sleep
sys.exit()
