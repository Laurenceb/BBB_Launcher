#!/usr/bin/python

import Adafruit_BBIO.GPIO as GPIO
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.UART as UART
import time
import serial

#global config
VCXO_FREQ=26000000#3.3v tcxo used on the board
RSSI_THRESH=-85#-85dBm RSSI, should be fine with ~1W into a yagi on the ground
active_level=32#gives ~ 15dBm at 3.3v
active_shift=300#300 hz tone sep
active_freq=434750000
outdiv=0#set by the frequency config function

#the silabs is on spi1
spione=SPI(1,0)
#and uses uart4 for direct modulation (RTTY at 200baud)
ser = []

#this function wakes up the radio and puts it into ready mode 
def setup_radio():
	spione.mode=0#SPI1 mode 0 at 2Mhz
	spione.msh=2000000
	spione.open(1,0) 
	UART.setup("UART4")#USART4 TX is used for direct modulation (RTTY at 200 baud), dts file altered to allow RX4, GPIO0_30 to be used for CTS
	ser=serial.Serial(port = "/dev/ttyO4", baudrate=200)
	ser.open()#Open the USART4 port as ser
	GPIO.setup("GPIO0_30",GPIO.IN)#This is the CTS pin, high==CTS
	GPIO.setup("GPIO1_14",GPIO.IN)#The IRQ pin, low==IRQ
	GPIO.setup("GPIO1_15",GPIO.OUT)#This is the SDN pin, high==shutdown
	GPIO.output("GPIO1_15",GPIO.HIGH)
	GPIO.setup("GPIO0_27",GPIO.OUT)#This is the nSEL pin, low==selected
	GPIO.output("GPIO0_27",GPIO.HIGH)
	time.sleep(0.005)#5ms sleep at bootup to allow everything to reset
	GPIO.output("GPIO1_15",GPIO.LOW)#Take the silabs out of shutdown mode
	#divide VCXO_FREQ into its bytes, MSB first
	x3 = (VCXO_FREQ // 0x1000000)&0xFF
	x2 = ((VCXO_FREQ - x3 * 0x1000000) // 0x10000)&0xFF
	x1 = ((VCXO_FREQ - x3 * 0x1000000 - x2 * 0x10000) // 0x100)&0xFF
	x0 = ((VCXO_FREQ - x3 * 0x1000000 - x2 * 0x10000 - x1 * 0x100))&0xFF 
	boot_config=[0x02, 0x01, 0x01, x3, x2, x1, x0]
	send_cmd_receive_answer( 1, boot_config)
	# Clear all pending interrupts and get the interrupt status back
	get_int_status_command = [0x20, 0x00, 0x00, 0x00]
	send_cmd_receive_answer( 9,  get_int_status_command)
	# Read the part info
	partinfo=send_cmd_receive_answer( 8, [0x01])
	# This is useful to check if the device is functional - sanity check
	print(partinfo)
	# Setup the GPIO pin, note that GPIO1 defaults to CTS, but we need to reset and set GPIO0 to TX direct mode mod input
	gpio_pin_cfg_command = [0x13, 0x04, 0x00, 0x01, 0x01, 0x00, 0x11, 0x00] # Set GPIO0 input, 1 CTS, rest disabled, NIRQ unchanged, 
	#SDO=SDO, Max drive strength
	send_cmd_receive_answer( 8, gpio_pin_cfg_command)
	set_frequency(active_freq)
	set_modem()
	set_deviation(active_shift)

def send_cmd_receive_answer( byteCountRx, Txdata):
	byteCountTx=len(Txdata)
	#There is a silicon bug on some revisions, need to send at least 2 bytes
	if (byteCountTx == 1):
		byteCountTx=byteCountTx+1
		Txdata.append(0x00)
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device
	spione.xfer2(Txdata)
	GPIO.output("GPIO0_27",GPIO.HIGH)#Deselect the SPI device
	t=time.time()#This function waits 150ms for CTS
	while not GPIO.input("GPIO0_30"):#Await CTS
		time.sleep(0.00001)
		#A one is returned if there is no CTS after 150ms
		if time.time()>t+0.15:
			return { 'failure':1 }
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device again to allow read, read the 8 reply bytes
	send=[0x44]
	#add on the CTS byte
	send.extend([0x00]*(byteCountRx+1))
	reply=spione.xfer2(send)
	#remove the dummy byte and the CTS byte
	reply=reply[2:len(reply)]
	GPIO.output("GPIO0_27",GPIO.HIGH)
	return { 'failure':0, 'reply':reply }

def silabs_read( addr, bytes):
	#write ss low to start
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device
	#make sure the msb is 0 so we do a read, not a write
	addr &= 0x7F
	spione.xfer2(addr)
	while bytes:
		val.append(spione.xfer2(0x00))
		bytes-=1
	#write ss high to end
	GPIO.output("GPIO0_27",GPIO.HIGH)
	return val

def silabs_write( addr, data):
	#write ss low to start
	GPIO.output("GPIO0_27",GPIO.LOW)#Select the SPI device
	#make sure the msb is 1 so we do a write
	addr |= 0x80
	spione.xfer2([addr,data])
	#write ss high to end
	GPIO.output("GPIO0_27",GPIO.HIGH)#Deselect the SPI device

def set_frequency( freq):
	#Set the output divider according to recommended ranges given in Si446x datasheet
	band = 0
	if (freq < 705000000):
		outdiv = 6
		band = 1
	if (freq < 525000000):
		outdiv = 8
		band = 2
	if (freq < 353000000):
		outdiv = 12
		band = 3
	if (freq < 239000000):
		outdiv = 16
		band = 4
	if (freq < 177000000):
		outdiv = 24
		band = 5
	f_pfd = 2 * VCXO_FREQ // outdiv
	n = (freq // f_pfd) - 1
	ratio = freq / f_pfd
	rest = ratio - n
	m = (rest * 524288)
	# set the band parameter
	sy_sel = 8
	set_band_property_command = [0x11, 0x20, 0x01, 0x51, (band + sy_sel)]
	# send parameters
	send_cmd_receive_answer(1, set_band_property_command)
	#Set the pll parameters
	m2 = m // 0x10000
	m1 = (m - m2 * 0x10000) // 0x100
	m0 = (m - m2 * 0x10000 - m1 * 0x100)
	channel_increment = 524288 * outdiv * active_shift // (2 * VCXO_FREQ)
	c1 = (channel_increment // 0x100) & 0xFF
	c0 = (channel_increment - (0x100 * c1)) & 0xFF
	#assemble parameter string
	set_frequency_property_command = [0x11, 0x40, 0x06, 0x00, n, m2, m1, m0, c1, c0]
	#send parameters
	send_cmd_receive_answer( 1, set_frequency_property_command)
	#Set the Power
	set_pa_pwr_lvl_property_command = [0x11, 0x22, 0x01, 0x01, active_level]
	#send parameters
	send_cmd_receive_answer( 1, set_pa_pwr_lvl_property_command)

def set_deviation( deviation):
	#Make sure that Si446x::sendFrequencyToSi446x() was called before this function, so that we have set the global variable 'outdiv' properly
	#outdiv = 8;
	units_per_hz = ( 0x40000 * outdiv ) / VCXO_FREQ
	#Set deviation for RTTY
	modem_freq_dev = units_per_hz * deviation / 2.0
	modem_freq_dev = int(round(modem_freq_dev))
	mask = 0xFF;
	modem_freq_dev_0 = mask & modem_freq_dev
	modem_freq_dev_1 = mask & (modem_freq_dev >> 8)
	modem_freq_dev_2 = mask & (modem_freq_dev >> 16)
	set_modem_freq_dev_command = [0x11, 0x20, 0x03, 0x0A, modem_freq_dev_2, modem_freq_dev_1, modem_freq_dev_0]
	send_cmd_receive_answer( 1, set_modem_freq_dev_command)

def set_modem():
	#Set to CW mode
	#Sets modem into direct asynchronous 2FSK mode using GPIO0 (UART4 TX on the daughterboard)
	set_modem_mod_type_command = [0x11, 0x20, 0x01, 0x00, 0x8A]
	send_cmd_receive_answer( 1, set_modem_mod_type_command)
	#Also configure the RX packet CRC stuff here, 6 byte payload for FIELD1, using CRC and CRC check for rx with no seed, and 2FSK
	set_modem_field1_config_command = [0x11, 0x12, 0x03, 0x22, 0x06, 0x00, 0x0A]
	send_cmd_receive_answer( 1, set_modem_field1_config_command)
	#Configure the RSSI thresholding for RX mode, with 12dB jump threshold (reset if RSSI changes this much during Rx), RSSI mean with packet toggle
	#RSSI_THRESH is in dBm, it needs to be converted to 0.5dBm steps offset by ~130
	rssi = (2*(RSSI_THRESH+130))&0xFF
	set_modem_rssi_config_command = [0x11, 0x20, 0x04, 0x4A, rssi, 0x0C, 0x12, 0x3E]
	send_cmd_receive_answer( 1, set_modem_rssi_config_command )
	#Configure the match value, this constrains the first 4 bytes of data to match $$RO
	set_modem_match_config_command = [0x11, 0x30, 0x0C, 0x00, 0x24, 0xFF, 0x41, 0x24, 0xFF, 0x42, 0x52, 0xFF, 0x43, 0x4F, 0xFF, 0x44 ]
	send_cmd_receive_answer( 1, set_modem_match_config_command )
	#Configure the Packet handler to use seperate FIELD config for RX, and turn off after packet rx
	set_modem_packet_config = [0x11, 0x12, 0x01, 0x06, 0x80]
	send_cmd_receive_answer( 1, set_modem_packet_config )
	#Use CCIT-16 CRC with 0xFFFF seed on the packet handler, same as UKHAS protocol
	set_modem_crc_config = [0x11, 0x12, 0x01, 0x00, 0x85]
	send_cmd_receive_answer( 1, set_modem_crc_config )
	#Set the sync word as two bytes 0xD391, this has good autocorrelation 8/1 peak to secondary ratio, default config used, no bit errors, 16 bit
	set_modem_sync_config = [0x11, 0x11, 0x02, 0x01, 0xD3, 0x91]
	send_cmd_receive_answer( 1, set_modem_sync_config )

def start_tx( channel):
	#char change_state_command[] = {0x34, 0x07}; // Change to TX state
	#SendCmdReceiveAnswer(2, 1, change_state_command);
	#tune_tx();
	start_tx_command = [0x31, channel, 0x30, 0x00, 0x00, 0x00]
	send_cmd_receive_answer( 1, start_tx_command)

def stop_txrx():
	change_state_command = [0x34, 0x03] # Change to Ready state, stops TX or RX states
	send_cmd_receive_answer(  1, change_state_command)

def tune_tx():
	change_state_command = [0x34, 0x05] # Change to TX tune state
	send_cmd_receive_answer(  1, change_state_command)

def tune_rx():
	change_state_command = [0x34, 0x06] # Change to RX tune state
	send_cmd_receive_answer(  1, change_state_command)

def start_rx( channel):
	#char change_state_command[] = {0x34, 0x07}; // Change to RX state
	#SendCmdReceiveAnswer(2, 1, change_state_command);
	#tune_tx();
	#setup ready state on CRC matched packet, return to RX on CRC packet error, use FIELD config in packet handler for packet engine
	start_rx_command = [0x32, channel, 0x00, 0x00, 0x03, 0x08]
	send_cmd_receive_answer( 1, start_rx_command)

