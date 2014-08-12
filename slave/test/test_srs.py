#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.srs import SR830, SR850
from slave.transport import SimulatedTransport


def test_sr830():
    # Test if instantiation fails
    SR830(SimulatedTransport())


def test_sr850():
    # Test if instantiation fails
    SR850(SimulatedTransport())
