#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
"""The :mod:`slave.protocol` module implements the intermediate abstraction
layer of the slave library.

The protocol knows how to create command messages and how to parse responses.
It has no knowledge of which commands are actually supported by the device and
does not care what kind of connection (e.g. ethernet, gpib, serial, ...) is used
to communicate with the device.

The common protocol api is defined by the :class:`slave.Protocol` class. Custom
protocols must implement the :meth:`~.Protocol.query` and
:meth:`~.Protocol.write` methods.

The following protocols are already implemented and ready to use:

 * :class:`~.IEC60488`
 * :class:`~.SignalRecovery`
 * :class:`~.OxfordIsobus`

"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import logging
import functools
import time

from slave.transport import Timeout

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Protocol(object):
    """Abstract protocol base class."""
    class Error(Exception):
        """Generic baseclass for all protocol related errors."""

    class ParsingError(Error):
        """Raised when a parsing error occurs."""

    def query(self, transport, *args, **kw):
        raise NotImplementedError()

    def write(self, transport, *args, **kw):
        raise NotImplementedError()


def _retry(errors, logger):
    def wrapper(fn):
        @functools.wraps(fn)
        def wrapped(self, transport, *args, **kw):
            try:
                return fn(self, transport, *args, **kw)
            except errors as e:
                logger.exception('Exception occured on 1. try. Msg: %r Retrying.', e)
            try:
                return fn(self, transport, *args, **kw)
            except errors as e:
                logger.exception('Exception occured on 2. try. Msg: %r Clearing device and retrying.', e)
                self.clear(transport)
            # Try one more time
            return fn(self, transport, *args, **kw)
        return wrapped
    return wrapper


class IEC60488(Protocol):
    """Implementation of IEC60488 protocol.

    This class implements the IEC-60488 protocol, formerly known as IEEE 488.2.

    :param msg_prefix: A string which will be prepended to the generated command
        string.
    :param msg_header_sep: A string separating the message header from the
        message data.
    :param msg_data_sep: A string separating consecutive data blocks.
    :param msg_term: A string terminating the message.
    :param resp_prefix: A string each response is expected to begin with.
    :param resp_header_sep: The expected separator of the response header and
        the response data.
    :param resp_data_sep: The expected data separator of the response message.
    :param resp_term: The response message terminator.
    :param stb_callback: For each read and write operation, a status byte is
        received. If a callback function is given, it will be called with the
        status byte.


    """
    class ParsingError(Protocol.ParsingError):
        pass

    def __init__(self, msg_prefix='', msg_header_sep=' ', msg_data_sep=',', msg_term='\n',
                 resp_prefix='', resp_header_sep='', resp_data_sep=',', resp_term='\n', encoding='ascii'):
        self.msg_prefix = msg_prefix
        self.msg_header_sep = msg_header_sep
        self.msg_data_sep = msg_data_sep
        self.msg_term = msg_term

        self.resp_prefix = resp_prefix
        self.resp_header_sep = resp_header_sep
        self.resp_data_sep = resp_data_sep
        self.resp_term = resp_term

        self.encoding = encoding

    def create_message(self, header, *data):
        if not data:
            msg = ''.join((self.msg_prefix, header, self.msg_term))
        else:
            data = self.msg_data_sep.join(data)
            msg = ''.join((self.msg_prefix, header, self.msg_header_sep, data, self.msg_term))
        return msg.encode(self.encoding)

    def parse_response(self, response, header=None):
        """Parses the response message.

        The following graph shows the structure of response messages.

        ::

                                                        +----------+
                                                     +--+ data sep +<-+
                                                     |  +----------+  |
                                                     |                |
                  +--------+        +------------+   |    +------+    |
              +-->| header +------->+ header sep +---+--->+ data +----+----+
              |   +--------+        +------------+        +------+         |
              |                                                            |
            --+                                         +----------+       +-->
              |                                      +--+ data sep +<-+    |
              |                                      |  +----------+  |    |
              |                                      |                |    |
              |                                      |    +------+    |    |
              +--------------------------------------+--->+ data +----+----+
                                                          +------+

       """
        response = response.decode(self.encoding)
        if header:
            header = "".join((self.resp_prefix, header, self.resp_header_sep))
            if not response.startswith(header):
                raise IEC60488.ParsingError('Response header mismatch')
            response = response[len(header):]
        return response.split(self.resp_data_sep)

    @_retry(errors=(ParsingError, UnicodeDecodeError, UnicodeEncodeError, Timeout), logger=logger)
    def query(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('IEC60488 query: %r', message)
        with transport:
            transport.write(message)
            response = transport.read_until(self.resp_term.encode(self.encoding))
        # TODO: Currently, response headers are not handled.
        logger.debug('IEC60488 response: %r', response)
        return self.parse_response(response)

    @_retry(errors=(ParsingError, UnicodeDecodeError, UnicodeEncodeError, Timeout), logger=logger)
    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('IEC60488 write: %r', message)
        with transport:
            transport.write(message)

    def trigger(self, transport):
        """Triggers the transport."""
        logger.debug('IEC60488 trigger')
        with transport:
            try:
                transport.trigger()
            except AttributeError:
                trigger_msg = self.create_message('*TRG')
                transport.write(trigger_msg)

    def clear(self, transport):
        """Issues a device clear command."""
        logger.debug('IEC60488 clear')
        with transport:
            try:
                transport.clear()
            except AttributeError:
                clear_msg = self.create_message('*CLS')
                transport.write(clear_msg)


class SignalRecovery(IEC60488):
    """An implementation of the signal recovery network protocol.

    Modern signal recovery devices are fitted with a ethernet port. This class
    implements the protocol used by these devices. Command
    messages are built with the following algorithm.

    ::

                                              +----------+
                                           +--+ data sep +<-+
                                           |  +----------+  |
                                           |                |
            +--------+    +------------+   |    +------+    |    +----------+
        --->+ header +--->+ header sep +---+--->+ data +----+--->+ msg term +-->
            +--------+    +------------+        +------+         +----------+

    Each command, query or write, generates a response. It is terminated with a
    null character '\\0' followed by the status byte and the overload byte.

    :param msg_prefix: A string which will be prepended to the generated command
        string.
    :param msg_header_sep: A string separating the message header from the
        message data.
    :param msg_data_sep: A string separating consecutive data blocks.
    :param msg_term: A string terminating the message.
    :param resp_prefix: A string each response is expected to begin with.
    :param resp_header_sep: The expected separator of the response header and
        the response data.
    :param resp_data_sep: The expected data separator of the response message.
    :param resp_term: The response message terminator.
    :param stb_callback: For each read and write operation, a status byte is
        received. If a callback function is given, it will be called with the
        status byte.

    :param olb_callback: For each read and write operation, a overload status
        byte is received. If a callback function is given, it will be called
        with the overload byte.
    :param encoding: The encoding used to convert the message string to bytes
        and vice versa.

    E.g.::

        >>>from slave.protocol import SignalRecovery
        >>>from slave.transport import Socket

        >>>transport = Socket(('192.168.178.1', 5900))
        >>>protocol = SignalRecovery()
        >>>print protocol.query(transport, '*IDN?')

    """
    def __init__(self, msg_prefix='', msg_header_sep=' ', msg_data_sep=' ', msg_term='\0',
                 resp_prefix='', resp_header_sep='', resp_data_sep=',', resp_term='\0',
                 stb_callback=None, olb_callback=None, encoding='ascii'):
        super(SignalRecovery, self).__init__(
            msg_prefix, msg_header_sep, msg_data_sep, msg_term,
            resp_prefix, resp_header_sep, resp_data_sep, resp_term, encoding
        )
        self.stb_callback = stb_callback
        self.olb_callback = olb_callback

    def query(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('SignalRecovery query: %r', message)
        with transport:
            transport.write(message)

            response = transport.read_until(self.resp_term.encode(self.encoding))
            logger.debug('SignalRecovery response: %r', response)
            status_byte, overload_byte = transport.read_bytes(2)

        logger.debug('SignalRecovery stb: %r olb: %r', status_byte, overload_byte)
        self.call_byte_handler(status_byte, overload_byte)
        return self.parse_response(response)

    def query_bytes(self, transport, num_bytes, header, *data):
        """Queries for binary data

        :param  transport: A transport object.
        :param num_bytes: The exact number of data bytes expected.
        :param header: The message header.
        :param data: Optional data.
        :returns: The raw unparsed data bytearray.

        """
        message = self.create_message(header, *data)
        logger.debug('SignalRecovery query bytes: %r', message)
        with transport:
            transport.write(message)

            response = transport.read_exactly(num_bytes)
            logger.debug('SignalRecovery response: %r', response)
            # We need to read 3 bytes, because there is a \0 character
            # separating the data from the status bytes.
            _, status_byte, overload_byte = transport.read_exactly(3)

        logger.debug('SignalRecovery stb: %r olb: %r', status_byte, overload_byte)
        self.call_byte_handler(status_byte, overload_byte)
        # returns raw unparsed bytes.
        return response

    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('SignalRecovery write: %r', message)
        with transport:
            transport.write(message)

            response = transport.read_until(self.resp_term.encode(self.encoding))
            status_byte, overload_byte = transport.read_bytes(2)
        logger.debug('SignalRecovery stb: %r olb: %r', status_byte, overload_byte)

        self.call_byte_handler(status_byte, overload_byte)

    def call_byte_handler(self, status_byte, overload_byte):
        if self.stb_callback:
            self.stb_callback(status_byte)
        if self.olb_callback:
            self.olb_callback(overload_byte)


class OxfordIsobus(Protocol):
    """Implements the oxford isobus protocol.

    :param address: The isobus address.
    :param echo: Enables/Disables device command echoing.
    :param msg_term: The message terminator.
    :param resp_term: The response terminator.
    :param encoding: The message and response encoding.

    Oxford Isobus messages messages are created in the following manner, where
    `HEADER` is a single char::

        +--------+    +------+
        + HEADER +--->+ DATA +
        +--------+    +------+

    Isobus allows to connect multiple devices on a serial line. To address a
    specific device a control character '@' followed by an integer address is
    used::

        +---+    +---------+    +--------+    +------+
        + @ +--->+ ADDRESS +--->+ HEADER +--->+ DATA +
        +---+    +---------+    +--------+    +------+

    On success, the device answeres with the header followed by data if
    requested. If no echo response is desired, the '$' control char must be
    prepended to the command message. This is useful if a single command must
    sent to all connected devices at once.

    On error, the device answeres with a '?' char followed by the command
    message. E.g the error response to a message `@7R10` would be `?R10`.

    """
    # TODO: Use base exception.
    class InvalidRequestError(Protocol.Error):
        """Raised when a command is not recognized by the device, has illegal
        parameters or cannot be obeyed for any reason.
        """


    class ParsingError(Protocol.ParsingError):
        """Raised when a parsing error occurs."""


    def __init__(self, address=None, echo=True, msg_term='\r',
                 resp_term='\r', encoding='ascii'):
        self.address = address
        self.echo = echo
        self.msg_term = msg_term
        self.resp_term = resp_term
        self.encoding = encoding

    def create_message(self, header, *data):
        msg = []
        if not self.echo:
            msg.append('$')
        if self.address:
            msg.append('@{}'.format(self.address))
        msg.append(header)
        msg.extend(data)
        msg.append(self.msg_term)
        return ''.join(msg).encode(self.encoding)

    def parse_response(self, response, header):
        response = response.decode(self.encoding)
        if response.startswith('?'):
            # TODO: Maybe we should raise a more informative exception.
            raise OxfordIsobus.InvalidRequestError(response)
        # ISOBUS uses a single char as message header but we allow longer header
        # for convenience.
        if not response.startswith(header[0]):
            raise OxfordIsobus.ParsingError('Response header mismatch')
        # TODO: Check if Isobus allows more than one return value. If it does,
        # this won't work.
        return response[1:]

    @_retry(errors=(InvalidRequestError, ParsingError, UnicodeDecodeError, UnicodeEncodeError, Timeout), logger=logger)
    def query(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('OxfordIsobus query: %r', message)
        with transport:
            transport.write(message)
            response = transport.read_until(self.resp_term.encode(self.encoding))

        logger.debug('OxfordIsobus response: %r', response)
        # Although isobus has only response item, we put it into a list to be
        # consistent with the other protocols.
        return [self.parse_response(response, header)]

    @_retry(errors=(InvalidRequestError, ParsingError, UnicodeDecodeError, UnicodeEncodeError, Timeout), logger=logger)
    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('OxfordIsobus write: %r', message)
        with transport:
            transport.write(message)
            if self.echo:
                response = transport.read_until(self.resp_term.encode(self.encoding))
                logger.debug('OxfordIsobus response: %r', response)

                parsed = self.parse_response(response, header)
                # A write should not return any data.
                if parsed:
                    raise OxfordIsobus.ParsingError('Unexpected response data:{}'.format(parsed))

    def clear(self, transport):
        """Issues a device clear command.

        .. note:: Only if the transport supports it.

        """
        logger.debug('OxfordIsobus clear')
        with transport:
            try:
                transport.clear()
            except AttributeError:
                pass