#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase

class SR7225(InstrumentBase):
    """Represents a Signal Recovery SR7225 lock-in amplifier."""
    def __init__(self, connection):
        super(SR7225, self).__init__(connection)
        #: Set or query the input