#!/usr/bin/env python
import time

import visa
from slave.srs import SR830

lockin = SR830(visa.instrument('GPIB::08'))
lockin.frequency = 22.08
lockin.amplitude = 5.0
lockin.reserve = 'high'
for i in xrange(60):
    print lockin.x
    time.sleep(1)
