#!/usr/bin/python

import sys
import time
from Precigenome.PGMFC import PGMFC

#print(str(sys.argv))

mfcs = PGMFC(serial_number=4)
mfcs.monitor_start(span=1000)
time.sleep(0.5)

channel_pulse = mfcs[1]
channel_refuel = mfcs[2]

current_pulse = str(round(channel_pulse.get_pressure()[0],5))
#current_pulse = str(channel_pulse.get_pressure()[0])

current_refuel = str(round(channel_refuel.get_pressure()[0],5))
#print("in script",current_pulse)
#print("in script",current_refuel)

sys.stdout.write(','.join([current_pulse,current_refuel]))
#sys.stdout.write(current_pulse)
  


