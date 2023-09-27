#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk # Tkinter for python2, tkinter for python3
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
import numpy as np
# from neuralnet import NeuralNet
import copy
import sys
import socket
import pickle
import time
from threading import Thread, Lock
from time import sleep
import os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from xelamiddleware import *
# import tensorflow  as tf
# sys.path.append('''C:/Users/funabashi/Desktop/XELA Robotics/magnetic_compensation/''')

ip = "192.168.0.113" #your computer IP on the network
# ip = "127.0.0.1" #your computer IP on the network
port = 5000 #the port the server is running on

# Setttings
sample_num = 300  # for calibration
Hz = 50         # sampling rate

# Parameters for tactile information
step_num = 60
zoom = 8
sensor_num = 1
axis_num = 3
taxel_rows = 4
taxel_cols = 6
taxel_num = taxel_rows*taxel_cols
val_tactile = np.zeros(taxel_rows*taxel_cols*axis_num)
log_dx = np.zeros((step_num, taxel_rows*taxel_cols))
log_dy = np.zeros((step_num, taxel_rows*taxel_cols))
log_dz = np.zeros((step_num, taxel_rows*taxel_cols))

# Parameters for loop system
state_text = 'Ready'
controller_state = 0
user_input = 0
slip_detector_mode = 0
counter = 0
logger_state = 0



class Application(tk.Frame):
    def __init__(self, master = None, messenger = None):
        super().__init__(master)
        self.ms = messenger
        self.mutex = Lock()
        time.sleep(0.5)
        self.base = np.zeros([taxel_num*axis_num*sensor_num])
        self.tactile_data = np.zeros([taxel_num*axis_num*sensor_num])
        # self.offset_tactile()
        # Tkinter Setting
        self.master = master
        self.master.geometry("750x500")
        self.master.title("XELA Tactile Graph")
        self.master.configure(bg="black")
        self.pack()
        self.create_widgets()
        self.plot_graph()
        # self.animate()
        self.master.mainloop()
        # self.map_taxel()
        # self.model=tf.keras.models.load_model("MachineLearnings/hoge.h5")

    def animate(self):
        plt.show()
        return self

    def init_datastream(self, ):
        # only required for blitting to give a clean state.
        # data_traj_list = [self.data_traj['x' + str(j)][0].set_ydata(np.zeros(step_num))
        #                   if i == 0 else self.data_traj['y' + str(j)][0].set_ydata(np.zeros(step_num)) 
        #                   if i == 1 else self.data_traj['z' + str(j)][0].set_ydata(np.zeros(step_num)) 
        #                   for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
        # data_traj_list = [self.data_traj['x' + str(j)][0] 
        #                   if i == 0 else self.data_traj['y' + str(j)][0] if i == 1 else self.data_traj['z' + str(j)][0]
        #                   for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
        data_traj_list = [self.data_traj[str(i) + str(j)][0].set_ydata(np.zeros(step_num))
                          for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
        data_traj_list = [self.data_traj[str(i) + str(j)][0]
                          for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
        return data_traj_list

    def create_widgets(self, ):
        self.canvas_frame = tk.Frame(self.master)
        self.canvas_frame.pack(side=tk.LEFT)
        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(side=tk.RIGHT)


        self.fig = Figure(facecolor="black", figsize=(13.5, 11), dpi=110)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master) # FuncAnimationより前に呼ぶ必要がある
        


        figure = plt.figure(figsize=(10, 8))
        gs_master = GridSpec(nrows=1, ncols=1)

        # gs_1 = GridSpecFromSubplotSpec(nrows=3, ncols=1, subplot_spec=gs_master[0:3, 0])
        # self.axes_1 = self.fig.add_subplot(gs_1[:, :])

        # gs_2_and_3_and_4 = GridSpecFromSubplotSpec(nrows=3, ncols=1, subplot_spec=gs_master[0:3, 0])
        # self.axes_2 = self.fig.add_subplot(gs_2_and_3_and_4[0, :])
        # self.axes_3 = self.fig.add_subplot(gs_2_and_3_and_4[1, :])
        # self.axes_4 = self.fig.add_subplot(gs_2_and_3_and_4[2, :])
        # self.axes_2.set_ylim([-5000, 5000])
        # self.axes_3.set_ylim([-5000, 5000])
        # self.axes_4.set_ylim([-5000, 5000])

        gs_5 = GridSpecFromSubplotSpec(nrows=1, ncols=1, subplot_spec=gs_master[0, :])
        self.axes_5 = self.fig.add_subplot(gs_5[:, :])
        
        self.axes_5.set_ylabel("Tactile Data (X,Y,Z) [digit]",fontsize=12)
        self.axes_5.yaxis.label.set_color('white')
        # self.axes_5.yaxis.set_label_coords(0,0.5)
        self.axes_5.set_ylim([-5000, 5000])
        self.axes_5.tick_params(axis='y', colors='w')
        
        self.axes_5.set_xlabel("Time [10ms]",fontsize=12)
        self.axes_5.xaxis.label.set_color('white')
        # self.axes_5.xaxis.set_label_coords(0.5,0)
        self.axes_5.tick_params(axis='x', colors='w')
        
        self.axes_5.set_facecolor('k')

        # plt_traj = {}
        # for i in range(axis_num):
        #     for j in range(taxel_rows*taxel_cols):
        #         if i == 0:
        #             axis_name = 'x'
        #         elif i == 1:
        #             axis_name = 'y'
        #         elif i == 2:
        #             axis_name = 'z'
        #         plt_traj[axis_name + str(j)] = self.fig.add_subplot(3,1,i+1)


        # plt_traj['x0'].set_ylim([-40000, 40000])
        # plt_traj['y0'].set_ylim([-40000, 40000])
        # plt_traj['z0'].set_ylim([-40000, 40000])
        # plt_traj['x0'].set_xlabel('steps', fontsize=18)
        # plt_traj['y0'].set_ylabel('force', fontsize=18)
        # plt_traj['z0'].set_xlabel('steps', fontsize=18)

        # # plt_y_0.set_ylabel('force y')
        # plt_traj['z0'].set_xlabel('steps', fontsize=18)
        # # plt_z_0.set_ylabel('force z')
        # plt.rcParams["font.size"] = 20
        # plt_traj['x0'].set_title('X', fontsize=30)
        # plt_traj['y0'].set_title('Y', fontsize=30)
        # plt_traj['z0'].set_title('Z', fontsize=30)
        # plt_traj['x0'].tick_params(labelbottom=True,
        #                     labelleft=True,
        #                     labelright=False,
        #                     labeltop=False,
        #                     bottom=False,
        #                     left=False,
        #                     right=False,
        #                     top=False)
        # plt_traj['y0'].tick_params(labelbottom=True,
        #                     labelleft=False,
        #                     labelright=False,
        #                     labeltop=False,
        #                     bottom=False,
        #                     left=False,
        #                     right=False,
        #                     top=False)
        # plt_traj['z0'].tick_params(labelbottom=True,
        #                     labelleft=False,
        #                     labelright=False,
        #                     labeltop=False,
        #                     bottom=False,
        #                     left=False,
        #                     right=False,
        #                     top=False)
        # plt_traj['x0'].grid(True)
        # plt_traj['y0'].grid(True)
        # plt_traj['z0'].grid(True)

        self.data_traj = {}
        placeholder = np.arange(0, step_num, 1)
        # for i in range(axis_num):
        #     for j in range(taxel_rows*taxel_cols):
        #         if i == 0:
        #             self.data_traj['x' + str(j)] = self.axes_2.plot(placeholder, np.zeros(step_num))
        #         elif i == 1:
        #             self.data_traj['y' + str(j)] = self.axes_3.plot(placeholder, np.zeros(step_num))
        #         elif i == 2:
        #             self.data_traj['z' + str(j)] = self.axes_4.plot(placeholder, np.zeros(step_num))

        for i in range(axis_num):
            for j in range(taxel_rows*taxel_cols):
                self.data_traj[str(i) + str(j)] = self.axes_5.plot(placeholder, np.zeros(step_num))


        # ani = animation.FuncAnimation(fig, self.animate,
        #                             init_func=self.init_datastream, interval=30, blit=True,
        #                             )
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        toolbar.config(background='#FFFFFF')
        toolbar._message_label.config(background='#FFFFFF')
        toolbar.update()
        self.canvas.get_tk_widget().pack()
        
        image_path = './button_images/'

        closing_icon = tk.PhotoImage(
            file=image_path + 'closing.PNG').subsample(6, 6)
        finish_icon = tk.PhotoImage(
            file=image_path + 'finish.PNG').subsample(6, 6)
        log_off_icon = tk.PhotoImage(
            file=image_path + '/log_off.PNG').subsample(6, 6)
        log_on_icon = tk.PhotoImage(
            file=image_path + '/log_on.PNG').subsample(6, 6)
        ready_icon = tk.PhotoImage(
            file=image_path + '/ready.PNG').subsample(6, 6)
        slip_detected_icon = tk.PhotoImage(
            file=image_path + '/slip_detected.PNG').subsample(6, 6)
        slip_off_icon = tk.PhotoImage(
            file=image_path + '/slip_off.PNG').subsample(6, 6)
        slip_on_icon = tk.PhotoImage(
            file=image_path + '/slip_on.PNG').subsample(6, 6)
        start_icon = tk.PhotoImage(
            file=image_path + '/start.PNG').subsample(6, 6)
        stop_icon = tk.PhotoImage(
            file=image_path + '/stop.PNG').subsample(6, 6)
        success_icon = tk.PhotoImage(
            file=image_path + '/success.PNG').subsample(6, 6)

        button_height_default = 120


        dummy_button1 = tk.Button(
            master=self.master, bg='#FFFFFF', command=self.do_nothing, height=10, width=30)
        dummy_button1.pack(fill='x', padx=0, side='left')

        start_stop_button = tk.Button(
            master=self.master, image=start_icon, command=self.start_stop, height=button_height_default, width=button_height_default * 2.1)
        start_stop_button.pack(fill='x', padx=0, side='left')

        slip_button = tk.Button(master=self.master, image=slip_off_icon,
                                    command=self.slip_detector_on_off, height=button_height_default, width=button_height_default)
        slip_button.pack(fill='x', padx=0, side='left')

        log_button = tk.Button(master=self.master, image=log_off_icon,
                                    command=self.logger_on_off, height=button_height_default, width=button_height_default)
        log_button.pack(fill='x', padx=0, side='left')

        state_bar = tk.Button(master=self.master, image=ready_icon,
                                command=self.do_nothing, height=button_height_default, width=button_height_default * 3.1)
        state_bar.pack(fill='x', padx=0, side='left')

        finish_button = tk.Button(master=self.master, image=finish_icon,
                                    command=self._quit, height=button_height_default, width=button_height_default)
        finish_button.pack(fill='x', padx=0, side='left')



    def _quit(self, ):
        self.master.quit()     # stops mainloop
        self.master.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def animate_graph(self, count):
        global log_dx
        global log_dy
        global log_dz
        # global val_tactile
        global val_tactile
        global base
        global user_input
        global controller_state
        
        # if controller_state is 0:
        #     state_bar.configure(image=ready_icon)
        # elif controller_state is 1:
        #     state_bar.configure(image=closing_icon)
        # elif controller_state is 2:
        #     state_bar.configure(image=success_icon)
        # elif controller_state is 3:
        #     state_bar.configure(image=success_icon)
        # elif controller_state is 4:
        #     state_bar.configure(image=slip_detected_icon)
        # elif controller_state is 5:
        #     state_bar.configure(image=success_icon)
        self.get_tactile_data()
        # print(self.tactile_data)

        # if count < step_num:  # wait until tactile data become stable
        time.sleep(0.001)

        # else:
        diff = np.array((self.tactile_data))
        dx = diff.reshape((taxel_num, axis_num))[:, 0]
        dy = diff.reshape((taxel_num, axis_num))[:, 1]
        dz = diff.reshape((taxel_num, axis_num))[:, 2]
        print("log_dx",log_dx.shape)

        log_dx = np.append(log_dx, dx.reshape(1, taxel_rows*taxel_cols), axis=0)
        log_dx = np.delete(log_dx, 0, 0)
        log_dy = np.append(log_dy, dy.reshape(1, taxel_rows*taxel_cols), axis=0)
        log_dy = np.delete(log_dy, 0, 0)
        log_dz = np.append(log_dz, dz.reshape(1, taxel_rows*taxel_cols), axis=0)
        log_dz = np.delete(log_dz, 0, 0)
        
        # self.data_traj_list = [self.data_traj['x' + str(j)][0].set_ydata(log_dx.T[j]) if i == 0 else self.data_traj['y' + str(j)][0].set_ydata(log_dx.T[j]) if i == 1 else self.data_traj['z' + str(j)][0].set_ydata(log_dx.T[j]) for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
        # self.data_traj_list = [self.data_traj['x' + str(j)][0] if i == 0 else self.data_traj['y' + str(j)][0] if i == 1 else self.data_traj['z' + str(j)][0] for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]

        # for faster visualization
        # self.data_traj["x0"][0].set_ydata(log_dx.T[0])
        # self.data_traj["x1"][0].set_ydata(log_dx.T[1])
        # self.data_traj["x2"][0].set_ydata(log_dx.T[2])
        # self.data_traj["x3"][0].set_ydata(log_dx.T[3])
        # self.data_traj["x4"][0].set_ydata(log_dx.T[4])
        # self.data_traj["x5"][0].set_ydata(log_dx.T[5])
        # self.data_traj["x6"][0].set_ydata(log_dx.T[6])
        # self.data_traj["x7"][0].set_ydata(log_dx.T[7])
        # self.data_traj["x8"][0].set_ydata(log_dx.T[8])
        # self.data_traj["x9"][0].set_ydata(log_dx.T[9])
        # self.data_traj["x10"][0].set_ydata(log_dx.T[10])
        # self.data_traj["x11"][0].set_ydata(log_dx.T[11])
        # self.data_traj["x12"][0].set_ydata(log_dx.T[12])
        # self.data_traj["x13"][0].set_ydata(log_dx.T[13])
        # self.data_traj["x14"][0].set_ydata(log_dx.T[14])
        # self.data_traj["x15"][0].set_ydata(log_dx.T[15])
        # self.data_traj["y0"][0].set_ydata(log_dy.T[0])
        # self.data_traj["y1"][0].set_ydata(log_dy.T[1])
        # self.data_traj["y2"][0].set_ydata(log_dy.T[2])
        # self.data_traj["y3"][0].set_ydata(log_dy.T[3])
        # self.data_traj["y4"][0].set_ydata(log_dy.T[4])
        # self.data_traj["y5"][0].set_ydata(log_dy.T[5])
        # self.data_traj["y6"][0].set_ydata(log_dy.T[6])
        # self.data_traj["y7"][0].set_ydata(log_dy.T[7])
        # self.data_traj["y8"][0].set_ydata(log_dy.T[8])
        # self.data_traj["y9"][0].set_ydata(log_dy.T[9])
        # self.data_traj["y10"][0].set_ydata(log_dy.T[10])
        # self.data_traj["y11"][0].set_ydata(log_dy.T[11])
        # self.data_traj["y12"][0].set_ydata(log_dy.T[12])
        # self.data_traj["y13"][0].set_ydata(log_dy.T[13])
        # self.data_traj["y14"][0].set_ydata(log_dy.T[14])
        # self.data_traj["y15"][0].set_ydata(log_dy.T[15])
        # self.data_traj["z0"][0].set_ydata(log_dz.T[0])
        # self.data_traj["z1"][0].set_ydata(log_dz.T[1])
        # self.data_traj["z2"][0].set_ydata(log_dz.T[2])
        # self.data_traj["z3"][0].set_ydata(log_dz.T[3])
        # self.data_traj["z4"][0].set_ydata(log_dz.T[4])
        # self.data_traj["z5"][0].set_ydata(log_dz.T[5])
        # self.data_traj["z6"][0].set_ydata(log_dz.T[6])
        # self.data_traj["z7"][0].set_ydata(log_dz.T[7])
        # self.data_traj["z8"][0].set_ydata(log_dz.T[8])
        # self.data_traj["z9"][0].set_ydata(log_dz.T[9])
        # self.data_traj["z10"][0].set_ydata(log_dz.T[10])
        # self.data_traj["z11"][0].set_ydata(log_dz.T[11])
        # self.data_traj["z12"][0].set_ydata(log_dz.T[12])
        # self.data_traj["z13"][0].set_ydata(log_dz.T[13])
        # self.data_traj["z14"][0].set_ydata(log_dz.T[14])
        # self.data_traj["z15"][0].set_ydata(log_dz.T[15])

        self.data_traj["00"][0].set_ydata(log_dx.T[0])
        self.data_traj["01"][0].set_ydata(log_dx.T[1])
        self.data_traj["02"][0].set_ydata(log_dx.T[2])
        self.data_traj["03"][0].set_ydata(log_dx.T[3])
        self.data_traj["04"][0].set_ydata(log_dx.T[4])
        self.data_traj["05"][0].set_ydata(log_dx.T[5])
        self.data_traj["06"][0].set_ydata(log_dx.T[6])
        self.data_traj["07"][0].set_ydata(log_dx.T[7])
        self.data_traj["08"][0].set_ydata(log_dx.T[8])
        self.data_traj["09"][0].set_ydata(log_dx.T[9])
        self.data_traj["010"][0].set_ydata(log_dx.T[10])
        self.data_traj["011"][0].set_ydata(log_dx.T[11])
        self.data_traj["012"][0].set_ydata(log_dx.T[12])
        self.data_traj["013"][0].set_ydata(log_dx.T[13])
        self.data_traj["014"][0].set_ydata(log_dx.T[14])
        self.data_traj["015"][0].set_ydata(log_dx.T[15])
        self.data_traj["10"][0].set_ydata(log_dy.T[0])
        self.data_traj["11"][0].set_ydata(log_dy.T[1])
        self.data_traj["12"][0].set_ydata(log_dy.T[2])
        self.data_traj["13"][0].set_ydata(log_dy.T[3])
        self.data_traj["14"][0].set_ydata(log_dy.T[4])
        self.data_traj["15"][0].set_ydata(log_dy.T[5])
        self.data_traj["16"][0].set_ydata(log_dy.T[6])
        self.data_traj["17"][0].set_ydata(log_dy.T[7])
        self.data_traj["18"][0].set_ydata(log_dy.T[8])
        self.data_traj["19"][0].set_ydata(log_dy.T[9])
        self.data_traj["110"][0].set_ydata(log_dy.T[10])
        self.data_traj["111"][0].set_ydata(log_dy.T[11])
        self.data_traj["112"][0].set_ydata(log_dy.T[12])
        self.data_traj["113"][0].set_ydata(log_dy.T[13])
        self.data_traj["114"][0].set_ydata(log_dy.T[14])
        self.data_traj["115"][0].set_ydata(log_dy.T[15])
        self.data_traj["20"][0].set_ydata(log_dz.T[0])
        self.data_traj["21"][0].set_ydata(log_dz.T[1])
        self.data_traj["22"][0].set_ydata(log_dz.T[2])
        self.data_traj["23"][0].set_ydata(log_dz.T[3])
        self.data_traj["24"][0].set_ydata(log_dz.T[4])
        self.data_traj["25"][0].set_ydata(log_dz.T[5])
        self.data_traj["26"][0].set_ydata(log_dz.T[6])
        self.data_traj["27"][0].set_ydata(log_dz.T[7])
        self.data_traj["28"][0].set_ydata(log_dz.T[8])
        self.data_traj["29"][0].set_ydata(log_dz.T[9])
        self.data_traj["210"][0].set_ydata(log_dz.T[10])
        self.data_traj["211"][0].set_ydata(log_dz.T[11])
        self.data_traj["212"][0].set_ydata(log_dz.T[12])
        self.data_traj["213"][0].set_ydata(log_dz.T[13])
        self.data_traj["214"][0].set_ydata(log_dz.T[14])
        self.data_traj["215"][0].set_ydata(log_dz.T[15])
        
        
        return [
            # self.data_traj["x0"][0], self.data_traj["x1"][0], self.data_traj["x2"][0], self.data_traj["x3"][0], self.data_traj["x4"][0], self.data_traj["x5"][0], self.data_traj["x6"][0], self.data_traj["x7"][0],self. data_traj["x8"][0], self.data_traj["x9"][0], self.data_traj["x10"][0], self.data_traj["x11"][0], self.data_traj["x12"][0], self.data_traj["x13"][0], self.data_traj["x14"][0], self.data_traj["x15"][0], self.data_traj["y0"][0], self.data_traj["y1"][0], self.data_traj["y2"][0], self.data_traj["y3"][0], self.data_traj["y4"][0], self.data_traj["y5"][0], self.data_traj["y6"][0], self.data_traj["y7"][0],self. data_traj["y8"][0], self.data_traj["y9"][0], self.data_traj["y10"][0], self.data_traj["y11"][0], self.data_traj["y12"][0], self.data_traj["y13"][0], self.data_traj["y14"][0], self.data_traj["y15"][0], self.data_traj["z0"][0], self.data_traj["z1"][0], self.data_traj["z2"][0], self.data_traj["z3"][0], self.data_traj["z4"][0], self.data_traj["z5"][0], self.data_traj["z6"][0], self.data_traj["z7"][0],self. data_traj["z8"][0], self.data_traj["z9"][0], self.data_traj["z10"][0], self.data_traj["z11"][0], self.data_traj["z12"][0], self.data_traj["z13"][0], self.data_traj["z14"][0], self.data_traj["z15"][0], 
            self.data_traj["00"][0], self.data_traj["01"][0], self.data_traj["02"][0], self.data_traj["03"][0], self.data_traj["04"][0], self.data_traj["05"][0], self.data_traj["06"][0], self.data_traj["07"][0],self. data_traj["08"][0], self.data_traj["09"][0], self.data_traj["010"][0], self.data_traj["011"][0], self.data_traj["012"][0], self.data_traj["013"][0], self.data_traj["014"][0], self.data_traj["015"][0], self.data_traj["10"][0], self.data_traj["11"][0], self.data_traj["12"][0], self.data_traj["13"][0], self.data_traj["14"][0], self.data_traj["15"][0], self.data_traj["16"][0], self.data_traj["17"][0],self. data_traj["18"][0], self.data_traj["19"][0], self.data_traj["110"][0], self.data_traj["111"][0], self.data_traj["112"][0], self.data_traj["113"][0], self.data_traj["114"][0], self.data_traj["115"][0], self.data_traj["20"][0], self.data_traj["21"][0], self.data_traj["22"][0], self.data_traj["23"][0], self.data_traj["24"][0], self.data_traj["25"][0], self.data_traj["26"][0], self.data_traj["27"][0],self. data_traj["28"][0], self.data_traj["29"][0], self.data_traj["210"][0], self.data_traj["211"][0], self.data_traj["212"][0], self.data_traj["213"][0], self.data_traj["214"][0], self.data_traj["215"][0]]

    def animate_map(self, count):
        global log_dx
        global log_dy
        global log_dz
        global val_tactile
        global val_tactile
        global user_input
        global controller_state
        
        # if controller_state is 0:
        #     state_bar.configure(image=ready_icon)
        # elif controller_state is 1:
        #     state_bar.configure(image=closing_icon)
        # elif controller_state is 2:
        #     state_bar.configure(image=success_icon)
        # elif controller_state is 3:
        #     state_bar.configure(image=success_icon)
        # elif controller_state is 4:
        #     state_bar.configure(image=slip_detected_icon)
        # elif controller_state is 5:
        #     state_bar.configure(image=success_icon)

        if count < step_num:  # wait until tactile data become stable
            sleep(0.01)

        else:
            diff = np.array((val_tactile))
            dx = diff.reshape((taxel_num, axis_num))[:, 0]
            dy = diff.reshape((taxel_num, axis_num))[:, 1]
            dz = diff.reshape((taxel_num, axis_num))[:, 2]

            log_dx = np.append(log_dx, dx.reshape(1, taxel_rows*taxel_cols), axis=0)
            log_dx = np.delete(log_dx, 0, 0)
            log_dy = np.append(log_dy, dy.reshape(1, taxel_rows*taxel_cols), axis=0)
            log_dy = np.delete(log_dy, 0, 0)
            log_dz = np.append(log_dz, dz.reshape(1, taxel_rows*taxel_cols), axis=0)
            log_dz = np.delete(log_dz, 0, 0)
            
            # self.data_traj_list = [self.data_traj['x' + str(j)][0].set_ydata(log_dx.T[j]) if i == 0 else self.data_traj['y' + str(j)][0].set_ydata(log_dx.T[j]) if i == 1 else self.data_traj['z' + str(j)][0].set_ydata(log_dx.T[j]) for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]
            # self.data_traj_list = [self.data_traj['x' + str(j)][0] if i == 0 else self.data_traj['y' + str(j)][0] if i == 1 else self.data_traj['z' + str(j)][0] for i in range(axis_num) for j in range(taxel_rows*taxel_cols)]

            # for faster visualization
            self.data_traj["x0"][0].set_ydata(log_dx.T[0])
            self.data_traj["x1"][0].set_ydata(log_dx.T[1])
            self.data_traj["x2"][0].set_ydata(log_dx.T[2])
            self.data_traj["x3"][0].set_ydata(log_dx.T[3])
            self.data_traj["x4"][0].set_ydata(log_dx.T[4])
            self.data_traj["x5"][0].set_ydata(log_dx.T[5])
            self.data_traj["x6"][0].set_ydata(log_dx.T[6])
            self.data_traj["x7"][0].set_ydata(log_dx.T[7])
            self.data_traj["x8"][0].set_ydata(log_dx.T[8])
            self.data_traj["x9"][0].set_ydata(log_dx.T[9])
            self.data_traj["x10"][0].set_ydata(log_dx.T[10])
            self.data_traj["x11"][0].set_ydata(log_dx.T[11])
            self.data_traj["x12"][0].set_ydata(log_dx.T[12])
            self.data_traj["x13"][0].set_ydata(log_dx.T[13])
            self.data_traj["x14"][0].set_ydata(log_dx.T[14])
            self.data_traj["x15"][0].set_ydata(log_dx.T[15])
            self.data_traj["y0"][0].set_ydata(log_dy.T[0])
            self.data_traj["y1"][0].set_ydata(log_dy.T[1])
            self.data_traj["y2"][0].set_ydata(log_dy.T[2])
            self.data_traj["y3"][0].set_ydata(log_dy.T[3])
            self.data_traj["y4"][0].set_ydata(log_dy.T[4])
            self.data_traj["y5"][0].set_ydata(log_dy.T[5])
            self.data_traj["y6"][0].set_ydata(log_dy.T[6])
            self.data_traj["y7"][0].set_ydata(log_dy.T[7])
            self.data_traj["y8"][0].set_ydata(log_dy.T[8])
            self.data_traj["y9"][0].set_ydata(log_dy.T[9])
            self.data_traj["y10"][0].set_ydata(log_dy.T[10])
            self.data_traj["y11"][0].set_ydata(log_dy.T[11])
            self.data_traj["y12"][0].set_ydata(log_dy.T[12])
            self.data_traj["y13"][0].set_ydata(log_dy.T[13])
            self.data_traj["y14"][0].set_ydata(log_dy.T[14])
            self.data_traj["y15"][0].set_ydata(log_dy.T[15])
            self.data_traj["z0"][0].set_ydata(log_dz.T[0])
            self.data_traj["z1"][0].set_ydata(log_dz.T[1])
            self.data_traj["z2"][0].set_ydata(log_dz.T[2])
            self.data_traj["z3"][0].set_ydata(log_dz.T[3])
            self.data_traj["z4"][0].set_ydata(log_dz.T[4])
            self.data_traj["z5"][0].set_ydata(log_dz.T[5])
            self.data_traj["z6"][0].set_ydata(log_dz.T[6])
            self.data_traj["z7"][0].set_ydata(log_dz.T[7])
            self.data_traj["z8"][0].set_ydata(log_dz.T[8])
            self.data_traj["z9"][0].set_ydata(log_dz.T[9])
            self.data_traj["z10"][0].set_ydata(log_dz.T[10])
            self.data_traj["z11"][0].set_ydata(log_dz.T[11])
            self.data_traj["z12"][0].set_ydata(log_dz.T[12])
            self.data_traj["z13"][0].set_ydata(log_dz.T[13])
            self.data_traj["z14"][0].set_ydata(log_dz.T[14])
            self.data_traj["z15"][0].set_ydata(log_dz.T[15])

        return [self.data_traj["x0"][0], self.data_traj["x1"][0], self.data_traj["x2"][0], self.data_traj["x3"][0], self.data_traj["x4"][0], self.data_traj["x5"][0], self.data_traj["x6"][0], self.data_traj["x7"][0],self. data_traj["x8"][0], self.data_traj["x9"][0], self.data_traj["x10"][0], self.data_traj["x11"][0], self.data_traj["x12"][0], self.data_traj["x13"][0], self.data_traj["x14"][0], self.data_traj["x15"][0], self.data_traj["y0"][0], self.data_traj["y1"][0], self.data_traj["y2"][0], self.data_traj["y3"][0], self.data_traj["y4"][0], self.data_traj["y5"][0], self.data_traj["y6"][0], self.data_traj["y7"][0],self. data_traj["y8"][0], self.data_traj["y9"][0], self.data_traj["y10"][0], self.data_traj["y11"][0], self.data_traj["y12"][0], self.data_traj["y13"][0], self.data_traj["y14"][0], self.data_traj["y15"][0], self.data_traj["z0"][0], self.data_traj["z1"][0], self.data_traj["z2"][0], self.data_traj["z3"][0], self.data_traj["z4"][0], self.data_traj["z5"][0], self.data_traj["z6"][0], self.data_traj["z7"][0],self. data_traj["z8"][0], self.data_traj["z9"][0], self.data_traj["z10"][0], self.data_traj["z11"][0], self.data_traj["z12"][0], self.data_traj["z13"][0], self.data_traj["z14"][0], self.data_traj["z15"][0]]

    # def get_tactile(self, ):
    #     self.mutex.acquire()
    #     self.tactile_data = copy.deepcopy(self.ms.deci_data)
    #     self.mutex.release()

    def split_data(self, message): # For accessing JSON data
        out = []
        print("message",message)
        if len(message) > 0:
            out = [int(x,16) for x in message["data"]] 
        return out
    
    def get_tactile_data(self,):
        self.mutex.acquire()
        self.tactile_data = client.getData()["data"]
        self.mutex.release()

    def offset_tactile(self, ):
        sample_num = 500
        for i in range(1, sample_num+1):
            self.get_tactile_data()
            val = np.array(self.tactile_data).reshape(1, -1)
            self.base = self.base + val
            if i%50 is 0:
                print("%d / %d, offsetting...",i,sample_num)
        self.base = self.base / sample_num
            
    def _quit(self,):
        self.master.quit()

    def start_stop(self,):
        global user_input
        global start_stop_icon
        if user_input is 1:
            start_stop_button.configure(image=start_icon)
            user_input = 0
            
        else:
            start_stop_button.configure(image=stop_icon)
            user_input = 1

    def logger_on_off(self,):
        global logger_state
        if logger_state is 1:
            log_button.configure(image=log_off_icon)
            logger_state = 0
        else:
            log_button.configure(image=log_on_icon)
            logger_state = 1

    def slip_detector_on_off(self,):
        global slip_detector_mode
        if slip_detector_mode is 1:
            slip_button.configure(image=slip_off_icon)
            slip_detector_mode = 0
        else:
            slip_button.configure(image=slip_on_icon)
            slip_detector_mode = 1

    def do_nothing(self,):
        pass

    def plot_graph(self, ):
        ani = animation.FuncAnimation(self.fig, self.animate_graph,
            init_func=self.init_datastream, interval=10, blit=True,
            )
        self.fig.canvas.draw()
        # button = tk.Button(master=self.master, text="Quit", command=self._quit)
        # button.pack()

    def map_taxel(self, ):
        fig = Figure()
        # FuncAnimationより前に呼ぶ必要がある
        canvas = FigureCanvasTkAgg(fig, master = self.master)         
        x = np.arange(0, 3, 0.01)  # x軸(固定の値)
        l = np.arange(0, 8, 0.01)  # 表示期間(FuncAnimationで指定する関数の引数になる)
        plt = fig.add_subplot(111)
        plt.set_ylim([-1.1, 1.1])
        line, = plt.plot(x, np.sin(x))
        line.set_ydata(np.sin(x))
        # self.master.after(0, self.animation) for loop?
        ani = animation.FuncAnimation(fig, self.animate_map, l,
            init_func=self.init_datastream, interval=1, blit=True,
            )

        toolbar = NavigationToolbar2Tk(canvas, self.master)
        canvas.get_tk_widget().pack()

        button = tk.Button(master=self.master, text="Quit", command=self._quit)
        button.pack()

class MyData(object):
    def __init__(self):
        self.__data = {}
    def newdata(self,data):
        self.__data = data
        #print("New data: {}".format(data))
    def getdata(self):
        return self.__data

if __name__ == "__main__":
    settings = XELA_Settings(client_port= 5001, server_port=5003)
    settings.iamserver()
    settings.iamclient()
    mydata = MyData()
    client = XELA_Client(settings,mydata.newdata)
    root = tk.Tk()
    tacApp = Application(master=root, messenger=None)
# May be speed up to viusalize https://qiita.com/nubata/items/5702c945ce7196ccc62b
#                              https://base64.work/so/python-2.7/3539242