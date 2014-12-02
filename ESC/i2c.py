import serial
import time

poles=14	#for the turnigy motor

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
ser.open()
ser.write("m\n")
time.sleep(1)
ser.flushInput()
ser.write("4\n")
time.sleep(1)
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
ser.write("4\n")
time.sleep(1)
ser.write("W\n")
time.sleep(1)
ser.write("P\n")
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
print ser.readline()
#This enables the ESC, but it stays off
ser.write("[0x52 0x00 0x00 0x00]\n")
time.sleep(0.02)
ser.write("[0x52 0x00 0x00 0x00]\n")
time.sleep(0.02)
ser.write("[0x52 0x00 0x00 0x00]\n")
time.sleep(0.02)
commut=0
time_=0
ser.flushInput()
ser.flushOutput()
throttle=20	#initial throttle setting
for n in range(150):
	if throttle>0:
		seq=("[0x52 0x00 ",hex(throttle)," 0xff]\n")
	else:
		seq=("[0x52 0x00 ",hex(throttle)," 0x00]\n")
	command=''
	ser.write(command.join(seq))
	if throttle<124:
		throttle=throttle+4 #This will take 0.8 seconds to rev up
	if n>100:
		throttle=0	#Turn off, but keep outputting the spin rate
	#ser.write("[0x52 0x00 0x7f 0xff]\n") #0x7f 0xff
	time.sleep(0.02)
	ser.flushInput()
	ser.write("[0x53 rr]\n")
	time.sleep(0.01)
	ser.readline()
	ser.readline()
	ser.readline()
	s=ser.readline()
	t=ser.readline()
	if len(t)>15 and len(s)>10 and s[8:10]!='CK':
		commut=int(t[13:15],16)+int(s[8:10],16)*256
	else:
		commut=0
	time__=time.time()
	print (commut)/((poles/2)*(time__-time_))
	time_=time__
for n in range(30):
	ser.write("[0x52 0x00 0x00 0x00\n")
	time.sleep(0.03)
ser.flushInput()
time.sleep(0.03)
for n in range(10):
	ser.write("[0x52 0x04 [0x53 r r r r r ]\n")
	time.sleep(0.75)
	for m in range(11):
		print ser.readline()
