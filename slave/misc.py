#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import csv
import collections
import threading
import logging


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


class Measurement(object):
    """Small measurement helper class.

    For each call to :meth:`.__call__` a comma separated row, representing the
    return values for each callable item in measurables is written to the file
    specified by path.

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
            self._file = open(self._path, 'wb')
            self._writer = csv.writer(self._file)
            if self._names:
                self._writer.writerow(self._names)

    def close(self):
        if self._file:
            self._file.close()
            self._file = None
            self._writer = None

    def __call__(self):
        self._writer.writerow([str(x()) for x in self._measurables])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
