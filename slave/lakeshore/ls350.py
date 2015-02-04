#  -*- coding: utf-8 -*-
#
# Slave, (c) 2015, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.driver import Command, Driver
from slave.iec60488 import IEC60488


class LS350(IEC60488):
    """Implements the lakeshore model 350 temperature controller.

    :ivar transport: A transport object.

    """
    def __init__(self, transport):
        super(LS350, self).__init__(transport)

    def clear_alarm(self):
        """Clears the alarm status for all inputs."""
        self._write('ALMRST')

    def reset_minmax(self):
        """Resets Min/Max functions for all inputs."""
        self._write('MNMXRST')

    def softcal(self, std, dest, serial, T1, U1, T2, U2, T3=None, U3=None):
        """Generates a softcal curve.

        :param std: The standard curve index used to calculate the softcal
            curve. Valid entries are 1, 6, 7.
        :param dest: The user curve index where the softcal curve is stored.
            Valid entries are 21-59.
        :param serial: The serial number of the new curve. A maximum of 10
            characters is allowed.
        :param T1: The first temperature point.
        :param U1: The first sensor units point.
        :param T2: The second temperature point.
        :param U2: The second sensor units point.
        :param T3: The third temperature point. Default: `None`.
        :param U3: The third sensor units point. Default: `None`.

        """
        args = [std, dest, serial, T1, U1, T2, U2]
        dtype = [Set(1, 6, 7), Integer(min=21, max=59), String(max=10), Float, Float, Float, Float]
        if (T3 is not None) and (U3 is not None):
            args.extend([T3, U3])
            dtype.extend([Float, Float])
        self._write(('SCAL', dtype), *args)

    def _factory_default(self):
        """Resets the device to factory defaults."""
        self._write(('DFLT', Integer), 99)
