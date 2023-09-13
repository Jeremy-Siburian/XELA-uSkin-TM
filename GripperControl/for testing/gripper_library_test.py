import serial #this is pySerial
import time
import binascii

import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from robotiq_library import*

gripper = Robotiq()
gripper.__init__(port = 'COM3')
counter = 0

while counter < 1:
   counter = counter + 1
   # reset all data
   gripper.reset()
   #data_raw = ser.readline()
   #print(data_raw)
   #data = binascii.hexlify(data_raw)
   #print ("Response 1 ", data)
   time.sleep(0.01)

   #ser.write(b'\x09\x03\x07\xD0\x00\x01\x85\xCF')
   #gripper.read_command(data)
   #data_raw = ser.readline()
   #print(data_raw)
   #data = binascii.hexlify(data_raw)
   #print ("Response 2 ", data)
   time.sleep(1)

while(True):
   print ("Close gripper")
   position = 0xFF
   speed = 0x01
   force = 0xFF
   gripper.move(position,speed,force)
   #data_raw = ser.readline()
   #print(data_raw)
   #data = binascii.hexlify(data_raw)
   #print ("Response 3 ", data)
   time.sleep(2)
   print ("Open gripper")
   gripper.home()
   #data_raw = ser.readline()
   #print(data_raw)
   #data = binascii.hexlify(data_raw)
   #print ("Response 4 ", data)
   time.sleep(2)
