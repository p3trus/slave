#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, Mapping, String


class Range(InstrumentBase):
    """Represents a MPS4G current range.

    :param connection: A connection object.
    :param idx: The current range index. Valid values are 0, 1, 2, 3, 4.
    :ivar limit: The upper limit of the current range.
    :ivar rate: The sweep rate of this current range.

    """
    def __init__(self, connection, idx):
        super(Range, self).__init__(connection)
        self.idx = idx = int(idx)
        if not idx in range(0, 5):
            raise ValueError('Invalid range index.'
                             ' Must be one of {0}'.format(range(0, 5)))
        self.limit = Command('RANGE? {0}'.format(idx),
                             'RANGE {0} '.format(idx),
                             Float)
        self.rate = Command('RATE? {0}'.format(idx),
                            'RATE {0}'.format(idx),
                            Float)


class MPS4G(InstrumentBase):
    """Represents the Cryomagnetics, inc. 4G Magnet Power Supply.

    :param connection: A connection object.
    :ivar error: The error response mode of the usb interface.
    :ivar output_current: The power supply output current.
    :ivar lower_limit: The lower current limit. Queriing returns a value, unit
        tuple. While setting the lower current limit, the unit is omited. The
        value must be supplied in the configured units (ampere, kilo gauss).
    :ivar name: The name of the currently selected coil. The length of the name
        is in the range of 0 to 16 characters.
    :ivar switch_heater: The state of the persistent switch heater. If `True`
        the heater is switched on and off otherwise.

    """
    def __init__(self, connection):
        super(MPS4G, self).__init__(connection)
        self.error = Command('ERROR?', 'ERROR', Boolean)
        self.output_current = Command(('IOUT?', [Float, String]))
        self.lower_limit = Command(('LLIM?', [Float, String],),
                                   ('LLIM', Float))
        self.name = Command('NAME?', 'NAME', String)
        self.switch_heater = Command('PSHTR?', 'PSHTR',
                                     Mapping({True: 'ON', False: 'OFF'}))
        for idx in range(0, 5):
            setattr(self, 'range{0}'.format(idx), Range(connection, idx))

    def local(self):
        """Sets the front panel in local mode."""
        self.connection.write('LOCAL')

    def remote(self):
        """Sets the front panel in remote mode."""
        self.connection.write('REMOTE')

    def quench_reset(self):
        """Resets the quench condition."""
        self.connection.write('QRESET')

    def locked(self):
        """Sets the front panel in locked remote mode."""
        self.connection.write('RWLOCK')
