import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sys
import json

file = open(sys.argv[1])

# Each "event" will hold the following variables:
# time i33 i25 i18 i12 hvtemp0 hvtemp1 caltemp0 caltemp1 rateXhv rateXcal rateX hitsXhv hitsXcal hitsX duration
# where the channel X is within [0,7]u[88,95]

time = []
i33 = []
i25 = []
i18 = []
i12 = []

caltempsensor = []
hvtempsensor = []
calpsensor = []
hvpsensor = []
time_sensor = [] ## separate time for the temp sensor, which is measured less often
time_thr = [] ## separate time for measure_threshold

hvtemp0 = []
hvtemp1 = []
caltemp0 = []
caltemp1 = []
gainhv = [[] for i in range(96)]
gaincal = [[] for i in range(96)]
thrhv = [[] for i in range(96)]
thrcal = [[] for i in range(96)]
vthrhv = [[] for i in range(96)]
vthrcal = [[] for i in range(96)]
vthr = [[] for i in range(96)]

ratehv = [[] for i in range(96)]
ratecal = [[] for i in range(96)]
rate = [[] for i in range(96)]
hitshv = [[] for i in range(96)]
hitscal = [[] for i in range(96)]
hits = [[] for i in range(96)]
duration = [[] for i in range(96)]

measure_thresh = 0
have_time_thr = 0
event = -1

for line in file:
    if len(line.split())<2:
        continue

    ### Comment out the method below. Easier to read settings from the output of measure_thresholds, and keep the settings aligned with the thresholds.
    ## Read gain/thresh settings
#    if line[:11] == 'Settings HV':
#        hvsettings = json.loads( line[13:].replace('{', '{"').replace(':','":').replace('], ','], "') )
#        for ichannel in range(96):
#            try:
#                gainhv[ichannel].append(hvsettings["%d" % ichannel][0])
#                thrhv[ichannel].append(hvsettings["%d" % ichannel][1])
#            except KeyError,e:
#                pass
#        continue
#    if line[:12] == 'Settings CAL':
#        calsettings = json.loads( line[14:].replace('{', '{"').replace(':','":').replace('], ','], "') )
#        for ichannel in range(96):
#            try:
#                gaincal[ichannel].append(calsettings["%d" % ichannel][0])
#                thrcal[ichannel].append(calsettings["%d" % ichannel][1])
#            except KeyError,e:
#                pass
#        continue


    ## Read rates
    if line.split()[0] == 'Rates':
        # New rate measurement
        if event%1000==0:
            print "Processing event", event
        event += 1

        time.append(float(line.split()[1]))
        rates = json.loads( line[line.find('{'):].replace('{', '{"').replace(':','":').replace('], ','], "') )
        for ichannel in range(96):
            try:
                ratecal[ichannel].append(rates["%d" % ichannel][0])
                ratehv[ichannel].append(rates["%d" % ichannel][1])
                rate[ichannel].append(rates["%d" % ichannel][2])
            except KeyError,e:
                pass
        continue

    ## Read sensor
    if line.split()[0] == 'CAL':
        if len(time)==0:
            continue
        time_sensor.append(time[-1])
        caltempsensor.append(float(line.split()[1])/100.)
        calpsensor.append(float(line.split()[2]))
    if line.split()[0] == 'HV':
        if len(time)==0:
            continue
        hvtempsensor.append(float(line.split()[1])/100.)
        hvpsensor.append(float(line.split()[2]))


    ## Read gain/thr settings and vthr
    if line.split()[0]=='Time=':
        try:
            time_thr.append(float(line.split()[1]))
            measure_thresh=1            
            continue
        except ValueError,e:
            continue        
    
    if measure_thresh and not line.split()[0].isdigit():
        # end of measure_thresh printout
        if measure_thresh<97: #Unexpected termination of rates measurement
            #remove the last entry
            time_thr.pop()
            for i_channel in [0,1,2,3,4,5,6,7,88,89,90,91,92,93,94,95]:
                while len(gainhv[i_channel])>len(time_thr):
                    gainhv[i_channel].pop()
                while len(thrhv[i_channel])>len(time_thr):
                    thrhv[i_channel].pop()
                while len(gaincal[i_channel])>len(time_thr):
                    gaincal[i_channel].pop()
                while len(thrcal[i_channel])>len(time_thr):
                    thrcal[i_channel].pop()
                while len(vthrhv[i_channel])>len(time_thr):
                    vthrhv[i_channel].pop()
                while len(vthrcal[i_channel])>len(time_thr):
                    vthrcal[i_channel].pop()
                while len(vthr[i_channel])>len(time_thr):
                    vthr[i_channel].pop()
        measure_thresh=0
        continue

    if measure_thresh:
        try:
            gainhv[measure_thresh-1].append(float(line.split()[0]))
            thrhv[measure_thresh-1].append(float(line.split()[1]))
            gaincal[measure_thresh-1].append(float(line.split()[2]))
            thrcal[measure_thresh-1].append(float(line.split()[3]))
            vthrhv[measure_thresh-1].append(float(line.split()[4]))
            vthrcal[measure_thresh-1].append(float(line.split()[5]))
            vthr[measure_thresh-1].append(float(line.split()[6]))
            measure_thresh += 1
            if measure_thresh==9:
                measure_thresh=89
            continue
        except ValueError,e:
            continue
        
        

#        time.append(float(line.split()[0]))
#        i33.append(float(line.split()[1][line.split()[1].index('=')+1:]))
#        i25.append(float(line.split()[2][line.split()[2].index('=')+1:]))
#        i18.append(float(line.split()[3][line.split()[3].index('=')+1:]))
#        i12.append(float(line.split()[4][line.split()[4].index('=')+1:]))

#    if "Temp" in line.split()[1]:
#        hvtemp0.append(float(line.split()[1][line.split()[1].index('=')+1:]))
#        hvtemp1.append(float(line.split()[2][line.split()[2].index('=')+1:]))
#        caltemp0.append(float(line.split()[3][line.split()[3].index('=')+1:]))
#        caltemp1.append(float(line.split()[4][line.split()[4].index('=')+1:]))

#    if line.split()[1][-1] is ':':
#        channel = int(line.split()[1][:-1])
#        ratehv[channel].append(int(line.split()[3]))
#        ratecal[channel].append(int(line.split()[6]))
#        rate[channel].append(int(line.split()[9]))
#        hitshv[channel].append(int(line.split()[11]))
#        hitscal[channel].append(int(line.split()[12]))
#        hits[channel].append(int(line.split()[13]))
#        duration[channel].append(int(line.split()[14]))

time0 = time[0]
time0_sensor = time_sensor[0]
time0_thr = time_thr[0]
time = np.array(time)
time_sensor = np.array(time_sensor)
time_thr = np.array(time_thr)


# Output data to text file
fileout = open("outrates.dat","w")
for i in range(len(ratehv[0])):
    ratestr=""
    for i_channel in [0,1,2,3,4,5,6,7,88,89,90,91,92,93,94,95]:
        ratestr = ratestr + '%f %f %f ' % (ratecal[i_channel][i], ratehv[i_channel][i], rate[i_channel][i])
    fileout.write("%f %s \n" % (time[i]-time0, ratestr))
fileout.close()

fileout = open("outthresh.dat","w")
for i in range(len(vthrcal[0])):
    thrstr=""
    for i_channel in [0,1,2,3,4,5,6,7,88,89,90,91,92,93,94,95]:
        thrstr = thrstr + '%f %f %f ' % (vthrcal[i_channel][i], vthrhv[i_channel][i], vthr[i_channel][i])
    fileout.write("%f %s \n" % (time_thr[i]-time0_thr, thrstr))
fileout.close()


for i_channel in [0,1,2,3,4,5,6,7,88,89,90,91,92,93,94,95]:
    ratehv_v = np.array(ratehv[i_channel])
    ratecal_v = np.array(ratecal[i_channel])
    rate_v = np.array(rate[i_channel])
    vthrhv_v = np.array(vthrhv[i_channel])
    vthrcal_v = np.array(vthrcal[i_channel])
    vthr_v = np.array(vthr[i_channel])

    plt.figure(1)
    plt.subplot(211)
    plt.plot((time-time0)/3600,ratehv_v/1000.,label="Channel %d HV rate" % i_channel)
    plt.plot((time-time0)/3600,ratecal_v/1000.,label="Channel %d Cal rate" % i_channel)
    plt.plot((time-time0)/3600,rate_v/1000.,label="Channel %d Coincidence rate" % i_channel)
    plt.legend()

#    print "len(time_thr) = ", len(time_thr)
#    print "len(vthrhv) = ", len(vthrhv[i_channel])
#    print "len(vthrcal) = ", len(vthrcal[i_channel])
#    print "len(vthr) = ", len(vthr[i_channel])
    plt.subplot(212)
    plt.plot((time_thr-time0_thr)/3600,vthrhv_v,label="Channel %d HV threshold" % i_channel)
    plt.plot((time_thr-time0_thr)/3600,vthrcal_v,label="Channel %d Cal threshold" % i_channel)
    plt.plot((time_thr-time0_thr)/3600,vthr_v,label="Channel %d sum threshold" % i_channel)
    plt.legend()

    plt.show()

plt.figure()
plt.plot((time_sensor-time0_sensor)/3600,caltempsensor,label="Cal sensor temp")
plt.plot((time_sensor-time0_sensor)/3600,hvtempsensor,label="HV sensor temp")
plt.legend()
plt.show()

plt.figure()
for i_channel in [0,1,2,3,4,5,6,7,88,89,90,91,92,93,94,95]:
    rate_v = np.array(rate[i_channel])
    plt.plot((time-time0)/3600,rate_v/1000,label="Ch.%d" % i_channel)
plt.legend()
plt.show()

plt.figure()
for i_channel in [0,1,2,3,4,6,7,88,89,90,91,92,94,95]:
    vthr_v = np.array(vthr[i_channel])
    plt.plot((time_thr-time0_thr)/3600,vthr_v,label="Ch.%d" % i_channel)
plt.title('Channel thresholds [mV] vs time')
plt.legend()
plt.show()

#plt.figure()
#plt.plot(time/3600,hvtemp0,label="hvtemp0")
#plt.plot(time/3600,hvtemp1,label="hvtemp1")
#plt.plot(time/3600,caltemp0,label="caltemp0")
#plt.plot(time/3600,caltemp1,label="caltemp1")
#plt.legend()
#plt.show()

#plt.figure()
#plt.plot(time/3600,i33,label="i33")
#plt.plot(time/3600,i25,label="i25")
#plt.plot(time/3600,i18,label="i18")
#plt.plot(time/3600,i12,label="i12")
#plt.legend()
#plt.show()

exit()



