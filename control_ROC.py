import sys
import glob
import os
import json
import struct
import time
import threading
import Queue
import serial
import readline
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math
import rlcompleter
from unpacker import *
from pprint import pprint
import constants
from draccommands import *
from utils import *

if "libedit" in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")

cmds = ['set_preamp_gain','set_preamp_thresh','pulser_on','pulser_off','set_caldac','dump_settings','mcpwritepin','calpulse','readSPI','readDeviceID','readSensor','readSlowAmp','testDDR','resetROC','digi_rw','readTVS','adc_rw','bitslip','find_alignment','read','plot_digi','check_ramp','rates', 'calibrate','adc_init_info','find_thresholds','histo','roc_rw','ddr_toggle','ddr_read','ddr_clean','ddr_memfifo_fill']

def completer(text, state):
    options = [x for x in cmds if x.startswith(text)]
    try:
        return options[state]
    except IndexError:
        return None

HISTORY_FILENAME = 'mu2e_roc.hist'
PREFIX = "run"

if os.path.exists(HISTORY_FILENAME):
    print 'reading'
    readline.read_history_file(HISTORY_FILENAME)


readline.set_completer(completer)        
readline.parse_and_bind("tab: complete")
        
SERIALPORT = "/dev/ttyUSB0"
if len(sys.argv) > 1:
  SERIALPORT = sys.argv[1]

SERIALRATE = 230400
if len(sys.argv) > 2:
  SERIALRATE = int(sys.argv[2])

TIMEOUT = 0.5

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
            ptype,rd,shl = serial_read(ser, True, fout, 5)
            if ptype == constants.READHISTO:
              calibhisto = rd["data"]
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
      except (serial.serialutil.SerialException, OSError) as e:
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
    if keys[0] == "set_preamp_gain":

        channel = int(get_key_value(keys,"c",-1))
        preamptype = int(get_key_value(keys,"hv",0))
        fvalue = float(get_key_value(keys,"v",-1))
        dvalue = int(get_key_value(keys,"d"))
        if fvalue >= 0:
            dvalue = fvalue/3.3*1023

        data=gainset(channel,dvalue,preamptype)
        output_queue.put(data)

      
    elif keys[0] == "set_preamp_thresh":

        channel = int(get_key_value(keys,"c",-1))
        preamptype = int(get_key_value(keys,"hv",0))
        fvalue = float(get_key_value(keys,"v",-1))
        dvalue = int(get_key_value(keys,"d"))
        print 'here'
        if fvalue >= 0:
            dvalue = fvalue/3.3*1023

        data=thresholdset(channel,dvalue,preamptype)
        output_queue.put(data)
      
    elif keys[0] == "set_caldac":
        chan_mask = int(get_key_value(keys,"C"),16)
        channel = int(get_key_value(keys,"c",-1))
        if channel >= 0:
            chan_mask |= (0x1 << channel)
        fvalue = float(get_key_value(keys,"v",-1))
        dvalue = int(get_key_value(keys,"d"))
        if fvalue >= 0:
            dvalue = fvalue/3.3*1023

        data=caldacset(chan_mask,dvalue)
        output_queue.put(data)

        
    elif keys[0] == "pulser_on":
        #-d 10000 -y 100

        chan_mask = int(get_key_value(keys,"C"),16)
        oddoreven = int(get_key_value(keys,"P"),16)
        channel = int(get_key_value(keys,"c",-1))
        pulser_odd = int(get_key_value(keys,"o",0))
        if channel >= 0:
            chan_mask |= (0x1 << channel)
        if channel % 2 == 0:
            oddoreven = 1
        else:
            oddoreven = 0

        freq = float(get_key_value(keys,"f",-1))
        delay = int(get_key_value(keys,"d",1000))
        dutycycle = int(get_key_value(keys,"y",10))
        if (freq > 0):
            delay = int(1./freq*1000000.)

        data=setpulseron(chan_mask,pulser_odd,dutycycle,delay)
        output_queue.put(data)

        
    elif keys[0] == "pulser_off":

        data=setpulseroff()
 
        output_queue.put(data)
        
    elif keys[0] == "dump_settings":

        channel = int(get_key_value(keys,"c",100))
        data=dumpsettings(channel)
        output_queue.put(data)

    elif keys[0] == "histo":
      channel = int(get_key_value(keys,"c",100))
      hv_or_cal = int(get_key_value(keys,"h",0))
      hv_or_cal = ((hv_or_cal)+1)%2
      data = readhisto(channel,hv_or_cal)
      output_queue.put(data)

    elif keys[0] == "plot_histo":
                  fig = plt.figure()
                  plt.plot(calibhisto)
                  plt.show()
                  plt.close(fig)


    elif keys[0] == "mcpwritepin":
        mcp = int(get_key_value(keys,"m",0))
        channel = int(get_key_value(keys,"c",0))
        pinvalue = int(get_key_value(keys,"v",0))
        data=mcpwritepin(mcp,channel,pinvalue)
        output_queue.put(data)
        
    elif keys[0] == "calpulse":

        chan_mask = int(get_key_value(keys,"C"),16)
        channel = int(get_key_value(keys,"c",-1))
        if channel >= 0:
            chan_mask |= (0x1 << channel)

        data=sendonecalpulse(chan_mask)
        output_queue.put(data)
        
    elif keys[0] == "readSPI":

        data=readspi()
        output_queue.put(data)
    elif keys[0] == "readDeviceID":

        data=readDeviceID()
        output_queue.put(data)

    elif keys[0] == "readSensor":
        data=readSensors()
        output_queue.put(data)
         
    elif keys[0] == "readSlowAmp":
        slot = int(get_key_value(keys,"s",0))
        channel = int(get_key_value(keys,"c",0))
        mode = int(get_key_value(keys,"m",0))
        rate = int(get_key_value(keys,"r",2))
        gain = int(get_key_value(keys,"g",0))
      
        data=readSlowAmps(slot, channel,mode,rate,gain)
        output_queue.put(data)

    elif keys[0] == "testDDR":
        ddrcs = int(get_key_value(keys,"c",0))
        ddrwen = int(get_key_value(keys,"w",0))
        ddrren = int(get_key_value(keys,"r",0))
        ddrdmaen = int(get_key_value(keys,"d",2))
        ddrnhits = int(get_key_value(keys,"n",0))
        ddrraddr = int(get_key_value(keys,"a",0))
        ddrdata = int(get_key_value(keys,"y",0))
        ddrpattern = int(get_key_value(keys,"p",0))
        ddroffset = int(get_key_value(keys,"o",0))
        
        # ddrwen = int(get_key_value(keys,"w",0))
        # ddrren = int(get_key_value(keys,"r",0))
        # ddrwaddr = int(get_key_value(keys,"a",0))
        # ddrraddr = int(get_key_value(keys,"b",0))
        # ddrwdata = int(get_key_value(keys,"y",0))

        data=testDDR(ddrcs,ddrwen,ddrren,ddrdmaen,ddrnhits,ddrpattern,ddrraddr,ddroffset)
        # data=testDDR(ddrwen,ddrren,ddrwaddr,ddrraddr,ddrwdata)

        output_queue.put(data)

    elif keys[0] == "resetROC":
        data=resetROC()
        output_queue.put(data)

    # toggle HV / CAL, HV = 1, CAL = 0 
    #elif keys[0] == "toggleCALHV":
    #    hvcal = int(keys[1])
    #    if hvcal != 0:
    #      hvcal = 1
    #    data=toggleCALHV(hvcal)
    #    output_queue.put(data)        
    
    elif keys[0] == "digi_rw":
      thishvcal = int(get_key_value(keys,"h",1))
      rw = int(get_key_value(keys,"w",0))
      rwaddress = int(get_key_value(keys,"a","0"),16)
      rwdata = int(get_key_value(keys,"d","0"),16)
      
      data = digiRW(rw, thishvcal, rwaddress, rwdata)
      output_queue.put(data)

    elif keys[0] == "roc_rw":
      raddress = int(get_key_value(keys,"a","0"),16)
      
      data = rocRW(raddress)
      output_queue.put(data)

    elif keys[0] == "readTVS":
      data = readTVS()
      output_queue.put(data)

    #=========================================================

    elif keys[0] == "ddr_toggle":
      ddr_select = int(get_key_value(keys,"d",1))
      page_no = int(get_key_value(keys,"p",100))
      # page_no = int(get_key_value(keys,"p",262144))
      if page_no > 262144:
        page_no = 262144
        print "Maximum page number is 262144. Page number is set to 262144."
      data = ddrToggle(ddr_select, page_no)
      output_queue.put(data)

    elif keys[0] == "ddr_read":
      page_no_to_read = int(get_key_value(keys,"p",100))
      ifclean = int(get_key_value(keys,"c",1))

      next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      while os.path.isfile(os.path.join(rundir,next_runname)):
        lastrun += 1
        next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      filename = get_key_value(keys,"f",next_runname)

      print "OPENING FILE",filename
      fout = open(os.path.join(rundir,filename),"w")

      if filename == next_runname:
        lastrun += 1

      data = ddrRead(page_no_to_read, ifclean)
      output_queue.put(data)

    elif keys[0] == "ddr_clean":
      data = ddrClean()
      output_queue.put(data)
      
    elif keys[0] == "ddr_memfifo_fill":
      data = ddrMemFifoFill()
      output_queue.put(data)

    #=========================================================
    
    elif keys[0] == "adc_rw":
      num = int(get_key_value(keys,"A",0))
      rw = int(get_key_value(keys,"w",0))
      rwaddress = int(get_key_value(keys,"a","0"),16)
      rwdata = int(get_key_value(keys,"d","0"),16)
      if rw == 0:
        rw = 1
      else:
        rw = 0
      data = adcRW(num, rw, rwaddress, rwdata)
      output_queue.put(data)
    
    elif keys[0] == "bitslip":
      bits = int(get_key_value(keys,"b",1))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      channel   = int(get_key_value(keys,"c",-1))
      if channel >= 0:
         chan_mask1,chan_mask2,chan_mask3 = channelmask(channel)

      data = bitSlip(bits, chan_mask1, chan_mask2, chan_mask3)
      output_queue.put(data)

    elif keys[0] == "find_alignment":
      clock = int(get_key_value(keys,"c",99))
      dophase = int(get_key_value(keys,"p",1))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      #chan_mask1 = int(get_key_value(keys,"C","C71C71C7"),16)
      #chan_mask2 = int(get_key_value(keys,"D","71C71C71"),16)
      #chan_mask3 = int(get_key_value(keys,"E","1C71C71C"),16)
      channel   = int(get_key_value(keys,"ch",-1))
      if channel >= 0:
         chan_mask1,chan_mask2,chan_mask3 = channelmask(channel)

      data = findAlignment(clock, dophase, chan_mask1, chan_mask2, chan_mask3)
      output_queue.put(data)

    elif keys[0] == "rates":
        lookback  = int(get_key_value(keys,"d",100))
        samples   = int(get_key_value(keys,"s",10))
        chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
        #      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
        chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
        chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
        channel   = int(get_key_value(keys,"c",-1))


        if channel >= 0 :
            chan_mask1,chan_mask2,chan_mask3 = channelmask(channel)

        data = readRates(lookback, samples, chan_mask1, chan_mask2, chan_mask3)
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
      data += struct.pack('B',constants.FINDALIGNMENTCMDID)
      output_queue.put(data)
    elif keys[0] == "read":
      adc_mode  = int(get_key_value(keys,"a","0"),16)
      tdc_mode  = int(get_key_value(keys,"t",0))
      lookback  = int(get_key_value(keys,"l",8))
      samples   = int(get_key_value(keys,"s",16))
      triggers  = int(get_key_value(keys,"T",0))
      chan_mask1 = int(get_key_value(keys,"C","C71C71C7"),16)
      chan_mask2 = int(get_key_value(keys,"D","71C71C71"),16)
      chan_mask3 = int(get_key_value(keys,"E","1C71C71C"),16)
      #chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      #chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      #chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
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
        chan_mask1,chan_mask2,chan_mask3 = channelmask(channel)

      datasize = triggers * (samples+4)
      if datasize > 64000:
        triggers = math.floor(64000/(samples+4))
        print "Assigned values for triggers and samples will cause a FIFO overflow"
        print "Trigger number is reduced to {}".format(triggers)
        
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
      data = readData(adc_mode, tdc_mode, lookback, samples, triggers, chan_mask1, chan_mask2, chan_mask3, clock, pulser, delay, mode)
      output_queue.put(data)
    elif keys[0] == "stop_run":
      data = stopRun()
      output_queue.put(data)
      
    # CMDID no longer exist in SoftConsole
    # elif keys[0] == "calibrate":
    #   chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
    #   chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
    #   chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
    #   clock     = int(get_key_value(keys,"c",1))
    #
    #   chan_mask2 = 0
    #  # chan_mask3 = (chan_mask1 & 0xFF00)<<16
    #  # chan_mask1 = (chan_mask1 & 0xFF)
    #   chan_mask3 = (chan_mask1 & 0xFFFF0000)
    #   chan_mask1 = (chan_mask1 & 0x0000FFFF)
    #   fout = open("calibrate_histogram.dat","w")
    #
    #   data = ""
    #   data += struct.pack('B',0xaa)
    #   data += struct.pack('B',0xaa)
    #   data += struct.pack('B',17)
    #   data += struct.pack('B',102)
    #   data += struct.pack('I',chan_mask1)
    #   data += struct.pack('I',chan_mask2)
    #   data += struct.pack('I',chan_mask3)
    #   data += struct.pack('B',clock)
    #   output_queue.put(data)

    elif keys[0] == "adc_init_info":
      data = adcInitInfo()
      output_queue.put(data)
    
    elif keys[0] == "package_test":
      data = packageTest()
      output_queue.put(data)

    elif keys[0] == "find_thresholds":
      lookback  = int(get_key_value(keys,"l",30))
      samples   = int(get_key_value(keys,"s",100))
      chan_mask1 = int(get_key_value(keys,"C","FFFFFFFF"),16)
      chan_mask2 = int(get_key_value(keys,"D","FFFFFFFF"),16)
      chan_mask3 = int(get_key_value(keys,"E","FFFFFFFF"),16)
      channel = int(get_key_value(keys,"ch",-1))
      target_rate = int(get_key_value(keys,"tr",10000))
      verbose = int(get_key_value(keys,"v",0))
   
      if channel >= 0:
        chan_mask1,chan_mask2,chan_mask3 = channelmask(channel)
      else: #finding process only print for single channel
        verbose = 0

      data = findThresholds(lookback, samples, chan_mask1, chan_mask2, chan_mask3, target_rate, verbose)
      output_queue.put(data)

 
    else:
      print "Unknown command"
  except (ValueError, struct.error), e:
    print "Bad Input:",e



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
