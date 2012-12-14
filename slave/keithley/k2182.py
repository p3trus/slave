#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488, Trigger, StoredSetting
from slave.types import Float


class K2182(IEC60488, StoredSetting, Trigger):
    """A keithley model 2182/A nanovoltmeter.

    :param connection: A connection object

    :ivar temperature: Performs a single-shot measurement of the temperature.

        ..note:: This Command is much slower than :meth:`.read`.

    :ivar voltage: Performs a single-shot measurement of the voltage.

        ..note:: This Command is much slower than :meth:`.read`.

    """
    def __init__(self, connection):
        super(K2182, self).__init__(connection)
        self.temperature = Command((':MEAS:TEMP?', Float))
        self.voltage = Command((':MEAS:VOLT?', Float))

    def abort(self):
        """Resets the trigger system, it put's the device in idle mode."""
        self.connection.write(':ABOR')

    def read(self):
        """A high level command to perform a singleshot measurement.

        It resets the trigger model(idle), initiates it, and fetches a new
        value.

        """
        return float(self.connection.ask(':READ?'))
