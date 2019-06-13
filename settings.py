import sys
import glob
import os
import json
import struct
import time
import threading
import re
import Queue
import serial
import serial.tools.list_ports
import readline
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math
import rlcompleter
import datetime
from draccommands import *
from utils import *
import platform

def main():
    
    serial_ports=[]
    if platform.system() == 'Darwin':    
        serial_ports = [
            p[0]
            for p in serial.tools.list_ports.comports()
            if 'SLAB_USB' in p[0]
        ]

    else :
        serial_ports = [
            p[0]
            for p in serial.tools.list_ports.comports()
            if 'ttyUSB' in p[0]
        ]
        

    print serial_ports



    if platform.system() == 'Darwin':
        SERIALPORTROC = serial_ports[0]
        SERIALPORTHV = serial_ports[1]
        SERIALPORTCAL = serial_ports[2]

    else :
        SERIALPORTROC = serial_ports[3]
        SERIALPORTHV = serial_ports[2]
        SERIALPORTCAL = serial_ports[1]


    
    # print SERIALPORTROC
    SERIALRATE = 57600
    TIMEOUT = None #set all serial calls to blocking


    print "Waiting for ARM to connect"
    print "=========================="

    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    print "ARMs connected"

    try:
        with open('settings.dat','r') as handle:
            current_settings = json.load(handle)

    except Exception, e:
        print type(e),e
        

    
    for item in current_settings:

        strawnumber = item['channel']
        threshold = item['threshold']
        gain = item['gain']

                           
        if item['type'] == 'cal':
            serroc.write(thresholdset(strawnumber, threshold, 0))
            serial_read(serroc)
            serroc.write(gainset(strawnumber, gain, 0))
            serial_read(serroc)
        elif item['type'] == 'hv':
            serroc.write(thresholdset(strawnumber, threshold, 1))
            serial_read(serroc)
            serroc.write(gainset(strawnumber, gain, 1))
            serial_read(serroc)
        else:
            print 'type unknown'
        

    
if __name__ == "__main__":
    main()

