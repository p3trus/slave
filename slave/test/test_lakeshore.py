#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

from slave.lakeshore import LS340, LS350, LS370
from slave.transport import SimulatedTransport


def test_ls340():
    # Test if instantiation fails
    LS340(SimulatedTransport())

def test_ls350():
    # Test if instantiation fails
    LS350(SimulatedTransport())

def test_ls370():
    # Test if instantiation fails
    LS370(SimulatedTransport())
