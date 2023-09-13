import asyncio
import socketio
loop = asyncio.get_event_loop()
sio = socketio.AsyncClient()
import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter
from threading import Thread
import time
import sys
import subprocess
subprocess.call('', shell=True)

row = 4
sda = 4
activation_threshold = 200
baseline_flag = 0
uSkin_data = []
baseline_avg = []
active_taxel = np.zeros((row * sda,1))

@sio.event
async def connect():
    print("Connection established")
    
@sio.event(namespace="/sensor1")
async def sensor_data(data):
    #normally the taxel data is in data element as list type string
    string_data = (data[u"data"])
    global uSkin_data
    uSkin_data = string_data.split(",")

    for i in range(0, len(uSkin_data)):
        uSkin_data[i] = np.array(int(uSkin_data[i], 16))
    #print(uSkin_data)

    # baseline calculation
    global baseline_flag
    global baseline_avg
    if(baseline_flag == 0):
        print("calculating baseline")
        baseline_avg = uSkin_data
        print("calculation finished")
        baseline_flag = 1 

    #print(np.subtract(uSkin_data,baseline_avg))
    Subtracted = np.subtract(uSkin_data,baseline_avg)
    #print(Subtracted)

    #generate taxel position
    x_spacing = 4.7
    y_spacing = 4.7

    global row
    global sda

    x_pos = np.zeros((row,sda))
    y_pos = np.zeros((row,sda))

    for i in range(row):
        for j in range(sda):
            x_pos[i,j] = j * x_spacing
            y_pos[i,j] = i * y_spacing

    return x_pos = np.reshape(x_pos, (row * sda,1))
    return y_pos = np.reshape(y_pos, (row * sda,1))
    
    #active taxel detection
    global active_taxel
    
    for i in range (0, row * sda):
       
        if(Subtracted[i*3+2] > activation_threshold): #if z-axis bigger than threshold
            active_taxel[i] = 1
        else:
            active_taxel[i] = 0
    #print(active_taxel)

    x_pos = x_pos * active_taxel
    y_pos = y_pos * active_taxel

    loc = []

    for i in range(len(active_taxel)):
        if active_taxel[i] == [0]:
            loc.append(i)
            
    loc = np.array(loc)
    
    if len(loc) != sda * row: #only perform DBSCAN if there is atleast 1 active taxel
        x_pos = np.transpose(np.delete(x_pos, loc))
        y_pos = np.transpose(np.delete(y_pos, loc))

        X = np.array(np.transpose([x_pos, y_pos]))

        #Compute DBSCAN
        db = DBSCAN(eps=7, min_samples=1).fit(X)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        labels_true = np.reshape(active_taxel, (row * sda, 1))
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)  

        sys.stdout.write("Estimated number of clusters: %d   " % n_clusters_)
        #print('Estimated number of noise points: %d' % n_noise_)
        
        # Calculate centroid
        centroid_x = []
        centroid_y = []

        key = Counter(labels).keys()

        for i in range(len(key)):
            centroid_x.append( round(np.mean(X[np.argwhere(labels == i),0]),2))
            centroid_y.append( round(np.mean(X[np.argwhere(labels == i),1]),2))

        sys.stdout.write('Centroid X : %s   ' % centroid_x)
        sys.stdout.write('Centroid Y : %s \033[0K\r' % centroid_y)

    else:
        sys.stdout.write('No touch \033[0K\r')
        
    sys.stdout.flush()

@sio.event
async def disconnect():
    print("Disconnected from server")

@sio.event
async def printing():
    print(uSkin_data)

async def start_server():
    """
using loop makes the application wait for connection
in case server takes too long to start
    """
    ncd = True
    while ncd:
        try:
            await sio.connect("http://localhost:5000", namespaces=["/sensor1"],transports=["polling"])
        except socketio.exceptions.ConnectionError:
            pass
        else:
            ncd = False
            break
        
    try:#make sure this is outside of while      
        await sio.wait()
        
    except KeyboardInterrupt:
        exit()


#run server
loop.run_until_complete(start_server())

