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

#if "libedit" in readline.__doc__:
#    readline.parse_and_bind("bind ^I rl_complete")
#else:
readline.parse_and_bind("tab: complete")


HISTORY_FILENAME = 'mu2e_cal.hist'
PREFIX = "run"

commands = [
    # List all commands
    "help",

    # read
    # -c <channel number> or -C <channel mask (hex)>
    # 
    "read"]



serial_ports = [
  p[0]
  for p in serial.tools.list_ports.comports()
  if 'SLAB_USBtoUART' in p[0]
]

print serial_ports

  

if len(sys.argv) > 1:
  if re.match("hv$",sys.argv[1], flags=re.I):
    SERIALPORT = serial_ports[1]
  elif re.match("cal$",sys.argv[1], flags=re.I):
    SERIALPORT = serial_ports[2]
  else:
    SERIALPORT = sys.argv[1]
else:
#    SERIALPORT = serial_ports[1]
    SERIALPORT = 'COM32'
SERIALRATE = 921600
# if len(sys.argv) > 2:
#   SERIALRATE = int(sys.argv[2])
TIMEOUT = 0.2

ser = None
fout = 0
mode = 0
outputmode = 0
calibhisto = []
samples = 0
triggers = 0
skiptrigs=-1

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
if len(sys.argv) > 2:
  rundir = sys.argv[2]
if not os.path.exists(rundir):
  os.makedirs(rundir)

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

def showdata(y):
    SampleRate = 20
    nplot = 200

    fig = plt.figure()

    ax1 = fig.add_subplot(111)

    ax1.set_title("Data")
    ax1.set_xlabel('ns')
    ax1.set_ylabel('ADC counts')


    x=range(0,SampleRate*len(y),SampleRate)
#    y2 = y[:]
#    for i in range(len(y)):
#      y[i] = y[i] + np.cos((x[i]-10200)/2400.)*95-1290
    ax1.plot(x,y)
    ax1.get_yaxis().get_major_formatter().set_useOffset(False)
#    ax1.plot(x,y2)
#    leg = ax1.legend()
    plt.show()
    plt.close(fig)

def plotfile(fout,samples,triggers,display,plot,chanmask,skiptrigs):
  allts = []
  deltats = []
  data = fout.read()
  if len(data) < 12:
    print "No data found"
    return
  data = data.split('\n')
  data = filter(lambda x: len(x)>0, data)
  data = [(int(i,16) & 0xFFF) for i in data]
  print len(data),"total words, expected",(samples+12)*triggers

  T1 = []
  adc1 = []
  deltaT1 = []
  deltaT2 = []

  if True:
    gtimeold = -1
    htimeold = -1
    ctimeold = -1
    latestold = 0

    for itrig in range(triggers):
      if (itrig+1)*(samples+12) > len(data):
        break
      tdata = data[itrig*(samples+12):(itrig+1)*(samples+12)]
      channel = (tdata[3] >> 6) & 0x3F

      gtime = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
      htime = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0))
      ctime = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0))
      htime = (htime & 0x3FFFFF00) + (0xFF - (htime&0xFF));
      ctime = (ctime & 0x3FFFFF00) + (0xFF - (ctime&0xFF));

      hvfired = 0
      calfired = 0

      if htime > 0 and htime != htimeold:
        hvfired = 1
      if ctime > 0 and ctime != ctimeold:
        calfired = 1

      adc1 = tdata[12:]
      T1.append(htime)

      
      if hvfired:
        hval = htime
      else:
        hval = "  X  "
      if calfired:
        cval = ctime
      else:
        cval = "  X  "
      if hvfired and calfired:
        hvcaldeltat = (ctime-htime)*15.625*10**-3 # in ns
      else:
        hvcaldeltat = "  X  "

      if gtimeold < 0:
        gtimeold = gtime
        htimeold = htime
        ctimeold = ctime
        if (htime >= ctime or not hvfired) and hvfired:
          latestold = htime
        elif (ctime >= htime or not calfired) and calfired:
          latestold = ctime
        mindeltat = "  X  "
      else:
        if (htime >= ctime or not hvfired) and calfired:
          mindeltat = ctime - latestold
          if gtime != gtimeold:
            mindeltat += (gtime-gtimeold)*2**28
          mindeltat *= 15.625*10**-6 # in us
          latestold = htime
        elif (ctime >= htime or not calfired) and hvfired:
          mindeltat = htime - latestold
          if gtime != gtimeold:
            mindeltat += (gtime-gtimeold)*2**28
          mindeltat *= 15.625*10**-6 # in us
          latestold = ctime
        else:
          mindeltat = "  X  "

      if display:
        print "Trig:",itrig," Channel",channel,"- time since last:",mindeltat,"deltat:",hvcaldeltat,"gtime:",gtime,"htime:",hval,"ctime:",cval
        dcvoltage = (-750. + np.mean(adc1)*1500./4096.)/10
        print "mean ped=",np.mean(adc1)," rms=",np.std(adc1), " voltage=",dcvoltage

      if plot and itrig>skiptrigs:
        showdata(adc1)
        adc1 = []
      gtimeold = gtime
      htimeold = htime
      ctimeold = ctime





def measure_rate(fout,nsamples,triggers):
    data = []
    data2 = []

    for line in fout:
      if line == '\n':
        continue;
      data.append(int(line,16) & 0xFFF)
      data2.append(int(line,16) & 0xF000)
      
    offset=0 ## first set offset (should just be zero) to extract #samples
    samples = 0
    while True:
      if data2[offset] != 0x0:
        while data2[offset+12+samples] == 0x0:
          samples += 1
        break

    if samples != nsamples:
        print "Extracted number of samples is wrong"
    
    skip=0 ## number of triggers at beginning of file to be skipped  
    print "Offset=",offset,", Samples=",samples,", Skip=",skip
    index = offset+skip*(12+samples)
    tdata = data[index:(index+12+samples)]
    gtime0 = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
    htime0 = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0))
    ctime0 = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0))
    htime0 = (htime0 & 0x3FFFFF00) + (0xFF - (htime0&0xFF));
    ctime0 = (ctime0 & 0x3FFFFF00) + (0xFF - (ctime0&0xFF));

    print "Global0=",gtime0,", HV0=",htime0,", Cal0=",ctime0

    hits = 0
    noise_hits = 0

    gtime_last = -1
    htime_last = -1
    ctime_last = -1

    start_counting=0 # only start after gtime is set to 0, some triggers in beginning come in very high gtime

    countfail=0
    badevent=0

    # Boolean that identifies which side is triggering (here used in general, not per trigger)
    triggerOnCal=0
    triggerOnHV=0

    while True:
        if (index+12+samples) >= len(data): #EOF
          break

        countfail=0
        #if data2[index]==0x1000: #this should always be true


        while True:
          countfail = countfail+1
          if data2[index+countfail]==0x1000: 
            if countfail != samples+12: #ensure correct number of samples, otherwise skip
              badevent=1
            break

        if badevent: #skip if n_samples not correct
          print "Badevent index:", index, "  -- words between 0x1000's :", countfail
          index+=countfail
          badevent=0
          continue  


        hits += 1

        tdata = data[index:(index+12+samples)]
        gtime = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
        htime = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0)) #time for HV side
        ctime = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0)) #time for Cal side
        htime = (htime & 0x3FFFFF00) + (0xFF - (htime&0xFF));
        ctime = (ctime & 0x3FFFFF00) + (0xFF - (ctime&0xFF));



        if gtime_last > -1:
          print index,":","Global=",gtime,", HV=",htime,", Cal=",ctime,", D[HV]=",(htime-htime_last)*15.625*10**-9,"ms , D[Cal]=",(ctime-ctime_last)*15.625*10**-9,"ms , D[G]=",(gtime-gtime_last)*2**28*15.625*10**-9,"[ms]"
    #      print index,":",(gtime-gtime_last)*2**28*15.625*10**-3 + (htime-htime_last)*15.625*10**-3,gtime,gtime_last,htime,htime_last
    #      print sumadc

        if htime==htime_last: ## if it happens once that's enough
          triggerOnCal=1 
        if ctime==ctime_last: ## if it happens once that's enough
          triggerOnHV=1 

        gtime_last = gtime
        htime_last = htime
        ctime_last = ctime
        index += 12+samples


    ## Calculate DeltaT
    num_hits = len(data)/(12+samples)
    if (gtime-gtime0)<0: # skip large initial gtime0, should go back to 0 after couple hits
      # should fix this to search for the first gtime=0 instead
      deltat = (gtime)*2**28*15.625*10**-9
      num_hits -= 2
    else:
      deltat = (gtime-gtime0)*2**28*15.625*10**-9
    if triggerOnHV: # use htime or ctime depending which side is triggering
      deltat += (htime-htime0)*15.625*10**-9 # in ms
    else: ## if here, then Dt[HV] was never zero. Whether -t was set to 0,1,2,3, below should be good
      deltat += (ctime-ctime0)*15.625*10**-9 # in ms


    if deltat<0:
      print "Dt = ", deltat


    if triggerOnHV:
        print "Triggered on HV"
    else:
        print "Trigger on cal"
    
    print "total time: ",deltat,"ms"
    print "total hits: ",num_hits
    print "\n Rate: ", num_hits/deltat,"kHz\n"



def serialloop():
  global ser
  global fout
  global mode
  global outputmode
  global calibhisto
  global transmissiondone
  
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
          data = ser.readline()
          if data:
            outdata = data.split("\n")
            for outline in outdata:
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
                    if outline.startswith("FAILED") or outline.startswith("SUCCESS"):
                      transmissiondone=1
              # data taking mode
              elif outputmode == 1:
                if outline.startswith("end"):
                  outputmode = 0
                  if fout and (mode == 0 or mode == 2):
                    fout.close()
                    fout = 0
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

def get_key_value(keys, flag, default = "0"):
  index = 1
  while True:
    if index >= len(keys) - 1:
      return default
    if keys[index] == ("-" + flag):
      return keys[index+1]
    index += 1

def process_command(line):
  global output_queue
  global lastrun
  global fout
  global mode
  global calibhisto
  global samples
  global triggers
  global skiptrigs
  
  keys = line.split(" ")
  try:
    if keys[0] == "read":
      adc_mode  = int(get_key_value(keys,"a","0"),16)
      tdc_mode  = int(get_key_value(keys,"t",0))
      lookback  = int(get_key_value(keys,"l",8))
      samples   = int(get_key_value(keys,"s",16))
      triggers  = int(get_key_value(keys,"T",1))
      chan_mask = int(get_key_value(keys,"C","FFFF"),16)
      channel   = int(get_key_value(keys,"c",-1))
      clock     = int(get_key_value(keys,"m",0))
      pulser    = int(get_key_value(keys,"p",0))
      delay     = int(get_key_value(keys,"d",1))
      next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      filename = get_key_value(keys,"f",next_runname)
      if channel >= 0:
        chan_mask = (0x1 << channel)
#      if tdc_mode == 0:
#        tdc_mode = 1
#      else:
#        tdc_mode = 0

      mode = 0
      if mode == 0 or mode == 1 or mode == 3:
        print "OPENING FILE"
        fout = open(os.path.join(rundir,filename),"w")
        if filename == next_runname:
          lastrun += 1

      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',20)
      data += struct.pack('B',10)
      data += struct.pack('B',adc_mode)
      data += struct.pack('B',tdc_mode)
      data += struct.pack('H',lookback)
      data += struct.pack('H',samples)
      data += struct.pack('I',triggers)
      data += struct.pack('H',chan_mask)
      data += struct.pack('B',clock)
      data += struct.pack('B',pulser)
      data += struct.pack('H',delay)
      output_queue.put(data)


    elif keys[0] == "stop_run":
      data = ""
      data += struct.pack('B',0xaa)
      data += struct.pack('B',0xaa)
      data += struct.pack('B',4)
      data += struct.pack('B',11)
      output_queue.put(data)
      print "PROCESSED STOPPING RUN"
    elif keys[0] == "plot_digi":
      display = int(get_key_value(keys,"d",1))
      plot = int(get_key_value(keys,"p",1))
      samples = int(get_key_value(keys,"s",samples))
      skiptrigs = int(get_key_value(keys,"k",skiptrigs))
      triggers = int(get_key_value(keys,"T",min(triggers,100)))
      chanmask = int(get_key_value(keys,"c","0xFF"),16)
      cur_runname = PREFIX + "_" + str(lastrun) + ".txt"
      filename = get_key_value(keys,"f",cur_runname)
      if fout:
        fout.close()

      fout = open(os.path.join(rundir,filename))
      plotfile(fout,samples,triggers,display,plot,chanmask,skiptrigs)
      fout.close()
    elif keys[0] == "rate":
      samples = int(get_key_value(keys,"s",samples))
      triggers = int(get_key_value(keys,"T",min(triggers,100)))
      cur_runname = PREFIX + "_" + str(lastrun) + ".txt"
      filename = get_key_value(keys,"f",cur_runname)
      if fout:
        fout.close()

      fout = open(os.path.join(rundir,filename))
      measure_rate(fout,samples,triggers)
      fout.close()
    elif keys[0] == "help":
      print "Possible commands are:"
      for i in range(len(commands)):
        print "  ",commands[i]

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
      if line.startswith("readall"):
        nline = line.replace('readall', 'read')
        nruns     = int(get_key_value(line.split(),"n",1))
        for i in range(0,nruns):
          transmissiondone=0
          process_command(nline)
          while transmissiondone==0:
            time.sleep(1)
      else:
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
