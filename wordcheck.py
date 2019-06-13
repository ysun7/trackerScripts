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
import argparse
from draccommands import *
from utils import *
from strawhit import *

PREFIX = "run"
message = ""

def main():

    global fout
    global mode
 
    global adc_mode
 
    global rundir
    global serroc
    
    serial_ports = [
        p[0]
        for p in serial.tools.list_ports.comports()
        if 'ttyUSB' in p[0]
                    #if 'SLAB_USB' in p[0]
    ]

    print serial_ports

    SERIALPORTROC = serial_ports[3]
    #SERIALPORTROC = serial_ports[0]


    SERIALRATE = 57600
    TIMEOUT = 300

    rundirname = "runs"
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

    serroc = serial.Serial(SERIALPORTROC,SERIALRATE, timeout = TIMEOUT)
    print "ARMs connected"

    nlback = 30
    tdc_mode = 0
    clock = 99
    enpulser = 1
    delay = 1
    mode = 0

    parser = argparse.ArgumentParser(description='Optional command arguments')
    parser.add_argument('-p','--printit', action='store_true',
                    help='Print triggers with missing words')
    parser.add_argument('-a','--adc_mode', type=str, nargs='?', default='1', 
                    help='ADC mode')
    parser.add_argument('-N','--n_trials', type=int, nargs='?', default=100, 
                    help='N trials for each channel')
    parser.add_argument('-n','--n_triggers', type=int, nargs='?', default=1, 
                    help='n triggers for each trial')
    parser.add_argument('-s','--n_samples', type=int, nargs='?', default=1, 
                    help='s samples for each trigger')
    parser.add_argument('-fa','--find_alignment', type=int, nargs='?', default=1, 
                    help='Find alignment first')
    #parser.add_argument('-f','--faketimestamp', type=int, nargs='?', default=0, 
    #                help='f=1: timestamp substituted by 0x0319 (default f=0). For diagnotics.')

    args = parser.parse_args()
    
    printit = args.printit
    adc_mode = args.adc_mode
    ntrials = args.n_trials
    ntrigs = args.n_triggers
    nsamples = args.n_samples
    ifalignment = args.find_alignment
    #faketimestamp=args.faketimestamp

    default_pattern = ['000','000']
    if adc_mode == '1':
        default_pattern = ['200','200']
    elif adc_mode == '2':
        default_pattern = ['3FF','3FF'] 
    elif adc_mode == '3':
        default_pattern = ['000','000'] 
    elif adc_mode == '4':
        default_pattern = ['2AA','155'] 
    elif adc_mode == '7':
        default_pattern = ['3FF','000'] 
    elif adc_mode == '9':
        default_pattern = ['2AA','2AA']
    elif adc_mode == 'a':
        default_pattern = ['01F','01F'] 
    elif adc_mode == 'b':
        default_pattern = ['200','200']
    elif adc_mode == 'c':
        default_pattern = ['263','263']
    else:
        print "ADC mode unknown"

    print ""
    print "Input ADC mode is ", adc_mode
    print "Pattern expected is ", default_pattern
    print ntrials, " trial(s) will be taken for each channel"
    print ntrigs, " trigger(s) will be read for each buffer"
    print nsamples, " sample(s) will be read for each trigger"
    print ""

    chan_mask1 = int("FFFFFFFF",16)
    chan_mask2 = int("FFFFFFFF",16)
    chan_mask3 = int("FFFFFFFF",16)

    try:
        # first find alignment
        
        if ifalignment:
            print "finding alignment"
            data=findAlignment(clock, 1, chan_mask1, chan_mask2, chan_mask3)
            serroc.write(data)
            
            try:
                serial_read(serroc, True)[0]
                print "alignment found"
                print ""
            except serial.serialutil.SerialException:
                serroc.close()
                print "ARM disconnected"
                print ""
                serroc = None
        
        for i in range (96):
            if i == 53:
                continue #ADC channel #95, different behaviour
            nfail = 0
            chan_mask1,chan_mask2,chan_mask3 = channelmask(i)
            
            for j in range (ntrials):

                # produce the data file for this run
                
                next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
                while os.path.isfile(os.path.join(rundir,next_runname)):
                    lastrun += 1
                    next_runname = PREFIX + "_" + str(lastrun+1) + ".txt"
                filename = next_runname
                
                run_settings = {'lookback':nlback,'samples':nsamples,'triggers':ntrigs,'mode':mode,'delay':delay,'filename':filename,'start_time':time.strftime("%Y-%m-%d %H:%M:%S"),'message':message}
                fout = open(os.path.join(rundir,filename),"w")
                try:
                    with open('settings.dat','r') as handle:
                        current_settings = json.load(handle)
                except Exception:
                    current_settings = {"thresh": [], "gain" : [], "caldac" : []}
                    for k in range(16):
                        current_settings["thresh"].append(0)
                        current_settings["gain"].append(0)
                    for k in range(8):
                        current_settings["caldac"].append(0)
                
                json.dump(current_settings,fout)
                fout.write("\n")
                json.dump(run_settings,fout)
                fout.write("\n")
                if filename == next_runname:
                    lastrun += 1
                
                data = readData(int(adc_mode, 16), tdc_mode, nlback, nsamples, ntrigs, chan_mask1, chan_mask2, chan_mask3, clock, enpulser, delay, mode)
                serroc.write(data)
                
                try:
                    serial_read(serroc, False, fout, 5)
                except serial.serialutil.SerialException:
                    serroc.close()
                    print "ARM disconnected"
                    print ""
                    serroc = None
                
                # check content. If as expected delete file, if not report file name
                fin = open(os.path.join(rundir,filename),"r")
                data = fin.read()
                data = data.split('\n')
                current_settings = json.loads(data[0])
                run_settings = json.loads(data[1])
                nsamples = run_settings["samples"]
                data = data[2:]
                data = filter(lambda x: len(x)>0, data)
                data = [(int(data[2*l],16)<<16) | (int(data[2*l+1],16) & 0xFFFF) for l in range(len(data)/2)]
                #data = [(int(i,16) & 0xFFF) for i in data]
                tadc = []
                
                iffail = 0
                if len(data) != (4+nsamples)*ntrigs:
                    iffail = 1
                    break
                else:
                    for itrig in range(ntrigs):
                        tdata = data[itrig*(nsamples+4):(itrig+1)*(nsamples+4)]
                        if ((tdata[0] & 0xFFFF0000)>>16) != int('8000',16):
                            tdata = [tdata[-1]]+tdata[:-1]
                            if ((tdata[0] & 0xFFFF0000)>>16) != int('8000',16):
                                iffail = 1
                                break
                        ttrig = StrawHit(tdata)
                        tadc = ttrig.adc
                        for h in range(len(tadc)):
                            if h == 0:
                                if tadc[0] == int(default_pattern[0],16):
                                    h0 = 0
                                elif tadc[0] == int(default_pattern[1],16):
                                    h0 = 1
                                else:
                                    iffail = 1
                                    break
                            if tadc[h] != int(default_pattern[(h+h0)%2],16):
                                iffail = 1
                                break
                      
                fin.close()
                if iffail == 1:
                    print "    Trial #", (j+1)," problematic in data, results stored in ", filename
                    if printit:
                        print "   ", tadc
                    nfail += 1
                elif iffail == 2:
                    print "    Trial #", (j+1)," problematic in fake timestamp, results stored in ", filename
                    nfail += 1
                else:
                    os.remove(os.path.join(rundir,filename))

            print "Channel ", i, " tests completed, ", nfail, "/", ntrials," trials had issues"

    except serial.serialutil.SerialException:
        serroc.close()
        print "ARM disconnected"

    except Exception, e:
      print type(e),e
    finally:
        serroc.close()

        print 'Ending...'

if __name__ == "__main__":
    main()
