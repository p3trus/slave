#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import pytest
from slave.misc import index


class TestIndex(object):
    def test_with_index_inrange(self):
        assert index(2, 10) == 2

    def test_with_negative_index(self):
        assert index(-2, 10) == 8

    def test_with_out_of_range_index(self):
        with pytest.raises(IndexError):
            assert index(11, 10)
