#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""The async module provides a compatibility layer for the async networking
library tornado.
"""
import socket
import logging

from tornado.iostream import IOStream
from tornado.gen import coroutine, Return, Task

from slave.core import Command
from slave.transport import SimulatedTransport


_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


class TCPIPDevice(object):
    """An asyncronous TCP/IP transport.

   It provides a similar API like :class:`slave.transport.TCPIPDevice`, but
   uses tornados asyncronous features.

    """
    def __init__(self, address, port, term_chars='\n'):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._transport = IOStream(s)
        # TODO connect asyncronously
        self._transport.connect((address, port))
        self.term_chars = term_chars

    @coroutine
    def ask(self, message):
        yield self.write(message)
        response = yield self.read()
        raise Return(response)

    @coroutine
    def read(self):
        response = yield Task(self._transport.read_until, self.term_chars)
        raise Return(response)

    @coroutine
    def write(self, message):
        yield Task(self._transport.write, message)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Closes the socket transport.

        .. note::

            Instead of directly calling `close()`, use it's ContextManager
            interface.

        """
        self._device.close()


class AsyncCommand(Command):
    @coroutine
    def query(self, *datas):
        """Generates and sends a query message unit.

        :param datas: The program data or an iterable of program datas.

        """
        if not self._query:
            raise AttributeError('Command is not queryable')
        if isinstance(self.transport, SimulatedTransport):
            response = self._simulate()
        else:
            qmu = self._program_message_unit(self._query, *datas)
            _logger.info('query message unit: "{0}"'.format(qmu))
            response = yield self.transport.ask(qmu)
        _logger.info('response:"{0}"'.format(response))
        header, parsed_data = self._parse_response(response)
        # TODO handle the response header

        # Return single value if parsed_data is 1-tuple.
        if len(parsed_data) == 1:
            raise Return(parsed_data[0])
        else:
            raise Return(parsed_data)

    @coroutine
    def write(self, *datas):
        """Generates and sends a command message unit.

        :param datas: The program data or an iterable of program datas.

        """
        if not self._write:
            raise AttributeError('Command is not writeable')
        if isinstance(self.transport, SimulatedTransport):
            # If queriable and types match buffer datas, else do nothing.
            resp_t = self._query.response_type
            sep = self.cfg['response data separator']
            if self._query and resp_t == self._write.data_type:
                self._simulated_resp = _make_response(datas, resp_t, sep)
        else:
            cmu = self._program_message_unit(self._write, *datas)
            _logger.info('command message unit: "{0}"'.format(cmu))
            yield self.transport.write(cmu)


def patch():
    """Monkey patches `slave.core.Command` and `slave.transport.TCPIPDevice` to
    use the async versions.
    """
    import slave.core
    slave.core.Command = AsyncCommand
    import slave.transport
    slave.transport.TCPIPDevice = TCPIPDevice

