#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, String


class MPS4G(InstrumentBase):
    """Represents the Cryomagnetics, inc. 4G Magnet Power Supply.

    :param connection: A connection object.
    :ivar error: The error response mode of the usb interface.
    :ivar output_current: The power supply output current.
    :ivar lower_limit: The lower current limit. Queriing returns a value, unit
        tuple. While setting the lower current limit, the unit is omited. The
        value must be supplied in the configured units (ampere, kilo gauss).

    """
    def __init__(self, connection):
        super(MPS4G, self).__init__(connection)
        self.error = Command('ERROR?', 'ERROR', Boolean)
        self.output_current = Command(('IOUT?', [Float, String]))
        self.lower_limit = Command(('LLIM?', [Float, String],),
                                   ('LLIM', Float))

    def local(self):
        """Sets the front panel in local mode."""
        self.connection.write('LOCAL')

    def remote(self):
        """Sets the front panel in remote mode."""
        self.connection.write('REMOTE')

    def locked(self):
        """Sets the front panel in locked remote mode."""
        self.connection.write('RWLOCK')
