#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import rospy
#import rospkg
import numpy as np
from threading import Thread, Lock
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
mpl.rcParams['toolbar'] = 'None'
plt.style.use(['dark_background'])
# Setttings

class XELATactileMap(object):
    def __init__(self, ):
        # Constants
        self.zoom = 9
        self.axis_num = 3
        self.sensor_num = 2
        self.taxel_rows = 4*self.sensor_num
        self.taxel_cols = 6
        self.taxel_num = self.taxel_rows*self.taxel_cols
        self.width = int(830/10*self.zoom)  # width of the image
        self.height = int(650/10*self.zoom) # height of the image
        self.margin = 100/15*self.zoom  # margin of the taxel in the image
        self.pitch = 150/15*self.zoom  # pitch between taxels in the image
        self.scale = 50*10/self.zoom  # scale from the sensor data to the image
        self.tz = 12/12*self.zoom  # default size of the circle
        self.color = (25, 255, 25, 255)
        self.tactile_data =  np.zeros([self.taxel_rows*self.taxel_cols*self.axis_num])
        self.running = True
        self.slip_result = False
        # self.run_real_time_tactile_map()

    def get_system_state(self, isAlive):
        self.running = isAlive

    def get_tactile_data(self, data):
        self.tactile_data = data
        # print("self.tactile_data",self.tactile_data)

    def get_slip_result(self, result):
        self.slip_result = result

    def run_real_time_tactile_map(self,):
        count = 0
        sum_orig = []
        while self.running:
            img = np.zeros((self.height+80, self.width, int(3)), np.uint8)

            diff = np.array(self.tactile_data)
            dx = diff.reshape((self.taxel_num, 3))[:, 0]*-1 # -1 changes the direction of sensor chip movement on the map
            dy = diff.reshape((self.taxel_num, 3))[:, 1]*-1 # -1 changes the direction of sensor chip movement on the map
            dz = diff.reshape((self.taxel_num, 3))[:, 2]
            img[:] = (0, 0, 0)
            k = 0
            # If sersor orientation is different
            # for j in range(self.taxel_rows):
            #     for i in range(self.taxel_cols):
            for j in reversed(range(self.taxel_rows)):
                for i in reversed(range(self.taxel_cols)):
                    x = np.clip(self.width-self.margin-i*self.pitch-dx[k]/self.scale-80, 0, self.width)
                    y = np.clip(self.margin+j*self.pitch+dy[k]/self.scale, 0, self.height+130)
                    z = np.clip(self.tz+dz[k]/self.scale, 0, 100)
                    cv2.circle(img, (int(y), int(x)), int(z), self.color, -1)
                    # cv2.putText(img,  'X: {:>5}'.format(int(dx[i+6*j])), ((int(j*self.pitch+self.width-100+j*self.pitch), int(i*self.pitch+self.width/6-30))), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                    # cv2.putText(img,  'Y: {:>5}'.format(int(dy[i+6*j])), ((int(j*self.pitch+self.width-100+j*self.pitch), int(i*self.pitch+self.width/6))), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                    # cv2.putText(img,  'Z: {:>5}'.format(int(dz[i+6*j])), ((int(j*self.pitch+self.width-100+j*self.pitch), int(i*self.pitch+self.width/6+30))), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                    k = k+1
            cv2.putText(img,  'Left Finger', ((int(115), int(100))), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(img,  'Right Finger', ((int(460), int(100))), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            if self.slip_result:
                cv2.putText(img,  'SLIP HAPPENING', ((int(250), int(40))), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            elif not self.slip_result:
                cv2.putText(img,  'No Slip', ((int(320), int(40))), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            count += 1
            # orig = np.array(list(map(int, np.array(tactile_data).reshape(-1))))
            # calib = np.array(list(map(int, np.array(tactile_data_calib).reshape(-1))))
            # print(orig)
            # print(calib)
            # sum_orig.append(orig)
            # sum_calib.append(calib)
            cv2.imshow("Tactile Map", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


if __name__ == '__main__':
    tacmap = XELATactileMap()
