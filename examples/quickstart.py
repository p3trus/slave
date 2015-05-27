#!/usr/bin/env python
import time

from slave.srs import SR830
from slave.transport import Visa


lockin = SR830(Visa('GPIB::08'))
lockin.frequency = 22.08
lockin.amplitude = 5.0
lockin.reserve = 'high'
for i in range(60):
    print lockin.x
    time.sleep(1)
