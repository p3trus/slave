#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012 - 2014 see AUTHORS.  Licensed under the GNU GPL.
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
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import collections
import itertools as it

from future.builtins import *

from slave.transport import SimulatedTransport
import slave.protocol
import slave.misc


_Message = collections.namedtuple(
    '_Message',
    ['header', 'data_type', 'response_type']
)


def _to_instance(x):
    """Converts x to an instance if its a class."""
    return x() if isinstance(x, type) else x

def _typelist(x):
    """Helper function converting all items of x to instances."""
    if isinstance(x, collections.Sequence):
        return list(map(_to_instance, x))
    elif isinstance(x, collections.Iterable):
        return x
    return None if x is None else [_to_instance(x)]

def _apply(function, types, values):
    try:
        t_len, d_len = len(types), len(values)
    except TypeError:
        pass
    else:
        if t_len > d_len:
            raise ValueError('Too few values.')
        elif t_len < d_len:
            raise ValueError('Too many values.')
    return [function(t, v) for t, v in zip(types, values)]

def _dump(types, values):
    return _apply(lambda t, v: t.dump(v), types, values)

def _load(types, values):
    return _apply(lambda t, v: t.load(v), types, values)


class Command(object):
    """Represents an instrument command.

    The Command class handles the communication with the instrument. It
    converts the user input into the appropriate command string and sends it to
    the instrument via the transport object.
    For example::

        # a read and writeable command
        cmd1 = Command('STRING?', 'STRING', String)

        # a readonly command returning a tuple of two strings
        cmd2 = Command(('STRING?', [String, String]))

        # a writeonly command
        cmd3 = Command(write=('STRING', String))

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
    :param protocol: When a protocol (an object implementing the
        :class:`slave.protocol.Protocol` interface) is given,
        :meth:`~.Command.query` and :meth:`~.Command.write` methods ignore it's
        protocol argument and use it instead.

    """
    def __init__(self, query=None, write=None, type_=None, protocol=None):
        default = _typelist(type_)
        def write_message(header, data_type=default):
            return _Message(str(header), _typelist(data_type), None)

        def query_message(header, response_type=default, data_type=None):
            if response_type is None:
                raise ValueError('Missing response type')
            return _Message(str(header), _typelist(data_type),
                            _typelist(response_type))

        def assign(x, fn):
            return x and (fn(x) if isinstance(x, (str, bytes)) else fn(*x))

        self.protocol = protocol
        self._query = assign(query, query_message)
        self._write = assign(write, write_message)

    def write(self, transport, protocol, *data):
        """Generates and sends a command message unit.

        :param transport: An object implementing the `.Transport` interface.
            It is used by the protocol to send the message.
        :param protocol: An object implementing the `.Protocol` interface.
        :param data: The program data.

        :raises AttributeError: if the command is not writable.

        """
        if not self._write:
            raise AttributeError('Command is not writeable')
        if self.protocol:
            protocol = self.protocol
        if self._write.data_type:
            data = _dump(self._write.data_type, data)
        else:
            # TODO We silently ignore possible data
            data = ()
        if isinstance(transport, SimulatedTransport):
            self.simulate_write(data)
        else:
            protocol.write(transport, self._write.header, *data)

    def query(self, transport, protocol, *data):
        """Generates and sends a query message unit.

        :param transport: An object implementing the `.Transport` interface.
            It is used by the protocol to send the message and receive the
            response.
        :param protocol: An object implementing the `.Protocol` interface.
        :param data: The program data.

        :raises AttributeError: if the command is not queryable.

        """
        if not self._query:
            raise AttributeError('Command is not queryable')
        if self.protocol:
            protocol = self.protocol
        if self._query.data_type:
            data = _dump(self._query.data_type, data)
        else:
            # TODO We silently ignore possible data
            data = ()
        if isinstance(transport, SimulatedTransport):
            response = self.simulate_query(data)
        else:
            response = protocol.query(transport, self._query.header, *data)
        response = _load(self._query.response_type, response)

        # Return single value if parsed_data is 1-tuple.
        return response[0] if len(response) == 1 else response

    def simulate_write(self, data):
        self._simulation_buffer = data

    def simulate_query(self, data):
        try:
            return self._simulation_buffer
        except AttributeError:
            response = [t.simulate() for t in self._query.response_type]
            # If the command is writeable it represents state. Therefore we
            # store the simulated response.
            if self._write:
                self._simulation_buffer = _dump(self._write.data_type, response)
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
    :param protocol: The protocol object. If no protocol is given, a
        :class:`IEC60488` protocol is used as default.

    """
    def __init__(self, transport, protocol=None, *args, **kw):
        self._transport = transport
        self._protocol = protocol or slave.protocol.IEC60488()
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
                    not isinstance(value, (str, bytes))):
                    attr.write(self._transport, self._protocol, *value)
                else:
                    attr.write(self._transport, self._protocol, value)
            else:
                object.__setattr__(self, name, value)


class CommandSequence(slave.misc.ForwardSequence):
    """A sequence forwarding item access to the query and write methods."""
    def __init__(self, transport, protocol, iterable):
        self._transport = transport
        self._protocol = protocol
        super(CommandSequence, self).__init__(
            iterable,
            get=lambda i: i.query(self._transport, self._protocol),
            set=lambda i, v: i.write(self._transport, self._protocol, v)
        )
