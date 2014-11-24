import Adafruit_BBIO.PWM as PWM
import time

def testp:
	while 1:
		PWM.start("P8_19",15,49500)
		time.sleep(2)
		PWM.stop("P8_19")
		time.sleep(0.15)
		PWM.cleanup()
		time.sleep(0.1)
