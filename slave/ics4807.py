#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488
from slave.types import Boolean, Enum, Float, Integer, Set, String


class Relay(InstrumentBase):
    """An ICS4807 relay.

    :param connection: A connection object.
    :param idx: An integer representing the relay index.

    """
    def __init__(self, connection, idx):
        super(Relay, self).__init__(connection)
        self.idx = idx = int(idx)
        self.status = Command(('ROUT:CLOS:STAT? {0}'.format(self.idx), String))

    def open(self):
        """Open's the relay."""
        self.connection.write('ROUT:OPEN {0}'.format(self.idx))

    def close(self):
        """Closes the relay."""
        self.connection.write('ROUT:CLOSE {0}'.format(self.idx))


class Input(InstrumentBase):
    """The analog input subsystem.

    :param connection: A connection object.

    :ivar average: The averaging value of the input channel. Valid entries are
        1 to 250.
    :ivar polarity: The polarity of the analog input, either 'unipolar' or
        'bipolar'.
    :ivar range: The A/D input range in volt. Valid entries are 5 or 10.
    :ivar voltage. The voltage of the analog input.

    """
    def __init__(self, connection, idx):
        super(Input, self).__init__(connection)
        self.idx = idx = int(idx)
        self.average = Command('MEAS:AVER? {0}'.format(idx),
                               'MEAS:AVER {0},'.format(idx),
                               Integer(min=1, max=250))
        self.polarity = Command('MEAS:POL? {0}'.format(idx),
                                'MEAS:POL {0},'.format(idx),
                                Enum('unipolar', 'bipolar', start=1))
        # Due to a bug in the isc4807 firmware, a query returns 10.0001 instead
        # of 10. This leads to problems when a Set type is used as query and
        # write type.
        self.range = Command(
            ('MEAS:RANG? {0}'.format(idx), Integer),
            ('MEAS:RANG {0},'.format(idx), Set(5, 10))
        )
        self.voltage = Command(('MEAS:VOLT? {0}'.format(idx), Float))


class GPIB(InstrumentBase):
    """The gpib subsystem.

    :param connection: A connection object.

    :ivar address: The gpib address, an integer between 0 and 30.
    :ivar external: The state of the external gpib address selector.

    """
    def __init__(self, connection):
        super(GPIB, self).__init__(connection)
        self.address = Command('SYST:COMM:GPIB:ADDR?',
                               'SYST:COMM:GPIB:ADDR',
                               Integer(min=0, max=30))
        self.external = Command('SYST:COMM:GPIB:ADDR:EXT?',
                                'SYST:COMM:GPIB:ADDR:EXT',
                                Boolean)


class ICS4807(IEC60488):
    """
    ICS Electronics Model 4807 GPIB-DAQ card instrument class.

    :param connection: A connection object.

    :ivar gpib: The gpib subsystem.
    :ivar temperature1: The value of the first temperature channel.
    :ivar temperature2: The value of the second temperature channel.
    :ivar temperature3: The value of the third temperature channel.
    :ivar temperature4: The value of the fourth temperature channel.
    :ivar input: A tuple holding six Input instances.

    """
    def __init__(self, connection):
        super(ICS4807, self).__init__(connection)
        self.gpib = GPIB(connection)
        self.input = tuple(Input(connection, i) for i in range(1, 7))
        # relays
        for i in range(1, 7):
            setattr(self, 'relay{0}'.format(i), Relay(connection, i))
        # temperature
        # TODO Use tuple instead of four instance vars.
        for i in range(1, 5):
            cmd = Command(('MEAS:TEMP? {0}'.format(i)))
			# TODO use command sequence.
            setattr(self, 'temperature{0}'.format(i), cmd)

    def abort(self):
        """Disables the trigger function."""
        self.connection.write('ABORT')
