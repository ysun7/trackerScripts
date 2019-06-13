WHOAREYOU = 0 
SETPREAMPGAIN = 1
SETPREAMPTHRESHOLD = 2
SETCALDAC = 3
SENDONECALPULSE = 4
SETPULSERON = 5
SETPULSEROFF = 6
DUMPSETTINGS = 7
READHISTO = 8
READMONADCS = 10
READBMES = 11
MCPWRITEPIN = 12
GETDEVICEID = 13
TESTDDR=14
RESETROC = 15
# TOGGLECALHV = 16
DIGIRW = 16
READTVS = 17
ROCREADREG = 18

DDRTOGGLE = 50
DDRREAD = 51
DDRCLEAN = 52
DDRMEMFIFOFILL = 53

ADCRWCMDID = 101
BITSLIPCMDID = 102
FINDALIGNMENTCMDID = 103
READRATESCMDID = 104
READDATACMDID = 105
STOPRUNCMDID = 106
ADCINITINFOCMDID = 107
FINDTHRESHOLDSCMDID = 108

PACKAGETESTCMDID = 151

RUN_STARTED = 254

STARTTRG = 0xfffe
STARTBUF = 0xfffd
EMPTY = 0xfffc
ENDOFDATA = 0xfffb

iconst = 3.25/(4096*0.015*20)
iconst5 = 3.25/(4096*0.5*20)
iconst1 = 3.25/(4096*0.005*20)
toffset = 0.509
tslope = 0.00645
tconst = 0.000806

cal_chan_mask1 = 0xC71C71C7
cal_chan_mask2 = 0x71C71C71
cal_chan_mask3 = 0x1C71C71C