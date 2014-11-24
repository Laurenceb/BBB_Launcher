#!/usr/bin/python

import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
from Adafruit_I2C import Adafruit_I2C
import struct
from array import array
import time
import os
import sys

#L3DG20 device
i2c = Adafruit_I2C(0x6a,2)


#this sets up the gyro to write values to the FIFO buffer
def configure_gyro():
	i2c.write8(0x20, 0x0F)#setup 95sps, 12.5hz mode
	i2c.write8(0x21, 0x29)#9mHz high pass, normal mode
	i2c.write8(0x22, 0x00)#no interrupts
	i2c.write8(0x23, 0x40)#blocking, 250deg/sec
	i2c.write8(0x24, 0x53)#FIFO+high pass mode with LPF1 and 2 + HPF
	i2c.write8(0x2E, 0x00)#wipe FIFO state
	i2c.write8(0x2E, 0x5F)#enable FIFO streaming


#this reads the FIFO buffer, used to check for vapid motion occuring recently
def read_gyro_fifo(debuglevel):
	samples=i2c.readS8(0x2F)%32#number of fifo samples is lower 5 bits
	n=samples		#number for averaging
	rms=[0,0,0]		#integration bins
	while samples:		#loop through the fifo
		samples-=1	#take off a sample
		datalist=i2c.readList(0xA6, 8)#read temp, status, and all registers
		if debuglevel>1:
			print datalist
		temperature=struct.unpack("b",chr(datalist[0]))
		temperature=temperature[0]
		a = array('B', datalist[2:4])
		x = struct.unpack('>h',a)
		x=x[0]/114.28
                a = array('B', datalist[4:6])
                y = struct.unpack('>h',a)
                y=y[0]/114.28
                a = array('B', datalist[6:8])
                z = struct.unpack('>h',a)
                z=z[0]/114.28
		if debuglevel:
			print x,y,z,temperature
		rms[0]+=x**2
		rms[1]+=y**2
		rms[2]+=z**2
	for m in range(3):
		rms[m]/=n	#normalize
		rms[m]=rms[m]**0.5#the RMS rotation vector
	return {'RMS': rms, 'Temperature': temperature}

def printf(format, *args):
	sys.stdout.write(format % args)

def gyro_read_task(filename,debuglevel):
	fid=open(filename,'w+')
	while 1:
		time.sleep(0.25)
		data=gyro.read_gyro_fifo(debuglevel)
		fid.write("{:.2f},{:.2f},{:.2f},{}\n".format(*data['RMS'][:3], data['Temperature']))
		fid.flush()
		os.fsync(fid.fileno())

	
