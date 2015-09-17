#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.cryomagnetics import MPS4G
from slave.transport import SimulatedTransport


def test_mps4g():
    # Test if instantiation fails
    MPS4G(SimulatedTransport())
