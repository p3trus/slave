#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import threading


class LockedConnection(object):
    """Helper class wrapping a connection object and to add thread locking.

    :param connection: The wrapped connection object.
    :param lock: Can be used to inject a custom thread lock, default: `None`.

    The LockedConnection wrapps a normal connection object and forwards the
    calls to :meth:`.ask` and :meth:`.write` member functions to the connection
    object. A thread lock is acquired before, and released after the call to
    the internal connection object.

    """
    lock = threading.Lock()

    def __init__(self, connection, lock=None):
        self._connection = connection
        self._lock = lock or LockedConnection.lock

    def ask(self, value):
        with self._lock:
            return self._connection.ask(value)

    def write(self, value):
        with self._lock:
            self._connection.write(value)

