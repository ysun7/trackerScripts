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
import argparse
from pprint import PrettyPrinter
from draccommands import *
from utils import get_key_value, plotfile

def main():
    global dcvoltages
    global fout
    global mode
    global settingscal
    global settingshv
    global calenvdata
    global hvenvdata
    global rundir
    global timestamp0
    global rates

    global serroc

    rates = {}
    
    serial_ports = [
      p[0]
      for p in serial.tools.list_ports.comports()
      if 'ttyUSB' in p[0]
                    #if 'SLAB_USB' in p[0]
    ]

    print serial_ports

    SERIALPORTROC = serial_ports[3]
    #SERIALPORTROC = serial_ports[0]
    #print SERIALPORTROC

    SERIALRATE = 57600
    TIMEOUT = 10

    fout = 0
    mode = 0
    triggers = 0

    print "Waiting for ARM to connect"
    print "=========================="

    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    print "ARMs connected"

    timestamp0=time.time() 

    irun = 0

    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('-s','--settings', action='store_true',
                    help='Print settings or not')
    parser.add_argument('channel', type=int,nargs='?',
                    help='Channel number')

    args = parser.parse_args()
    

    #fout = open(os.path.join('/home/ysun/ROCCALHV_1FIFO','testrun.txt'))
    try:
        
        serroc.write(disablepulser())
        serial_read(serroc)

        serroc.write(readstrawrates())
        serial_read(serroc)[0]
        rd = serial_read(serroc)[0]

        for ch in rd:
            rates[int(ch)] = [int(rd[ch]["RateHV"]), int(rd[ch]["RateCal"]), int(rd[ch]["RateCoinc"])]
        
        if (args.channel):
            print "Rates ",time.time(),rates[args.channel]
        else:
            #           print "Rates ",time.time(),rates
            pp = PrettyPrinter(indent=4)
            pp.pprint(rates)
        
        if (args.settings):
            
            #serroc.write(dumpsettings(100))
            #rd = serial_read(serroc, True)[0]
            rd1 = ''
            serroc.write(readSensors())
            while(len(rd1)<=0):
            #time.sleep(10)
                rd1 = serial_read(serroc, True)[0]
        
        print 'all done'

    except Exception, e:
      print type(e),e
    finally:
        serroc.close()
        print 'Ending...'


if __name__ == "__main__":
    main()
