#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.driver import Command, CommandSequence, Driver
from slave.iec60488 import IEC60488
from slave.types import Boolean, Enum, Float, Integer, Set, String


class Relay(Driver):
    """An ICS4807 relay.

    :param transport: A transport object.
    :param protocol: A protocol object.
    :param idx: An integer representing the relay index.

    :ivar status:

    """
    def __init__(self, transport, protocol, idx):
        super(Relay, self).__init__(transport, protocol)
        self.idx = idx = int(idx)
        self.status = Command(('ROUT:CLOS:STAT? {0}'.format(self.idx), String))

    def open(self):
        """Open's the relay."""
        self._write(('ROUT:OPEN', Integer), self.idx)

    def close(self):
        """Closes the relay."""
        self._write(('ROUT:CLOSE', Integer), self.idx)


class Input(Driver):
    """The analog input subsystem.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar average: The averaging value of the input channel. Valid entries are
        1 to 250.
    :ivar polarity: The polarity of the analog input, either 'unipolar' or
        'bipolar'.
    :ivar range: The A/D input range in volt. Valid entries are 5 or 10.
    :ivar voltage. The voltage of the analog input.

    """
    def __init__(self, transport, protocol, idx):
        super(Input, self).__init__(transport, protocol)
        self.idx = idx = int(idx)
        self.average = Command(
            'MEAS:AVER? {0}'.format(idx),
            'MEAS:AVER {0},'.format(idx),
            Integer(min=1, max=250)
        )
        self.polarity = Command(
            'MEAS:POL? {0}'.format(idx),
            'MEAS:POL {0},'.format(idx),
            Enum('unipolar', 'bipolar', start=1)
        )
        # Due to a bug in the isc4807 firmware, a query returns 10.0001 instead
        # of 10. This leads to problems when a Set type is used as query and
        # write type.
        self.range = Command(
            ('MEAS:RANG? {0}'.format(idx), Integer),
            ('MEAS:RANG {0},'.format(idx), Set(5, 10))
        )
        self.voltage = Command(('MEAS:VOLT? {0}'.format(idx), Float))


class GPIB(Driver):
    """The gpib subsystem.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar address: The gpib address, an integer between 0 and 30.
    :ivar external: The state of the external gpib address selector.

    """
    def __init__(self, transport, protocol):
        super(GPIB, self).__init__(transport, protocol)
        self.address = Command(
            'SYST:COMM:GPIB:ADDR?',
            'SYST:COMM:GPIB:ADDR',
            Integer(min=0, max=30)
        )
        self.external = Command(
            'SYST:COMM:GPIB:ADDR:EXT?',
            'SYST:COMM:GPIB:ADDR:EXT',
            Boolean
        )


class ICS4807(IEC60488):
    """ICS Electronics Model 4807 GPIB-DAQ card instrument class.

    .. warning:: The Implementation is not complete yet!

    :param transport: A transport object.

    :ivar gpib: The gpib subsystem.
    :ivar temperature: A sequence with four temperatures.
    :ivar input: A tuple holding six :class:`Input` instances.
    :ivar relay: A tuple holding six :class:`Relay` instances.

    """
    def __init__(self, transport):
        super(ICS4807, self).__init__(transport)
        self.gpib = GPIB(self._transport, self._protocol)
        self.input = tuple(
            Input(self._transport, self._protocol, i) for i in range(1, 7)
        )
        self.relay = tuple(
            Relay(self._transport, self._protocol, i) for i in range(1, 7)
        )
        self.temperature = CommandSequence(
            self._transport,
            self._protocol,
            [Command((':MEAS:TEMP? {}'.format(i), Float)) for i in range(1, 5)]
        )

    def abort(self):
        """Disables the trigger function."""
        self._write('ABORT')
