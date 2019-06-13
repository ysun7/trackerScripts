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
from draccommands import *
from utils import *
import platform

# Functions with idendical copies are all in utils now

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


  

#  SERIALPORTROC = "/dev/tty.SLAB_USBtoUART"
  #SERIALRATE = 921600
  SERIALRATE = 57600
  TIMEOUT = 0.2

  PREFIX = "run"

  mode = 0
  triggers = 0

  topdir = os.path.dirname(os.path.realpath(__file__))

  try:
    configfile = open(os.path.join(topdir,'localconfig.txt'))
  except Exception:
    configfile = open(os.path.join(topdir,'defaultconfig.txt'))

  rundir = os.path.join(topdir,'runs')
  for line in configfile:
    line = line[:-1].strip('=').split('=')
    if len(line) > 1: 
      if line[0] == "rundir":
        rundir = line[1]
      elif line[0] == "prefix":
        prefix = line[1]
  if not os.path.exists(rundir):
    os.makedirs(rundir)

  print "Waiting for ARM to connect"
  print "=========================="
  try:
    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    print "Connected to ARM on",SERIALPORTROC
  except (serial.serialutil.SerialException, OSError) as e:
    serroc = None

  samples=200
  # keyboard input loop
  try:

    dcvoltages=[]




    if len(sys.argv)>1:
      strawch = int(sys.argv[1])
    else:
      strawch = 100

    strawnumber = strawch

    cmd = dumpsettings(strawnumber)
    serroc.write(cmd)

    mysettings = serial_read(serroc)[1]
    #print mysettings

    for iside in range(3):
        if iside == 0: #zero the cal side
          cmd=gainset(strawnumber,0,0)
          serroc.write(cmd)
          serial_read(serroc)
          cmd=gainset(strawnumber,mysettings[strawnumber]['GainHV'],1)    
          serroc.write(cmd)
          serial_read(serroc)
        elif iside == 1: #zero the hv side
          cmd=gainset(strawnumber,mysettings[strawnumber]['GainCal'],0)
          serroc.write(cmd)
          serial_read(serroc)
          cmd=gainset(strawnumber,0,1)    
          serroc.write(cmd)
          serial_read(serroc)
        elif iside == 2: #set both to default
          cmd=gainset(strawnumber,mysettings[strawnumber]['GainCal'],0)
          serroc.write(cmd)
          serial_read(serroc)
          cmd=gainset(strawnumber,mysettings[strawnumber]['GainHV'],1)    
          serroc.write(cmd)
          serial_read(serroc)

        cmd = readstrawcmd(strawnumber,samples)
        serroc.write(cmd)

        try:
          ptype, rd, strawHitList = serial_read(serroc, False, None ,5)
          dcvoltages.append( (-1000. + strawHitList[0].getAverageSample()*2000./1024.)/10.  )
        except serial.serialutil.SerialException:
            serroc.close()
            print "ARM disconnected"
            print ""
            serroc = None
            while not output_queue.empty():
              try:
                output_queue.get(False)
              except Empty:
                continue
              output_queue.task_done()
    print "==========================="

    cmd = disablepulser()
    serroc.write(cmd)
    serial_read(serroc)

    serroc.close()



    print 'ch HVGAIN HVTHR CALGAIN CALTHR HV(mV) CAL(mV) TOT(mV)'
    print '%2d %6d %5d %7d %6d %6.2f %6.2f %6.2f' % (strawnumber, mysettings[strawnumber]['GainHV'],mysettings[strawnumber]['ThresholdHV'],mysettings[strawnumber]['GainCal'],mysettings[strawnumber]['ThresholdCal'],dcvoltages[0],dcvoltages[1],dcvoltages[2])




    print 'all done'


  except Exception, e:
    print type(e),e
  finally:
    print 'Ending...'


if __name__ == "__main__":
    main()

