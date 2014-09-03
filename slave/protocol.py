#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Protocol(object):
    """Abstract protocol base class."""
    def query(self, transport, *args, **kw):
        raise NotImplementedError()

    def write(self, transport, *args, **kw):
        raise NotImplementedError()


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
                raise ValueError('Response header mismatch')
            response = response[len(header):]
        return response.split(self.resp_data_sep)

    def query(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('IEC60488 query: "%s"', message)
        with transport:
            transport.write(message)
            response = transport.read_until(self.resp_term.encode(self.encoding))
        # TODO: Currently, response headers are not handled.
        logger.debug('IEC60488 response: "%s"', response)
        return self.parse_response(response)

    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('IEC60488 write: "%s"', message)
        with transport:
            transport.write(message)


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
        logger.debug('SignalRecovery query: "%s"', message)
        with transport:
            transport.write(message)

            response = transport.read_until(self.resp_term.encode(self.encoding))
            logger.debug('SignalRecovery response: "%s"', response)
            status_byte, overload_byte = transport.read_bytes(2)

        logger.debug('SignalRecovery stb: "%s" olb: "%s"', status_byte, overload_byte)
        self.call_byte_handler(status_byte, overload_byte)
        return self.parse_response(response)

    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        logger.debug('SignalRecovery write: "%s"', message)
        with transport:
            transport.write(message)

            response = transport.read_until(self.resp_term.encode(self.encoding))
            status_byte, overload_byte = transport.read_bytes(2)
        logger.debug('SignalRecovery stb: "%s" olb: "%s"', status_byte, overload_byte)

        self.call_byte_handler(status_byte, overload_byte)

    def call_byte_handler(self, status_byte, overload_byte):
        if self.stb_callback:
            self.stb_callback(status_byte)
        if self.olb_callback:
            self.olb_callback(overload_byte)
