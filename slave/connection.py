#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The connection module provides a consistent device communication interface.

To be consistent with slave, a device connection must implement a simple
interface. It must have two methods

 * :meth:`ask()` taking a string command, returning a string response.
 * :meth:`write()` taking a string command.

Packages, such as pyvisa, already implement this and can be used out of the
box. One huge disadvantage of visa, not pyvisa, is the lacking support for
modern linux kernels (>2.6). Alternatives do exist, e.g. :mod:`pyserial` can be
used to interface with serial devices, The :mod:`socket` module allows network
communication, linux has native support for usbtmc devices and linux-gpib can
be used to talk to gpib devices. But they all lack a consistent interface. To
overcome this issue, a consistent interface to all of them is implemented in
this module.

E.g::

    from slave.connection import UsbtmcDevice

    # connect to a tektronix tds2012C mountet at `/dev/usbtmc0` using it's
    # ContextManager interface.
    with UsbtmcDevice(0) as TDS2012C:
        # emit clear command.
        tds.write('*CLS')
        # query status byte.
        print tds.ask('*STB?')

"""
import threading
import collections
import ctypes as ct
import ctypes.util
import os
import socket


class _LockDict(collections.defaultdict):
    def __init__(self):
        super(_LockDict, self).__init__(threading.Lock)
        self._lock = threading.Lock()

    def __getitem__(self, key):
        with self._lock:
            return super(_LockDict, self).__getitem__(key)


#: A dictionairy of resource locks.
_resource_locks = _LockDict()


class Connection(object):
    """An abstract base class defining the connection interface.

    :param lock: A thread lock used to control access to the resource. This
        allows multiple sessions to use the same resource.

    The :class:`Connection` base class defines an interface for all
    connections. The following hooks are mandatory and must be implemented by
    a child class:

    Mandatory hooks:
     * :meth:`__read__`
     * :meth:`__write__`

    Optional hooks:
     * :meth:`__delay__`

    """
    def __init__(self, lock):
        self._lock = lock

    def ask(self, value):
        """Writes the `value`, reads the response."""
        with self._lock:
            self.__write__(value)
            self.__delay__()
            return self.__read__().strip()

    def read(self):
        """Reads from the device."""
        with self._lock:
            return self.__read__().strip()

    def write(self, value):
        """Writes the `value` to the device."""
        with self._lock:
            self.__write__(value)

    def __delay__(self):
        """Overwrite this to add a delay between the read and write operations
        in the ask() method.
        """
        pass

    def __read__(self):
        """The read hook should return a string response."""
        raise NotImplementedError()

    def __write__(self, value):
        """The write hook should send the string value to the device."""
        raise NotImplementedError()


class GpibDevice(Connection):
    """Wrapps a linux-gpib device.

    :param primary: The primary gpib address in the range of 0 to 30.
    :param secondary: The secondary gpib address.
    :param board: The gpib board index. Linux-gpib supports up to 16 boards.
    :param timeout: The timeout in seconds.

    Usage::

        from slave.connection import GpibDevice


        # Connecting to a gpib device at address 8, using the context manager
        # interface.
        with GpibDevice(8) as connection:
            # print the identification string of the device.
            print connection.ask('*IDN?')

    """
    def __init__(self, primary=0, secondary=0, board=0, timeout=13, send_eoi=1,
                 eos=0):
        # Use visa resource identifier as key in the resource lock dict.
        super(GpibDevice, self).__init__(
            lock=_resource_locks['GPIB{0}::{1}'.format(board, primary)]
        )

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
        # TODO check device descriptor
        # TODO allow customizable term char
        self._term_chars = '\n'

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Closes the gpib connection.

        .. note::

            Instead of directly calling `close()`, use it's ContextManager
            interface.

        """
        self._lib.ibonl(self._device, ct.c_int(0))

    def __write__(self, value):
        value = value + self._term_chars
        self._lib.ibwrt(self._device, ct.c_char_p(value), ct.c_long(len(value)))

    def __read__(self, bytes=1024):
        buffer = ct.create_string_buffer(bytes)
        self._lib.ibrd(self._device, ct.byref(buffer), ct.c_long(bytes))
        return buffer.value

    def trigger(self):
        """Triggers the device.

        The trigger method sens a GET(group execute trigger) command byte to
        the device.
        """
        self._lib.ibtrg(self._device)  # TODO check error conditions.


class TCPIPDevice(Connection):
    """A tiny wrapper for a socket connection.

    :param address: The ip address as string.
    :param port: The port.

    Usage::

        from slave.connection import TCPIPDevice


        # Connecting to a tcpip device at address 168.178.0.1:1337, using the
        # context manager interface.
        with TCPIPDevice('168.178.0.1',1337) as connection:
            # print the identification string of the device.
            print connection.ask('*IDN?')

    """
    def __init__(self, address, port):
        super(TCPIPDevice, self).__init__(
            # TODO convert dns address to ip
            lock=_resource_locks['TCPIP::{0}:{1}'.format(address, port)]
        )
        self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._device.connect((address, port))
        self._term_chars = '\n'

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Closes the socket connection.

        .. note::

            Instead of directly calling `close()`, use it's ContextManager
            interface.

        """
        self._device.close()

    def __read__(self, bytes=1024):
        return self._device.recv(bytes)

    def __write__(self, value):
        self._device.send(value + self._term_chars)


class UsbtmcDevice(Connection):
    """A generic usbtmc device connection.

    :param primary: The usbtmc primary address. A primary address of `0`
        corresponds to the '/dev/usbtmc0' device.

    .. note::

        * This class needs Linux kernel >= 2.6.28 to work properly.

        * Read and write access to the device descriptors, e.g. '/dev/usbtmc0'
          is required.

    Usage::

        from slave.connection import UsbtmcDevice


        # Connecting to a usbtmc device at '/dev/usbtmc0', using the
        # context manager interface.
        with UsbtmcDevice(0) as connection:
            # print the identification string of the device.
            print connection.ask('*IDN?')

    """
    def __init__(self, primary):
        super(UsbtmcDevice, self).__init__(
            lock=_resource_locks['usbtmc{0}'.format(primary)]
        )
        self._device = os.open('/dev/usbtmc{0}'.format(primary), os.O_RDWR)
        self._term_chars = '\n'

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Closes the Usbtmc connection.

        .. note::

            Instead of directly calling `close()`, use it's ContextManager
            interface.

        """
        os.close(self._device)

    def __read__(self, bytes=1024):
        return os.read(self._device, bytes)

    def __write__(self, value):
        os.write(self._device, value + self._term_chars)

