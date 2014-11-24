#!/usr/bin/python

import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import time


def simple_ignite(debuglevel):
	GPIO.setup("P8_14",GPIO.OUT) #This pin fires the ignition
	GPIO.output("P8_14",GPIO.LOW)
	PWM.start("P8_19",15,49500) #works best with an 11 turn primary
	GPIO.output("P8_14",GPIO.HIGH)
	if debuglevel:
		print "Igniting"
	time.sleep(2) #plenty of time for ignition
	GPIO.output("P8_14",GPIO.LOW)
	PWM.stop("P8_19")
	PWM.cleanup()
	failure=0
	return {'failure':failure}

def selftest(debuglevel):
	threshold=1024 #450mv threshold
	threshigh=1550 #680mv upper threshold
	ADC.setup()
	ADC.read_raw("AIN4") #Flush this
	baseline=ADC.read_raw("AIN4")
	GPIO.setup("P8_14",GPIO.OUT) #This pin fires the ignition
	GPIO.output("P8_14",GPIO.LOW)
	PWM.start("P8_19",15,49500) #works best with an 11 turn primary
	time.sleep(0.05) #50ms Settling time for the analogue front end
	ADC.read_raw("AIN4")
	selftest=ADC.read_raw("AIN4")
	if selftest>threshold and selftest<threshigh and baseline<128:
		if debuglevel:
			print "Self test ok"
		failure=0		
	else:
		if debuglevel:
			print "Failed"
		failure=1
	PWM.stop("P8_19")
	time.sleep(0.2)
	PWM.cleanup()
	GPIO.cleanup()
	#Debug output
	if debuglevel:
		print baseline
		print selftest
	return {'failure':failure, 'baseline':baseline ,'selftest':selftest }

def ignite(debuglevel):
	threshold=1024 #450mv threshold
	threshigh=1550 #680mv upper threshold
	ADC.setup()
	ADC.read_raw("AIN4") #Flush this
	baseline=ADC.read_raw("AIN4")
	GPIO.setup("P8_14",GPIO.OUT) #This pin fires the ignition
	GPIO.output("P8_14",GPIO.LOW)
	PWM.start("P8_19",15,49500) #works best with an 11 turn primary
	time.sleep(0.05) #50ms Settling time for the analogue front end
	ADC.read_raw("AIN4")
	selftest=ADC.read_raw("AIN4")
	if selftest>threshold and selftest<threshigh and baseline<128:
		GPIO.output("P8_14",GPIO.HIGH)
		if debuglevel:
			print "Igniting"
		time.sleep(2) #plenty of time for ignition
		failure=0		
	else:
		if debuglevel:
			print "Failed"
		failure=1
	GPIO.output("P8_14",GPIO.LOW)
	PWM.stop("P8_19")
	PWM.cleanup()
	#Debug output
	if debuglevel:
		print baseline
		print selftest
	return {'failure':failure, 'baseline':baseline ,'selftest':selftest }
