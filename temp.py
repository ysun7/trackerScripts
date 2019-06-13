#!/usr/bin/env python
import readpanel
import sys
import time

nruns = int(sys.argv[1])

for irruns in range(nruns):
    readpanel.main()
    time.sleep(5)




