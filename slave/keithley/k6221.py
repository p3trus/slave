#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.iec60488 import (IEC60488, Trigger, ObjectIdentification,
    StoredSetting)
from slave.types import Enum, Mapping


class Output(InstrumentBase):
    """A keithley 6221 output object.

    :param connection: A connection object.

    :ivar inner_shield: The inner shield connection, either 'output low' or
        'guard'.
    :ivar interlock: Represents the state of the interlock, either 'open' or
        'closed'.
    :ivar output_low: The output low connection, either 'float' or 'ground'.
    :ivar response: The output response mode, either 'fast' or 'slow'.

    """
    def __init__(self, connection):
        super(Output, self).__init__(connection)
        self.inner_shield = Command(
            'OUTP:ISH?',
            'OUTP:ISH',
            Mapping({'output low': 'OLOW', 'guard': 'GUAR'})
        )
        self.interlock = Command((
            'OUTP:INT:TRIP?',
            Enum('open', 'closed')
        ))
        self.output_low = Command(
            'OUTP:LTE?',
            'OUTP:LTE',
            Enum('float', 'ground')
        )
        self.response = Command(
            'OUTP:RESP?',
            'OUTP:RESP',
            Mapping({'fast': 'FAST', 'slow': 'SLOW'})
        )
        self.status = Command((
            'OUTP?',
            Enum('disabled', 'enabled')
        ))

    def enable(self):
        """Enables the output."""
        self.connection.write('OUTP 1')

    def disable(self):
        """Disables the output."""
        self.connection.write('OUTP 0')


class K6221(IEC60488, Trigger, ObjectIdentification, StoredSetting):
    """The Keithley model 6221 ac/dc current source reference.

    :param connection: A connection object.

    :ivar output: A keithley 6221 output object.

    """
    def __init__(self, connection):
        super(K6221, self).__init__(connection)
        self.output = Output(connection)

