import sys
import glob
import os
import json
import struct
import matplotlib.pyplot as plt
import numpy as np
import constants
from unpacker import *
from strawhit import *
from utils import channelmask

def thresholdset(channel,dvalue,type):
    if type == 1:
        channel = channel + 96

    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0x8)
    data += struct.pack('B',constants.SETPREAMPTHRESHOLD)
    data += struct.pack('H',channel)
    data += struct.pack('H',dvalue)

    return data



def gainset(channel,dvalue,type):

    
    if type == 1:
        channel = channel + 96
    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0x8)
    data += struct.pack('B',constants.SETPREAMPGAIN)
    data += struct.pack('H',channel)
    data += struct.pack('H',dvalue)

    return data

def caldacset(chan_mask,dvalue):
    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0x7)
    data += struct.pack('B',constants.SETCALDAC)
    data += struct.pack('B',chan_mask)
    data += struct.pack('H',dvalue)

    return data

def setpulseron(chan_mask,pulser_odd,dutycycle,delay):

    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',12)
    data += struct.pack('B',constants.SETPULSERON)
    data += struct.pack('B',chan_mask)
    data += struct.pack('B',pulser_odd)
    data += struct.pack('H',dutycycle)
    data += struct.pack('I',delay)

    return data

def setpulseroff():

    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.SETPULSEROFF)

    return data

def dumpsettings(channel):

    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',6)
    data += struct.pack('B',constants.DUMPSETTINGS)
    data += struct.pack('H',channel)

    return data

def readhisto(channel,hv_or_cal):
    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',6)
    data += struct.pack('B',constants.READHISTO)
    data += struct.pack('B',channel)
    data += struct.pack('B',hv_or_cal)
    return data

def sendonecalpulse(chan_mask):
    data = ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0x5)
    data += struct.pack('B',constants.SENDONECALPULSE)
    data += struct.pack('B',chan_mask)

    return data

def readspi():

    data= ""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B', constants.READMONADCS)

    return data

def readSensors():
     data= ""
     data += struct.pack('B',0xaa)
     data += struct.pack('B',0xaa)
     data += struct.pack('B',4)
     data += struct.pack('B',constants.READBMES)
     return data


def readSlowAmps(slot, channel,mode,rate,gain):
     data= ""
     data += struct.pack('B',0xaa)
     data += struct.pack('B',0xaa)
     data += struct.pack('B',9)
     data += struct.pack('B',constants.READSLOWAMPS)
     data += struct.pack('B',slot)
     data += struct.pack('B',channel)
     data += struct.pack('B',mode)
     data += struct.pack('B',rate)
     data += struct.pack('B',gain)

     return data



def mcpwritepin(mcp,channel,pinvalue):
     data= ""
     data += struct.pack('B',0xaa)
     data += struct.pack('B',0xaa)
     data += struct.pack('B',8)
     data += struct.pack('B',constants.MCPWRITEPIN)     
     data += struct.pack('H',channel)
     data += struct.pack('B',mcp)
     data += struct.pack('B',pinvalue)

     return data



def testDDR(ddrcs,ddrwen,ddrren,ddrdmaen,ddrnhits,ddrpattern,ddrraddr,ddroffset):
# def testDDR(ddrwen,ddrren,ddrwaddr,ddrraddr,ddrwdata):
     data= ""
     data += struct.pack('B',0xaa)
     data += struct.pack('B',0xaa)

     data += struct.pack('B',16)
    #  data += struct.pack('B',10)
     
     data += struct.pack('B',constants.TESTDDR)     
     data += struct.pack('B',ddrcs)
     data += struct.pack('B',ddrwen)
     data += struct.pack('B',ddrren)
     data += struct.pack('B',ddrdmaen)
     data += struct.pack('B',ddrnhits)
     data += struct.pack('B',ddrpattern)
     data += struct.pack('H',ddrraddr)
     data += struct.pack('I',ddroffset)

    #  data += struct.pack('B',ddrwen)
    #  data += struct.pack('B',ddrren)
    #  data += struct.pack('B',ddrwaddr)
    #  data += struct.pack('B',ddrraddr)
    #  data += struct.pack('H',ddrwdata)

     return data

def resetROC():
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.RESETROC)     
    return data



def readDeviceID():
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.GETDEVICEID)     
    return data
    
def digiRW(rw, thishvcal, rwaddress, rwdata):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',9)
    data += struct.pack('B',constants.DIGIRW)  
    
    data += struct.pack('B',rw)
    data += struct.pack('B',thishvcal)
    data += struct.pack('B',rwaddress)
    data += struct.pack('H',rwdata)
    
    return data

def rocRW(raddress):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',5)
    data += struct.pack('B',constants.ROCREADREG)  
    data += struct.pack('B',raddress)
    
    return data

def readTVS():
    data=''
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.READTVS) 
    return data

#def toggleCALHV(hvcal):
#    data=""
#    data += struct.pack('B',0xaa)
#    data += struct.pack('B',0xaa)
#    data += struct.pack('B',5)
#    data += struct.pack('B',constants.TOGGLECALHV)
#    data += struct.pack('B', hvcal)  
#    return data

################  DDR Read commands ###################
def ddrToggle(ddr_select, page_no):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',9)
    data += struct.pack('B',constants.DDRTOGGLE)
    data += struct.pack('B',ddr_select)
    data += struct.pack('I',page_no)     
    return data

def ddrRead(page_no_to_read, ifclean):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',9)
    data += struct.pack('B',constants.DDRREAD)
    data += struct.pack('I',page_no_to_read)
    data += struct.pack('B',ifclean)
    return data

def ddrClean():
    data=''
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.DDRCLEAN) 
    return data

def ddrMemFifoFill():
    data=''
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.DDRMEMFIFOFILL) 
    return data

################ FullPFCal commands ###################

def packageTest():
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.PACKAGETESTCMDID)     
    return data


def adcRW(adc_num, rw, rwaddress, rwdata):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',10)
    data += struct.pack('B',constants.ADCRWCMDID)
    data += struct.pack('B',adc_num)
    data += struct.pack('B',rw)
    data += struct.pack('H',rwaddress)
    data += struct.pack('H',rwdata)
    return data

def bitSlip(num_bits, channel_mask1, channel_mask2, channel_mask3):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',18)
    data += struct.pack('B',constants.BITSLIPCMDID)
    data += struct.pack('H',num_bits)
    data += struct.pack('I',channel_mask1)
    data += struct.pack('I',channel_mask2)
    data += struct.pack('I',channel_mask3)
    return data

def findAlignment(clock, dophase, channel_mask1, channel_mask2, channel_mask3):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',18)
    data += struct.pack('B',constants.FINDALIGNMENTCMDID)
    data += struct.pack('B',clock)
    data += struct.pack('B',dophase)
    data += struct.pack('I',channel_mask1)
    data += struct.pack('I',channel_mask2)
    data += struct.pack('I',channel_mask3)
    return data

def readRates(num_lookback, num_samples, channel_mask1, channel_mask2, channel_mask3):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',20)
    data += struct.pack('B',constants.READRATESCMDID)
    data += struct.pack('H',num_lookback)
    data += struct.pack('H',num_samples)
    data += struct.pack('I',channel_mask1)
    data += struct.pack('I',channel_mask2)
    data += struct.pack('I',channel_mask3)
    return data

def readData(adc_mode, tdc_mode, num_lookback, num_samples, num_triggers, channel_mask1, channel_mask2, channel_mask3, clock, enable_pulser, max_total_delay, mode):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',31)
    data += struct.pack('B',constants.READDATACMDID)
    data += struct.pack('B',adc_mode)
    data += struct.pack('B',tdc_mode)
    data += struct.pack('H',num_lookback)
    data += struct.pack('H',num_samples)
    data += struct.pack('I',num_triggers)
    data += struct.pack('I',channel_mask1)
    data += struct.pack('I',channel_mask2)
    data += struct.pack('I',channel_mask3)
    data += struct.pack('B',clock)
    data += struct.pack('B',enable_pulser)
    data += struct.pack('H',max_total_delay)
    data += struct.pack('B',mode)
    return data

def stopRun():
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.STOPRUNCMDID)     
    return data

def adcInitInfo():
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',4)
    data += struct.pack('B',constants.ADCINITINFOCMDID)     
    return data

def findThresholds(num_lookback, num_samples, channel_mask1, channel_mask2, channel_mask3, target_rate, verbose):
    data=""
    data += struct.pack('B',0xaa)
    data += struct.pack('B',0xaa)
    data += struct.pack('B',23)
    data += struct.pack('B',constants.FINDTHRESHOLDSCMDID)
    data += struct.pack('H',num_lookback)
    data += struct.pack('H',num_samples)
    data += struct.pack('I',channel_mask1)
    data += struct.pack('I',channel_mask2)
    data += struct.pack('I',channel_mask3)
    data += struct.pack('H',target_rate)
    data += struct.pack('B',verbose)
    return data


################ Serial commands ###################

def serial_read(ser, printit = False, fout = None, nstore = 5):
    rd = {}
    strawHitList=[]
    
        # Print data from serial to screen
    data = ser.readline()
    ptype = -1
    if data:
        if data.startswith("monitoring"):

            ptype = ord(ser.read())
            nbytes = ord(ser.read())
            nbytes += ord(ser.read())*256
            
            if printit:
                print ptype,nbytes
                
            if nbytes > 0 :
                data=ser.read(nbytes)
                rd = unpack_data(ptype, nbytes, data, printit)

                if ptype == constants.READDATACMDID:
                    if rd['Mode'] != 0:
                        if ord(ser.read()) == constants.RUN_STARTED:
                            print "Run Started."
                                    
                    elif rd['Mode'] == 0:
                        strawHitList=serial_read_data(ser,fout,5)
                                
                        if ord(ser.read()) == constants.READDATACMDID:
                            nbytes = ord(ser.read())
                            nbytes += ord(ser.read())*256

                            if printit:
                                print nbytes
                                    
                            data=ser.read(nbytes)
                            rd.update(unpack_data(ptype, nbytes, data, printit))
                
                elif ptype == constants.READHISTO:
                    print rd["data"]

                elif ptype == constants.DDRREAD:
                    strawHitList=serial_read_data(ser,fout,5)

                    if ord(ser.read()) == constants.DDRREAD:
                        nbytes = ord(ser.read())
                        nbytes += ord(ser.read())*256

                        if printit:
                            print nbytes

                        data=ser.read(nbytes)
                        rd.update(unpack_data(ptype, nbytes, data, printit))


        elif data.startswith("datastream"):
            strawHitList=serial_read_data(ser,fout,0)

        else:
            print data
    return ptype, rd, strawHitList
     




# function exists for historical reason
# functionalities covered by "serial_read" command
# may consider replacing all instances by "serail_read" in the future
def serial_read_digi(ser,fout,nstore):
        rd = {}
        strawHitList=[]
    
        data = ser.readline()
        if data:
            if data.startswith("monitoring"):
                   
                ptype = ord(ser.read())
                nbytes = ord(ser.read())
                nbytes += ord(ser.read())*256
                
                print ptype, nbytes
            
                if nbytes > 0:
                    data=ser.read(nbytes)
                    rd = unpack_data(ptype, nbytes, data, True)

                    if ptype == constants.READDATACMDID:
                        if rd['Mode'] != 0:
                            if ord(ser.read()) == constants.RUN_STARTED:
                                print "Run Started."
                                    
                        elif rd['Mode'] == 0:
                            strawHitList=serial_read_data(ser,fout,5)
                                
                            if ord(ser.read()) == constants.READDATACMDID:
                                nbytes = ord(ser.read())
                                nbytes += ord(ser.read())*256

                                print nbytes
                                    
                                data=ser.read(nbytes)
                                rd.update(unpack_data(ptype, nbytes, data, True))
                            
            elif data.startswith("datastream"):
                strawHitList=serial_read_data(ser,fout,nstore)

            else:
                print data
        return rd, strawHitList

def serial_read_data(ser,fout, nstore):
    strawHitList=[]
    istore = 0
    while True:
        ser.timeout=100
        datastream_header = ord(ser.read())
        datastream_header += ord(ser.read())*256
        ser.timeout=0.5
        nTrigger = 0 
            
        if datastream_header == constants.EMPTY:
        #    print "Empty buffer. End of data Stream."
            break
        elif datastream_header == constants.ENDOFDATA:
        #    print "All triggers read. End of data Stream."
            break
        nbytes = ord(ser.read())
        nbytes += ord(ser.read())*256                
                        
        # read nbytes and put into fout/class object
        this_buffer=ser.read(nbytes)
        this_trigger = ""
        if datastream_header == constants.STARTTRG:
            this_trigger = this_buffer
            nTrigger = int(nbytes/2)
        elif datastream_header == constants.STARTBUF:
            this_trigger += this_buffer
            nTrigger += int(nbytes/2)
        istore = istore + 1
        this_trigger = StrawHit(unpackToFout(this_trigger,nTrigger,fout))
        #yield this_trigger
        if istore < nstore:
            strawHitList.append(this_trigger)
    if fout != None:
        fout.close()
    return strawHitList

################ Device test commands ###################

def readstrawcmd(channel,samples):
    chan_mask1, chan_mask2, chan_mask3 = channelmask(channel)
  
    adc_mode = 0
    tdc_mode = 0
    lookback = 2
    mode = 0
    clock = 99

    triggers=1
    pulser=1
    delay=1

    data = readData(adc_mode, tdc_mode, lookback, samples, triggers, chan_mask1, chan_mask2, chan_mask3, clock, pulser, delay, mode)
  
    return data


def disablepulser():
    chan_mask1 = 0xFFFFFFFF
    chan_mask2 = 0xFFFFFFFF
    chan_mask3 = 0xFFFFFFFF

    adc_mode = 0
    tdc_mode = 1
    lookback = 30
    samples = 10
    mode = 0
    clock = 99

    triggers = 0
    pulser = 0
    delay = 1

    data = readData(adc_mode, tdc_mode, lookback, samples, triggers, chan_mask1, chan_mask2, chan_mask3, clock, pulser, delay, mode)
  
    return data

def readstrawrates():
    chan_mask1 = 0xFFFFFFFF
    chan_mask2 = 0xFFFFFFFF
    chan_mask3 = 0xFFFFFFFF

    lookback = 2
    samples = 100

    data = readRates(lookback, samples, chan_mask1, chan_mask2, chan_mask3)

    return data




