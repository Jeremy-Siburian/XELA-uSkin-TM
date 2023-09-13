#!/usr/bin/env python3
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from xelamiddleware import *

import keyboard
import numpy as np
import time
from sklearn.cluster import DBSCAN
from collections import Counter

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
postdata = MyData() #keeping incoming and outgoing data separate is a good idea to avoid messages without new info.
message_no = 0

#initiate settings object before starting the server and client
settings = XELA_Settings(client_port= 5000, server_port=5001)#client_ip="192.168.0.111", server_ip = "192.168.0.111", #IPs can be left out when you use "Iam" functions
settings.iamserver()
settings.iamclient()

print(settings.get_client())#print current client IP and Port

server = XELA_Server(settings,postdata.getdata)#pass in XELA_Settings object for IP and Port, second function must be the one which returns the dictionary to output data (for additional data, it should use client.getData() as base)
client = XELA_Client(settings,mydata.newdata)#pass in XELA_Settings object for IP and Port, second function must be the one which handles incoming data (storage), alternatively you can set request to client.getData() from your function to get latest info (safer)

# uSkin related
model = "XR1946"

global row
global sda
global x_spacing
global y_spacing
global DBSCAN_eps #can be tuned to achieve desired clustering

if(model == "XR1844"):
    row = 4
    sda = 4
    x_spacing = 4.7
    y_spacing = 4.7
    DBSCAN_eps = 7

elif model == "XR1946":
    row = 4
    sda = 6 #actually number of sensors per sda
    x_spacing = 7.25
    y_spacing = 7.25
    DBSCAN_eps = 14

activation_threshold = 200
baseline_flag = 0
uSkin_data = []
baseline_avg = []
x_axis_data = np.zeros((row * sda,1))
y_axis_data = np.zeros((row * sda,1))
z_axis_data = np.zeros((row * sda,1))
active_taxel = np.zeros((row * sda,1))
#loc = []
Subtracted = []

def split_data(message):
    out = []
    if len(message) > 0:
        out = message[u"1"][u"data"].split(",")
    for i in range(0, len(out)):
        out[i] = int(out[i], 16)
        np.array(out)       
    return out

def calculate_baseline(uSkin_data):
    global baseline_flag
    global baseline_avg
    if(baseline_flag == 0):
        if(len(uSkin_data) > 0):
            print("calculating baseline")
            baseline_avg = uSkin_data
            print("calculation finished")
            baseline_flag = 1
            return baseline_avg    

def generate_taxel(): #generate taxel position
    global x_pos
    global y_pos
    global z_axis_data
    
    x_pos = np.zeros((row,sda))
    y_pos = np.zeros((row,sda))    

    for i in range(row):
        for j in range(sda):
            x_pos[i,j] = j * x_spacing
            y_pos[i,j] = i * y_spacing

    x_pos = np.reshape(x_pos, (row * sda,1))
    y_pos = np.reshape(y_pos, (row * sda,1))
    
    #return x_pos
    #return y_pos

def touch_detection(): #active taxel detection
    global Subtracted   
    global active_taxel
    global x_pos
    global y_pos
    global x_axis_data
    global y_axis_data
    global z_axis_data
    
    if len(Subtracted) > 0:
        for i in range (0, row * sda):           
            if(Subtracted[i*3+2] > activation_threshold): #if z-axis bigger than threshold
                active_taxel[i] = 1
            else:
                active_taxel[i] = 0
            x_axis_data[i] = Subtracted[i*3]
            y_axis_data[i] = Subtracted[i*3+1]
            z_axis_data[i] = Subtracted[i*3+2]
            
        generate_taxel()
        x_pos = x_pos * active_taxel
        y_pos = y_pos * active_taxel

        touch_detection.loc = []

        for i in range(len(active_taxel)):
            if active_taxel[i] == [0]:
                touch_detection.loc.append(i)
            
        touch_detection.loc = np.array(touch_detection.loc)
        if sum(active_taxel == 1) > 0:
            return 1
        else:
            return -1

    else:
        return -1

def clear_data():
    do_clustering.centroid_x = []
    do_clustering.centroid_y = []
    do_clustering.average_x = []
    do_clustering.average_y = []
    do_clustering.average_z = []    

def do_clustering():
    global x_pos
    global y_pos
    global x_axis_data
    global y_axis_data
    global z_axis_data

    do_clustering.centroid_x = []
    do_clustering.centroid_y = []
    do_clustering.average_x = []
    do_clustering.average_y = []
    do_clustering.average_z = []    

    if  len(touch_detection.loc) != sda * row: #only perform DBSCAN if there is atleast 1 active taxel
        x_pos = np.transpose(np.delete(x_pos, touch_detection.loc))
        y_pos = np.transpose(np.delete(y_pos, touch_detection.loc))
        x_axis_data = np.transpose(np.delete(x_axis_data, touch_detection.loc))
        y_axis_data = np.transpose(np.delete(y_axis_data, touch_detection.loc))
        z_axis_data = np.transpose(np.delete(z_axis_data, touch_detection.loc))
        X = np.array(np.transpose([x_pos, y_pos]))
        
        #Compute DBSCAN
        db = DBSCAN(DBSCAN_eps, min_samples=1).fit(X)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        labels_true = np.reshape(active_taxel, (row * sda, 1))
        do_clustering.n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

        n_noise_ = list(labels).count(-1)  

        sys.stdout.write("Estimated number of clusters: %d   " % do_clustering.n_clusters_)
        #print('Estimated number of noise points: %d' % n_noise_)
        # Calculate centroid
   

        key = Counter(labels).keys()

        for i in range(len(key)):
            # centroid
            do_clustering.centroid_x.append( round(np.sum(X[np.argwhere(labels == i),0] * z_axis_data[np.argwhere(labels == i)] /np.sum(z_axis_data[np.argwhere(labels == i)])),2))
            do_clustering.centroid_y.append( round(np.sum(X[np.argwhere(labels == i),1] * z_axis_data[np.argwhere(labels == i)]/np.sum(z_axis_data[np.argwhere(labels == i)])),2))

            #do_clustering.centroid_x.append( round(np.mean(X[np.argwhere(labels == i),0]),2)) #original without weight
            #do_clustering.centroid_y.append( round(np.mean(X[np.argwhere(labels == i),1]),2))

            # average force (digit)
            do_clustering.average_x.append( round(np.sum(x_axis_data[np.argwhere(labels == i)]/ np.sum(labels == i)),2))
            do_clustering.average_y.append( round(np.sum(y_axis_data[np.argwhere(labels == i)]/ np.sum(labels == i)),2))
            do_clustering.average_z.append( round(np.sum(z_axis_data[np.argwhere(labels == i)]/ np.sum(labels == i)),2))

        sys.stdout.write('Average X : %s   ' % do_clustering.average_x)
        sys.stdout.write('Average Y : %s   ' % do_clustering.average_y)
        sys.stdout.write('Average Z : %s   ' % do_clustering.average_z)
        sys.stdout.write('Centroid X : %s   ' % do_clustering.centroid_x)
        sys.stdout.write('Centroid Y : %s \033[0K\r' % do_clustering.centroid_y)

    else:
        clear_data()
        
    sys.stdout.flush()
    x_axis_data = np.zeros((row * sda,1))
    y_axis_data = np.zeros((row * sda,1))
    z_axis_data = np.zeros((row * sda,1))

def make(): 
    if(len(do_clustering.centroid_x)>0):
        x_list = [str(x) for x in do_clustering.centroid_x]
        y_list = [str(y) for y in do_clustering.centroid_y]

        avg_x_list = [str(i) for i in do_clustering.average_x]
        avg_y_list = [str(i) for i in do_clustering.average_y]
        avg_z_list = [str(i) for i in do_clustering.average_z]

        points = []
        points.append(str(str(do_clustering.n_clusters_)))
        for i in range(min(len(x_list),len(y_list))):
            points.append((x_list[i],y_list[i]))
            points.append((avg_x_list[i],avg_y_list[i],avg_z_list[i]))
      
        return points
    else:
        return ["0"]

def make_message():
    global message_no
    message_no += 1
    myc = mydata.getdata().copy()#make a copy of the data
    try:
        #nyc = myc
        #nyc["extradots"] = make() #use the first 2 if you want to add clustering info and the next one for only the specific data
        nyc = {
            "message":myc["message"],
            "time":myc["time"],
            "data":make()
        }
    except Exception as e:
        #you can also forward the error to the client if needed
        nyc = {
            "message":"Error",
            "time":message_no,
            "data":[str(type(e).__name__),str(e)]
        }
    return nyc#the server will handle JSON.dumps on the data, so keep clean dict here

while True:    #your core method here to keep the app running. Once it ends, the program will close
    try:
        uSkin_data = split_data(client.getData())
        if keyboard.is_pressed('b'):
            baseline_flag = 0
            
        calculate_baseline(uSkin_data) #only calculate once unless there is an external trigger (baseline_flag == 0)
        if(len(uSkin_data) & len(baseline_avg) > 0):
            Subtracted = np.subtract(uSkin_data,baseline_avg)

        if touch_detection() == 1:
            #at times the clustering function encountered an error. It is always advisable to have a try-catch block to avoid application crash
            try:
                do_clustering()
            except Exception as e:
                print("Exception [DC]: {}: {}\033[0K".format(type(e).__name__, e),end="\r")#DC stands for "do_clustering"
                pass
        else:           
            sys.stdout.write('No touch \033[0K\r')        
        
        postdata.newdata(make_message())
        clear_data()

        time.sleep(0.001)
    except KeyboardInterrupt:
        break #break on KeyboardInterrupt

#turn all off
client.close()
server.close()

time.sleep(5) #safe sleep
sys.exit()
