Slave
=====

The main goal of slave is to make it easier to communicate with scientific
instruments. Slave tries to ease the implementation of new instruments and
comes with a variety of ready-to-use implementations. A simple measurement
script, using [pyvisa][] for the GPIB connection, might look like

```python
import time

import visa
from slave.sr830 import SR830

# construct and initialize a SR830 instrument with a GPIB connection on 
# channel 8.
lockin = SR830(visa.instrument('GPIB::08'))
lockin.reserve = 'high' # Set the dynamic reserve to `high`.
lockin.time_constant = 3 # Set the time constant to 3s.

# measure the x value 60 times and wait 1s between each measurement.
for i in range(60):
    print lockin.x
    time.sleep(1) # delay for 1s.
```

Requirements
------------
 * Python 2.6 or higher

Licensing
---------

You should have received a copy of the [GNU General Public License][] along 
with Slave; see the file COPYING.
  [GNU General Public License]: http://www.gnu.org/licenses/gpl.html
  [pyvisa]: http://pyvisa.sourceforge.net/
