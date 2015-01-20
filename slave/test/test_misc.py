#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import os
import pytest
from slave.misc import (index, ForwardSequence, range_to_numeric, AutoRange,
                        Measurement, LockInMeasurement)


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


def test_sens_to_numeric():
    ranges = ['1 nOhm', '2 uOhm', '5 mOhm', '1 Ohm']
    assert range_to_numeric(ranges) == [1e-9, 2e-6, 5e-3, 1.]


class TestAutoRange(object):
    def test_with_numeric_range(self):
        auto = AutoRange([1e-6, 1e-3, 1.], scale=1., buffer_len=3)
        assert auto.range(.9e-6) == 1e-6 # mean is .9e-6
        assert auto.range(.9e-6) == 1e-6 # mean is .9e-6
        assert auto.range(1.2e-6) == 1e-3 # mean is 1e-6; sens should switch.

    def test_with_numeric_range_and_negative_values(self):
        auto = AutoRange([1e-6, 1e-3, 1.], scale=1., buffer_len=3)
        assert auto.range(.9e-6) == 1e-6 # mean is .9e-6
        assert auto.range(-.9e-6) == 1e-6 # mean of magnitude is still .9e-6
        assert auto.range(-1.2e-6) == 1e-3 # mean is 1e-6; sens should switch.

    def test_with_out_of_range_value(self):
        auto = AutoRange([1e-6, 1e-3, 1.], scale=1.)
        assert auto.range(1.1) == 1.

    def test_with_named_ranges(self):
        auto = AutoRange([1e-6, 1e-3, 1.], ['1 uV', '1 mV', '1 V'],
                         scale=1., buffer_len=3)
        assert auto.range(.9e-6) == '1 uV' # mean is .9e-6
        assert auto.range(-.9e-6) == '1 uV' # mean of magnitude is still .9e-6
        assert auto.range(-1.2e-6) == '1 mV' # mean is 1e-6; sens should switch.

    def test_with_unequal_length_of_ranges_and_names(self):
        with pytest.raises(ValueError):
            AutoRange([1e-6, 1e-3, 1], names=['1 mV', '1 V'])


class TestMeasurement(object):
    def test_calling(self, tmpdir):
        path = tmpdir.join('data.csv')
        params = [lambda: 1, lambda: 2]
        with Measurement(str(path), params) as measure:
            measure()
        assert path.read() == '1,2\n'

    def test_calling_with_names(self, tmpdir):
        path = tmpdir.join('data.csv')
        params = [lambda: 1, lambda: 2]
        names = ['A', 'B']
        with Measurement(str(path), params, names) as measure:
            measure()
        assert path.read() == 'A,B\n1,2\n'

    def test_if_filehandle_is_closed_on_error(self, tmpdir):
        path = tmpdir.join('data.csv')
        params = [lambda: 1, lambda: 2]
        try:
            with Measurement(str(path), params) as measure:
                measure()
                raise ValueError()
        except ValueError:
            pass
        finally:
            assert measure._file.closed


class MockLockIn(object):
    def __init__(self, x, y, sensitivities):
        self.x = x
        self.y = y
        self.SENSITIVITY = sensitivities
        self.sensitivity = self.SENSITIVITY[0]


class TestLockInMeasurement(object):
    def test_without_autorange(self, tmpdir):
        path = tmpdir.join('data.csv')
        SENSITIVITY = [1e-6, 1e-3, 1.]
        lockins = [MockLockIn(1.3, 1.4, SENSITIVITY)]
        env_params = [lambda: 'env']
        names = ['X1', 'Y1', 'ENV']
        with LockInMeasurement(str(path), lockins, env_params, names, autorange=False) as measure:
            measure()
        assert path.read() == 'X1,Y1,ENV\n1.3,1.4,env\n'
        # Sensitivity should not be changed.
        assert lockins[0].sensitivity == 1e-6

    def test_with_string_sensitivities(self, tmpdir):
        path = tmpdir.join('data.csv')
        SENSITIVITY = ['1 uV', '1 mV', '1 V']
        lockins = [MockLockIn(1.3, 1.4, SENSITIVITY)]
        env_params = [lambda: 'env']
        names = ['X1', 'Y1', 'ENV']
        with LockInMeasurement(str(path), lockins, env_params, names, autorange=True) as measure:
            measure()
        assert path.read() == 'X1,Y1,ENV\n1.3,1.4,env\n'
        assert lockins[0].sensitivity == '1 V'

    def test_with_numeric_sensitivities(self, tmpdir):
        path = tmpdir.join('data.csv')
        SENSITIVITY = [1e-6, 1e-3, 1.]
        lockins = [MockLockIn(1.3, 1.4, SENSITIVITY)]
        env_params = [lambda: 'env']
        names = ['X1', 'Y1', 'ENV']
        with LockInMeasurement(str(path), lockins, env_params, names, autorange=True) as measure:
            measure()
        assert path.read() == 'X1,Y1,ENV\n1.3,1.4,env\n'
        assert lockins[0].sensitivity == 1.
