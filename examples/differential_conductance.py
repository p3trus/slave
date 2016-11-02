"""This example shows a differential conductance measurement.

In this example we're showing how to use the Keithley :class:`~.K6221`
currentsource and :class:`~.K2182` nanovoltmeter combo to perform a differential
conductance measurement.

"""
# To use the ethernet connection instead of the GPIB interface import Socket
# instead of Visa
from slave.transport import Visa
# We don't need to import the nanovoltmeter driver, the K6221 does this for us.
from slave.keithley import K6221


current_source = K6221(Visa('GPIB::22'))
# Note: The nanovoltmeter has to be connected to the K6221 with the serial and
# trigger link cable.
nanovolt_meter = current_source.system.communicate.serial.k2182

# Now configure the nanovoltmeter.
nanovolt_meter.sense.auto_range = True
nanovolt_meter.sense.nplc = 1

# Then configure the current source
current_source.reset()
current_source.source.differential_conductance.start = 0     # start at 0 A
current_source.source.differential_conductance.step = 1e-6   # 10 uA steps
current_source.source.differential_conductance.stop = 50e-6  # stop at 50 uA
current_source.source.differential_conductance.delta = 20e-6 # 20 uA delta
current_source.source.differential_conductance.delay = 1e-3  # 1 ms delay
current_source.source.differential_conductance.compliance_abort = True
current_source.trace.points = 6
current_source.source.differential_conductance.arm()
current_source.initiate()

# Finally we read back the measurements
data = current_source.trace.data[:]