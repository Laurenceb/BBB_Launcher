#!/bin/sh

echo cape-bone-iio > /sys/devices/bone_capemgr.9/slots
i2cset -f -y 0 0x24 0x09 0x01
#cat /sys/bus/iio/devices/iio:device0/in_voltage7_raw to read
