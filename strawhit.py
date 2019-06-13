import matplotlib.pyplot as plt
import numpy as np
import sys
from pprint import pprint
import glob
import math
import os
import json

class StrawHit:
    def __init__ (self, data):

        adc1=[]
        self.channel = data[0] & 0x7F

        self.gtime = data[1] & 0xEFFFFFFF
        rhtime = data[2]&0xFFFFFF
        rctime = data[3]&0xFFFFFF
        self.htime = (rhtime & 0xFFFF00) + (0xFF - (rhtime&0xFF));
        self.ctime = (rctime & 0xFFFF00) + (0xFF - (rctime&0xFF));

        self.fifo_error = 1 if (data[0] & 0x80) != 0x0 else 0


        for a in data[4:]:
            n = (a>>0) & 0x3FF
            adc1.append (int('{:010b}'.format(n)[::-1], 2))
            n = (a>>10) & 0x3FF
            adc1.append (int('{:010b}'.format(n)[::-1], 2))
            n = (a>>20) & 0x3FF
            adc1.append (int('{:010b}'.format(n)[::-1], 2))

          #   adc1.append((a>>0) & 0x3FF)
          # adc1.append((a>>10) & 0x3FF)
          # adc1.append((a>>20) & 0x3FF)
#            adc1.append(int('{:010b}'.format(a)[::-1], 2) )
        self.adc = adc1
        # print adc1

    def getAverageSample(self):
        return np.mean(self.adc)
    def getSamplesRMS(self):
        return np.std(self.adc)
