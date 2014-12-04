#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS.  Licensed under the GNU GPL.
"""The :mod:`slave.transport` module implements the lowest level abstraction
layer of the slave library.

The transport is responsible for sending and receiving raw bytes. It interfaces
with the hardware, but has no knowledge of the semantic meaning of the
transfered bytes.

The :class:`.Transport` class defines a common api used in higher abstraction
layers. Custom transports should subclass :class:`slave.Transport` and implement
the `__read__()` and `__write__()` methods.

The following transports are already available:

 * :class:`Serial` - A wrapper of the pyserial library
 * :class:`Socket` - A wrapper around the standard socket library.
 * :class:`LinuxGpib` - A wrapper of the linux-gpib library
 * :func:`visa` - A wrapper of the pyvisa library. (Supports pyvisa 1.4 - 1.5).

"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import socket
import threading

import ctypes as ct
import pkg_resources
from distutils.version import LooseVersion


class Transport(object):
    """A utility class to write and read data.

    The :class:`~.Transport` base class defines a common interface used by the
    `slave` library. Transports are intended to be used as context managers.

    Subclasses must implement `__read__` and `__write__`.

    """
    def __init__(self, max_bytes=1024, lock=None):
        self._buffer = bytearray()
        self._max_bytes = max_bytes
        self.lock = lock or threading.Lock()

    def read_bytes(self, num_bytes):
        """Reads at most `num_bytes`."""
        buffer_size = len(self._buffer)
        if buffer_size > num_bytes:
            # The buffer is larger than the requested amount of bytes.
            data, self._buffer = self._buffer[:num_bytes], self._buffer[num_bytes:]
        elif 0 < buffer_size <= num_bytes:
            # This might return less bytes than requested.
            data, self._buffer = self._buffer, bytearray()
        else:
            # Buffer is empty. Try to read `num_bytes` and call `read_bytes()`
            # again. This ensures that at most `num_bytes` are returned.
            self._buffer += self.__read__(num_bytes)
            return self.read_bytes(num_bytes)
        return data

    def read_exactly(self, num_bytes):
        """Reads exactly `num_bytes`"""
        buffer_size = len(self._buffer)
        if buffer_size > num_bytes:
            # The buffer is larger than the requested amount of bytes.
            data, self._buffer = self._buffer[:num_bytes], self._buffer[num_bytes:]
        elif buffer_size == num_bytes:
            # Buffer size matches requested number of bytes.
            data, self._buffer = self._buffer, bytearray()
        else:
            # Buffer is too small. Try to read `num_bytes` and call `read_bytes()`
            # again. This ensures that `num_bytes` are returned.
            self._buffer += self.__read__(num_bytes)
            return self.read_exactly(num_bytes)
        return data

    def read_until(self, delimiter):
        """Reads until the delimiter is found."""
        if delimiter in self._buffer:
            data, delimiter, self._buffer = self._buffer.partition(delimiter)
            return data
        else:
            self._buffer += self.__read__(self._max_bytes)
            return self.read_until(delimiter)

    def write(self, data):
        self.__write__(data)

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, type, value, traceback):
        self.lock.release()

    def __read__(self, num_bytes):
        raise NotImplementedError()

    def __write__(self, data):
        raise NotImplementedError()


class SimulatedTransport(object):
    """The SimulatedTransport.

    The SimulatedTransport does not have any functionallity. It servers as a
    sentinel value for the Command class to enable the simulation mode.
    """


class Socket(Transport):
    """A slave compatible adapter for pythons socket.socket class.

    :param address: The socket address a tuple of host string and port. E.g.
        ::

            from slave.signal_recovery import SR7230
            from slave.transport import Socket

            lockin = SR7230(Socket(address=('192.168.178.1', 50000)))

    :param alwaysopen: A boolean flag deciding wether the socket should be
        opened and closed for each use as a contextmanager or should be opened
        just once and kept open until closed explicitely. E.g.::

            from slave.transport import Socket

            transport = Socket(address=('192.168.178.1', 50000), alwaysopen=False)
            with transport:
                # connection is created
                transport.write(b'*IDN?')
                response = transport.read_until(b'\\n')
                # connection is closed again.

            transport = Socket(address=('192.168.178.1', 50000), alwaysopen=True)
            # connection is already opened.
            with transport:
                transport.write(b'*IDN?')
                response = transport.read_until(b'\\n')
                # connection is kept open.

    """
    def __init__(self, address, alwaysopen=True, *args, **kw):
        super(Socket, self).__init__()
        self.address = address
        self.alwaysopen = alwaysopen
        self._socket = None
        if self.alwaysopen:
            self.open()

    def __write__(self, data):
        self._socket.sendall(data)

    def __read__(self, num_bytes):
        return self._socket.recv(num_bytes)

    def open(self):
        if self._socket:
            raise ValueError('Socket is already open.')
        self._socket = socket.create_connection(self.address)

    def close(self):
        if not self._socket:
            raise ValueError("Can't close socket. Not opened yet.")
        self._socket.close()

    def __enter__(self):
        super(Socket, self).__enter__()
        if self._socket is None:
            self.open()

    def __exit__(self, type, value, tb):
        if not self.alwaysopen:
            self.close()
            self._socket = None
        super(Socket, self).__exit__(type, value, tb)

def visa(*args, **kw):
    """A pyvisa adapter factory function."""
    version = pkg_resources.get_distribution('pyvisa').version
    import visa

    if LooseVersion(version) < LooseVersion('1.5'):
        return Visa_1_4(visa.instrument(*args, **kw))
    else:
        rm = visa.RessourceManager()
        return Visa_1_5(rm.get_instrument(*args, **kw))


class Visa_1_4(Transport):
    """A pyvisa 1.4 adapter."""
    def __init__(self, instrument):
        super(Visa_1_4, self).__init__()
        self._instrument = instrument

    def __read__(self, num_bytes):
        return self._instrument.read_raw()

    def __write__(self, data):
        self._instrument.write(data)


class Visa_1_5(Transport):
    """A pyvisa 1.5 adapter."""
    def __init__(self, instrument):
        super(Visa_1_5, self).__init__()
        self._instrument = instrument

    def __read__(self, num_bytes):
        return self._instrument.read_raw(num_bytes)

    def __write__(self, data):
        self.instrument.write_raw(data)


class Serial(Transport):
    """A pyserial adapter."""
    def __init__(self, *args, **kw):
        super(Serial, self).__init__()
        # We import serial inside the class, because pyserial is only neccessary
        # if the serial adapter is used.
        import serial
        self._serial = serial.Serial(*args, **kw)

    def __write__(self, data):
        self._serial.write(data)

    def __read__(self, num_bytes):
        return self._serial.read(num_bytes)


class LinuxGpib(Transport):
    """A linuxgpib adapter."""
    def __init__(self, primary=0, secondary=0, board=0, timeout=13, send_eoi=1,
                 eos=0):
        super(LinuxGpib, self).__init__()
        lib = ctypes.util.find_library('gpib')
        self._lib = ct.CDLL(lib)
        self._device = self._lib.ibdev(
            ct.c_int(board),
            ct.c_int(primary),
            ct.c_int(secondary),
            ct.c_int(timeout),
            ct.c_int(send_eoi),
            ct.c_int(eos)
        )

    def close(self):
        """Closes the gpib transport."""
        self._lib.ibonl(self._device, ct.c_int(0))

    def __write__(self, data):
        self._lib.ibwrt(self._device, ct.c_char_p(data), ct.c_long(len(data)))

    def __read__(self, num_bytes):
        buffer = ct.create_string_buffer(bytes)
        self._lib.ibrd(self._device, ct.byref(buffer), ct.c_long(bytes))
        return buffer.value

    def trigger(self):
        """Triggers the device.

        The trigger method sens a GET(group execute trigger) command byte to
        the device.
        """
        self._lib.ibtrg(self._device)  # TODO check error conditions.
