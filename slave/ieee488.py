#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The ieee488 module implements a IEEE Std 488.2-1992 compliant interface.

The minimal required interface is implemented by the IEEE488 class. Optional
command groups a provided by mixin classes. They should not be used on their
own.

"""
from slave.core import Command, InstrumentBase
from slave.types import Boolean, Register


STATUS_BYTE = {
    0: '0',
    1: '1',
    2: '2',
    3: '3',
    4: 'MAV',
    5: 'ESB',
    6: 'RQS',
    7: '7',
}

EVENT_STATUS_BYTE = {
    0: 'operation complete',
    1: 'request control',
    2: 'query error',
    3: 'device dependent error',
    4: 'execution error',
    5: 'command error',
    6: 'user request',
    7: 'power on',
}


def __construct_register(reg, default_reg):
    """Constructs a register dict."""
    if reg:
        x = dict((k, reg.get(k, d)) for k, d in default_reg.iteritems())
    else:
        x = dict(default_reg)
    # XXX invert dict because Register type uses inverted key, value pairs
    x = dict((v, k) for k, v in x.iteritems())
    return x


class IEEE488(InstrumentBase):
    """The IEEE488 class implements a IEEE Std 488.2-1992 compliant base class.

    :param connection: A connection object.
    :param esb: A dictionary mapping the 8 bit standard event status register.
        Integers in the range 0 to 7 are valid keys. If present they replace
        the default values.
    :param stb: A dictionary mapping the 8 bit status byte. Integers in the
        range 0 to 7 are valid keys. If present they replace the default
        values.
    :ivar event_status: A dictionary representing the 8 bit event status
        register.
    :ivar event_status_enable: A dictionary representing the 8 bit event status
        enable register.
    :ivar status: A dictonary representing the 8 bit status byte.
    :ivar status_enable: A dictionary representing the status enable register.

    A IEEE Std 488.2-1992 compliant interface must implement the following
    status reporting commands:

    * "*CLS" - See IEEE Std 488.2-1992 section 10.3
    * "*ESE" - See IEEE Std 488.2-1992 section 10.10
    * "*ESE?" - See IEEE Std 488.2-1992 section 10.11
    * "*ESR" - See IEEE Std 488.2-1992 section 10.12
    * "*SRE" - See IEEE Std 488.2-1992 section 10.34
    * "*SRE?" - See IEEE Std 488.2-1992 section 10.35
    * "*STB?" - See IEEE Std 488.2-1992 section 10.36

    In addition, the following internal operation common commands are required:

    * "*IDN?" - See IEEE Std 488.2-1992 section 10.14
    * "*RST" - See IEEE Std 488.2-1992 section 10.32
    * "*TST?" - See IEEE Std 488.2-1992 section 10.38

    Furthermore the following synchronisation commands are required:

    * "*OPC" - See IEEE Std 488.2-1992 section 10.18
    * "*OPC?" - See IEEE Std 488.2-1992 section 10.19
    * "*WAI" - See IEEE Std 488.2-1992 section 10.39

    """
    def __init__(self, connection, esb=None, stb=None):
        super(IEEE488, self).__init__(connection)
        esb = __construct_register(esb, EVENT_STATUS_BYTE)
        stb = __construct_register(stb, STATUS_BYTE)

        self.event_status = Command(('*ESR?', Register(esb)))
        self.event_status_enable = Command('*ESE?', '*ESE', Register(esb))
        self.status = Command(('*STB?', Register(stb)))
        self.operation_complete = Command(('*OPC?', Boolean))

    def clear(self):
        """Clears the status data structure."""
        self.connection.write('*CLS')

    def complete_operation(self):
        """Sets the operation complete bit high of the event status byte."""
        self.connection.write('*OPC')

    def reset(self):
        """Performs a device reset."""
        self.connection.write('*RST')

    def test(self):
        """Performs a internal self-test and returns an integer in the range
        -32767 to + 32767.
        """
        return int(self.connection.ask('*TST?'))

    def wait_to_continue(self):
        """Prevents the device from executing any further commands or queries
        until the no operation flag is `True`.

        .. note::

           In devices implementing only sequential commands, the no-operation
           flag is always True.

        """
        self.connection.write('*WAI')
