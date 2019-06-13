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




def plotfile(filename,samples,triggers,display,plot):
  global dcvoltages
  
  fout = open(os.path.join(rundir,filename),"r")
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
#        print "Channel",channel,"- time since last:",mindeltat,"deltat:",hvcaldeltat,"gtime:",gtime,"htime:",hval,"ctime:",cval
        dcvoltage = (-750. + np.mean(adc1)*1500./4096.)/10
        print "mean ped=",np.mean(adc1)," rms=",np.std(adc1), " voltage=",dcvoltage
        dcvoltages.append(dcvoltage)
      if plot:
        showdata(adc1)
        adc1 = []

      gtimeold = gtime
      htimeold = htime
      ctimeold = ctime


def serialread(ser):
  global fout
  global mode
  global gainsettings
  global threshsettings
  global calenvdata
  global hvenvdata
  
  outputmode = 0
  
  while True:
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
            else:
              if len(outline) > 0:
                print " ",outline
                if outline.find("gain/threshold")>0:
                  gainsettings[int(outline.split()[1])] = int(outline.split()[5])
                  threshsettings[int(outline.split()[1])] = int(outline.split()[6])

                if outline.startswith("CAL")>0:
                  calenvdata = outline.split()[-3:]
                if outline.startswith("HV")>0:
                  hvenvdata = outline.split()[-3:]
                if outline.startswith("FAILED") or outline.startswith("SUCCESS") or outline.startswith("Channel 15") or outline.startswith("HV"):
                  return 0
          # data taking mode
          elif outputmode == 1:
            if outline.startswith("end"):
              outputmode = 0
              if fout:
                fout.close()
                print "File closed"
                fout = 0
            else:
              if fout:
  #		    print "RECIEVED",len(outline)
                fout.write(outline.replace(" ","\n"))


    except serial.serialutil.SerialException:
      ser.close()
      print "ARM disconnected"
      print ""
      ser = None




        

def get_key_value(keys, flag, default = "0"):
  index = 1
  while True:
    if index >= len(keys) - 1:
      return default
    if keys[index] == ("-" + flag):
      return keys[index+1]
    index += 1

def readstrawcmdthresh(strawnumber,samples,clock):
  
  chan_mask = (0x1 << strawnumber)

  if strawnumber == 0:
    chan_mask = 0xFFFF

  adc_mode = 0
  tdc_mode = 1
  lookback = 2

  triggers=1
  pulser=1
  delay=1
  
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

  return data


def readstrawcmd(tdc_mode):
  
#  chan_mask = 0xD6
  channel = 5
  chan_mask = (0x1 << channel)
  
  adc_mode = 0
#  tdc_mode = 0
  lookback = 12
  samples = 16
  clock = 1

  
  triggers=400
  pulser=0
  delay=100
  
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

  return data



def thresholdset(channel,dvalue):

  chan_mask=0
  chan_mask |= (0x1 << channel)
  data = ""
  data += struct.pack('B',0xaa)
  data += struct.pack('B',0xaa)
  data += struct.pack('B',0x8)
  data += struct.pack('B',0x1)
  data += struct.pack('H',chan_mask)
  data += struct.pack('H',dvalue)
  return data


def gainset(channel,dvalue):

  chan_mask=0
  chan_mask |= (0x1 << channel)
  data = ""
  data += struct.pack('B',0xaa)
  data += struct.pack('B',0xaa)
  data += struct.pack('B',0x8)
  data += struct.pack('B',0x0)
  data += struct.pack('H',chan_mask)
  data += struct.pack('H',dvalue)
  return data


def dump_settings():
        
    command_id = 7
    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',command_id)

    return data


def readSPI():
    data= ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',10)
    return data

def readSensors():
    data= ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',11)
    return data




def main():
    global dcvoltages
    global fout
    global mode
    global gainsettings
    global threshsettings
    global calenvdata
    global hvenvdata
    global rundir

    serial_ports = [
        p[0]
        for p in serial.tools.list_ports.comports()
        if 'ttyUSB' in p[0]
    ]

    print serial_ports


    SERIALPORTROC = serial_ports[3]
    SERIALPORTHV = serial_ports[2]
    SERIALPORTCAL = serial_ports[1]

    print SERIALPORTROC

    SERIALRATE = 921600
    TIMEOUT = 1

    PREFIX = "run"

    fout = 0
    mode = 0
    samples = 0
    triggers = 0

    topdir = os.path.dirname(os.path.realpath(__file__))

    # if len(sys.argv) > 1:
    #     rundir = sys.argv[1]
    # else:
    rundir = os.path.join(topdir,'data/noise_180320_json_singles') #noise_coolant_100HzRates')
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

    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    sercal = serial.Serial(SERIALPORTCAL,SERIALRATE, timeout = TIMEOUT)
    serhv = serial.Serial(SERIALPORTHV,SERIALRATE, timeout = TIMEOUT)
    print "ARMs connected"


    samples=2000
    # keyboard input loop
    try:

      dcvoltages=[]
      gainsettings=[]
      threshsettings=[]
      calenvdata=[]
      hvenvdata=[]
      for i in range (16):
        gainsettings.append(0)
        threshsettings.append(0)


      if (lastrun+1) % 1 == 0:  ## Define how often thresholds and temps will be read
        cmd = dump_settings()
        serroc.write(cmd)
        serialread(serroc)
        cmd = readSPI()
        serroc.write(cmd)
        serroc.readline()
        serroc.readline()



        print gainsettings
        print threshsettings

        strawmask = 0xFF

        for strawnumber in range(8):

          if (1<<strawnumber & strawmask)==0:
            continue

          for iside in range(3):

            if iside == 0: #zero the cal side
              cmd=gainset(strawnumber,0)
              serroc.write(cmd)
              print serroc.readline()
              cmd=gainset(strawnumber+8,gainsettings[strawnumber+8])    
              serroc.write(cmd)
              print serroc.readline()
            elif iside == 1: #zero the hv side
              cmd=gainset(strawnumber,gainsettings[strawnumber])
              serroc.write(cmd)
              print serroc.readline()
              cmd=gainset(strawnumber+8,0)    
              serroc.write(cmd)
              print serroc.readline()
            elif iside == 2: #set both to default
              cmd=gainset(strawnumber,gainsettings[strawnumber])
              serroc.write(cmd)
              print serroc.readline()
              cmd=gainset(strawnumber+8,gainsettings[strawnumber+8])    
              serroc.write(cmd)
              print serroc.readline()

            filename = 'threshdata.txt'

            mode=1
#            if strawnumber==2 or strawnumber==4:
#              mode = 0

            cmd = readstrawcmdthresh(strawnumber,samples,mode)
            if strawnumber==0:
              sercal.write(cmd)
            else:
              serhv.write(cmd)


            fout = open(os.path.join(rundir,filename),"w")

            if strawnumber==0:
              serialread(sercal)
            else:
              serialread(serhv)        

            plotfile(filename,samples,1,1,0)


        print "==========================="


        for istraw in range(8):

            if strawmask == 0xFF:
                print '%d %d %d %d %4.2f %4.2f %4.2f' % (gainsettings[istraw+8],threshsettings[istraw+8],gainsettings[istraw],threshsettings[istraw],dcvoltages[3*istraw],dcvoltages[3*istraw+1],dcvoltages[3*istraw+2])
            else:
              if ( (1<<istraw) & strawmask): 
                print '%d %d %d %d %4.2f %4.2f %4.2f' % (gainsettings[istraw+8],threshsettings[istraw+8],gainsettings[istraw],threshsettings[istraw],dcvoltages[0],dcvoltages[1],dcvoltages[2])




        cmd = readSensors()
        serroc.write(cmd)
        serialread(serroc)

      print calenvdata
      print hvenvdata
      timestamp=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      run_settings={'gain':gainsettings, 'threshold':threshsettings, 'threshmv':dcvoltages}
      env_data = {'time':timestamp,'calenv':calenvdata, 'hvenv':hvenvdata}


      if (lastrun+1)%3==0:
          tdc_mode=0 #coincidence
      elif  (lastrun+1)%3==1:
          tdc_mode=1 #Cal
      elif  (lastrun+1)%3==2:
          tdc_mode=2 #HV
      cmd = readstrawcmd(tdc_mode)
      serhv.write(cmd)

      print "OPENING FILE"
      next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
      filename = next_runname

      fout = open(os.path.join(rundir,filename),"w")
      if filename == next_runname:
                lastrun += 1


      json.dump(run_settings, fout)
      json.dump(env_data,fout)
      fout.write("\n")
      serialread(serhv)

      serroc.close()
      serhv.close()
      sercal.close()

      print 'all done'


    except Exception, e:
      print type(e),e
    finally:
      print 'Ending...'


if __name__ == "__main__":
    main()
