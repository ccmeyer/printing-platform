#!/usr/bin/python

import sys
import time
from Precigenome.PGMFC import PGMFC

#print(str(sys.argv))

mfcs = PGMFC(serial_number=4)
mfcs.monitor_start(span=1000)
time.sleep(1)

channel_pulse = mfcs[1]
channel_refuel = mfcs[2]

pressure_pulse = float(sys.argv[1])
pressure_refuel = float(sys.argv[2])

if pressure_pulse == 0:
    channel_pulse.purge_off()
else:
    channel_pulse.set_params(peak=pressure_pulse, runtime=50)
    channel_pulse.purge_on()

if pressure_refuel == 0:
    channel_refuel.purge_off()
else:
    channel_refuel.set_params(peak=pressure_refuel, runtime=50)
    channel_refuel.purge_on()
