#!/usr/bin/env python3

import can
import time
from can.interface import Bus
from can.io.asc import ASCReader

can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'vcan0'
can.rc['bitrate'] = 500000

bus = Bus()
readerr = ASCReader("/doc/docs/WUR/data/R4C/logs/Sprayer_AllData2022-06-30_18-44-38.asc")



i = 0.0
for elem in readerr:
    if (elem.arbitration_id == 0x09F8011C) or (elem.arbitration_id == 0x0CFE49F0):
        bus.send(elem)
