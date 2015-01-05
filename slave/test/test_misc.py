#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import pytest
from slave.misc import index, ForwardSequence


class TestIndex(object):
    def test_with_index_inrange(self):
        assert index(2, 10) == 2

    def test_with_negative_index(self):
        assert index(-2, 10) == 8

    def test_with_out_of_range_index(self):
        with pytest.raises(IndexError):
            assert index(11, 10)


class TestForwardSequence(object):
    def test_getter_forwarding_with_single_item(self):
        getter = lambda item:  item**2
        sequence = ForwardSequence([1, 2, 3], getter)
        assert sequence[1] == 4

    def test_getter_forwarding_with_slice(self):
        getter = lambda item:  item**2
        sequence = ForwardSequence([1, 2, 3], getter)
        assert sequence[0:2] == (1, 4)

    def test_setter_with_single_item(self):
        getter = lambda item: item # Identity
        setter = lambda item, value: item.__setitem__(0, value)
        sequence = ForwardSequence([[0], [1], [2]], getter, setter)
        sequence[1] = 3
        assert sequence[1] == [3]

    def test_setter_with_slice(self):
        getter = lambda item: item # Identity
        setter = lambda item, value: item.__setitem__(0, value)
        sequence = ForwardSequence([[0], [1], [2]], getter, setter)
        sequence[0:2] = 3
        assert sequence[0:2] == ([3], [3])

    def test_setting_without_setter(self):
        getter = lambda item: item
        sequence = ForwardSequence([1, 2, 3], getter)
        with pytest.raises(RuntimeError):
            sequence[0] = 1
