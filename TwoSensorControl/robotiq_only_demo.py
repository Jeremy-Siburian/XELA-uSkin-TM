from copy import deepcopy
import sys
import time
import numpy as np
import os

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentdir)
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from SensorUtils.xelamiddleware import *

from GripperControl.UR_robotiq_library import *

from SensorUtils.xela_tactile_map import *
from SensorUtils.xela_tactile_plotter import *
from SensorUtils.tactile_gui import *
from SensorUtils.xela_utils import *

import socket
from threading import Thread, Lock
# from my_robot_common.import_me_if_you_can import say_it_works
# from xela_robotiq_gripper import XELARobotiqGripper
from sklearn.cluster import DBSCAN
import collections
#from getkey import getkey

import os
skipnet = os.environ.get("SKIPNET", False) == "1"
if skipnet:
    print("""    \033[5m\033[31m**********************************************
    *\033[0m \033[33mWARNING: Gripper communication is skipped.\033[0m \033[5m\033[31m*
    **********************************************\033[0m""")

#USKIN
monitored_sensor1 = 1 
monitored_sensor2 = 2 

#GRASP_PLANNING
slip_threshold = 20
x_slip_threshold = 150
z_softness_threshold = 100
# max_grip_force = 2500
max_grasp_width = 250
min_touch_force = 500
grasp_force_slip = 1500

RUNNING = Bit(True)

#Socket setings
Hz=100
uSkin_data = []
baseline_avg = []
landscape = Bit(True)

slip_flag = False
slip_state = [False, []]
slip_detection_mode = True
prev_slip_detection_mode = False
gripper_activation_mode = True
touch_flag = False
finish_slip_demo = False
baseline_flag = False
deformation_flag = False
feedback_control = "force"
demonstration_mode = 0
mutex = Lock()
cluster_lock = Lock()
slipper_lock = Lock()
baselin_lock = Lock()

x_spacing = 1
y_spacing = 1
kill_loop = False


class KeyboardHandler():
    def __init__(self, ):
        pass
    def ask_input(self,functions:str="ftsbg"):
        global slip_detection_mode
        global gripper_activation_mode
        global demonstration_mode
        global baseline_flag
        global mutex
        # used_functions = ["q"]
        used_functions = [""]
        used_functions.extend([*functions])
        print("------------------------------------------")
        print("Please type a command ")
        print("------------------------------------------")
        if "s" in used_functions:
            print("s: Slip on")
        if "f" in used_functions:
            print("f: Slip off")
        if "g" in used_functions:
            print("g: Gripper open")
        if "t" in used_functions:
            print("t: Gripper close")
        if "b" in used_functions:
            print("b: Baseline sensors")
        # print("q: Kill system")
        print("------------------------------------------")
        #confirmed = False
        valid = False
        while not valid:
            # input_str = input("Enter a command: ")
            input_str = getkey()
            valid = input_str in used_functions#["g", "s", "a", "m", "b", "q"]
            if valid:
                mutex.acquire()
                # if input_str == "q":
                #     print(f"{Color.YELLOW}Q pressed: {Color.RED}Shutting down{Color.END}")
                #     mutex.release()
                #     gripper_activation_mode = False
                #     sys.exit()
                if input_str == "s":
                    slip_detection_mode = True
                    print(f"{Color.YELLOW}S pressed: Slip detection on{Color.END}")
                elif input_str == "f":
                    slip_detection_mode = False
                    print(f"{Color.YELLOW}S pressed: Slip detection off{Color.END}")
                elif input_str == "b":
                    print(f"{Color.YELLOW}B pressed: {Color.BLUE}Running baseline{Color.END}")
                    detector.reset(True)
                    baseline_flag = True
                elif input_str == "t":
                    gripper_activation_mode = True
                    print(f"{Color.YELLOW}G pressed: Gripper close {Color.END}") 
                elif input_str == "g":
                    gripper_activation_mode = False
                    print(f"{Color.YELLOW}G pressed: Gripper open {Color.END}") 
                mutex.release()
            else:
                print("No valid command")
                valid = False
        return input_str

class SensorClusteringModel(object):
    #Special Class only for Clustering model
    def __init__(self, gripper):
        self.inlock = Lock()
        self.cent = Lock()
        self.baseline_avg = [0 for _ in range(144)]
        self.threshold = 200
        self.lastdata = []
        self.running = False
        self.set_specs(4,6,100,100,147)#specs for 4x4 sensors #default is self.set_specs(4,4,4.7,4.7,7)
        self.reset_data()
        self.indata = []
        self.thr = threader(self._run)
        self.clusters = []
        self.prev_centroid_x = [0]
        self.prev_centroid_y = [0]
        self.FULLY_OPEN = 0
        self.FULLY_CLOSED = 255 #in reality maybe it is lower than this
        self.gripper = gripper
        self.kill_loop = False

    def get_tactile_data(self, data):
        self.tactile_data = data

    def _run(self):
        global slip_flag
        count=0
        past_data = np.array([self.indata.copy()[x] for x in range(int(len(self.indata.copy()))) if x % 3 == 2])
        while RUNNING:
            try:
                if self.indata:
                    #print(".",end="")
                    self.inlock.acquire(True,3)
                    data = self.indata.copy()
                    self.indata=[]
                    self.inlock.release()
                    if data is None:
                        self.lastdata = []
                    else:
                        self.reset_data()
                        self.data = data
                        baselined = self.calculate_baseline(data)
                        if baselined:
                            self.delta = np.subtract(data,self.baseline_avg)
                            self.deltas = np.array(self.delta.tolist())
                            if self.touch_detection():
                                count+=1
                                # self.do_clustering()
                                self.detect_slip_thre()
                                self.lastdata = self.make()
                                # if count==10:
                                #     # past_data = np.array(self.prev_data)
                                #     # print(self.data)
                                #     self.detect_slow_slip_thre(past_data)
                                #     count=0
                                #     past_data = np.array([self.prev_data[x] for x in range(int(len(self.prev_data))) if x % 3 == 2])
                            else:
                                slip_flag = False
                                self.lastdata = []
                    self.prev_data = self.data
            except Exception as e:
                print(f"SCM264: {e2t(e)}")
                self.lastdata = []
            time.sleep(0.001)

    def func(self, d, p=None):
        newdata = []
        return newdata

    def run(self,data):
        if self.inlock.locked():
            return
        self.inlock.acquire(True,3)
        indata1 = [int(x,16) for x in data[str(monitored_sensor1)]["data"].split(",")]
        indata2 = [int(x,16) for x in data[str(monitored_sensor2)]["data"].split(",")]
        self.indata = indata2 + indata1
        self.inlock.release()
        # print("self.indata",np.array(self.indata))
        return self.indata
    
    def set_specs(self,row:int=0,sda:int=0,x_s:float=0,y_s:float=0,eps:int=0):#Clustering special
        self.row = row
        self.sda = sda
        self.taxels = row * sda
        self.active_taxel = np.zeros((self.taxels,1))
        self.x_spacing = x_s
        self.y_spacing = y_s
        self.eps = eps
        self.reset()
    def pos_reset(self):
        self.x_pos = np.zeros((self.row,self.sda))
        self.y_pos = np.zeros((self.row,self.sda))
    def reset_axis(self):
        self.x_axis_data = np.zeros((self.taxels))
        self.y_axis_data = np.zeros((self.taxels))
        self.z_axis_data = np.zeros((self.taxels))
    def reset_data(self):
        self.centroid_x = []
        self.centroid_y = []
        self.cent.acquire(True,2)
        self.cent_x = []
        self.cent_y = []
        self.cent.release()
        self.average_x = []
        self.average_y = []
        self.average_z = []
    def reset(self,rebaseline=False):#Clustering special
        global slip_flag
        slip_flag = False
        cluster_lock.acquire(True,1)
        slipper_lock.acquire(True,1)
        baselin_lock.acquire(True,1)
        self.delta = []
        self.deltas = np.array([0 for _ in range(self.taxels*3)])
        self.loc = []
        self.pos_reset()
        self.reset_axis()
        self.baseline_flag = rebaseline
        self.reads = 0
        self.last0count = 0
        self.sensor_data = []
        if self.baseline_flag:
            self.baseline_avg = [0 for _ in range(self.taxels*3)]
        self.reset_data()
        cluster_lock.release()
        slipper_lock.release()
        baselin_lock.release()
    def calculate_baseline(self, data):
        try:
            if not self.baseline_flag or sum(self.baseline_avg) == 0:
                baselin_lock.acquire(True,1)
                if(len(data) > 0):
                    if self.reads > 20:
                        self.baseline_avg = data
                        self.baseline_flag = True
                        self.reads = 0
                        return True
                    self.reads += 1
                baselin_lock.release()
                return False
            else:
                return True
        except Exception as e:
            print(f"CB328: {e2t(e)}")
            return False

    def detect_softness(self,):
        # global uSkin_data
        global deformation_flag
        try:
            cluster_lock.acquire(True,1)
            if(len(self.data) > 1):
                past_data = np.array(self.prev_data)
                current_position = self.gripper.position()
                moved_range = current_position - prev_position
                present_data = np.array(self.data)
                delta_digit =  present_data - past_data
                if (moved_range > 1) and any(delta_digit < z_softness_threshold):
                    deformation_flag = True
                else:
                    deformation_flag = False
            past_data = present_data
            prev_position = current_position
            cluster_lock.release()
        except IndexError:
            deformation_flag = False
            pass
        except Exception as e:
            print(f"CLUS: DC Error2: {e2t(e)}")

    def detect_slip_thre(self,):
        # global uSkin_data
        global slip_flag
        global slip_state
        past_data = np.array(self.prev_data)
        # past_data = np.array([self.prev_data[x*3+1] for x in range(int(len(self.prev_data)/3))])
        counter = 0
        try:
            cluster_lock.acquire(True,1)
            if(len(self.data) > 1):
                # print(np.array(self.data).shape)
                
                present_data = np.array(self.data)
                delta_digit =  present_data - past_data
                # print("delta_digit",delta_digit)
                if any(abs(delta_digit) > slip_threshold):
                    slip_flag = True
                    slip_state[0] = slip_flag
                    slip_state[1] = delta_digit
                else:
                    slip_flag = False
                    slip_state[0] = slip_flag
                # print(delta_digit)
                # print("slip_flag", slip_flag)
            past_data = present_data
            cluster_lock.release()
        except IndexError:
            slip_flag = False
            pass
        except Exception as e:
            print(f"CLUS: DC Error: {e2t(e)}")

    def detect_slow_slip_thre(self,past_data):
        # global uSkin_data
        global slip_flag
        # past_data = np.array(self.prev_data)
        # past_data = np.array([self.prev_data[x] for x in range(int(len(self.prev_data))) if x % 3 != 2])
        counter = 0
        # print("self.data",self.data)
        try:
            cluster_lock.acquire(True,1)
            if(len(self.data) > 1):
                # print(np.array(self.data).shape)
                present_data = np.array([self.data[x] for x in range(int(len(self.data))) if x % 3 == 2])
                delta_digit =  abs(present_data - past_data)
                print("delta_digit",delta_digit)
                print("delta_digit",any(delta_digit))
                if any(delta_digit > 500):
                    slip_flag = True
                else:
                    slip_flag = False
                # print(delta_digit)
                # print("slip_flag", slip_flag)
            # past_data = present_data
            cluster_lock.release()
        except IndexError:
            slip_flag = False
            pass
        except Exception as e:
            print(f"CLUS: DC Error: {e2t(e)}")
                
    def generate_taxel(self): #generate taxel position
        try:    
            self.pos_reset()
            for i in range(self.row):
                for j in range(self.sda):
                    self.x_pos[i,j] = j * self.x_spacing
                    self.y_pos[i,j] = i * self.y_spacing
            self.x_pos = np.reshape(self.x_pos, (self.taxels,1))
            self.y_pos = np.reshape(self.y_pos, (self.taxels,1))
        except Exception as e:
            print(f"GT342: {e2t(e)}")

    def touch_detection(self) -> bool: #active taxel detection
        self.reset_axis()
        i = -1
        try:
            if len(self.delta) > 0:
                for i in range (0, self.taxels): 
                    if self.delta[i*3+2] > self.threshold:
                        self.active_taxel[i] = 1
                    else:
                        self.active_taxel[i] = 0
                    self.x_axis_data[i] = self.delta[i*3]
                    self.y_axis_data[i] = self.delta[i*3+1]
                    self.z_axis_data[i] = self.delta[i*3+2]
                self.generate_taxel()
                self.x_pos = self.x_pos * self.active_taxel
                self.y_pos = self.y_pos * self.active_taxel
                self.loc = []
                for i in range(len(self.active_taxel)):
                    if self.active_taxel[i] == [0]:
                        self.loc.append(i)
                self.loc = np.array(self.loc)
                if sum(self.active_taxel == 1) > 0:
                    return True
            return False
        except Exception as e:
            print(f"TD366: {e2t(e)}")
            return False  

    def do_clustering(self):
        global slip_flag
        labels = []
        key=[]
        try:
            cluster_lock.acquire(True,1)
            self.reset_data()
            #self.reset_axis()
            if  len(self.loc) != self.taxels: #only perform DBSCAN if there is atleast 1 active taxel
                self.x_pos = np.transpose(np.delete(self.x_pos, self.loc))
                self.y_pos = np.transpose(np.delete(self.y_pos, self.loc))
                self.x_axis_data = np.transpose(np.delete(self.x_axis_data, self.loc))
                self.y_axis_data = np.transpose(np.delete(self.y_axis_data, self.loc))
                self.z_axis_data = np.transpose(np.delete(self.z_axis_data, self.loc))
                X = np.array(np.transpose([self.x_pos, self.y_pos]))
                
                #Compute DBSCAN
                db = DBSCAN(self.eps, min_samples=1).fit(X)
                core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
                core_samples_mask[db.core_sample_indices_] = True
                labels = db.labels_

                # Number of clusters in labels, ignoring noise if present.
                #labels_true = np.reshape(self.active_taxel, (self.taxels, 1))
                #n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

                #n_noise_ = list(labels).count(-1)
                # Calculate centroid
                key = collections.Counter(labels).keys()
                for i in range(min(len(key),self.taxels)):
                    # centroid
                    try:
                        xp = np.argwhere(labels == i)
                        zxp = self.z_axis_data[xp]
                        zxp_sum = np.sum(zxp)
                        lsum=np.sum(labels == i)
                        if zxp_sum != 0 and lsum != 0:
                            self.centroid_x.append(round(np.sum(X[xp,0]*zxp/zxp_sum),2))
                            self.centroid_y.append(round(np.sum(X[xp,1]*zxp/zxp_sum),2))
                            # average force (digit)
                            self.average_x.append(round(np.sum(self.x_axis_data[xp]/lsum),2))
                            self.average_y.append(round(np.sum(self.y_axis_data[xp]/lsum),2))
                            self.average_z.append(round(np.sum(zxp/lsum),2))
                    except Exception as ei:
                        pass#ERRMGR._log(f"Centroid error: {e2t(ei)} | {trace(ei,returnonly=True)}",["CLUS","blue"])
                # self.cent.acquire(True,1)
                # self.cent_x = self.centroid_x.copy()
                # self.cent_y = self.centroid_y.copy()
                # self.cent.release()
                if self.centroid_x and self.centroid_y:
                    cx = self.centroid_x[0] - self.prev_centroid_x[0]
                    cy = self.centroid_y[0] - self.prev_centroid_y[0]
                    lx = len(self.centroid_x)
                    ly = len(self.centroid_y)
                    # print(f"centroid X: {self.centroid_x}, Y: {self.centroid_y}\t\tPREV: X: {self.prev_centroid_x}, Y: {self.prev_centroid_y}\t\tDelta: x: {cx}, y: {cy}\t\tLength: x: {lx}, y: {ly}")
                    if lx != 1 or ly != 1:#if len(self.centroid_x) != len(self.centroid_y) or len(self.centroid_x) != 1:  
                        # if each size is different, touch states other than slip must happen (such as a multiple touch)
                        pass
                    else:
                        try:
                            if demonstration_mode==1: 
                                centroid_x_thre = 13.0
                                centroid_y_thre = 13.0
                            elif demonstration_mode==2: 
                                centroid_x_thre = 13.0
                                centroid_y_thre = 13.0
                            else:
                                centroid_x_thre = 0.2
                                centroid_y_thre = 0.2
                            # print("abs(cx)",abs(cx))
                            # print("abs(cy)",abs(cy))
                            # if (np.abs(np.array(self.centroid_x) - np.array(self.prev_centroid_x)) > 0.1).any() and (np.abs(np.array(self.centroid_y) - np.array(self.prev_centroid_y)) > 0.1).any():
                            if abs(cx) > centroid_x_thre or abs(cy) > centroid_y_thre:#if abs((self.centroid_x[0] - self.prev_centroid_x[0]) > 0.1) or abs((self.centroid_y[0] - self.prev_centroid_y[0]) > 0):
                                # print("ssssssssss")
                                if self.prev_centroid_x[0] > 0 and self.prev_centroid_y[0] > 0:
                                    slip_flag = True
                                    # print("ssssssssssa")
                                    # print(np.abs(np.array(centroid_x) - np.array(prev_centroid_x)))
                                    # print('\033[31m'+ "slip_flag " + str(slip_flag) +'\033[0m')
                                    ### when slip happens, error between original and current positions is over threshold,
                                    ### current position will become next prev_centroid to check error with next centroid 
                                self.prev_centroid_x = self.centroid_x
                                self.prev_centroid_y = self.centroid_y
                            else:
                                self.centroid_x = [0]
                                self.centroid_y = [0]
                                slip_flag = False
                                # print('\033[32m' + "slip_flag " + str(slip_flag) +'\033[0m')
                        except Exception as e:
                            print(f"CENTR: {e2t(e)}")
                            slip_flag = False
                else:
                    slip_flag = False
            else:
                slip_flag = False
                self.reset_data()
            cluster_lock.release()
        except IndexError:
            slip_flag = False
            pass
        except Exception as e:
            print(f"CLUS: DC Error: {e2t(e)}")
            #ERRMGR._log(f"Trace: {trace(e,returnonly=True)} with labels={labels}, key={key} and z_axis={self.z_axis_data}",["CLUS","yellow"])
        return self.centroid_x, self.centroid_y


    def make(self):

        if self.data is None:
            return None
        if(len(self.centroid_x)>0):
            x_list = [str(x/self.x_spacing) for x in self.centroid_x]
            y_list = [str(y/self.y_spacing) for y in self.centroid_y]

            #avg_x_list = [str(i) for i in self.average_x]
            #avg_y_list = [str(i) for i in self.average_y]
            avg_z_list = [str(i/25) for i in self.average_z]

            points = []
            for i in range(min(len(x_list),len(y_list))):
                points.append((x_list[i],y_list[i],avg_z_list[i]))
            #ERRMGR._log(f"CLUS: {points}")
            self.clusters = points
        else:
            #ERRMGR._log(f"CLUS: no points found")
            self.clusters = []
        return self.clusters

    def get(self):
        #return data for visualization here
        data = {
            "message": "GripperController",
            "slip": bool(slip_flag),
            # "baselined": bool(self.baseline_flag),
            # "reads": self.reads,
            "landscape": bool(landscape),
            # "baseline_avg": list(self.baseline_avg),
            "data": self.deltas.tolist(),
            "clusters": self.clusters
        }
        # print(f"GET REQ: {data}")
        return data

    def feedback_gripper_force(self,):
        global slip_state
        global slip_detection_mode
        global gripper_activation_mode
        global demonstration_mode
        global finish_slip_demo

        global force_sensing_flag
        
        process_time = time.time()
        
        back_flag = [False, 0]
        curr_time = -1
        grip_pos = None
        
        while True:
            grip_pos = gripper.position()[0]
            if grip_pos != None and not np.isnan(grip_pos):
                break

        print("Starting slip detection")
        print("Gripper position:", grip_pos)

        initial_grasp = grip_pos
        print("Initial grasping position: ",initial_grasp)
        position_value = initial_grasp
        speed_value = 1
        force_value = 1

        while RUNNING:
            # print("self.tactile_datax",np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 1]))
            # print("self.tactile_dataz",np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 2]))
            start_time = time.time()

            # print("slip_state[0]",slip_state[0])
            tacmap.get_slip_result(slip_state[0])
            if slip_state[0]:
                if back_flag[0] and back_flag[1] <20:
                    back_flag[1] += 1
                    continue
                elif back_flag[0] and back_flag[1]==20:
                    back_flag[0] = False
                    back_flag[1] = 0
                normal_baseline = np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 2]) # Normal 
                thear_delta = np.array([slip_state[1][x] for x in range(int(len(slip_state[1]))) if x % 3 == 1])
                gstart_time = time.time()
                # gripper.move(position_value, speed_value, force_value)
                gelaplsed_time = time.time() - gstart_time
                # print("gelaplsed_time",gelaplsed_time)
                while(True):
                    # if touch_count > 100:
                    #     break
                    #print("position_value",position_value)
                    #position_value +=1
                    gripper.move(FULLY_CLOSED, speed_value, force_value)
                    # print("self.tactile_data",self.tactile_data)
                    if(len(self.tactile_data) > 0):
                        
                        #print("self.tactile_dataz",np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 2]))
                        #print("self.tactile_datax",np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 1]))

                        tactile_normal = np.array([self.tactile_data[x] for x in range(int(len(self.tactile_data))) if x % 3 == 2])
                        if any(tactile_normal > (normal_baseline + thear_delta)):
                        # if any(tactile_normal > params["GRASP_PLANNING"]["grasp_force_slip"]):
                            #print("stop")
                            gripper.stop()
                            print("Gripper adjusted")
                            break
                    else:
                        print("No data")
                        break
      
            time.sleep(0.02) # consider 4x6 uSkin samping rate is 80 Hz
            
    def grasp_min_force(self,gripper):
        global uSkin_data
        print("Gripper moving...")
        
        speed_value = 1
        force_value = 1
        gripper.move(FULLY_CLOSED, speed_value, force_value)
        position_value = 0
        touch_baseline = np.array(uSkin_data)
        touch_baseline1 = touch_baseline[:72]
        touch_baseline2 = touch_baseline[72:]
        while(True):
            if(len(uSkin_data) > 0):
                uSkin_data1 = np.array(uSkin_data)[:72]
                uSkin_data2 = np.array(uSkin_data)[72:]
                if any((uSkin_data1 - touch_baseline1) > min_touch_force) and any((uSkin_data2 - touch_baseline2) > min_touch_force): #stop as soon as a touch is detected
                    # print((np.array(uSkin_data) - touch_baseline))
                    gripper.stop()
                    time.sleep(0.001)
                    break
            else:
                print("No data")
                break
            time.sleep(0.01)
        

if __name__ == "__main__":
    if os.name == 'posix': #Linux OS
        import getch as user_input
        portname = '/dev/ttyUSB0'
    else:
        import msvcrt as user_input #Windows OS
        portname = 'COM3' #must be auto detect / drop down menu
    gripper = Robotiq(portname)
    detector = SensorClusteringModel(gripper)
    tacmap = XELATactileMap()
    tacmap_thread = threader(tacmap.run_real_time_tactile_map)
    settings = XELA_Settings()
    settings.iamserver()
    settings.iamclient()

    tactile_client = XELA_Client(settings,detector.run) #incomingdata.newdata
    tactile_server = XELA_Server(settings,detector.get) #outgoingdata.getdata

    def split_data(message): # For accessing JSON data
        out = []
        if len(message) > 0:
            out1 = [int(x,16) for x in message[str(monitored_sensor1)]["data"].split(",")] #originally to access the raw sensor data
            out2 = [int(x,16) for x in message[str(monitored_sensor2)]["data"].split(",")] #originally to access the raw sensor data
            out = out2 + out1
            # print("out",message)
        return out

    def thread_function(name):
        global uSkin_data
        global baseline_flag
        mutex.acquire()
        baseline = split_data(tactile_client.getData())
        # print("baseline",baseline)
        mutex.release()
        while True:    #your core method here to keep the app running. Once it ends, the program will close
            # print("split_data(tactile_client.getData())",tactile_client.getData())
            try:
                mutex.acquire()
                uSkin_data = split_data(tactile_client.getData())
                mutex.release()
                if baseline_flag:
                    baseline = uSkin_data
                    mutex.acquire()
                    baseline_flag = False
                    mutex.release()
                mutex.acquire()
                tacmap.get_tactile_data(np.array(uSkin_data)-np.array(baseline))
                mutex.release()
                mutex.acquire()
                detector.get_tactile_data(np.array(uSkin_data)-np.array(baseline))
                mutex.release()
                time.sleep(0.01)
            except Exception as e:
                print(f"Tactile Error: {e2t(e)}")
                sys.exit()
            if not RUNNING:
                break

    uSkin_thread = threader(target=thread_function, args=(1,)) #A thread for accessing uSkin data from the middleware
    keyhandle = KeyboardHandler()


    def activate_gripper():
        time.sleep(1)
        #gripper.reset() # is it dangerous with uSkin installed?
        time.sleep(1)
        gripper.home()
        print('Port is opened')

    activate_gripper()
    time.sleep(5)

    while RUNNING:
        if gripper_activation_mode and not touch_flag:
            if(len(uSkin_data) > 0):
                detector.grasp_min_force(gripper)
                touch_flag = True
                print("touch_flag1",touch_flag)
                if slip_detection_mode:
                    finish_slip_demo = False
                    gripper_moving_thread = threader(target=detector.feedback_gripper_force)
            else:
                print("No data. Please check the middleware")
        elif gripper_activation_mode and touch_flag:
            pass

        else:
            finish_slip_demo = True
            touch_flag = False
            gripper.home()
    RUNNING.off()
    tacmap.get_system_state(RUNNING)
    tacmap_thread.join()