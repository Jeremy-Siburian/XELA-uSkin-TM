from xelamiddleware import *
import sys
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
message_no = 0

#initiate settings object before starting the server and client
settings = XELA_Settings(client_ip="192.168.0.111", server_ip = "192.168.0.111", client_port= 5000, server_port=5001)

#demo of the functions of XELA_Settings
print(settings.get_client())#print current client IP and Port
#settings.iamclient()#set local IP as client IP
#print(settings.get_client())
#settings.__client_ip = "4.4.4.4"#show that IP element is immutable
#print(settings.get_client())

#Server will be self
settings.iamserver()#required for XELA_Server app as it uses local IP instead of localhost
server = XELA_Server(settings,mydata.getdata)#pass in XELA_Settings object for IP and Port, second function must be the one which returns the dictionary to output data (for additional data, it should use client.getData() as base)

#Client will be self
settings.iamclient()
client = XELA_Client(settings,mydata.newdata)#pass in XELA_Settings object for IP and Port, second function must be the one which handles incoming data (storage), alternatively you can set request to client.getData() from your function to get latest info (safer)

# uSkin related
row = 4 # can be configured based on sensor model info
sda = 4
activation_threshold = 200
baseline_flag = 0
uSkin_data = []
baseline_avg = []
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
    global row
    global sda
    global x_pos
    global y_pos
    global z_axis_data
    
    x_pos = np.zeros((row,sda))
    y_pos = np.zeros((row,sda))
    
    x_spacing = 4.7
    y_spacing = 4.7

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
    global z_axis_data
    
    if len(Subtracted) > 0:
        for i in range (0, row * sda):           
            if(Subtracted[i*3+2] > activation_threshold): #if z-axis bigger than threshold
                active_taxel[i] = 1
            else:
                active_taxel[i] = 0
            z_axis_data[i] = Subtracted[i*3+2]
            
        generate_taxel()
        x_pos = x_pos * active_taxel
        y_pos = y_pos * active_taxel

        touch_detection.loc = []

        for i in range(len(active_taxel)):
            if active_taxel[i] == [0]:
                touch_detection.loc.append(i)
            
        touch_detection.loc = np.array(touch_detection.loc)
        return 1

    else:
        return -1

def do_clustering():
    global x_pos
    global y_pos
    global z_axis_data

    if  len(touch_detection.loc) != sda * row: #only perform DBSCAN if there is atleast 1 active taxel
        x_pos = np.transpose(np.delete(x_pos, touch_detection.loc))
        y_pos = np.transpose(np.delete(y_pos, touch_detection.loc))
        z_axis_data = np.transpose(np.delete(z_axis_data, touch_detection.loc))
        X = np.array(np.transpose([x_pos, y_pos]))
        
        #Compute DBSCAN
        db = DBSCAN(eps=7, min_samples=1).fit(X)
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
        do_clustering.centroid_x = []
        do_clustering.centroid_y = []

        key = Counter(labels).keys()

        for i in range(len(key)):
            do_clustering.centroid_x.append( round(np.sum(X[np.argwhere(labels == i),0] * z_axis_data[np.argwhere(labels == i)] /np.sum(z_axis_data[np.argwhere(labels == i)])),2))
            do_clustering.centroid_y.append( round(np.sum(X[np.argwhere(labels == i),1] * z_axis_data[np.argwhere(labels == i)]/np.sum(z_axis_data[np.argwhere(labels == i)])),2))

            #do_clustering.centroid_x.append( round(np.mean(X[np.argwhere(labels == i),0]),2)) #original without weight
            #do_clustering.centroid_y.append( round(np.mean(X[np.argwhere(labels == i),1]),2))

        sys.stdout.write('Centroid X : %s   ' % do_clustering.centroid_x)
        sys.stdout.write('Centroid Y : %s \033[0K\r' % do_clustering.centroid_y)

    else:
        do_clustering.centroid_x = []
        do_clustering.centroid_y = []
        sys.stdout.write('No touch \033[0K\r')        
    sys.stdout.flush()
    z_axis_data = np.zeros((row * sda,1))

def make(): 
    if(len(do_clustering.centroid_x)>0):
        x_list = [str(x) for x in do_clustering.centroid_x]
        y_list = [str(y) for y in do_clustering.centroid_y]
        #cluster_list = [str(z) for z in do_clustering.n_clusters_]
        points = []
        #points.append(str(do_clustering.n_clusters_))
        for i in range(min(len(x_list),len(y_list))):
            points.append((x_list[i],y_list[i]))
        points.append([str(1)])
        return points
    else:
        return []

def make_message():
    global message_no
    message_no += 1
    myc = client.getData().copy()
    try:
        myc["1"]["extradots"] = make()
    except Exception:
        pass
    return json.dumps(myc)

while True:    #your core method here to keep the app running. Once it ends, the program will close
    try:
        uSkin_data = split_data(client.getData())
        calculate_baseline(uSkin_data) #only calculate once unless there is an external trigger (baseline_flag == 0)
        if(len(uSkin_data) & len(baseline_avg) > 0):
            Subtracted = np.subtract(uSkin_data,baseline_avg)

        if touch_detection() == 1:
            do_clustering()
            
        mydata = make_message()

        time.sleep(0.001)
    except KeyboardInterrupt:
        break #break on KeyboardInterrupt

#turn all off
client.close()
server.close()

time.sleep(5) #safe sleep
sys.exit()
