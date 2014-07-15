#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""
The core module contains several helper classes to ease instrument control.

Implementing an instrument interface is pretty straight forward. A simple
implementation might look like::

    from slave.core import InstrumentBase, Command
    from slave.types import Integer


    class MyInstrument(InstrumentBase):
        def __init__(self, transport):
            super(MyInstrument, self).__init__(transport)
            # A simple query and writeable command, which takes and writes an
            # Integer.
            self.my_cmd = Command('QRY?', 'WRT', Integer)
            # A query and writeable command that converts a string parameter to
            # int and vice versa.
            self.my_cmd2 = Command('QRY2?', 'WRT2', Enum('first', 'second'))

"""
import collections
import itertools as it
import logging

from slave.transport import SimulatedTransport
import slave.misc


_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

_Message = collections.namedtuple(
    '_Message',
    ['header', 'data_type', 'response_type']
)


def _to_instance(x):
    """Converts x to an instance if its a class."""
    return x() if isinstance(x, type) else x


def _typelist(x):
    """Helper function converting all items of x to instances."""
    if isinstance(x, collections.Iterable):
        return map(_to_instance, x)
    return None if x is None else [_to_instance(x)]


def _make_response(data, resp_t, sep):
    """Helper function to generate a response string.

    :param data: An iterable of datas.
    :param resp_t: An iterable of corresponding response types.
    :param sep: A string representing the response data separator.

    .. note:: No response header is used.

    """
    return sep.join(t.dump(v) for t, v in it.izip(resp_t, data))


class Command(object):
    """Represents an instrument command.

    The Command class handles the communication with the instrument. It
    converts the user input into the appropriate command string and sends it to
    the instrument via the transport object.
    For example::

        # a read and writeable command
        cmd1 = Command('STRING?', 'STRING', String, c)

        # a readonly command returning a tuple of two strings
        cmd2 = Command(('STRING?', [String, String]), transport=c)

        # a writeonly command
        cmd3 = Command(write=('STRING', String), transport=c)

    :param query: A string representing the *query program header*, e.g.
        `'*IDN?'`. To allow customisation of the queriing a 2-tuple or 3-tuple
        value with the following meaning is also possible.

        * (<query header>, <response data type>)
        * (<query header>, <response data type>, <query data type>)

        The types have the same requirements as the type parameter. If they are
    :param write: A string representing the *command program header*, e.g.
        '*CLS'. To allow for customization of the writing a 2-tuple value
        with the following requirements is valid as well.

        * (<command header>, <response data type>)

        The types have the same requirements as the type parameter.
    :param protocol: The configuration dictionary is used to customize the
        configuration.

    """
    #: Default configuration
    CFG = {
        'program header prefix': '',
        'program header separator': ' ',
        'program data separator': ',',
        'response header separator': None,
        'response data separator': ',',
    }

    def __init__(self, query=None, write=None,
                 type_=None, protocol=None):
        default = _typelist(type_)
        def write_message(header, data_type=default):
            return _Message(str(header), _typelist(data_type), None)

        def query_message(header, response_type=default, data_type=None):
            if response_type is None:
                raise ValueError('Missing response type')
            return _Message(str(header), _typelist(data_type),
                            _typelist(response_type))

        def assign(x, fn):
            return x and (fn(x) if isinstance(x, basestring) else fn(*x))

        self.protocol = protocol
        self._query = assign(query, query_message)
        self._write = assign(write, write_message)
        self._simulated_resp = None  # Used as a buffer in the simulation mode
        _logger.debug('Command: "{0}"'.format(self))

    def _program_message_unit(self, protocol, message, *datas):
        """Constructs a program message unit.

        :param header: The program header, can either be a command program
            header e.g. `'*CLS'` or a query program header e.g. `'*IDN?'`.
        :param datas: The program data or an iterable of program datas.

        The following algorithm is used to construct the program message unit::

            +---------+    +---------+    +-----------+    +---------+
            | Program |    | Program |    | Program   |    | Program |
            | Header  |--->| Header  +--->| Header    +--->| Data    +-+->
            | Prefix  |    +---------+    | Separator | ^  +---------+ |
            +---------+                   +-----------+ |              |
                                                        | +-----------+|
                                                        | | Program   ||
                                                        +-+ Data      <+
                                                          | Separator |
                                                          +-----------+

        """
        php = protocol['program header prefix']
        if not message.data_type:
            # Short cut if data_type is None
            # XXX Should we check if datas are available?
            return php + message.header

        if len(datas) != len(message.data_type):
            raise ValueError('Number of datas must match the number of types.')

        phs = protocol['program header separator']
        pds = protocol['program data separator']
        program_data = [t.dump(v) for v, t in it.izip(datas, message.data_type)]
        return ''.join((php, message.header, phs, pds.join(program_data)))

    def write(self, transport, protocol, *data):
        """Generates and sends a command message unit.

        :param transport: An object implementing the `.Transport` interface.
            It is used by the protocol to send the message.
        :param protocol: An object implementing the `.Protocol` interface.
        :param data: The program data.

        """
        if self.protocol:
            # Merge dict with default values.
            # TODO: In the future, this will be a protocol class instead of a
            #       dict and the protocol argument should be ignored.
            protocol = dict(it.chain(protocol.items(), self.protocol.items()))

        if not self._write:
            raise AttributeError('Command is not writeable')
        if isinstance(transport, SimulatedTransport):
            # If queriable and types match buffer datas, else do nothing.
            resp_t = self._query.response_type
            sep = protocol['response data separator']
            if self._query and resp_t == self._write.data_type:
                self._simulated_resp = _make_response(datas, resp_t, sep)
        else:
            cmu = self._program_message_unit(protocol, self._write, *data)
            _logger.info('command message unit: "{0}"'.format(cmu))
            transport.write(cmu)

    def query(self, transport, protocol, *data):
        """Generates and sends a query message unit.

        :param transport: An object implementing the `.Transport` interface.
            It is used by the protocol to send the message and receive the
            response.
        :param protocol: An object implementing the `.Protocol` interface.
        :param datas: The program data.

        """
        if not self._query:
            raise AttributeError('Command is not queryable')
        if self.protocol:
            # Merge dict with default values.
            # TODO: In the future, this will be a protocol class instead of a
            #       dict and the protocol argument should be ignored.
            protocol = dict(it.chain(protocol.items(), self.protocol.items()))

        if isinstance(transport, SimulatedTransport):
            response = self._simulate(protocol)
        else:
            qmu = self._program_message_unit(protocol, self._query, *data)
            _logger.info('query message unit: "{0}"'.format(qmu))
            response = transport.ask(qmu)
        _logger.info('response:"{0}"'.format(response))
        header, parsed_data = self._parse_response(protocol, response)
        # TODO handle the response header

        # Return single value if parsed_data is 1-tuple.
        return parsed_data[0] if len(parsed_data) == 1 else parsed_data

    def _parse_response(self, protocol, response):
        """Parses the response."""
        rhs = protocol['response header separator']
        rds = protocol['response data separator']
        resp_t = self._query.response_type

        if rhs:
            # Strip of response header.
            # XXX What if we wan't to split on any whitespace?
            header, response = response.split(rhs, 1)
        else:
            header = None

        parsed_data = []
        for v, t in it.izip_longest(response.split(rds), resp_t):
            parsed_data.append(t.load(v) if t else v)
        return header, tuple(parsed_data)

    def _simulate(self, protocol):
        response = self._simulated_resp
        if not response:
            response = _make_response(
                (t.simulate() for t in self._query.response_type),
                self._query.response_type,
                protocol['response data separator']
            )
            # This simulates a response without a response header.
            assert(protocol['response header separator'] is None)
            # store response if writeable
            if self._write:
                self._simulated_resp = response
        return response

    def __repr__(self):
        """The commands representation."""
        return '<Command({0},{1},{2})>'.format(self._query, self._write,
                                                   self.protocol)


class InstrumentBase(object):
    """Base class of all instruments.

    The InstrumentBase class applies some *magic* to simplify the Command
    interaction. Read access on :class:`~.Command` attributes is redirected to
    the :class:`Command.query`, write access to the :class:`Command.write`
    member function.

    :param transport: The transport object.
    :param protocol: The protocol object.

    """
    def __init__(self, transport, protocol=None, *args, **kw):
        self._transport = transport
        # Merge dict with default values.
        # TODO: In the future, this will be a protocol class instead of a dict.
        if protocol:
            self._protocol = dict(it.chain(Command.CFG.items(), protocol.items()))
        else:
            self._protocol = dict(Command.CFG)
        # super must be the last call, otherwise mixin classes relying on the
        # existance of `_protocol` and `_transport` will fail.
        super(InstrumentBase, self).__init__(*args, **kw)

    def _write(self, cmd, *datas):
        """Helper function to simplify writing."""
        cmd = Command(write=cmd)
        cmd.write(self._transport, self._protocol, *datas)

    def _query(self, cmd, *datas):
        """Helper function to allow method queries."""
        cmd = Command(query=cmd)
        return cmd.query(self._transport, self._protocol, *datas)

    def __getattribute__(self, name):
        """Redirects read access of command attributes to
        the :class:`~Command.query` function.
        """
        attr = object.__getattribute__(self, name)
        if isinstance(attr, Command):
            return attr.query(self._transport, self._protocol)
        return attr

    def __setattr__(self, name, value):
        """Redirects write access of command attributes to the
        :class:`~Command.write` function and injects transport, and command
        config into commands.
        """
        try:
            attr = object.__getattribute__(self, name)
        except AttributeError:
            # Attribute does not exist.
            object.__setattr__(self, name, value)
        else:
            if isinstance(attr, Command):
                # Redirect write access
                if (isinstance(value, collections.Iterable) and
                    not isinstance(value, basestring)):
                    attr.write(self._transport, self._protocol, *value)
                else:
                    attr.write(self._transport, self._protocol, value)
            else:
                object.__setattr__(self, name, value)


class CommandSequence(slave.misc.ForwardSequence):
    """A sequence forwarding item access to the query and write methods."""
    def __init__(self, iterable, transport):
        self._transport = transport
        super(CommandSequence, self).__init__(
            iterable,
            get=lambda i: i.query(self._transport),
            set=lambda i, v: i.write(self._transport, v)
        )

