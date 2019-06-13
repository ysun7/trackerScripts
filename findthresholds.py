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




    SERIALRATE = 57600
    TIMEOUT = None #set all serial calls to blocking


    print "Waiting for ARM to connect"
    print "=========================="

    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    print "ARMs connected"

    nlback = 30
    nsamples = 100
    
    strawnumber = int(sys.argv[1])
    
    timestamp0=time.time() 

    TARGETRATE = 10000
    #serroc.write(readData(0,0,30,100,0,0xffffffff,0xffffffff,0xffffffff,99,0,1,0))
    #serial_read(serroc)
    
    try:
        #turn off calibration pulser
        serroc.write(disablepulser())
        serial_read(serroc)
        
        # take current settings
        serroc.write(dumpsettings(strawnumber))
        mysettings = serial_read(serroc)[1]

        #start playing with thresholds
        startthresholdcal = mysettings[strawnumber]['ThresholdCal']
        startthresholdhv  = mysettings[strawnumber]['ThresholdHV']
        foundMyRate = False
        thresholdcal = startthresholdcal
        thresholdhv = startthresholdhv

        print startthresholdcal, startthresholdhv
        
        lastrate = 10000000
        foundRate = False
        lastthreshold = -1
        while (not foundRate):
            
            serroc.write(thresholdset(strawnumber, thresholdcal, 0))
            serial_read(serroc)

            #print 'done'
            #FIXME: this should really be done for individual channels

            serroc.write(readRates(nlback, nsamples, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))

            rates = serial_read(serroc, False, None, 0)[1]
            rates = serial_read(serroc, False, None, 0)[1]
            #print rates

            rate = int(rates[strawnumber]['RateCal'])
            print "CAL: ",rate,thresholdcal

            #print lastrate, TARGETRATE, rate,
            if ((lastrate < TARGETRATE and rate > TARGETRATE) or (lastrate > TARGETRATE and rate < TARGETRATE) and lastrate!=10000000):
                serroc.write(thresholdset(strawnumber, min(thresholdcal,lastthreshold), 0))
                serial_read(serroc, False, None, 0)
                foundRate = True
                continue

            lastthreshold = thresholdcal
            lastrate = rate
            
            if (rate > TARGETRATE) : #more rate than we want, increase threshold
                thresholdcal = thresholdcal - 1
                continue

            if (rate < TARGETRATE) :
                thresholdcal = thresholdcal + 1
                continue


        lastrate = 10000000
        foundRate = False
        lastthreshold = -1
        while (not foundRate):

            serroc.write(thresholdset(strawnumber, thresholdhv, 1))
            serial_read(serroc)

    
            #FIXME: this should really be done for individual channels
            serroc.write(readRates(nlback, nsamples, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))
            rates = serial_read(serroc, False, None, 0)[1]
            rates = serial_read(serroc, False, None, 0)[1]
            rate = int(rates[strawnumber]['RateHV'])
            print "HV: ",rate,thresholdhv


            if ((lastrate < TARGETRATE and rate > TARGETRATE) or (lastrate > TARGETRATE and rate < TARGETRATE) and lastrate!=10000000):
                
                serroc.write(thresholdset(strawnumber, min(lastthreshold, thresholdhv), 1))
                serial_read(serroc, False, None, 0)
                foundRate = True
                continue


            lastthreshold = thresholdhv
            lastrate = rate
            
            if (rate > TARGETRATE) : #more rate than we want, increase threshold
                thresholdhv = thresholdhv - 1
                continue

            if (rate < TARGETRATE) :
                thresholdhv = thresholdhv + 1
                continue
            

        # take final settings

        serroc.write(dumpsettings(strawnumber))
        mysettings = serial_read(serroc)[0]

        serroc.write(readRates(nlback, nsamples, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))
        rates = serial_read(serroc, False, None, 1)[1]
        rates = serial_read(serroc, False, None, 1)[1]

        print("GainCal, ThresholdCal, GainHV, ThresholdHV")
        print("%d, %d, %d, %d" %(mysettings[strawnumber]['GainCal'], mysettings[strawnumber]['ThresholdCal'], mysettings[strawnumber]['GainHV'], mysettings[strawnumber]['ThresholdHV']))
        print("Cal Rate, HV Rate, Coin Rate")
        print("%d, %d, %d" %(rates[strawnumber]['RateCal'], rates[strawnumber]['RateHV'], rates[strawnumber]['RateCoinc']))
            #print 'all done'

    except serial.serialutil.SerialException:
        serroc.close()
        print "ARM disconnected"

    except Exception, e:
      print type(e),e
    finally:
        serroc.close()

        print 'Ending...'


if __name__ == "__main__":
    main()
