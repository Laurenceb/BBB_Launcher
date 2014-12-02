#!/usr/bin/python

import Adafruit_BBIO.GPIO as GPIO
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.UART as UART
import time

#global config
VCXO_FREQ=26000000#3.3v tcxo used on the board

#the silabs is on spi1
spione=SPI(2,0)

#this function wakes up the radio and puts it into ready mode 
def setup_radio():
	spione.mode=0#SPI1 mode 0 at 2Mhz
	spione.msh=2000000
	spione.open(2,0) 
	UART.setup("UART4")#USART4 TX is used for direct modulation (RTTY at 200 baud), dts file altered to allow RX4, GPIO0_30 to be used for CTS
	GPIO.setup("GPIO0_30",GPIO.IN#This is the CTS pin, high==CTS
	GPIO.setup("GPIO1_14",GPIO.IN#The IRQ pin, low==IRQ
	GPIO.output("GPIO1_15",GPIO.HIGH)
	GPIO.setup("GPIO1_15",GPIO.OUT#This is the SDN pin, high==shutdown
	GPIO.output("GPIO0_27",GPIO.HIGH)
	GPIO.setup("GPIO0_27",GPIO.OUT#This is the nSEL pin, low==selected
	time.sleep(0.005)#5ms sleep at bootup to allow everything to reset
	GPIO.output("GPIO1_15",GPIO.LOW)#Take the silabs out of shutdown mode
	#divide VCXO_FREQ into its bytes, MSB first
	x3 = (VCXO_FREQ // 0x1000000)&0xFF
	x2 = ((VCXO_FREQ - x3 * 0x1000000) // 0x10000)&0xFF
	x1 = ((VCXO_FREQ - x3 * 0x1000000 - x2 * 0x10000) // 0x100)&0xFF
	x0 = ((VCXO_FREQ - x3 * 0x1000000 - x2 * 0x10000 - x1 * 0x100))&0xFF 
	boot_config=[0x02, 0x01, 0x01, x3, x2, x1, x0]


def send_cmd_receive_answer( byteCountRx, Txdata):
	byteCountTx=len(Txdata)
	#There is a silicon bug on some revisions, need to send at least 2 bytes
	if (byteCountTx == 1):
		byteCountTx=byteCountTx+1
		Txdata.append(0x00)
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device
	spi.xfer2(Txdata)
	GPIO.output("GPIO0_27",GPIO.HIGH)#Deselect the SPI device
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device
	while GPIO.read("GPIO0_30")==GPIO.LOW:#await cts
		time.sleep(0.00001)
