#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dearpygui.dearpygui as dpg
import numpy as np
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentdir)
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from SensorUtils.xelamiddleware import *


# Setttings
sample_num = 500  # for calibration
Hz = 100         # sampling rate

num_axis = 3
num_taxel_rows = 4
num_taxel_cols = 4
num_patch = 3


class XELATactilePlotter(object):
    def __init__(self, ):
        self.stoprequest = False
        self.min_val = 0
        self.max_val = 2500
        self.elements = 1000
        self.axis_num = 3
        self.sensor_num = 1
        self.taxel_rows = 4
        self.taxel_cols = 6
        
        self.x_data = [self.min_val for _ in range(self.elements+1)]
        # self.y_data = [self.min_val for _ in range(self.elements+1)]
        self.z_data = [self.min_val for _ in range(self.elements+1)]
        self.baseline_x = -1
        self.baseline_y = -1
        self.baseline_z = -1
        self.mx = np.array([self.max_val+1 for _ in range(self.elements+1)])
        self.mn = np.array([self.min_val-1 for _ in range(self.elements+1)])
        self.data_len: int = 1001
        self.x_data_line: np.ndarray = np.linspace(0, self.data_len - 1, self.data_len)
        self.tactile_data =  np.zeros((self.data_len, self.taxel_rows*self.taxel_cols*self.axis_num))
        # self.fig, self.ax = plt.subplots(figsize=(12, 12))
        # self.fig.canvas.manager.set_window_title('Average values of the axes')
        # #ax.set_autoscale_on(False)
        # #ax = np.arange(0, 10, 0.1)
        # self.ax.set_autoscale_on(False)
        # plt.axis([0.0,20.0,0.0,10.0])
        self.running = True
        self.initialize_widget()
        # self.run_real_time_tactile_plot()
    def initialize_widget(self,):
        dpg.create_context()
        dpg.create_viewport(title='Plot view port', width=420, height=300)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        self.elapsed_time: float = 0.0
        self.interval: float = 0.05

        with dpg.window(label='Plot window', width=-1, height=-1):
            with dpg.plot(label=f"Real time plot \n interval: {self.interval} sec", width=400, height=250):
                dpg.add_plot_legend()  # 凡例追加
                # x, y軸追加
                dpg.add_plot_axis(dpg.mvXAxis, label='x', tag='xaxis')
                dpg.add_plot_axis(dpg.mvYAxis, label='y', tag='yaxis')
                # データ線追加, 親は最後に追加したアイテム (=y軸)
                # print("y_data size",np.array(self.y_data).shape)
                self.y_data = np.empty(self.data_len)
                self.y_data[:] = np.nan
                dpg.add_line_series(self.x_data_line, self.tactile_data, label='data', parent=dpg.last_item(), tag='line')

    def get_system_state(self, isAlive):
        self.running = isAlive

    def get_tactile_data(self,):
        self.tactile_data = client.getData()
        # try:
        #     xs = [self.tactile_data[x*3] for x in range(int(len(self.tactile_data)/3))]
        #     ys = [self.tactile_data[x*3+1] for x in range(int(len(self.tactile_data)/3))]
        #     zs = [self.tactile_data[x*3+2] for x in range(int(len(self.tactile_data)/3))]
        #     #calculate baseline
        #     if self.baseline_x == -1:
        #         self.baseline_x = xs
        #     if self.baseline_y == -1:
        #         self.baseline_y = ys
        #     if self.baseline_z == -1:
        #         self.baseline_z = zs
        #     #add the averages to the list of data and remove the first element
        #     self.x_data.append(self.avg([self.baseline_x[i]-xs[i] for i in range(len(xs))]))
        #     del self.x_data[0]
        #     self.y_data.append(self.avg([self.baseline_y[i]-ys[i] for i in range(len(ys))]))
        #     del self.y_data[0]
        #     self.z_data.append(self.avg([self.baseline_z[i]-zs[i] for i in range(len(zs))]))
        #     del self.z_data[0]
        # except KeyboardInterrupt:
        #     stoprequest = True
        # except Exception as e:
            # print(f"{type(e).__name__}:{e}")
        print(self.tactile_data)
        
    def avg(self, data):
        l = len(data)
        s = sum(data)
        a = abs(s/l)
        return a if a < self.max_val-1 else self.max_val-1

    def plot_callback(self,) -> None:
        # 第1引数は値を入力したいアイテムのtag (= dpg.add_line_series(tag='line'))
        dpg.set_value('line', [self.x_data_line, self.tactile_data])

    def run_real_time_tactile_plot(self,):
        while dpg.is_dearpygui_running():
            total_time = dpg.get_total_time()  # 画面が開いてからのトータル時間 (秒)
            # interval 秒経過したらグラフ更新
            if total_time - self.elapsed_time >= self.interval:
                self.elapsed_time = total_time
                # print("ewwafsfsfs")
                self.plot_callback()
            dpg.render_dearpygui_frame()
            # starttime = time.time()
            # if self.stoprequest:
            #     break
            # try:
   
            #     #make all axis histories into numpy arrays
            #     xn = np.array(self.x_data)
            #     yn = np.array(self.y_data)
            #     zn = np.array(self.z_data)
            #     # print(xn, yn, zn)
            #     self.ax.cla() #Clear the plot to avoid overdraw
            #     self.ax.plot(self.mx)
            #     self.ax.plot(self.mn)
            #     self.ax.plot(xn, color='#FF0000', label='X-axis')
            #     self.ax.plot(yn, color='#00FF00', label='Y-axis')
            #     self.ax.plot(zn, color='#0099FF', label='Z-axis')
            #     #draw the legend
            #     self.ax.legend()
            #     #force the limits
            #     self.ax.set_xlim(0, self.elements)
            #     self.ax.set_ylim(self.min_val, self.max_val)
            #     #draw the plot and wait 10 ms before doing it again
            #     plt.pause(0.1)
            # except KeyboardInterrupt:
            #     self.stoprequest = True
            # except Exception as e:
            #     print(f"{type(e).__name__}:{e}")
        dpg.destroy_context()
            # self.r.sleep()
            # print(time.time()-starttime)

class MyData(object):
    def __init__(self):
        self.__data = {}
    def newdata(self,data):
        self.__data = data
        #print("New data: {}".format(data))
    def getdata(self):
        return self.__data


if __name__ == '__main__':
    settings = XELA_Settings(client_port= 5001, server_port=5003)
    settings.iamserver()
    settings.iamclient()
    mydata = MyData()
    client = XELA_Client(settings,mydata.newdata)
    tacplot = XELATactilePlotter()
    tacplot.run_real_time_tactile_plot()
