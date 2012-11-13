#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.types import Enum, Float


class SR850(InstrumentBase):
    """A Stanford Research SR850 lock-in amplifier.

    :param connection: A connection object.

    .. rubric:: Reference and Phase Commands

    :ivar reference_phase: The reference phase shift. A float between -360. and
        719.999 in degree.
    :ivar reference_source: The reference source, either 'internal', 'sweep' or
        'external'.

    """
    def __init__(self, connection):
        super(SR850, self).__init__(connection)
        self.refrence_phase = Command(
            'PHAS?',
            'PHAS',
            Float(min=-360., max=719.999)
        )
        self.reference_source = Command(
            'FMOD?',
            'FMOD',
            Enum('internal', 'sweep', 'external')
        )
