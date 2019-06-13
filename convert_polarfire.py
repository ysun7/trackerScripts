import sys
import json
import numpy as np
import ROOT
from array import array
import matplotlib.pyplot as plt
import os

def read_chunk(file,chunk_size=5000):
  while True:
    data = file.read(chunk_size)
    if not data:
      break
    yield data



channel_map = np.linspace(0,47,48)

inputfn = sys.argv[1]
outputfn = sys.argv[2]

fout = ROOT.TFile(outputfn, 'RECREATE' )
tree = ROOT.TTree( 'T', 'Tree' )
channel = array('i',[0])
timeGlobal = array('L',[1])
timeHV = array('L',[1])
timeCal = array('L',[1])
timePrevCal = array('L',[1])
deltaT = array('d',[1])
totHV = array('H',[1])
totCal = array('H',[1])
pedestal = array('f',[1])
ssum = array('f',[1])
peakl = array('f',[1])
pedestalrms = array('f',[1])
peak = array('f',[1])
minimum = array('f',[1])
samples = array('H',50*[0])

tree.Branch("channel",channel,"channel/I")
tree.Branch("timeGlobal",timeGlobal,"timeGlobal/i")
tree.Branch("timeHV",timeHV,"timeHV/i")
tree.Branch("timeCal",timeCal,"timeCal/i")
tree.Branch("timePrevCal",timePrevCal,"timePrevCal/i")
tree.Branch("deltaT",deltaT,"deltaT/D")
tree.Branch("totHV",totHV,"totHV/s")
tree.Branch("totCal",totCal,"totCal/s")
tree.Branch("pedestal",pedestal,"pedestal/F")
tree.Branch("ssum",ssum,"ssum/F")
tree.Branch("pedestalrms",pedestalrms,"pedestalrms/F")
tree.Branch("peak",peak,"peak/F")
tree.Branch("peakl",peakl,"peakl/F")
tree.Branch("minimum",minimum,"minimum/F")
tree.Branch("samples",samples,"samples[50]/s")


fin = open(inputfn)

filesize = os.path.getsize(inputfn)
num_chunks = 0
line = fin.readline()
current_settings = json.loads(line)
line = fin.readline()
run_settings = json.loads(line)
numsamples = run_settings["samples"]
print numsamples
lookback = run_settings["lookback"]
num_words = 12 + numsamples

total_hits = np.zeros(21)

temp_events = []
starting_gtime = -1


done = False
last_data = ''
for chunk in read_chunk(fin):
  if done:
    break
  if num_chunks % 1000 == 0:
    print num_chunks * 5000,"/",filesize
  num_chunks += 1
  data = last_data + chunk
  last_data = ''
  data = data.split('\n')
  if (len(data)-1) % num_words != 0:
    for j in range((len(data)-1) % num_words):
      last_data += data[-((len(data)-1) % num_words) + j - 1] + '\n'
  last_data += data[-1]
  data = data[:-((len(data)-1) % num_words)-1]
  data = map(lambda x: int(x,16),data)


  timeCal[0] = 0;
  
  itrig = 0
  while True:
    this_start = itrig*(numsamples+12)
    next_start = (itrig+1)*(numsamples+12)
    if next_start >= len(data):
      break
    if data[this_start] & 0x1000 != 0x1000:
      print "MISSING WORD START:",this_start
      raw_input()
      continue

    tdata = map(lambda x: x & 0xFFF,data[this_start:next_start])
    adc_channel = (tdata[3] >> 6) & 0x3F
    if adc_channel > len(channel_map)-1:
      print "BAD CHANNEL:",adc_channel,this_start
      itrig += 1
      continue
    channel = channel_map[adc_channel]
    if channel == -1:
      print "BAD CHANNEL:",adc_channel,this_start
      itrig += 1
      continue
    timeGlobal[0] = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
    htime = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0))
    ctime = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0))
    timeHV[0] = (htime & 0x3FFFFF00) + (0xFF - (htime&0xFF));
    timeCal[0] = (ctime & 0x3FFFFF00) + (0xFF - (ctime&0xFF));
    totHV[0] = (tdata[9]>>4)&0xF
    totCal[0] = (tdata[9])&0xF
    hvfired = (tdata[3]>>4)&0x1
    calfired = (tdata[6]>>4)&0x1

    wasfull = (tdata[6]>>11)&0x1
    adc = tdata[12:12+numsamples]
    adc1 = []
    for a in adc:
      adc1.append(int('{:010b}'.format(a)[::-1], 2) )
    for isample in range(min(100,numsamples)):
      samples[isample] = adc1[isample]
    peak[0] = np.max(adc1)


    deltaT[0] = timeHV[0] - timeCal[0]
    pedestal[0] = np.mean(adc1[:6])


    # if np.argmax(adc1) < 99 and np.argmax(adc1)>1:
    #   peakl[0] = adc1[np.argmax(adc1)-1]+adc1[np.argmax(adc1)+1]+peak[0]-3*pedestal[0]
    # else:
    #   peakl[0] = 0
    
    pedestalrms[0] = np.std(adc1[:6])
    ssum[0] = sum(i-pedestal[0] for i in adc1)
    
    
    minimum[0] = np.min(adc1)

    tree.Fill()

    timePrevCal[0] = timeCal[0]
    
    itrig += 1
tree.Write()
fout.Close()
