import matplotlib.pyplot as plt
import numpy as np
import struct
import sys
from pprint import pprint
import constants
import binascii as bs


def unpack_data(ptype,nbytes,data,printit):
    
    keys = []
    values=[]
    
    if ptype == constants.READMONADCS:
    
        s = struct.Struct('<16H')
        keys = ['I3.3','I2.5','IHV5.0','HVDIGITEMP','HVROCTEMP','VDMBHV5.0','V3.8HV','V2.9',
                'I1.8','I1.2','ICAL5.0','CALDIGITEMP','VDMBCAL5.0','V3.8CAL','V2.3','V2.0']
        d = s.unpack(data)

        for index, element in enumerate(d):
            if index==3 or index==4 or index==11:
                v=(d[index]*constants.tconst-constants.toffset)/constants.tslope
            elif index==0 or index==1 :
                v=d[index]*constants.iconst
            elif index==2 or index==10 :
                v=d[index]*constants.iconst5
            elif index==8 or index==9 :
                v=d[index]*constants.iconst1
            elif index==5 or index==6 or index==7 or index==12 or index==13 or index==14 or index==15:
                v=d[index]*3.25*2/4096
            values.append(round(v,2))
        rd = dict(zip(keys, values))          
        if printit:
            pprint(rd)
        
    elif ptype == constants.SETPREAMPGAIN:
        s=struct.Struct('2H')
        d = s.unpack(data)
        keys = ['Channel','Gain']
        values.append(d[0])
        values.append(d[1])
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
        
    elif ptype == constants.SETPREAMPTHRESHOLD:
        s=struct.Struct('2H')
        d = s.unpack(data)
        keys = ['Channel','Threshold']
        values.append(d[0])
        values.append(d[1])
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
        
    elif ptype == constants.SETPULSERON:
        s=struct.Struct('<BBHI')
        d = s.unpack(data)
        keys = ['Channel','PulserOdd','DutyCycle','Delay']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))          
        if printit:
            pprint(rd)
        
    elif ptype == constants.READBMES:
        # print len(data)
        s=struct.Struct('<6I')
        d = s.unpack(data)
        keys = ['CalTemp','CalPressure','CalHumidity','HVTemp','HVPressure','HVHumidity']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)


    elif ptype == constants.TESTDDR:
        if nbytes == 20:
            s=struct.Struct('<6BIH2I')
            keys = ['NHITS','CS','WEN','REN','DMAEN','PATTERN','ERROR','ADDR','DATA','OFFSET']
        elif nbytes == 8:
            s=struct.Struct('<4B2H')
            keys = ['WEN','REN','WADDR','RADDR','WDATA','RDATA']
        d = s.unpack(data)
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.GETDEVICEID:
        s=struct.Struct('2Q')
        d = s.unpack(data)
        keys = ['ID0','ID1']
        for index, element in enumerate(d):
            values.append(hex(element))
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.MCPWRITEPIN:
        s=struct.Struct('<BBH')
        d = s.unpack(data)
        keys = ['MCP','RETV','CHANNEL']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.SETCALDAC:
        s=struct.Struct('<BH')
        d = s.unpack(data)
        keys = ['CHANNELMASK','VALUE']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
            
    elif ptype == constants.DUMPSETTINGS:

        if nbytes == 10:
            s=struct.Struct('<5H')
            d = s.unpack(data)
            keys.append(d[0])
            values.append({'GainHV':d[1],'ThresholdHV':d[2],'GainCal':d[3], 'ThresholdCal':d[4]})            
        elif nbytes == 768:
            s=struct.Struct('<384H')
            d = s.unpack(data)
            for index in range(96):
                keys.append(index)
                values.append({'GainHV':d[4*index],'ThresholdHV':d[4*index+1],'GainCal':d[4*index+2], 'ThresholdCal':d[4*index+3]})            
        rd = dict(zip(keys, values))
        if printit:
            print "{:<8} {:<10} {:<12} {:<12} {:<12}".format('Straw','GainHV','ThresholdHV','GainCal','ThresholdCal')
            for k, v in rd.iteritems():
                print "{:<8} {:<12} {:<12} {:<12} {:<12}".format(k, v['GainHV'], v['ThresholdHV'], v['GainCal'], v['ThresholdCal'])


    elif ptype == constants.DIGIRW:
        s=struct.Struct('<3BH')
        d = s.unpack(data)
        keys = ['IS_WRITE','HVCAL','ADDR','DATA']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)


    elif ptype == constants.ROCREADREG:
        s=struct.Struct('<BHH')
        d = s.unpack(data)
        keys = ['ADDR','DATA']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
            

    elif ptype == constants.READTVS:
        s=struct.Struct('<3hH3hH3hH')
        d = s.unpack(data)
        keys = ['ROC_RAIL_1V(mV)','ROC_RAIL_1.8V(mV)','ROC_RAIL_2.5V(mV)','ROC_TEMP(CELCIUS)','CAL_RAIL_1V(mV)','CAL_RAIL_1.8V(mV)','CAL_RAIL_2.5V(mV)','CAL_TEMP(CELCIUS)','HV_RAIL_1V(mV)','HV_RAIL_1.8V(mV)','HV_RAIL_2.5V(mV)','HV_TEMP(CELCIUS)']
        for index, element in enumerate(d):
            if (index%4) < 3:
                values.append('%.3f'%(float(element)/float(8)))
            else:
                values.append('%.4f'%(float(element)/float(16)-273.15))
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
        
################  DDR Read unpacker ###################

    elif ptype == constants.DDRTOGGLE:
        s=struct.Struct('<BI')
        d = s.unpack(data)
        keys = ['DDR_SELECT','WRITE_PAGE_NO']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
    
    elif ptype == constants.DDRREAD:
        if nbytes == 13:
            s=struct.Struct('<B3I')
            d = s.unpack(data)
            keys = ['DDR_FULL','PAGES_WRITTEN','PAGES_READ','PAGE_NO_TO_READ']
            for index, element in enumerate(d):
                values.append(element)
            rd = dict(zip(keys, values))
            if printit:
                pprint(rd)
        elif nbytes == 11:
            s=struct.Struct('<7BI')
            d = s.unpack(data)
            keys = ['MEM_FIFO_EMPTY (INIT)','MEM_FIFO_FULL (INIT)','MEM_FIFO_EMPTY (TRANSFERED)','MEM_FIFO_FULL (TRANSFERED)','MEM_FIFO_EMPTY (END)','MEM_FIFO_FULL (END)','IF_CLEAN','PAGES_READ']
            for index, element in enumerate(d):
                values.append(element)
            rd = dict(zip(keys, values))
            if printit:
                pprint(rd)

    elif ptype == constants.DDRCLEAN:
        print "DDR Cleaned."
    
    elif ptype == constants.DDRMEMFIFOFILL:
        s=struct.Struct('<4B')
        d = s.unpack(data)
        keys = ['EMPTY_INIT','FULL_INIT','EMPTY_END','FULL_END']
        for index, element in enumerate(d):
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
    
################ FullPFCal unpacker ###################

    elif ptype == constants.PACKAGETESTCMDID:
        fmt = '<'
        fmt += str(nbytes)
        fmt += 'B'
        s=struct.Struct(fmt)
        d = s.unpack(data)
        for index, element in enumerate(d):
            keys.append(index)
            values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.ADCRWCMDID:
        s0=struct.Struct('<B')
        rwflag = s0.unpack(data[0])
        if rwflag == 1:
            s=struct.Struct('<2BHB')
            d = s.unpack(data[0:5])
            keys = ['RW', 'ADC_NUM', 'ADDRESS', 'RESULT']
        else:
            s=struct.Struct('<2B2H')
            d = s.unpack(data)
            keys = ['RW', 'ADC_NUM', 'ADDRESS', 'DATA']
        for index, element in enumerate(d):
            if index == 2 or index == 3:
                values.append(hex(element))
            else:
                values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.BITSLIPCMDID:
        s=struct.Struct('<4I')
        d = s.unpack(data)
        keys = ['EMPTY','FULL','DATA1','DATA2']
        for index, element in enumerate(d):
            if (index % 4) == 2 or (index % 4) == 3:
                values.append(hex(element))
            else:
                values.append(element)
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)

    elif ptype == constants.FINDALIGNMENTCMDID:
        print len(data)
        fmt='<B'
        for index in range(96):
            fmt += '3B3H'
        fmt += '25B3I'
        s=struct.Struct(fmt)
        d = s.unpack(data)
        d_count = 0
        keys.append('DOPHASE')
        values.append(d[d_count])
        d_count += 1
        if d[d_count-1] == 0:
            d_count += 6*96
            printflag = 0
        else:
            printflag = 1
            for index in range(96):
                keys.append(str(index))
                values.append({'Channel':d[d_count+index*6],'NumEnoughTrigger':d[d_count+index*6+1],'BestClock':d[d_count+index*6+2],'Results0':d[d_count+index*6+3],'Results3':d[d_count+index*6+4],'Results6':d[d_count+index*6+5]})
            d_count += 6*96
        keys.append('FindAlignmentSuccess')
        values.append({'Ch[00:07]':d[d_count],'Ch[08:15]':d[d_count+1],'Ch[16:23]':d[d_count+2],'Ch[24:31]':d[d_count+3],'Ch[32:39]':d[d_count+4],'Ch[40:47]':d[d_count+5],'Ch[48:55]':d[d_count+6],'Ch[56:63]':d[d_count+7],'Ch[64:71]':d[d_count+8],'Ch[72:79]':d[d_count+9],'Ch[80:87]':d[d_count+10],'Ch[88:95]':d[d_count+11]})
        d_count += 12
        keys.append('MixedFreqAdcCheck')
        values.append({'Ch[00:07]':d[d_count],'Ch[08:15]':d[d_count+1],'Ch[16:23]':d[d_count+2],'Ch[24:31]':d[d_count+3],'Ch[32:39]':d[d_count+4],'Ch[40:47]':d[d_count+5],'Ch[48:55]':d[d_count+6],'Ch[56:63]':d[d_count+7],'Ch[64:71]':d[d_count+8],'Ch[72:79]':d[d_count+9],'Ch[80:87]':d[d_count+10],'Ch[88:95]':d[d_count+11]})
        d_count += 12
        keys.append('ChannelsW/EnoughTriggers')
        values.append(d[d_count])
        keys.append('ErrorMask[00:31]')
        values.append(d[d_count+1])
        keys.append('ErrorMask[32:63]')
        values.append(d[d_count+2])
        keys.append('ErrorMask[64:95]')
        values.append(d[d_count+3])
        rd = dict(zip(keys, values))
        if printit:
            print 'DOPHASE', rd['DOPHASE']
            if printflag:
                print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12}".format('Ch', 'NumEnofTrgr', 'BestClock', 'Results0(0x)', 'Results3(0x)', 'Results6(0x)')
                for index in range(96):
                    v=rd[str(index)]
                    print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12}".format(v['Channel'], v['NumEnoughTrigger'], v['BestClock'], hex(v['Results0']), hex(v['Results3']), hex(v['Results6']))
            print 'FindAlignmentSuccess'
            for kk in sorted(rd['FindAlignmentSuccess'].keys()):
                print kk, bin(rd['FindAlignmentSuccess'][kk])
            print 'MixedFreqAdcCheck'
            for kk in sorted(rd['MixedFreqAdcCheck'].keys()):
                print kk, bin(rd['MixedFreqAdcCheck'][kk])
            print 'ChannelsW/EnoughTriggers', rd['ChannelsW/EnoughTriggers']
            print 'ErrorMask[00:31]', hex(rd['ErrorMask[00:31]'])
            print 'ErrorMask[32:63]', hex(rd['ErrorMask[32:63]'])
            print 'ErrorMask[64:95]', hex(rd['ErrorMask[64:95]'])
            
    elif ptype == constants.READRATESCMDID:
        #print len(data)
        nn=nbytes/17
        fmt='<'
        for index in range(nn):
            fmt += 'B4I'
        s=struct.Struct(fmt)
        d = s.unpack(data)
        for index in range(nn):
            keys.append(d[5*index])
            if d[5*index+4] == 0:
                d = d[:5*index+4]+(-1,)+d[5*index+5:]
            hvrate =  d[5*index+1]/(20e-9 * float(d[5*index+4]))
            calrate = d[5*index+2]/(20e-9 * float(d[5*index+4]))
            crate =   d[5*index+3]/(20e-9 * float(d[5*index+4]))
            values.append({'TotalHV':d[5*index+1],'TotalCal':d[5*index+2], 'TotalCoinc':d[5*index+3],'TotalTimeCounts':d[5*index+4], 'RateHV' : hvrate, 'RateCal' : calrate, 'RateCoinc' : crate })            
        rd = dict(zip(keys, values))
        if printit:
            print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format('Channel','TotalHV','TotalCal','TotalCoinc','TotalTimeCounts', 'RateHV', 'RateCal' , 'RateCoinc')
            for k, v in rd.iteritems():
                print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format(k, v['TotalHV'], v['TotalCal'], v['TotalCoinc'], v['TotalTimeCounts'], v['RateHV'],v['RateCal'],v['RateCoinc'] )

    elif ptype == constants.READDATACMDID:
        #print len(data)
        if nbytes == 35:
            s=struct.Struct('<B2HI2H8sBI4HB')
            d = s.unpack(data)
            keys=['EnablePulser','NumSamples','NumLookback','Ch_mask1','AdcMode','TdcMode','TdcString','Clock','NumTriggers', 'digi_read(0xb)','digi_read(0xe)','digi_read(0xd)','digi_read(0xc)','Mode']
            for index, element in enumerate(d):
                if index == 3 or (index > 8 and index < 13):
                    values.append(bin(element))
                else: 
                    values.append(element)
            rd = dict(zip(keys, values))
            if printit:
                pprint(rd)
        elif nbytes == 5:
            s=struct.Struct('<BI')
            d = s.unpack(data)
            if d[0] == 1:
                keys=['TriggerCountMatchNumTriggers','DelayCount']
            else:
                keys=['TriggerCountMatchNumTriggers','TriggerCount']
            for index, element in enumerate(d):
                values.append(element)
            rd = dict(zip(keys, values))
            if printit:
                pprint(rd)


    elif ptype == constants.STOPRUNCMDID:
        s=struct.Struct('<BH')
        d = s.unpack(data)
        if d[0] == 0:
            rd = dict(zip(['ReadoutEnabled'], [0]))
        else:
            rd = dict(zip(['ReadoutEnabled','ReadoutTotalTriggers'], [d[0],d[1]]))
        if printit:
            pprint(rd)

    elif ptype == constants.ADCINITINFOCMDID:
        s=struct.Struct('<H26BH')
        d = s.unpack(data)
        keys = ['ADCMask(0x)','PATTERN(0x)','PHASE']
        values = [hex(d[0]), hex(d[1]), d[2]]
        for index in range(12):
            keys.append("[Config] ADCRead(0x00,"+str(index)+")")
            values.append(hex(d[3+2*index]))
            keys.append("[ChipID] ADCRead(0x01,"+str(index)+")")
            values.append(hex(d[4+2*index]))
        keys.append("ERRORS(bin)")
        values.append(bin(d[27]))
        rd = dict(zip(keys, values))
        if printit:
            pprint(rd)
    elif ptype == constants.READHISTO:
      s=struct.Struct("H"*256)
      d = s.unpack(data)
      rd = {"data":d} 

    elif ptype == constants.FINDTHRESHOLDSCMDID:
        s0=struct.Struct('<3HB')
        verbose = s0.unpack(data[:7])[3]
        if verbose == 0:
            nn = (nbytes-7)/21
            fmt='<3HB'
            for index in range(nn):
                fmt += 'B4HHIHI'
            s=struct.Struct(fmt)
            d = s.unpack(data)
            keys=['LOOKBACK','SAMPLES','TARGET_RATE','VERBOSE']
            values=[d[0],d[1],d[2],d[3]]
            for index in range(nn):
                keys.append(str(index))
                values.append({'Ch':d[9*index+4],'DefaultCalGain':d[9*index+5],'DefaultCalThres':d[9*index+6], 'DefaultHvGain':d[9*index+7],'DefaultHvThres':d[9*index+8], 'ThresCal':d[9*index+9], 'RateCal':d[9*index+10], 'ThresHv':d[9*index+11], 'RateHv':d[9*index+12]})            
            rd = dict(zip(keys, values))
            if printit:
                print 'LOOKBACK', rd['LOOKBACK']
                print 'SAMPLES', rd['SAMPLES']
                print 'TARGET_RATE', rd['TARGET_RATE']
                print 'VERBOSE', rd['VERBOSE']
                print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format('Ch', 'CalGain', 'DftCalThres', 'HvGain', 'DftHvThres', 'ThresCal', 'RateCal', 'ThresHv', 'RateHv')
                for index in range(nn):
                    v=rd[str(index)]
                    print "{:<8} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format(v['Ch'],v['DefaultCalGain'],v['DefaultCalThres'],v['DefaultHvGain'],v['DefaultHvThres'],v['ThresCal'],v['RateCal'],v['ThresHv'],v['RateHv'])
        else:
            nn = (nbytes-16)/6
            fmt='<3HBB4H'
            for index in range(nn):
                fmt += 'HI'
            s=struct.Struct(fmt)
            d = s.unpack(data)
            keys=['LOOKBACK','SAMPLES','TARGET_RATE','VERBOSE','CHANNEL','DefaultCalGain','DefaultCalThres','DefaultHvGain','DefaultHvThres']
            for index in range(9):
                values.append(d[index])
            if verbose == 2:# HV process printed
                keys.append('ThresCal')
                keys.append('RateCal')
                values.append(d[9])
                values.append(d[10])
            for index in range(nn-1):
                keys.append(str(index))
                values.append({'Thres':d[2*index+9+2*(verbose-1)],'Rate':d[2*index+10+2*(verbose-1)]})
            if verbose == 1:# CAL process printed
                keys.append('ThresHv')
                keys.append('RateHv')
                values.append(d[2*nn+7])
                values.append(d[2*nn+8])
            rd = dict(zip(keys, values))
            if printit:
                print 'LOOKBACK', rd['LOOKBACK']
                print 'SAMPLES', rd['SAMPLES']
                print 'TARGET_RATE', rd['TARGET_RATE']
                print 'VERBOSE', rd['VERBOSE']
                print 'CHANNEL', rd['CHANNEL']
                print 'DefaultCalGain', rd['DefaultCalGain']
                print 'DefaultCalThres', rd['DefaultCalThres']
                print 'DefaultHvGain', rd['DefaultHvGain']
                print 'DefaultHvThres', rd['DefaultHvThres']
                if verbose == 2:
                    print 'ThresCal', rd['ThresCal']
                    print 'RateCal', rd['RateCal']
                    print "======================================"
                    print "HV Threshold Search History"
                elif verbose == 1:
                    print 'ThresHv', rd['ThresHv']
                    print 'RateHv', rd['RateHv']
                    print "======================================"
                    print "CAL Threshold Search History"
                print "{:<12} {:<12}".format('Thres','Rate')
                for index in range(nn-1):
                    v=rd[str(index)]
                    print "{:<12} {:<12}".format(v['Thres'],v['Rate'])


    return rd


##################### Data unpackers #####################

def unpackToFout(data,nTrigger,fout):
    # print len(data)
    s=struct.Struct('<'+str(nTrigger)+'H')
    d = s.unpack(data)
    if fout != None:
        for element in d:
            fout.write('%04X \n' % element)

    d = [(d[2*i]<<16) | (d[2*i+1] & 0xFFFF) for i in range(len(d)/2)]
  
    return d


