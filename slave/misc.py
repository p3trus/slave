#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import future.utils
import csv
import collections
import threading
import logging
import os.path
import io


SI_PREFIX = {
    'y': 1e-24,  # yocto
    'z': 1e-21,  # zepto
    'a': 1e-18,  # atto
    'f': 1e-15,  # femto
    'p': 1e-12,  # pico
    'n': 1e-9,   # nano
    'u': 1e-6,   # micro
    'm': 1e-3,   # mili
    'c': 1e-2,   # centi
    'd': 1e-1,   # deci
    '': 1.,
    'k': 1e3,    # kilo
    'M': 1e6,    # mega
    'G': 1e9,    # giga
    'T': 1e12,   # tera
    'P': 1e15,   # peta
    'E': 1e18,   # exa
    'Z': 1e21,   # zetta
    'Y': 1e24,   # yotta
}


class ForwardSequence(collections.Sequence):
    """Sequence forwarding item access and write operations.

    :param iterable: An iterable of items to be stored.
    :param get: A callable used on item access, receiving the item.
        It's result is returned.
    :param set: A callable receiving the item and a value on item set
        operations.

    Implements a immutable sequence, which forwards item access and write
    operations to the stored items.

    """
    def __init__(self, iterable, get, set=None):
        super(ForwardSequence, self).__init__()
        self._sequence = tuple(iterable)
        self._get = get
        self._set = set

    def __len__(self):
        return len(self._sequence)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return tuple(map(self._get, self._sequence[item]))
        return self._get(self._sequence[item])

    def __setitem__(self, item, value):
        if not self._set:
            raise RuntimeError('Item not settable')
        if isinstance(item, slice):
            for i in self._sequence[item]:
                self._set(i, value)
        else:
            self._set(self._sequence[item], value)


def index(index, length):
    """Generates an index.

    :param index: The index, can be positive or negative.
    :param length: The length of the sequence to index.

    :raises: IndexError

    Negative indices are typically used to index a sequence in reverse order.
    But to use them, the indexed object must convert them to the correct,
    positive index. This function can be used to do this.

    """
    if index < 0:
        index += length
    if 0 <= index < length:
        return index
    raise IndexError()


def range_to_numeric(ranges):
    """Converts a sequence of string ranges to a sequence of floats.

    E.g.::

        >>> range_to_numeric(['1 uV', '2 mV', '1 V'])
        [1E-6, 0.002, 1.0]

    """
    values, units = zip(*(r.split() for r in ranges))
    # Detect common unit.
    unit = os.path.commonprefix([u[::-1] for u in units])

    # Strip unit to get just the SI prefix.
    prefixes = (u[:-len(unit)] for u in units)

    # Convert string value and scale with prefix.
    values = [float(v) * SI_PREFIX[p] for v, p in zip(values, prefixes)]
    return values


class AutoRange(object):
    """Estimates an appropriate sensitivity range.

    A mean value is calculated from the magnitude of the value and previous
    ones(the number depends on the `buffer_len`). The best range is chosen
    as the largest range, where the mean is smaller than `scale * range`. If
    the mean is larger than any range, the largest range is returned.

    :param range: A sequence of sensitivity ranges.
    :param names: An optional sequence of names corresponding to the ranges. If
        given, :meth:`AutoRange.range` returns the name instead of the range.
    :param scale: An optional parameter scaling the ranges.
    :param buffer_len: Defines the buffer length used to calculate the mean
        value in :meth:`~.AutoRange.range`.

    """
    def __init__(self, ranges, names=None, scale=1., buffer_len=10):
        if names:
            if len(ranges) != len(names):
                raise ValueError('Unequal length of names and ranges.')
            self._mapping = {r:k for r, k in zip(ranges, names)}
        else:
            self._mapping = None
        self.ranges = sorted(ranges)
        self.scale = scale
        self._buffer = collections.deque(maxlen=buffer_len)

    def range(self, value):
        """Estimates an appropriate sensitivity range."""
        self._buffer.append(abs(value))
        mean = sum(self._buffer) / len(self._buffer)
        estimate = next(
            (r for r in self.ranges if mean < self.scale * r),
            self.ranges[-1]
        )
        if self._mapping:
            return self._mapping[estimate]
        else:
            return estimate


class Measurement(object):
    """Small measurement helper class.

    For each call to :meth:`.__call__` a comma separated row, representing the
    return values for each callable item in measurables is written to the file
    specified by path.
    ::

        >>> from slave.misc import Measurement
        >>> names = ['A', 'B']
        >>> measurables = [lambda: 'a', lambda: 'b']
        >>> with Measurement('test.csv', measurables, names) as m:
        ...     m()
        ...     m()
        ...
        >>> with open('test.csv', 'r') as f:
        ...     print(f.readlines())
        ...
        ['A,B\n', 'a,b\n', 'a,b\n']

    :param path: The file path.
    :param measurables: A sequence of callables.
    :param names: An optional sequence of names, used to create the csv header.
        The number of names and measurables must be equal.

    """
    def __init__(self, path, measurables, names=None):
        self._path = path
        self._measurables = measurables
        self._names = names
        self._file = None
        self._writer = None
        self.open()

    def open(self):
        if not self._file:
            if future.utils.PY3:
                self._file = open(self._path, 'w', newline='')
            else:
                self._file = open(self._path, 'wb')
            self._writer = csv.writer(self._file, lineterminator='\n')
            if self._names:
                self._writer.writerow(self._names)

    def close(self):
        if self._file:
            self._file.close()
            self._writer = None

    def __call__(self):
        self._writer.writerow([str(x()) for x in self._measurables])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class LockInMeasurement(Measurement):
    """A measurement helper optimized for lock-in amplifier measurements.

    E.g.::

        ppms = PPMS(visa('GPIB::12'))
        lia1 = SR7230(socket(address=('192.168.178.1', 50000)))
        lia2 = SR7230(socket(address=('192.168.178.2', 50000)))

        ppms.set_field(10000, 100)
        ppms.set_temperature(2, 10)

        env_params = [
            lambda: ppms.temperature,
            lambda: ppms.field,
        ]
        names = ['x1', 'y1', 'x2', 'y2', 'temperature', 'field']

        with LockInMeasurement('data.csv', [lia1, lia2], env_params, names) as measure:
            ppms.scan_temperature(measure, 300, 1)

    :param path: The filepath.
    :param lockins: A sequence of lockin drivers. A lockin driver must have a
        readable `x` and `y` attribute to get the data. Additionally a readable
        `SENSITIVITY` attribute and a read and writeable `sensitivity`
        attribute are mandatory.
    :param measurables: An optional sequence of functions.
    :param names: A sequence of names used to generate the csv file header.
    :param bool autorange: Enables/disables auto ranging.

    """
    def __init__(self, path, lockins, measurables=None, names=None, autorange=True):
        super(LockInMeasurement, self).__init__(path, measurables or [], names=names)
        self._lockins = lockins
        self._autorange = []
        if autorange:
            for lia in lockins:
                ranges, names = lia.SENSITIVITY, None
                # Check if sensitivity ranges are already numeric or strings.
                if isinstance(ranges[0], str):
                    ranges, names = range_to_numeric(ranges), ranges
                self._autorange.append(AutoRange(ranges, names))

    def __call__(self):
        lockin_xy = [(lia.x, lia.y) for lia in self._lockins]
        optional_data = [m() for m in self._measurables]
        # If autoranging is enabled,
        if self._autorange:
            for lia, auto, (x, y) in zip(self._lockins, self._autorange, lockin_xy):
                sens = auto.range(max(x, y))
                if lia.sensitivity != sens:
                    lia.sensitivity = sens

        # Flatten lockin data and concatenate with optional data.
        data = [d for xy in lockin_xy for d in xy] + optional_data
        self._writer.writerow(data)
