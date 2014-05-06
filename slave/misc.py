#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

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
            return map(self._get, self._sequence[item])
        return self._get(self._sequence[item])

    def __setitem__(self, item, value):
        if not self._set:
            raise RuntimeError('Item not settable')
        if isinstance(item, slice):
            for i in self._sequence[item]:
                self._set(i, value)
        return self._set(item, value)


class LockedTransport(object):
    """Helper class wrapping a transport object and to add thread locking.

    :param transport: The wrapped transport object.
    :param lock: Can be used to inject a custom thread lock, default: `None`.

    The LockedTransport wrapps a normal transport object and forwards the
    calls to :meth:`.ask` and :meth:`.write` member functions to the transport
    object. A thread lock is acquired before, and released after the call to
    the internal transport object.

    """
    lock = threading.Lock()

    def __init__(self, transport, lock=None):
        self._transport = transport
        self._lock = lock or LockedTransport.lock

    def ask(self, value):
        with self._lock:
            return self._transport.ask(value)

    def write(self, value):
        with self._lock:
            self._transport.write(value)


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
