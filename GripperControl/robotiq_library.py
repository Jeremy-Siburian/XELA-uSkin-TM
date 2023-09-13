#!/usr/bin/env python
# XELA Robotics 2022

import re
from re import ASCII
from tkinter import COMMAND
import serial
import time
import crcmod
import socket
import threading

import os, sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from GripperControl.robotiq_def import *
import binascii

crc_check = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0) #to calculate CRC checksum; Robotiq uses modbus (8005)

class Robotiq(object):

	def __init__(self, port = None):
		#port = 'COM0' #change according to your PC
		
		if port != None:
			baudrate = 115200
			try:
				self.ser = serial.Serial(port,baudrate,timeout=1,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
			except:
				print('This port is not available')
				exit()
	
	def __read_command(self, register_address, data_length):
		data = bytearray()
		data.append(SLAVE_ID)
		data.append(READ_FUNCTION)
		if (register_address - READ_REGISTER_1) == 0:			
			data.extend(READ_REGISTER_1.to_bytes(2, 'big'))
		elif (register_address - READ_REGISTER_1) == 1:
			data.extend(READ_REGISTER_2.to_bytes(2, 'big'))
		elif (register_address - READ_REGISTER_1) == 2:
			data.extend(READ_REGISTER_3.to_bytes(2, 'big'))		
			
		 # number of registers written to 
		data.extend(data_length.to_bytes(2,'big'))
	
		CRC = crc_check(data)
		data.extend(CRC.to_bytes(2, 'little'))

		message = bytes(data)
		self.ser.write(message)	
		#data_raw = self.ser.readline()
   		#print(data_raw)
	
	def __status_thread(self, name): # a thread for reading the gripper status	
		while True:
			if (self.ser.inWaiting() > 0):	
				try:
					self.__read_command(READ_REGISTER_1, 3)
					data = self.ser.readline(self.ser.inWaiting())
				except:
					print('Serial is not available, try again.')
		
			if len(data) == 11:
				self.GRIPPER_STATUS = data[3]
				# 7 |6|5 |4|  3 | 2 | 1  | 0
				# gOBJ|gSTA|gGTO|Reserved|gACT
				# gACT--> 0x0: gripper reset | 0x1: gripper activation
				# gGTO--> 0x0: stopped (or performing activation/automatic release) | 0x1: go to position request
				# gSTA --> 0x00: gripper in reset | 0x01: activation in progress | 0x02: noot used | 0x03: activation is completed
				# gOBJ --> 0x0: fingers are in motion - no object detected | 0x03 : fingers at requested position - no object detected
				self.FAULT_STATUS = data[5]  			
				self.POS_REQUEST_ECHO = data[6]
				self.POSITION = data[7]
				self.CURRENT = data[8]
				#print(self.POSITION)
			
			time.sleep(0.002) 

	def initialize_status_thread(self): # to activate the thread
		status_thread = threading.Thread(target=self.__status_thread, args=(1,)) #A thread for accessing uSkin data from the middleware
		status_thread.start()
		

	def __write_command(self, args): # write a message to Robotiq gripper
		data = bytearray()
		data.append(SLAVE_ID)
		data.append(WRITE_FUNCTION)
		if (args[0] - WRITE_REGISTER_1) == 0:			
			data.extend(WRITE_REGISTER_1.to_bytes(2, 'big'))
		elif (args[0] - WRITE_REGISTER_1) == 1:
			data.extend(WRITE_REGISTER_2.to_bytes(2, 'big'))
		elif (args[0] - WRITE_REGISTER_1) == 2:
			data.extend(WRITE_REGISTER_3.to_bytes(2, 'big'))		
			
		data_length = len(args) - 1 # number of registers written to 
		data.extend(data_length.to_bytes(2,'big'))
		data.append(data_length*2) # number of data bytes to follow (x registers * 2 bytes/register)

		for i in range(len(args) - 1): # contains motor speed, position, etc.
			data.extend(args[i+1].to_bytes(2, 'big'))

		CRC = crc_check(data)
		data.extend(CRC.to_bytes(2, 'little'))

		message = bytes(data)
		self.ser.write(message)	
	
	def reset(self):
		data = [WRITE_REGISTER_1, 0x0000, 0x0000, 0x0000]
		self.__write_command(data)

	def home(self):
		position = 0x00	
		speed = 0xFF
		force = 0xFF

		COMMAND_1 = 0x09 << 8 | 0x00
		COMMAND_2 = 0x00 << 8 | position
		COMMAND_3 = speed << 8 | force

		self.__write_command([WRITE_REGISTER_1, COMMAND_1, COMMAND_2,COMMAND_3])

	def move(self, position, speed, force):
		COMMAND_1 = 0x09 << 8 | 0x00
		COMMAND_2 = 0x00 << 8 | position
		COMMAND_3 = speed << 8 | force
		
		self.__write_command([WRITE_REGISTER_1, COMMAND_1, COMMAND_2, COMMAND_3])             		

	def stop(self):
		COMMAND_1 = 0x01 << 8 | 0x00	
			
		self.__write_command([WRITE_REGISTER_1, COMMAND_1])             		
			
	def position(self):
		self.__read_command(WRITE_REGISTER_3, 1)             		
		data = self.ser.readline()
		pos = binascii.hexlify(data)
		
		print(pos)	
 
def e2t(e:Exception) -> str:
    return f"{type(e).__name__}: {e}"

class Robotiq_UR(object):
	def __init__(self,ip:str,port:int):
		self.ip = ip
		self.port = port
	
	def position(self):
		data = self.send_to_gripper("GET POS\n",True)
		pos = re.findall("\d+",str(data))
		return int(pos[0])
	
	def __status_thread(self, name): # a thread for reading the gripper status	
		while True:
			try:
				self.POSITION = self.position()
				#print(self.POSITION) # foe dwbugging
			except:
				print('Communication is not available, try again.')
		
			time.sleep(0.002) 

	def initialize_status_thread(self): # to activate the thread
		status_thread = threading.Thread(target=self.__status_thread, args=(1,)) #A thread for accessing uSkin data from the middleware
		status_thread.start()

	def send_to_gripper(self, data:str,receive:bool=False):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.ip, self.port))
			s.sendall(data.encode('utf-8'))
			if receive:
				return s.recv(2**10)

	
	def move(self, position:int, speed:int, force:int):
		self.send_to_gripper(f"SET POS {position}\n")
		self.send_to_gripper(f"SET SPE {speed}\n")
		self.send_to_gripper(f"SET FOR {force}\n")
		self.start()

	def home(self):
		self.send_to_gripper(f"SET POS 0\n")
		self.start()

	def reset(self):
		self.send_to_gripper(f"SET ACT 1\n")
	
	def stop(self):
		self.send_to_gripper(f"SET GTO 0\n")

	def start(self):
		self.send_to_gripper(f"SET GTO 1\n")
 
