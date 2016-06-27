#  -*- coding: utf-8 -*-
#
# Slave, (c) 2016, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

from slave.tdk_lambda import Genesys
from slave.transport import SimulatedTransport


def test_genesys():
    # Test if instantiation fails
    Genesys(SimulatedTransport())