#!/bin/sh

export http_proxy=http://mainproxy.nottingham.ac.uk:8080/
route add default gw 192.168.7.1
ntpdate -b -s -u pool.ntp.org
