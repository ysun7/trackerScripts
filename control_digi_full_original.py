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

from utils import *

#if "libedit" in readline.__doc__:
#    readline.parse_and_bind("bind ^I rl_complete")
#else:

cmds = ['read','plot_digi','rates', 'calibrate']

def completer(text, state):
    options = [x for x in cmds if x.startswith(text)]
    try:
        return options[state]
    except IndexError:
        return None

readline.set_completer(completer)        
readline.parse_and_bind("tab: complete")


HISTORY_FILENAME = 'mu2e.hist'
PREFIX = "run"


serial_ports = [
  p[0]
  for p in serial.tools.list_ports.comports()
  if 'ttyUSB' in p[0]
]
print serial_ports

if len(sys.argv) > 1:
  if re.match("hv$",sys.argv[1], flags=re.I):
    SERIALPORT = serial_ports[2]
  elif re.match("cal$",sys.argv[1], flags=re.I):
    SERIALPORT = serial_ports[1]
  else:
    SERIALPORT = sys.argv[1]
else:
#    SERIALPORT = serial_ports[1]
    SERIALPORT = 'COM32'

SERIALRATE = 230400
if len(sys.argv) > 2:
  SERIALRATE = int(sys.argv[2])
TIMEOUT = 0.2

ser = None
fout = 0
mode = 0
outputmode = 0
calibhisto = []
samples = 0
triggers = 0

rundirname = "runs"
if len(sys.argv) > 3:
  rundirname = sys.argv[3]


topdir = os.path.dirname(os.path.realpath(__file__))
rundir = os.path.join(topdir,rundirname)
files = glob.glob(rundir + "/" + PREFIX + "_*.txt")
lastrun = -1
for fn in files:
  num = int(fn.split("_")[-1].split(".txt")[0])
  if num > lastrun:
    lastrun = num

print "Waiting for ARM to connect"
print "=========================="

output_queue = Queue.Queue()

interrupted = threading.Lock()
interrupted.acquire()

def serialloop():
  global ser
  global fout
  global mode
  global outputmode
  global calibhisto

  last_read = ""

  while not interrupted.acquire(False):
    if ser != None:

      # Write data from queue to ARM
      try:
        output_data = output_queue.get(timeout = TIMEOUT)
        ser.write(output_data)
      except serial.serialutil.SerialException:
        ser.close()
        print "ARM disconnected"
        print ""
        ser = None
        while not output_queue.empty():
          try:
            output_queue.get(False)
          except Empty:
            continue
          output_queue.task_done()
      except Queue.Empty:

        # Print data from serial to screen
        try:
          bytesToRead = ser.inWaiting()
          data = last_read + ser.read(bytesToRead)
          #data = ser.readline()
          if data:
          #  outdata = data.split("\n")
            outdata = data.split("\n")
            last_read = outdata[-1]
            outdata = data.split("\n")
            for outline in outdata[:-1]:
              #
              #
              # normal printout
              if outputmode == 0:
                if outline.startswith("start"):
                  outputmode = 1
                elif outline.startswith("histostart"):
                  calibhisto = []
                  outputmode = 3
                else:
                  if len(outline) > 0:
                    print "  ",outline
              # data taking mode
              elif outputmode == 1:
                if outline.startswith("end"):
                  outputmode = 0
                  if fout and (mode == 0 or mode == 2):
                    fout.close()
                    fout = 0
                elif outline.startswith("pause"):
                  outputmode = 0
                  if fout:
                    fout.flush()
                else:
                  if fout:
#		    print "RECIEVED",len(outline)
                    fout.write(outline.replace(" ","\n"))
#                    data = ""
#                    data += struct.pack('B',0xaa)
#                    data += struct.pack('B',0xaa)
#                    data += struct.pack('B',4)
#                    data += struct.pack('B',12)
#                    output_queue.put(data)

              elif outputmode == 3:
                if outline.startswith("histoend"):
                  outputmode = 0
                else:
                  if len(outline) > 0:
                    calibhisto += outline.split(" ")


        except serial.serialutil.SerialException:
          ser.close()
          print "ARM disconnected"
          print ""
          ser = None
          while not output_queue.empty():
            try:
              output_queue.get(False)
            except Empty:
              continue
            output_queue.task_done()

    else:
      try:
        ser = serial.Serial(SERIALPORT,SERIALRATE, timeout = TIMEOUT)
        print "Connected to ARM on",SERIALPORT
      except (serial.serialutil.SerialException, OSError),e:
        ser = None

serialloop_thread = threading.Thread(target=serialloop)
serialloop_thread.start()
    
def process_command(line):
  global output_queue
  global lastrun
  global fout
  global mode
  global calibhisto
  global samples
  global triggers

  keys = line.split(" ")
  try:
    if keys[0] == "adc_rw":
      num = int(get_key_value(keys,"A",0))
      rw = int(get_key_value(keys,"w",0))
      rwaddress = int(get_key_value(keys,"a","0"),16)
      rwdata = int(get_key_value(keys,"d","0"),16)
      if rw == 0:
        rw = 1
      else:
        rw = 0
      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',10)
      data += struct.pack('B',0)
      data += struct.pack('B',num)
      data += struct.pack('B',rw)
      data += struct.pack('H',rwaddress)
      data += struct.pack('H',rwdata)
      output_queue.put(data)
    elif keys[0] == "bitslip":
      bits = int(get_key_value(keys,"b",1))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      channel   = int(get_key_value(keys,"c",-1))
      if channel >= 0:
        chan_mask1 = 0
        chan_mask2 = 0
        chan_mask3 = 0
        if channel < 32:
          chan_mask1 |= (0x1 << channel)
        elif channel < 64:
          chan_mask2 |= (0x1 << (channel-32))
        else:
          chan_mask3 |= (0x1 << (channel-64))
      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',18)
      data += struct.pack('B',1)
      data += struct.pack('H',bits)
      data += struct.pack('I',chan_mask1)
      data += struct.pack('I',chan_mask2)
      data += struct.pack('I',chan_mask3)
      output_queue.put(data)

    elif keys[0] == "find_alignment":
      clock = int(get_key_value(keys,"c",99))
      dophase = int(get_key_value(keys,"p",1))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      channel   = int(get_key_value(keys,"ch",-1))
      if channel >= 0:
        chan_mask1 = 0
        chan_mask2 = 0
        chan_mask3 = 0
        if channel < 32:
          chan_mask1 |= (0x1 << channel)
        elif channel < 64:
          chan_mask2 |= (0x1 << (channel-32))
        else:
          chan_mask3 |= (0x1 << (channel-64))

      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',18)
      data += struct.pack('B',2)
      data += struct.pack('B',clock)
      data += struct.pack('B',dophase)
      data += struct.pack('I',chan_mask1)
      data += struct.pack('I',chan_mask2)
      data += struct.pack('I',chan_mask3)
      output_queue.put(data)

    elif keys[0] == "rates":
      lookback  = int(get_key_value(keys,"d",100))
      samples   = int(get_key_value(keys,"s",10))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
#      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      channel   = int(get_key_value(keys,"c",-1))
#      chan_mask2 = 0
#      chan_mask3 = (chan_mask1 & 0xFFFFFF00)
#      chan_mask1 = (chan_mask1 & 0x00FFFFFF)
#      chan_mask1 = (chan_mask1 & 0x0000FFFF)
      if channel >= 0:
        chan_mask1 = 0
        chan_mask2 = 0
        chan_mask3 = 0
        if channel < 32:
          chan_mask1 |= (0x1 << channel)
        elif channel < 64:
          chan_mask2 |= (0x1 << (channel-32))
        else:
          chan_mask3 |= (0x1 << (channel-64))

      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',20)
      data += struct.pack('B',10)
      data += struct.pack('H',lookback)
      data += struct.pack('H',samples)
      data += struct.pack('I',chan_mask1)
      data += struct.pack('I',chan_mask2)
      data += struct.pack('I',chan_mask3)
      output_queue.put(data)
    elif keys[0] == "check_ramp":
      samples = int(get_key_value(keys,"s",samples))
      triggers = int(get_key_value(keys,"T",min(triggers,100)))
      cur_runname = PREFIX + "_" + str(lastrun) + ".txt"
      filename = get_key_value(keys,"f",cur_runname)
      if fout:
        fout.close()
      fout = open(os.path.join(rundir,filename))
      checkramp(fout,samples,triggers)
      fout.close()
    elif keys[0] == "plot_digi":
      display = int(get_key_value(keys,"d",1))
      plot = int(get_key_value(keys,"p",1))
      samples = int(get_key_value(keys,"s",samples))
      triggers = int(get_key_value(keys,"T",min(triggers,100)))
      chanmask = int(get_key_value(keys,"c","0xFF"),16)
      cur_runname = PREFIX + "_" + str(lastrun) + ".txt"
      filename = get_key_value(keys,"f",cur_runname)
      if fout:
        fout.close()

      fout = open(os.path.join(rundir,filename))
      plotfile(fout,samples,triggers,display,plot,chanmask)
      fout.close()
    elif keys[0] == "close":
      fout.close()
      print "CLOSED"
    elif keys[0] == "test":
      next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      while os.path.isfile(os.path.join(rundir,next_runname)):
        lastrun += 1
      	next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      filename = next_runname
      print "OPENING FILE",filename
      fout = open(os.path.join(rundir,filename),"w")
      lastrun += 1

      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',4)
      data += struct.pack('B',2)
      output_queue.put(data)
    elif keys[0] == "read":
      adc_mode  = int(get_key_value(keys,"a","0"),16)
      tdc_mode  = int(get_key_value(keys,"t",0))
      lookback  = int(get_key_value(keys,"l",8))
      samples   = int(get_key_value(keys,"s",16))
      triggers  = int(get_key_value(keys,"T",0))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      #clock     = int(get_key_value(keys,"c",99))
      pulser    = int(get_key_value(keys,"p",0))
      delay     = int(get_key_value(keys,"d",1))
      mode      = int(get_key_value(keys,"m",0))
      message = get_message_value(keys,'M')
      channel = int(get_key_value(keys,"ch",-1))
      clock = 99
      #chan_mask2 = 0
      #chan_mask3 = (chan_mask1 & 0xFFFF0000)
      #chan_mask1 = (chan_mask1 & 0xFFFF)
      

      if channel >= 0:
        chan_mask1 = 0
        chan_mask2 = 0
        chan_mask3 = 0
        if channel < 32:
          chan_mask1 |= (0x1 << channel)
        elif channel < 64:
          chan_mask2 |= (0x1 << (channel-32))
        else:
          chan_mask3 |= (0x1 << (channel-64))

        

      
      next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      while os.path.isfile(os.path.join(rundir,next_runname)):
        lastrun += 1
      	next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      filename = get_key_value(keys,"f",next_runname)

#        run_settings = {'adc_mode':adc_mode,'tdc_mode':tdc_mode,'lookback':lookback,'samples':samples,'triggers':triggers,'chan_mask':chan_mask,'mode':mode,'clock':clock,'delay':delay,'pulser':pulser,'filename':filename,'start_time':time.strftime("%Y-%m-%d %H:%M:%S"),'message':message}
      run_settings = {'lookback':lookback,'samples':samples,'triggers':triggers,'mode':mode,'delay':delay,'filename':filename,'start_time':time.strftime("%Y-%m-%d %H:%M:%S"),'message':message}
      print "OPENING FILE",filename
      fout = open(os.path.join(rundir,filename),"w")
      try:
        with open('settings.dat','r') as handle:
          current_settings = json.load(handle)
      except Exception:
        current_settings = {"thresh": [], "gain" : [], "caldac" : []}
        for i in range(16):
          current_settings["thresh"].append(0)
          current_settings["gain"].append(0)
        for i in range(8):
          current_settings["caldac"].append(0)

      json.dump(current_settings,fout)
      fout.write("\n")
      json.dump(run_settings,fout)
      fout.write("\n")
      if filename == next_runname:
        lastrun += 1
      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',32)
      data += struct.pack('B',100)
      data += struct.pack('B',adc_mode)
      data += struct.pack('B',tdc_mode)
      data += struct.pack('H',lookback)
      data += struct.pack('H',samples)
      data += struct.pack('I',triggers)
      data += struct.pack('I',chan_mask1)
      data += struct.pack('I',chan_mask2)
      data += struct.pack('I',chan_mask3)
      data += struct.pack('B',clock)
      data += struct.pack('B',pulser)
      data += struct.pack('H',delay)
      data += struct.pack('H',mode)
      output_queue.put(data)
    elif keys[0] == "stop_run":
      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',4)
      data += struct.pack('B',101)
      output_queue.put(data)


    elif keys[0] == "calibrate":
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      clock     = int(get_key_value(keys,"c",1))

      chan_mask2 = 0
     # chan_mask3 = (chan_mask1 & 0xFF00)<<16
     # chan_mask1 = (chan_mask1 & 0xFF)
      chan_mask3 = (chan_mask1 & 0xFFFF0000)
      chan_mask1 = (chan_mask1 & 0x0000FFFF)
      fout = open("calibrate_histogram.dat","w")

      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',17)
      data += struct.pack('B',102)
      data += struct.pack('I',chan_mask1)
      data += struct.pack('I',chan_mask2)
      data += struct.pack('I',chan_mask3)
      data += struct.pack('B',clock)
      output_queue.put(data)


    else:
      print "Unknown command"
  except (ValueError, struct.error), e:
    print "Bad Input:",e

    
if os.path.exists(HISTORY_FILENAME):
  readline.read_history_file(HISTORY_FILENAME)

# keyboard input loop
try:
  while True:
    line = raw_input()
    if line:
      process_command(line)
except KeyboardInterrupt:
  interrupted.release()
  serialloop_thread.join()
except Exception, e:
  print type(e),e
  interrupted.release()
  serialloop_thread.join()
finally:
  print 'Ending...'
  readline.write_history_file(HISTORY_FILENAME)
