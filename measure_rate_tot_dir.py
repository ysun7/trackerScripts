## Analyze DRAC digi data files in a directory

#### Test file under modification, to change the structure of the results ROOT file
#### # Modify to have a tree branch for each of 96 channels

import numpy as np
import sys
import os
import glob
import re
import string
import matplotlib.pyplot as plt
import json
import ROOT
from ROOT import TTree, TFile, AddressOf, gROOT
import time

# Pass the directory as argument
dir = sys.argv[1]
fulldir = os.path.join(os.getcwd(), dir)
print fulldir
nfiles=1000
if len(sys.argv) > 2:
  nfiles = int(sys.argv[2])
display=0
if len(sys.argv) > 3:
  display = sys.argv[3]

vocal=3


  
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



  
fileout = open("outfile.txt","w") 

deltat = []
pmp = [] #Peak minus pedestal
pedestal_v = []
pedestal_rms_v = []
charge=[]

total_time=np.zeros(96)
total_accepted_hits=np.zeros(96)
finalnum_hits   =0
overflow        =0
n_overflow      =0
n_error255      =0
n_mismatch      =0
noise_hits      =0
n_skipped_runs  =0
skipped_runs    = []
tdc=0

# Boolean that identifies which side is triggering (here used in general, not per trigger)
triggerOnCal=0
triggerOnHV=0


  
rootfileout = ROOT.TFile(dir+"/results_run.root", "recreate")
mytree = ROOT.TTree("tree", "The Tree of Life")

## The branch for each run
struct_run_string = "struct MyStruct{\
   Int_t run;\
   Int_t tdc;\
   Float_t peak;\
   Float_t dt;\
   Float_t pedestal;\
   Float_t pedrms;\
   Float_t time;\
   Double_t localtime;\
   Int_t skipped_words;\
   Int_t overflows;\
   Float_t caltemp;\
   Float_t hvtemp;\
   Float_t calp;\
   Float_t hvp;\
      };"  

## The branch for each channel
struct_channel_string = "struct MyStructChannel{\
   Float_t run_time;\
   Float_t rate;\
   Int_t hits;\
   Float_t thr;\
   Float_t vthrcal;\
   Float_t vthrhv;\
      };"  
  
# Create a ROOT struct to hold information from each json run
gROOT.ProcessLine(struct_run_string)
gROOT.ProcessLine(struct_channel_string)

from ROOT import MyStruct
from ROOT import MyStructChannel

# Create branches in the tree
s = MyStruct() ## general run info
channel_branch = [MyStructChannel() for i in range(96)]
  
mytree.Branch('run',AddressOf(s,'run'),'run/I')
mytree.Branch('peak',AddressOf(s,'peak'),'peak/F')
mytree.Branch('dt',AddressOf(s,'dt'),'dt/F')
mytree.Branch('pedestal',AddressOf(s,'pedestal'),'pedestal/F')
mytree.Branch('pedrms',AddressOf(s,'pedrms'),'pedrms/F')
mytree.Branch('time',AddressOf(s,'time'),'time/F')
mytree.Branch('localtime',AddressOf(s,'localtime'),'localtime/D')
mytree.Branch('skipped_words',AddressOf(s,'skipped_words'),'skipped_words/I')
mytree.Branch('overflows',AddressOf(s,'overflows'),'overflows/I')
mytree.Branch('caltemp',AddressOf(s,'caltemp'),'caltemp/F')
mytree.Branch('hvtemp',AddressOf(s,'hvtemp'),'hvtemp/F')
mytree.Branch('calp',AddressOf(s,'calp'),'calp/F')
mytree.Branch('hvp',AddressOf(s,'hvp'),'hvp/F')
if ("singles" in dir): # this file includes runs with all 3 values of tdc, 0/1/2 (coinc/Cal/HV triggers)
  mytree.Branch('tdc',AddressOf(s,'tdc'),'tdc/I')
  
for i_channel in range(96):
  mytree.Branch("ch%d" % i_channel, channel_branch[i_channel], "run_time/F:rate/F:hits/I:thr/F:vthrcal/F:vthrhv/F")
  #mytree.Branch( 'mycode', AddressOf( mystruct, 'fMyCode' ), 'MyCode/C' )
  

filecount = 0
# Iterate over files in the directory
for filename in os.listdir(fulldir):

  if filename.endswith(".txt") and "run" in filename and filecount<nfiles :
    file_path = os.path.join(fulldir, filename)
    f = open(file_path)
    i_run = re.findall('\d+', filename )
    print "Processing file #", filecount, "::", filename, "-- run", i_run[0]

    if ("singles" in dir): # this file includes runs with all 3 values of tdc, 0/1/2 (coinc/Cal/HV triggers)
      tdc = int(i_run[0])%3

    lines = f.read().rstrip()
    lines = lines.split('\n')
#    [lines for lines in file_lines.split('\n') if lines.strip() != '']
    #if ("json" in dir): # and (i_run[0] % n_json)==0: ## Load json fields into dac_settings and run_settings
    json_string=""
    for i_line in range(len(lines)):
      if lines[i_line]=="1000":
        print "\n\n\n\n Found start of file\n\n\n\n"
        startline = i_line
        break
      try:
        json_object = json.loads("[{}]".format(lines[0].replace('}{', '},{')))
      except ValueError, e:
        print "Error reading file"
        break
      json_string = json_string + lines[i_line]
      print json_string
    json_string = string.replace(json_string,'start_time','time')
    print json_string
      
    if json_string:
      run_settings = json.loads("[{}]".format(json_string.replace('}{', '},{')))
      if vocal>1:
        print run_settings

      if filecount==0:
        startrealtime = time.mktime(time.strptime(run_settings[1]["time"], "%Y-%m-%d %H:%M:%S"))
        print startrealtime
      realtime = time.mktime(time.strptime(json.loads("[{}]".format(json_string.replace('}{', '},{')))[1]["time"], "%Y-%m-%d %H:%M:%S"))
      realtime= realtime-startrealtime

    data2 = [int(i,16)&0xF000 for i in lines[2:]]
    data = [int(i,16)&0xFFF for i in lines[2:]]
    if vocal:
      print "Number of words in file: ", len(data)
    
    if (12+40) >= len(data): #0 or 1 triggers in this run
      if vocal:
        print "Skipping, too few triggers in run", i_run[0], " , len(data) =", len(data)
      continue
    filecount = filecount+1

  
    index = 0 #index will be set at beginning of each hit/trigger
    samples = 0

    while True:
      if data2[index] != 0x0:
        while data2[index+12+samples] == 0x0:
          samples += 1
        break
      else:
        index += 1  
    if vocal>1:
      print "Samples per trigger :",samples

    run_time=np.zeros(96) # measure run_time for each channel
    ## Store time for previous event for every channel to calculate run_time between successive triggers
    previous_gtime=np.zeros(96)
    previous_htime=np.zeros(96)
    previous_ctime=np.zeros(96)

    dt_crosstalk=0.050 # in ms
    channel=-1
    previous_channel=-1
    previous_peak=0
    time_between_hits=0
    n_crosstalk=0
    
    countfail=0
    mismatch=0
    skip_event=0 #Flag to skip event for whatever reason (buffer overflow, serial glitch)
    previous_skipped=0 #Marks whether previous event was skipped. If so don't add time.
    skipped_words=0 #Counts skipped words in the run
    overflows=0 #Counts overflows in the run
    
    triggerOnCal=0
    triggerOnHV=0

    # Count hits for each channel to get rate
    hits=np.zeros(96)
    rate=np.zeros(96)
    accepted_hits=np.zeros(96)

    while True:
        if (index+12+samples+6) >= len(data): #EOF
          break
        
        # Search that next event begins where expected
        countfail=0
        while True:
          countfail = countfail+1
          if data2[index+countfail]==0x1000: #continue until you find new trigger
            if countfail != samples+12: #ensure correct number of samples, otherwise skip
              print "Mismatched nsamples -- Mismatch index:", index, "  -- words between 0x1000's :", countfail
              skip_event=1
              n_mismatch+=1
              skipped_words+=countfail
            break
          
        # check if overflow bit is set in next trigger -- refers to the current event
        if (data[index+12+samples+6] & 0x0F00):
          if vocal>1:
            print "\n Overflow detected in next event, index #", index, "\n"
          skip_event=1
          overflow=1 # turn on a flag to avoid adding frozen time in next event
          n_overflow+=1
          overflows+=1

        # skip on mismatch/overflow
        if skip_event:
          index+=countfail # bring index to beginning of next trigger
          skip_event=0 # reset before next event
          ## A skipped event may cause errors in the run_time calculation
          for i_channel in range(8):
            previous_gtime[i_channel]=-1 # set previous_time to -1 to avoid adding to run_time in next event for all channels
          continue  


        ## Event accepted, read data
        tdata = data[index:(index+12+samples)]
        adc_channel = (tdata[3] >> 6) & 0x3F
        gtime = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
        htime = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0)) #time for HV side
        ctime = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0)) #time for Cal side
        htime = (htime & 0x3FFFFF00) + (0xFF - (htime&0xFF));
        ctime = (ctime & 0x3FFFFF00) + (0xFF - (ctime&0xFF));

        # Map the ADC channel
        if adc_channel==15: #in latest FW
          channel=0
        if adc_channel==31:
          channel=1
        elif adc_channel==47:
          channel=2
        elif adc_channel==7:
          channel=3
        elif adc_channel==23:
          channel=4
        elif adc_channel==39:
          channel=5
        elif adc_channel==14:
          channel=6
        elif adc_channel==30:
          channel=7
        elif adc_channel==25:
          channel=88
        elif adc_channel==41:
          channel=89
        elif adc_channel==0:
          channel=90
        elif adc_channel==16:
          channel=91
        elif adc_channel==32:
          channel=92
        elif adc_channel==8:
          channel=93
        elif adc_channel==24:
          channel=94
        elif adc_channel==40:
          channel=95
        
        hits[channel]+=1        

        if (gtime<previous_gtime[channel] or gtime>1000000): # probably something goes wrong in this trigger
          print "\n Index", index, "\n gtime large or <gtime_previous for channel", channel,"\n\n"
          previous_gtime[channel]=-1 # set previous_time to -1 to avoid adding to run_time in next event for this channel
          ## Count as overflow -- as does Richie in the script he sent
          n_overflow+=1
          overflows+=1
          index += 12+samples ## increment index to skip to next event
          continue   

        if (htime==255 and ctime==255): # probably something goes wrong in this trigger
          print "\n Index", index, "\n htime and ctime both stuck at 255 for channel", channel,"\n\n"
          previous_gtime[channel]=-1 # set previous_time to -1 to avoid adding to run_time in next event for this channel
          ## Count as overflow
          n_error255+=1
          index += 12+samples ## increment index to skip to next event
          continue   

        
        accepted_hits[channel] += 1

        adc = tdata[12:]
        peak = np.max(adc)
        pedestal = np.mean(adc[:5]) # this needs to be at most lookback-3, otherwise it will include signal in the pedestal calculation
        pedestal_rms = 0
        for i in range(0,5):
          pedestal_rms += (adc[i]**2 - pedestal**2)/ 5
        pedestal_rms = np.sqrt(pedestal_rms)
        sumadc = np.sum(adc)-pedestal*len(adc)


    
            
        if htime==previous_htime[channel]: ## if it happens once that's enough
          triggerOnCal=1 
        if ctime==previous_ctime[channel]: ## if it happens once that's enough
          triggerOnHV=1
        #both of these could be on, in a -t 3 run
        
        ## Add to run_time for this channel if there are no issues that caused the previous event to be skipped
        if (previous_gtime[channel]>=0):
          time_between_hits = (gtime-previous_gtime[channel])*2**28*15.625*10**-9
          time_between_hits += max(htime-previous_htime[channel], ctime-previous_ctime[channel])*15.625*10**-9 # in ms
          if time_between_hits<0:
            print "\n\nWow!! Why negative time between hits?! ", time_between_hits,"\n\n"
          run_time[channel] += time_between_hits

        
        ### cut conditions
        ## only append run_time and pmp if it's not a noise hit
        #if (peak-pedestal)>=00: # and (peak-pedestal)<=15000 and abs((htime-ctime)*15.625*10**-3)<=10 and (htime-ctime)*15.625*10**-3>=-10 and pedestal_rms<=200: 
        if pedestal_rms>2000:# or abs((htime-ctime)*15.625*10**-3)>300: 
          noise_hits += 1
        else: #only append run_time and pmp if it's not a noise hit
          pmp.append(peak-pedestal)
          if sumadc>0 and sumadc<2000:
            charge.append(sumadc)
          #    hpmp.Fill(peak-pedestal)
          #if index < 1500:
          dt=(htime-ctime)*15.625*10**-3
          deltat.append(dt)
          pedestal_v.append(pedestal)
          pedestal_rms_v.append(pedestal_rms)

          ## Output to txt file
          if json_string:
            fileout.write("%d %d %d %3.1f %5.1f %3.2f %3.1f %6.3f %7.4f %d \n" % (int(i_run[0]), realtime, channel,pedestal,peak-pedestal,dt,pedestal_rms, time_between_hits, run_time[channel], tdc))
          else:
            dummy=0
            fileout.write("%d %d %d %3.1f %5.1f %3.2f %3.1f %6.3f %7.4f %d \n" % (int(i_run[0]), dummy, channel,pedestal,peak-pedestal,dt,pedestal_rms, time_between_hits, run_time[channel], dummy))

        if vocal>2 :
          print "Index", index,", Channel", channel, ":","Global=",gtime,", HV=",htime,", Cal=",ctime,", D[HV]=",(htime-previous_htime[channel])*15.625*10**-9,"ms , D[Cal]=",(ctime-previous_ctime[channel])*15.625*10**-9,"ms , D[G]=",(gtime-previous_gtime[channel])*2**28*15.625*10**-9,"[ms], Time between hits=",time_between_hits,"[ms], Total run time so far=",run_time[channel],"[ms]"
    #      print index,":",(gtime-previous_gtime[channel])*2**28*15.625*10**-3 + (htime-previous_htime[channel])*15.625*10**-3,gtime,previous_gtime[channel],htime,previous_htime[channel]
    #      print sumadc

        
        ## See if this event may be crosstalk            
        if ((abs(ctime-previous_ctime[channel])*15.625*10**-9<dt_crosstalk
             or abs(htime-previous_htime[channel])*15.625*10**-9<dt_crosstalk)
            and (channel!=previous_channel and peak<0.2*previous_peak) ): #hit within crosstalk range
          print "\n Potential crosstalk hit\n dt[Cal] or dt[HV] less than ", dt_crosstalk, "ms\n Aggressor channel :: ", previous_channel, "   with previous_peak =", previous_peak, "\n Victim channel :: ", channel, "   with peak =", peak,"\n"
          n_crosstalk+=1


        if (display): # and peak-pedestal<0) :
          print "Channel", channel, " #",index,":","Peak=",peak,", Ped=", pedestal, "\nGlobal=",gtime,", HV=",htime,", Cal=",ctime,", D[HV]=",(htime-previous_htime[channel])*15.625*10**-9,"ms , D[Cal]=",(ctime-previous_ctime[channel])*15.625*10**-9,"ms , D[G]=",(gtime-previous_gtime[channel])*2**28*15.625*10**-9,"[ms]"
          for i_word in range(12+samples):
            print lines[index+1+i_word]
          showdata(adc)

          
        previous_gtime[channel] = gtime
        previous_htime[channel] = htime
        previous_ctime[channel] = ctime
        previous_channel = channel
        previous_peak = peak
        index += 12+samples


    ### End of this run file

    ## Check that we've had at least some accepted hits, otherwise skip
    test_hits=0
    for i_channel in range(8):
      test_hits+=accepted_hits[i_channel]
    if test_hits<5: # probably garbage file, skip
      if vocal:
        print "\n\n\n\n \t Probably garbage file, skipping run_%d.txt\n\n\n\n\n" % int(i_run[0])
        skipped_runs.append(int(i_run[0]))
        n_skipped_runs+=1
      continue
    
    ## With complete run_time calculation for every channel, get rates for each channel in this run
    for i_channel in range(96):
      if run_time[i_channel]!=0:
        channel_branch[i_channel].hits = accepted_hits[i_channel]
        channel_branch[i_channel].run_time = run_time[i_channel]
        channel_branch[i_channel].rate = accepted_hits[i_channel] / run_time[i_channel]
        print ("Channel %i:\n\tHits = %i\n\tRun time = %f\n\tRate = %f" %  (i_channel, channel_branch[i_channel].hits, channel_branch[i_channel].run_time, channel_branch[i_channel].rate))
        total_time[i_channel] += run_time[i_channel]
        total_accepted_hits[i_channel] += accepted_hits[i_channel]

    num_hits = len(data)/(12+samples)
    finalnum_hits += num_hits


    ## For every file that contains json fields, write to root file
    if json_string:
      if vocal:
        print "Reading json fields"
      s.run=int(i_run[0])
      s.peak=peak-pedestal
      s.dt=dt
      s.pedestal=pedestal
      s.pedrms=pedestal_rms
      s.time=realtime # the real time in sec since beginning of first run in dir
      s.localtime = gtime*2**28*15.625*10**-9 +  htime*15.625*10**-9 # the time associated with the last event
      s.skipped_words = skipped_words
      s.overflows = overflows
      if 'calenv' in data:
        s.caltemp=float(run_settings[1]["calenv"][0])/100.
        s.hvtemp=float(run_settings[1]["hvenv"][0])/100.
        s.calp=float(run_settings[1]["calenv"][1])/100.
        s.hvp=float(run_settings[1]["hvenv"][1])/100.

        # len(run_settings[0]["threshmv"]) is 3*N_ch, where N_ch is the number of channels read
        # Some hard wiring is needed based on the format of the thresh output
        if len(run_settings[0]["threshmv"])>20: ## default for channels 0-7, on 8-ch proto board
          for i_channel in range(8):
            channel_branch[i_channel].vthrcal=int(run_settings[0]["threshold"][3*i_channel])
            channel_branch[i_channel].vthrhv=int(run_settings[0]["threshold"][3*i_channel+1])
            channel_branch[i_channel].thr=int(run_settings[0]["threshold"][3*i_channel+2])

          s.thr1=int(run_settings[0]["threshold"][1])
          s.thr2=int(run_settings[0]["threshold"][2])
          s.thr3=int(run_settings[0]["threshold"][3])
          s.thr4=int(run_settings[0]["threshold"][4])
          s.thr5=int(run_settings[0]["threshold"][5])
          s.thr6=int(run_settings[0]["threshold"][6])
          s.thr7=int(run_settings[0]["threshold"][7])
          s.vthrcal0=float(run_settings[0]["threshmv"][1])
          s.vthrcal1=float(run_settings[0]["threshmv"][4])            
          s.vthrcal2=float(run_settings[0]["threshmv"][7])
          s.vthrcal3=float(run_settings[0]["threshmv"][10])            
          s.vthrcal4=float(run_settings[0]["threshmv"][13])
          s.vthrcal5=float(run_settings[0]["threshmv"][16])            
          s.vthrcal6=float(run_settings[0]["threshmv"][19])
          s.vthrcal7=float(run_settings[0]["threshmv"][22])            
          s.vthrhv0=float(run_settings[0]["threshmv"][0])
          s.vthrhv1=float(run_settings[0]["threshmv"][3])            
          s.vthrhv2=float(run_settings[0]["threshmv"][6])
          s.vthrhv3=float(run_settings[0]["threshmv"][9])            
          s.vthrhv4=float(run_settings[0]["threshmv"][12])
          s.vthrhv5=float(run_settings[0]["threshmv"][15])            
          s.vthrhv6=float(run_settings[0]["threshmv"][18])
          s.vthrhv7=float(run_settings[0]["threshmv"][21])            

        elif len(run_settings[0]["threshmv"])>10: ## channels 4, 5, 94, 95 on long board
          s.vthrhv4=float(run_settings[0]["threshmv"][0])
          s.vthrcal4=float(run_settings[0]["threshmv"][1])
          s.thr4=int(run_settings[0]["threshold"][2])      
          s.vthrhv5=float(run_settings[0]["threshmv"][3])
          s.vthrcal5=float(run_settings[0]["threshmv"][4])
          s.thr5=int(run_settings[0]["threshold"][5])      
          s.vthrhv6=float(run_settings[0]["threshmv"][6])
          s.vthrcal6=float(run_settings[0]["threshmv"][7])
          s.thr6=int(run_settings[0]["threshold"][8])      
          s.vthrhv7=float(run_settings[0]["threshmv"][9])
          s.vthrcal7=float(run_settings[0]["threshmv"][10])
          s.thr7=int(run_settings[0]["threshold"][11])      

        elif len(run_settings[0]["threshmv"])>3: ## channels 4 and 5 on long board
          ### This should be just modified during data taking to print out all channels. But still problematic for reading out straws 94,95
          s.vthrhv4=float(run_settings[0]["threshmv"][0])
          s.vthrcal4=float(run_settings[0]["threshmv"][1])
          s.thr4=int(run_settings[0]["threshold"][2])      
          s.vthrhv5=float(run_settings[0]["threshmv"][3])
          s.vthrcal5=float(run_settings[0]["threshmv"][4])
          s.thr5=int(run_settings[0]["threshold"][5])      

        elif len(run_settings[0]["threshmv"])>1: ## only one channel read, call it 0
          s.vthrhv0=float(run_settings[0]["threshmv"][0])
          s.vthrcal0=float(run_settings[0]["threshmv"][1])
          s.thr0=int(run_settings[0]["threshold"][2])      

      if ("singles" in dir):
        s.tdc=tdc

      mytree.Fill()
    

if triggerOnHV:
    print "Triggered on HV"
if triggerOnCal:
    print "Triggered on cal"
    
print "total skipped runs: ",n_skipped_runs
print skipped_runs
print "total hits (no mismatch assumption): ",finalnum_hits
print "total mismatched events: ",n_mismatch
print "total noise hits: ",noise_hits
print "total overflow events: ",n_overflow
print "total error255 events: ",n_error255
print "potential crosstalk hits: ",n_crosstalk,"\n"
#print "frozen time: ",frozen_time,"ms"
print "total time for each channel:"
for i_channel in range(96):
  if total_time[i_channel]!=0:
    print i_channel,total_time[i_channel],"ms"
print "total accepted hits for each channel: "
for i_channel in range(96):
  if total_time[i_channel]!=0:
    print i_channel,total_accepted_hits[i_channel]
  
print "\n Total avg hit rate for each channel: "
for i_channel in range(96):
  if total_time[i_channel]!=0:
    print i_channel,total_accepted_hits[i_channel]/total_time[i_channel], "kHz"




#hpmp.GetXaxis().SetTitle("Peak minus pedestal (counts)")
#hpmp.Draw()
#raw_input()

nbins=100


#sys.exit() ## Comment out to plot 


## Plot pmp
plt.figure()
n,bins,patches = plt.hist(pmp,nbins,normed=0,facecolor='green',alpha=0.75)
plt.title("Fe55 E distribution, 1275V")
plt.xlabel(r"Peak minus Pedestal [ADC counts]")

## Plot charge
plt.figure()
n,bins,patches = plt.hist(charge,nbins,normed=0,facecolor='green',alpha=0.75)
plt.title("Fe55 E distribution, 1275V")
plt.xlabel(r"Total charge [ADC counts]")

## Output data to file
f= open("pmp.dat","w+")
for i in range(0,len(pmp)):
  buf = "%7.4f\n" % (pmp[i])
  f.write(buf)
f.close()


## Plot pedestal
plt.figure()
n,bins,patches = plt.hist(pedestal_v,nbins,normed=0,facecolor='green',alpha=0.75)
plt.title("Pedestal distribution")
plt.xlabel("Pedestal [ADC counts]")

## Plot pedestal RMS
plt.figure()
n,bins,patches = plt.hist(pedestal_rms_v,nbins,normed=0,facecolor='green',alpha=0.75)
plt.title("Pedestal RMS distribution")
plt.xlabel("Pedestal RMS [ADC counts]")


## Plot Dt
fig, ax = plt.subplots() #plt.figure()
plt.hist(deltat,nbins,normed=0,facecolor='green',alpha=0.75)

## Grab the histogram and perform gaussian gaussian fit
hist, bin_edges = np.histogram(deltat, 2*nbins) #, density=True)
bins = (bin_edges[:-1] + bin_edges[1:])/2
const=np.max(hist)
mean=np.mean(hist)
sigma=np.sqrt(np.var(hist))
## Why are these so wrong?
# print "Dt constant=", const
# print "Dt mean=", mean
# print "Dt sigma=", sigma
mean = np.mean(deltat)
deltat_rms = np.std(deltat)
print "DeltaT mean =", mean, "(ns)"
print "DeltaT resolution (np.std) =", deltat_rms, "(ns)"

## Fit the gaussian
from scipy.optimize import curve_fit
def gaus(x,const,mean,sigma):
  return const*np.exp(-(x-mean)**2/(2*sigma**2))
#params,cov_matrix = curve_fit(gaus,bins,hist,p0=[const,mean,sigma])
#hist_fit=gaus(bins,*params)

plt.plot(bins, hist)
#plt.plot(bins, hist_fit, 'r--', linewidth=2)
plt.title("$\Delta t$ distribution, Fe55, 1325V, no shaper")
plt.xlabel(r"$\Delta t$ (ns)")
# plt.annotate("mean = %.4f ns\nsigma = %.4f ns" % (params[1],params[2]) ,
#               xy=(0.05, 0.85), xycoords='axes fraction', size=15,
#               bbox=dict(boxstyle="square,pad=0.4",facecolor='none') )

plt.show()

fileout.close()
rootfileout.Write()
rootfileout.Close()
