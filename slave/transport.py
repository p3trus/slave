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
 * :class:`Visa` - A wrapper of the pyvisa library. (Supports pyvisa 1.4 - 1.5).

"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
from future.utils import raise_with_traceback
import socket
import threading
import ctypes as ct
import ctypes.util
import pkg_resources
from distutils.version import LooseVersion
import contextlib

from slave.misc import wrap_exception


class TransportError(IOError):
    """Baseclass for all transport errors."""


class Timeout(TransportError):
    """Baseclass for all transport timeouts."""


class Transport(object):
    """A utility class to write and read data.

    The :class:`~.Transport` base class defines a common interface used by the
    `slave` library. Transports are intended to be used as context managers.
    Entering the `with` block locks a transport, leaving it unlocks it.

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
    class Error(TransportError):
        pass

    class Timeout(Timeout, Error):
        pass

    def __init__(self, address, alwaysopen=True, *args, **kw):
        super(Socket, self).__init__()
        self.address = address
        self.alwaysopen = alwaysopen
        self._socket = None
        if self.alwaysopen:
            self.open()

    @wrap_exception(exc=socket.error, new_exc=Error)
    @wrap_exception(exc=socket.timeout, new_exc=Timeout)
    def __write__(self, data):
        self._socket.sendall(data)

    @wrap_exception(exc=socket.error, new_exc=Error)
    @wrap_exception(exc=socket.timeout, new_exc=Timeout)
    def __read__(self, num_bytes):
        return self._socket.recv(num_bytes)

    @wrap_exception(exc=socket.error, new_exc=Error)
    @wrap_exception(exc=socket.timeout, new_exc=Timeout)
    def open(self):
        if self._socket:
            raise ValueError('Socket is already open.')
        self._socket = socket.create_connection(self.address)

    @wrap_exception(exc=socket.error, new_exc=Error)
    @wrap_exception(exc=socket.timeout, new_exc=Timeout)
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

# TODO:
# 1. Wrap visa exceptions
# 2. Implement trigger functionality
try:
    import visa
    VISA_VERSION = pkg_resources.get_distribution('pyvisa').version

    @contextlib.contextmanager
    def _wrap_visa_exceptions():
        try:
            yield
        except visa.VisaIOError as e:
            if e.error_code == VI_ERROR_TMO:
                raise_with_traceback(Visa.Timeout(e))
            else:
                raise_with_traceback(Visa.Error(e))
        except visa.Error as e:
            raise_with_traceback(Visa.Error(e))


    if LooseVersion(VISA_VERSION) < LooseVersion('1.5'):
        from vpp43_constants import VI_ERROR_TMO

        class Visa(Transport):
            """A pyvisa wrapper."""
            class Error(TransportError):
                """Base class for visa exceptions."""

            class Timeout(Timeout, Error):
                """Raised when a visa timeout occurs."""

            def __init__(self, *args, **kw):
                super(Visa, self).__init__()
                self._instrument = visa.instrument(*args, **kw)

            def __read__(self, num_bytes):
                with _wrap_visa_exceptions():
                    return self._instrument.read_raw()

            def __write__(self, data):
                with _wrap_visa_exceptions():
                    self._instrument.write(data)

    else:
        from pyvisa.errors import VI_ERROR_TMO

        class Visa(Transport):
            """A pyvisa wrapper."""
            class Error(TransportError):
                """Base class for serial port exceptions."""

            class Timeout(Timeout, Error):
                """Raised when a serial timeout occurs."""

            def __init__(self, *args, **kw):
                super(Visa, self).__init__()
                rm = visa.ResourceManager()
                self._instrument = rm.get_instrument(*args, **kw)

            def __read__(self, num_bytes):
                with _wrap_visa_exceptions():
                    return self._instrument.read_raw(num_bytes)

            def __write__(self, data):
                with _wrap_visa_exceptions():
                    self._instrument.write_raw(data)

except ImportError:
    pass

try:
    import serial

    class Serial(Transport):
        """A pyserial adapter."""

        class Error(TransportError):
            """Base class for serial port exceptions."""

        class Timeout(Timeout, Error):
            """Raised when a serial timeout occurs."""

        def __init__(self, *args, **kw):
            super(Serial, self).__init__()
            self._serial = serial.Serial(*args, **kw)

        @wrap_exception(exc=serial.SerialException, new_exc=Error)
        @wrap_exception(exc=serial.SerialTimeoutException, new_exc=Timeout)
        def __write__(self, data):
            self._serial.write(data)

        def __read__(self, num_bytes):
            return self._serial.read(num_bytes)

except ImportError:
    pass


class LinuxGpib(Transport):
    """A linux-gpib adapter.

    E.g.::

        transport = LinuxGpib(primary=11, timeout='1 s')
        with transport:
            transport.write(b'*IDN?\\n')
            idn = transport.read_until(b'\\n')
        transport.close()

    :param int primary: The primary gpib address.
    :param int secondary: The secondary gpib address. An integer in the range 0
        to 30 or `None`. `None` disables the use of secondary addressing.
    :param int board: The gpib board index.
    :param timeout: The timeout for IO operations. See :attr:`LinuxGpib.TIMEOUT`
        for possible values.
    :param bool send_eoi: If `True`, the EOI line will be asserted with the last
        byte sent during write operations.
    :param str eos_char: End of string character.
    :param int eos_mode: End of string mode.

    """
    #: Valid timeout parameters.
    TIMEOUT = [
        None, '10 us', '30 us', '100 us', '300 us', '1 ms', '3 ms',
        '10 ms', '30 ms', '100 ms', '300 ms', '1 s', '3 s', '10 s', '30 s',
        '100 s', '300 s', '1000 s'
    ]
    #: Enable termination of reads when eos character is received.
    REOS = 0x400
    #: Assert the EOI line whenever the eos character is sent during writes.
    XEOS = 0x800
    #: Match eos character using all 8 bits instead of the 7 least significant bits.
    BIN = 0x1000

    #: Possible error messages.
    ERRNO = {
        0: 'A system call has failed.',
        1: 'Your interface needs to be controller-in-charge, but is not.',
        2: 'You have attempted to write data or command bytes, but there are no listeners currently addressed.',
        3: 'The interface board has failed to address itself properly before starting an io operation.',
        4: 'One or more arguments to the function call were invalid.',
        5: 'The interface board needs to be system controller, but is not.',
        6: 'A read or write of data bytes has been aborted, possibly due to a timeout or reception of a device clear command.',
        7: 'The GPIB interface board does not exist, its driver is not loaded, or it is not configured properly.',
        8: 'Not used (DMA error), included for compatibility purposes.',
        10: 'Function call can not proceed due to an asynchronous IO operation (ibrda(), ibwrta(), or ibcmda()) in progress.',
        11: 'Incapable of executing function call, due the GPIB board lacking the capability, or the capability being disabled in software.',
        12: 'File system error. ibcnt/ibcntl will be set to the value of errno.',
        14: 'An attempt to write command bytes to the bus has timed out.',
        15: 'One or more serial poll status bytes have been lost.',
        16: 'The serial poll request service line is stuck on.',
        20: 'ETAB'
    }

    #: Status Register. Please consult the linux-gpib manual for a description.
    STATUS = {
        0: 'device clear',
        1: 'device trigger',
        2: 'listener',
        3: 'talker',
        4: 'atn',
        5: 'controller-in-charge',
        6: 'remote',
        7: 'lockout',
        8: 'io complete',
        9: 'event',
        10: 'serial polled',
        11: 'srq',
        12: 'eoi',
        13: 'timeout',
        14: 'error'
    }

    class Error(TransportError):
        """Generic linux-gpib error."""

    class Timeout(Error, Timeout):
        """Raised when a linux-gpib timeout occurs."""

    def __init__(self, primary=0, secondary=None, board=0, timeout='10 s',
                 send_eoi=True, eos_char=None, eos_mode=0):
        super(LinuxGpib, self).__init__()

        valid_address = range(0, 31)
        if primary not in valid_address:
            raise ValueError('Primary address must be in the range 0 to 30.')

        if secondary not in (valid_address + [None]):
            raise ValueError('Secondary address must be in the range 0 to 30 or None')
        # Linux-gpib secondary addresses need an offset of 96 following NI
        # convention.
        secondary = 0 if secondary is None else secondary + 96
        timeout = self.TIMEOUT.index(timeout)
        send_eoi = bool(send_eoi)

        if not eos_mode in [0, Linux.Gpib.REOS, LinuxGpib.XEOS, LinuxGpib.BIN]:
            raise ValueError('Invalid eos_mode')

        if eos_char is None:
            eos = eos_mode
        else:
            eos = ord(eos_char) + eos_mode

        self._lib = ct.CDLL(ct.util.find_library('gpib'))
        self._device = self._lib.ibdev(
            ct.c_int(board), ct.c_int(primary), ct.c_int(secondary),
            ct.c_int(timeout), ct.c_int(send_eoi), ct.c_int(eos)
        )
        self._ibsta_parser = Register(LinuxGpib.STATUS)

    def __del__(self):
        self.close()

    def close(self):
        """Closes the gpib transport."""
        if self._device is not None:
            ibsta = self._lib.ibonl(self._device, 0)
            self._check_status(ibsta)
            self._device = None

    def __write__(self, data):
        ibsta = self._lib.ibwrt(self._device, ct.c_void_p(data), ct.c_long(len(data)))
        self._check_status(ibsta)

    def __read__(self, num_bytes):
        buffer = ct.create_string_buffer(num_bytes)
        ibsta = self._lib.ibrd(self._device, ct.byref(buffer), ct.c_long(num_bytes))
        self._check_status(ibsta)
        return buffer.value

    def clear(self):
        """Issues a device clear command."""
        ibsta = self._lib.ibclr()
        self._check_status()

    def trigger(self):
        """Triggers the device.

        The trigger method sens a GET(group execute trigger) command byte to
        the device.
        """
        ibsta = self._lib.ibtrg(self._device)
        self._check_status(ibsta)

    @property
    def status(self):
        ibsta = self._lib.ThreadIbsta()
        return self._ibsta_parser.load(ibsta)

    @property
    def error_status(self):
        error = self._lib.ThreadIberr()
        return LinuxGpib.ERRNO[error]

    def _check_status(self, ibsta):
        """Checks ibsta value."""
        if ibsta & 0x4000:
            raise LinuxGpib.Timeout()
        elif ibsta & 0x8000:
            raise LinuxGpib.Error(self.error_status)
