#!/usr/bin/env python
import sys
import os
import signal
#import readrates
import measure_thresholds

#nruns = int(sys.argv[1])
nruns=200000

def handler(signum, frame):
    print('Signal handler called with signal', signum)
    raise Exception("program ran too long!")

# Set the signal handler and an alarm
signal.signal(signal.SIGALRM, handler)

for i_run in range(nruns):

    if (i_run % 10 != 0):
        os.system('python readrates.py')
        continue
   
    os.system('python readrates.py -s')
    
    signal.alarm(1000)
    try:
        measure_thresholds.main()
    except Exception, msg:
        print "Timed out!"

    signal.alarm(0)          # Disable the alarm







