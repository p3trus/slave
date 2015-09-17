#  -*- coding: utf-8 -*-
#
# Slave, (c) 2015, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.ics import ICS4807
from slave.transport import SimulatedTransport


def test_sr830():
    # Test if instantiation fails
    ICS4807(SimulatedTransport())
