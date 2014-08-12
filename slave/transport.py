#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import socket
import ctypes as ct


class Transport(object):
    """A utility class to write and read data.

    The :class:`~.Transport`base class defines a common interface used by the
    `slave` library. Subclasses must implement `__read__` and `__write__`.

    """
    def __init__(self):
        self._buffer = bytearray()
        self._max_bytes = 1024

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

    E.g.::

        from slave.signal_recovery import SR7230
        from slave.transport import Socket

        lockin = SR7230(Socket(address=('192.168.178.1', 50000)))

    """
    def __init__(self, address, *args, **kw):
        super(Socket, self).__init__()
        self._socket = socket.socket(*args, **kw)
        self._socket.connect(address)

    def __write__(self, data):
        self._socket.sendall(data)

    def __read__(self, num_bytes):
        return self._socket.recv(num_bytes)


class Visa(Transport):
    """A pyvisa adapter."""
    def __init__(self, *args, **kw):
        import visa

        # TODO pyvisa versions after 1.5 should be handled differently.
        self._visa = visa.instrument(*args, **kw)

    def __read__(self, num_bytes):
        self._visa.read_raw(num_bytes)

    def __write__(self, data):
        self._visa.write_raw(num_bytes)


class Serial(Transport):
    """A pyserial adapter."""
    def __init__(self, *args, **kw):
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
