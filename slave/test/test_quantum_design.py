
#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.quantum_design import PPMS
from slave.transport import SimulatedTransport


def test_ppms():
    # Test if instantiation fails
    PPMS(SimulatedTransport(), max_field=10e4)
