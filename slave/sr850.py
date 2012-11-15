#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.types import Enum, Float


class SR850(InstrumentBase):
    """A Stanford Research SR850 lock-in amplifier.

    :param connection: A connection object.

    .. rubric:: Reference and Phase Commands

    :ivar phase: The reference phase shift. A float between -360. and
        719.999 in degree.
    :ivar reference_mode: The reference source mode, either 'internal', 'sweep'
        or 'external'.
    :ivar frequency: The reference frequency in Hz. A float between 0.001 and
        102000.

        .. note::

            For harmonics greater than 1, the sr850 limits the max frequency to
            102kHz / harmonic.

    :ivar frequency_sweep: The type of the frequency sweep, either 'linear' or
        'log', when in 'internal' reference_mode.

    """
    def __init__(self, connection):
        super(SR850, self).__init__(connection)
        self.phase = Command('PHAS?', 'PHAS', Float(min=-360., max=719.999)
        )
        self.reference_mode = Command(
            'FMOD?',
            'FMOD',
            Enum('internal', 'sweep', 'external')
        )
        self.frequency = Command('FREQ?', 'FREQ', Float(min=0.001, max=102000))
        self.frequency_sweep = Command('SWPT?', 'SWPT', Enum('linear', 'log'))
