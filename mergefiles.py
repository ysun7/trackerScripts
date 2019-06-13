import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import json
import ROOT
from ROOT import TTree, TFile, AddressOf, gROOT
import time

chmap = {12:1, 5:2,14:3,8:4,7:5,10:6,1:7}



def showdata(y):
    SampleRate = 20
    nplot = 200

    fig = plt.figure()

    ax1 = fig.add_subplot(111)

    ax1.set_title("Data")
    ax1.set_xlabel('ns')
    ax1.set_ylabel('ADC counts')


    x=range(0,SampleRate*len(y),SampleRate)
    ax1.plot(x,y)
    ax1.get_yaxis().get_major_formatter().set_useOffset(False)
    plt.show()
    plt.close(fig)


# Pass the directory as argument
dir = sys.argv[1]
fulldir = os.path.join(os.getcwd(), dir)
print fulldir
nfiles = len(os.listdir(fulldir))
if len(sys.argv)>2:
    nfiles = int(sys.argv[2])

printfile = 1
plot = 0
skiptrigs=9466
totrigs = 9473



if printfile:
    fileout = open("outfile.txt","w") 


    rootfileout = ROOT.TFile("outfile.root", "recreate")
    mytree = ROOT.TTree("mytree", "The Tree of Life")

# Create a struct
    gROOT.ProcessLine(\
      "struct MyStruct{\
        Int_t channel;\
        Float_t peak;\
        Float_t pedestal;\
        Float_t pedrms;\
        Float_t deltat;\
        Float_t time;\
        Float_t caltemp;\
        Float_t hvtemp;\
        Float_t thr0;\
        Float_t thr1;\
        Float_t thr2;\
        Float_t thr3;\
        Float_t thr4;\
        Float_t thr5;\
        Float_t thr6;\
        Float_t thr7;\
        Float_t vthrcal0;\
        Float_t vthrcal1;\
        Float_t vthrcal2;\
        Float_t vthrcal3;\
        Float_t vthrcal4;\
        Float_t vthrcal5;\
        Float_t vthrcal6;\
        Float_t vthrcal7;\
        Float_t vthrhv0;\
        Float_t vthrhv1;\
        Float_t vthrhv2;\
        Float_t vthrhv3;\
        Float_t vthrhv4;\
        Float_t vthrhv5;\
        Float_t vthrhv6;\
        Float_t vthrhv7;\
      };")

    from ROOT import MyStruct

    # Create branches in the tree
    s = MyStruct()
    mytree.Branch('rootInt',AddressOf(s,'channel'),'channel/I')
    mytree.Branch('rootFloat',AddressOf(s,'peak'),'peak/F')
    mytree.Branch('rootFloat',AddressOf(s,'pedestal'),'pedestal/F')
    mytree.Branch('rootFloat',AddressOf(s,'pedrms'),'pedrms/F')
    mytree.Branch('rootFloat',AddressOf(s,'deltat'),'deltat/F')
    mytree.Branch('rootFloat',AddressOf(s,'time'),'time/F')
    mytree.Branch('rootFloat',AddressOf(s,'caltemp'),'caltemp/F')
    mytree.Branch('rootFloat',AddressOf(s,'hvtemp'),'hvtemp/F')
    mytree.Branch('rootInt',AddressOf(s,'thr0'),'thr0/I')
    mytree.Branch('rootInt',AddressOf(s,'thr1'),'thr1/I')
    mytree.Branch('rootInt',AddressOf(s,'thr2'),'thr2/I')
    mytree.Branch('rootInt',AddressOf(s,'thr3'),'thr3/I')
    mytree.Branch('rootInt',AddressOf(s,'thr4'),'thr4/I')
    mytree.Branch('rootInt',AddressOf(s,'thr5'),'thr5/I')
    mytree.Branch('rootInt',AddressOf(s,'thr6'),'thr6/I')
    mytree.Branch('rootInt',AddressOf(s,'thr7'),'thr7/I')
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal0'),'vthrcal0/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal1'),'vthrcal1/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal2'),'vthrcal2/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal3'),'vthrcal3/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal4'),'vthrcal4/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal5'),'vthrcal5/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal6'),'vthrcal6/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrcal7'),'vthrcal7/F')    

    mytree.Branch('rootFloat',AddressOf(s,'vthrhv0'),'vthrhv0/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv1'),'vthrhv1/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv2'),'vthrhv2/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv3'),'vthrhv3/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv4'),'vthrhv4/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv5'),'vthrhv5/F')    
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv6'),'vthrhv6/F')
    mytree.Branch('rootFloat',AddressOf(s,'vthrhv7'),'vthrhv7/F')    





    
deltats = []
pmp = [] #Peak minus pedestal
pedestal_v = []
pedestal_rms_v = []
charge=[]

finaldeltat     =0
finalnum_hits   =0
finalhits       =0
finalnoisehits  =0



countgood=0

filecount = 0
# Iterate over files in the directory
for filename in os.listdir(fulldir):

  if filename.endswith(".txt") and filecount<nfiles and not(filename.startswith("threshdata")):
    file_path = os.path.join(fulldir, filename)
    f = open(file_path)
    print "Processing file ", filename

    data = f.read().rstrip()
    data = data.split('\n')
    run_settings = json.loads("[{}]".format(data[0].replace('}{', '},{')))

    if filecount==0:
      startrealtime = time.mktime(time.strptime(run_settings[1]["time"], "%Y-%m-%d %H:%M:%S"))



    realtime = time.mktime(time.strptime(run_settings[1]["time"], "%Y-%m-%d %H:%M:%S"))

    realtime= realtime-startrealtime

    data2 = [int(i,16)&0xF000 for i in data[1:]]
    data = [int(i,16)&0xFFF for i in data[1:]]
    filecount = filecount+1

      
    offset=0 ## first set offset (should just be zero) to extract #samples
    samples = 0
    while True:
      if data2[offset] != 0x0:
        while data2[offset+12+samples] == 0x0:
          samples += 1
        break

    skip=0 ## number of triggers at beginning of file to be skipped  
#    print "Offset=",offset,", Samples=",samples,", Skip=",skip
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
        channel = (tdata[3] >> 6) & 0x3F
        gtime = ((tdata[0]<<24) + (tdata[1]<<12) + (tdata[2]<<0))
        htime = (((tdata[3]&0xF)<<24) + (tdata[4]<<12) + (tdata[5]<<0)) #time for HV side
        ctime = (((tdata[6]&0xF)<<24) + (tdata[7]<<12) + (tdata[8]<<0)) #time for Cal side
        htime = (htime & 0x3FFFFF00) + (0xFF - (htime&0xFF));
        ctime = (ctime & 0x3FFFFF00) + (0xFF - (ctime&0xFF));

        # if start_counting==0: ## see if gtime==0 before start counting
        #   if int(gtime)==0: 
        #     print "we're in here"
        #     start_counting=1
        #   else:
        #     continue

        adc = tdata[12:]
        peak = np.max(adc)
        pedestal = np.mean(adc[-5:]) # this needs to be at most lookback-3, otherwise it will include signal in the pedestal calculation
        pedestal_rms = 0
        for i in range(0,5):
          pedestal_rms += (adc[i]**2 - pedestal**2)/ 5
        pedestal_rms = np.sqrt(pedestal_rms)
        sumadc = np.sum(adc)-pedestal*len(adc)

        dt = -9999.
#        if (peak-pedestal)>=00 and (peak-pedestal)<=15000 and abs((htime-ctime)*15.625*10**-3)<=10 and (htime-ctime)*15.625*10**-3>=-10 and pedestal_rms<=200: #only append deltat and pmp if it's not a noise hit
#        if pedestal_rms<=200: #only append deltat and pmp if it's not a noise hit
        if True:
          pmp.append(peak-pedestal)
          if sumadc>0 and sumadc<1500:
            charge.append(sumadc)
          #    hpmp.Fill(peak-pedestal)
          #if index < 1500:
          countgood+=1
          deltats.append((htime-ctime)*15.625*10**-3)
          pedestal_v.append(pedestal)
          pedestal_rms_v.append(pedestal_rms)
          dt=(htime-ctime)*15.625*10**-3

          if printfile:
            fileout.write("%d %3.1f %5.1f %3.2f %3.1f %12.9f \n" % (chmap[channel],pedestal,peak-pedestal,dt,pedestal_rms,(filecount-1)*100+realtime))
            s.channel=chmap[channel]
            s.peak=peak-pedestal
            s.pedestal=pedestal
            s.pedrms=pedestal_rms
            s.deltat=dt
            s.time=realtime
            s.caltemp=float(run_settings[1]["calenv"][0])/100.
            s.hvtemp=float(run_settings[1]["hvenv"][0])/100.
            s.thr0=int(run_settings[0]["threshold"][0])
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
            

            mytree.Fill()
            
        else:
          noise_hits += 1

#        if gtime_last > -1:
#          print index,":","Global=",gtime,", HV=",htime,", Cal=",ctime,", D[HV]=",(htime-htime_last)*15.625*10**-9,"ms , D[Cal]=",(ctime-ctime_last)*15.625*10**-9,"ms , D[G]=",(gtime-gtime_last)*2**28*15.625*10**-9,"[ms]", " Deltat=",dt," Channel=",channel," Pedestal=",pedestal, " Hits=",finalnum_hits+hits
    #      print index,":",(gtime-gtime_last)*2**28*15.625*10**-3 + (htime-htime_last)*15.625*10**-3,gtime,gtime_last,htime,htime_last
    #      print sumadc

        if plot and dt<10 and dt>-10 and chmap[channel]==6:
            print index,":","Global=",gtime,", HV=",htime,", Cal=",ctime,", D[HV]=",(htime-htime_last)*15.625*10**-9,"ms , D[Cal]=",(ctime-ctime_last)*15.625*10**-9,"ms , D[G]=",(gtime-gtime_last)*2**28*15.625*10**-9,"[ms]", " Deltat=",dt," Channel=",channel," Pedestal=",pedestal, " Hits=",finalnum_hits+hits
            print index,":",(gtime-gtime_last)*2**28*15.625*10**-3 + (htime-htime_last)*15.625*10**-3,gtime,gtime_last,htime,htime_last
            showdata(adc)
            adc = []

          
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


    finaldeltat += deltat
    finalnum_hits += num_hits
    finalhits+=hits
    finalnoisehits+=noise_hits
  

if triggerOnHV:
    print "Triggered on HV"
else:
    print "Trigger on cal"
    
print "total time: ",finaldeltat,"ms"
print "total hits: ",finalnum_hits,finalhits
print "noise hits: ",finalnoisehits
print "\n Rate: ", finalnum_hits/finaldeltat,"kHz\n"

#hpmp.GetXaxis().SetTitle("Peak minus pedestal (counts)")
#hpmp.Draw()
#raw_input()

nbins=100


#sys.exit() ## Comment out to plot 



if printfile:
    fileout.close()
    rootfileout.Write()
    rootfileout.Close()
