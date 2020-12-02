#!/usr/bin/python

import sys
import time
from Precigenome.PGMFC import PGMFC

#print(str(sys.argv))

mfcs = PGMFC(serial_number=4)
mfcs.monitor_start(span=100)
time.sleep(2)

channel_pulse = mfcs[1]
channel_pulse.set_params(peak=10, runtime=50)

while(True):
    channel_pulse.purge_on()
    print("on: ",channel_pulse.get_pressure()[0])
    time.sleep(5)

    channel_pulse.purge_off()
    print("off:",channel_pulse.get_pressure()[0])
    time.sleep(5)

