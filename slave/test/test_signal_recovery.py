#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.signal_recovery import SR7225
from slave.transport import SimulatedTransport


def test_sr7225():
    # Test if instantiation fails
    SR7225(SimulatedTransport())
