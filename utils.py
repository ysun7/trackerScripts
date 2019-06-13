import matplotlib.pyplot as plt
import numpy as np
import json
from strawhit import *

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

def checkramp(fout,samples,triggers):
  data = fout.read()
  errorcount = 0
  data = data.split('\n')

  current_settings = json.loads(data[0])
  run_settings = json.loads(data[1])
  data = data[2:]
  if len(data) < 4:
    print "No data found"
    return
  samples = run_settings["samples"]
  data = filter(lambda x: len(x)>0, data)
  data = [(int(data[2*i],16)<<16) | (int(data[2*i+1],16) & 0xFFFF) for i in range(len(data)/2)]
  #data = [(int(i,16) & 0xFFF) for i in data]
  for itrig in range(triggers):
    if (itrig+1)*(samples+4) > len(data):
      break
    tdata = data[itrig*(samples+4):(itrig+1)*(samples+4)]
    channel = (tdata[0] & 0x7F)
    adc = []
    for i in range(samples):
      adc.append((tdata[4+i]>>0) & 0x3FF)
      adc.append((tdata[4+i]>>10) & 0x3FF)
      adc.append((tdata[4+i]>>20) & 0x3FF)
    lastadc = adc[0]
    for i in range(1,len(adc)):
      if adc[i] != ((lastadc + 1) % 4096):
        if errorcount == 0:
          print "Error at ",(itrig*(samples+4)+i),lastadc,adc[i]
        errorcount += 1
      lastadc = adc[i]
  print errorcount,"total errors"


def plotfile(fout,samples,triggers,display,plot,chanmask):

  allts = []
  deltats = []
  data = fout.read()
  if len(data) < 4:
    print "No data found"
    return
  data = data.split('\n')
  current_settings = json.loads(data[0])
  run_settings = json.loads(data[1])
  print run_settings["message"]
  data = data[2:]
  samples = run_settings["samples"]
  data = filter(lambda x: len(x)>0, data)
  data = [(int(data[2*i],16)<<16) | (int(data[2*i+1],16) & 0xFFFF) for i in range(len(data)/2)]
  #data = [(int(i,16) & 0xFFF) for i in data]
  print len(data),"total words, expected",(samples+4)*triggers

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
      if (itrig+1)*(samples+4) > len(data):
        break
      tdata = data[itrig*(samples+4):(itrig+1)*(samples+4)]
      print itrig,"%08x %08x %08x %08x" % (tdata[0],tdata[1],tdata[2],tdata[3])
      
      ttrig = StrawHit(tdata)
      
      hvfired = 0
      calfired = 0

      if ttrig.htime > 0 and ttrig.htime != htimeold:
        hvfired = 1
      if ttrig.ctime > 0 and ttrig.ctime != ctimeold:
        calfired = 1

      T1.append(ttrig.htime)

      if hvfired:
        hval = ttrig.htime
      else:
        hval = "  X  "
      if calfired:
        cval = ttrig.ctime
      else:
        cval = "  X  "
      if hvfired and calfired:
        hvcaldeltat = (ttrig.ctime-ttrig.htime)*24.4140625*10**-3 # in ns
      else:
        hvcaldeltat = "  X  "

      if gtimeold < 0:
        gtimeold = ttrig.gtime
        htimeold = ttrig.htime
        ctimeold = ttrig.ctime
        if (ttrig.htime >= ttrig.ctime or not hvfired) and hvfired:
          latestold = ttrig.htime
        elif (ttrig.ctime >= ttrig.htime or not calfired) and calfired:
          latestold = ttrig.ctime
        mindeltat = "  X  "
      else:
        if (ttrig.htime >= ttrig.ctime or not hvfired) and calfired:
          mindeltat = ttrig.ctime - latestold
          if ttrig.gtime != gtimeold:
            mindeltat += (ttrig.gtime-gtimeold)*2**22
          mindeltat *= 24.4140625*10**-6 # in us
          latestold = ttrig.htime
        elif (ttrig.ctime >= ttrig.htime or not calfired) and hvfired:
          mindeltat = ttrig.htime - latestold
          if ttrig.gtime != gtimeold:
            mindeltat += (ttrig.gtime-gtimeold)*2**22
          mindeltat *= 24.4140625*10**-6 # in us
          latestold = ttrig.ctime
        else:
          mindeltat = "  X  "

      if display:
        print "Channel",ttrig.channel,"- time since last:",mindeltat,"deltat:",hvcaldeltat,"gtime:",ttrig.gtime,"htime:",hval,"ctime:",cval,"error:",ttrig.fifo_error
        dcvoltage = (-1000. + ttrig.getAverageSample()*2000./1024.)/10. 
        print "mean ped=",ttrig.getAverageSample()," rms=",ttrig.getSamplesRMS(), " voltage=",dcvoltage
      if plot:
        showdata(ttrig.adc)
        ttrig.adc1 = []
      gtimeold = ttrig.gtime
      htimeold = ttrig.htime
      ctimeold = ttrig.ctime

def get_key_value(keys, flag, default = "0"):
  index = 1
  while True:
    if index >= len(keys) - 1:
      return default
    if keys[index] == ("-" + flag):
      return keys[index+1]
    index += 1

def get_message_value(keys, flag):
  index = 1
  while True:
    if index >= len(keys) - 1:
      return ""
    if keys[index] == ("-" + flag):
      return " ".join(keys[index+1:]).split('"')[1]
    index += 1

def plotcalibhisto(y):
    ldata=[int(i,16) for i in filter(lambda y: len(y)>0, y) ]
#    ldata=range(0,len(y))
    data  =np.array(ldata)
    print ldata
    fig = plt.figure()
    fig1 =plt.figure()

    alist=['ssd','sdsd']
    
    
    ax1 = fig.add_subplot(211)
    ax1.set_title("Data")
    ax1.set_xlabel('bin')
    ax1.set_ylabel('Differential')

    ax2 = fig.add_subplot(212)
    ax2.set_title("Data")
    ax2.set_xlabel('bin')
    ax2.set_ylabel('Integral')

    ax3 = fig1.add_subplot(211)
    ax3.set_title("Data")
    ax3.set_xlabel('bin')
    ax3.set_ylabel('Differential')

    ax4 = fig1.add_subplot(212)
    ax4.set_title("Data")
    ax4.set_xlabel('bin')
    ax4.set_ylabel('Integral')


    x=range(0,len(data)-1)
    datadata = np.diff(data)
    zdata = datadata[datadata != 0]
    z = np.cumsum(zdata)
    print datadata
    ax1.bar(x,datadata,width=1)
    ax1.get_yaxis().get_major_formatter().set_useOffset(False)

    x=range(0,len(z))
    print z
    ax4.plot(x,z)
    ax4.get_yaxis().get_major_formatter().set_useOffset(False)

    print zdata
    ax3.bar(x,zdata,width=1)
    ax3.get_yaxis().get_major_formatter().set_useOffset(False)

    x=range(0,len(data))
    ax2.plot(x,ldata)
    ax2.get_yaxis().get_major_formatter().set_useOffset(False)
#    ax1.plot(x,data2)
#    leg = ax1.legend()
    plt.show()

def channelmask(channel):
      chan_mask1 = -999
      chan_mask2 = -999
      chan_mask3 = -999
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
      return chan_mask1, chan_mask2, chan_mask3
