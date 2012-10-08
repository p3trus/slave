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
        def __init__(self, connection):
            super(MyInstrument, self).__init__(connection)
            # A simple query and writeable command, which takes and writes an
            # Integer.
            self.my_cmd = Command('QRY?', 'WRT', Integer)
            # A query and writeable command that converts a string parameter to
            # int and vice versa.
            self.my_cmd2 = Command('QRY2?', 'WRT2', Enum('first', 'second'))

"""
import collections
import logging
from itertools import izip, izip_longest

import slave.types


_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
print __name__

class SimulatedConnection(object):
    def ask(self, value):
        return ''

    def write(self, value):
        pass


class Command(object):
    """Represents an instrument command.

    The Command class handles the communication with the instrument. It
    converts the user input into the appropriate command string and sends it to
    the instrument via the connection object.
    For example::

        # a read and writeable command
        cmd1 = Command('STRING?', 'STRING', String, c)

        # a readonly command returning a tuple of two strings
        cmd2 = Command(('STRING?', [String, String]), connection=c)

        # a writeonly command
        cmd3 = Command(write=('STRING', String), connection=c)

    :param query: A string representing the *query program header*, e.g.
        `'*IDN?'`. To allow customisation of the queriing a 2-tuple or 3-tuple
        value with the following meaning is also possible.

        * (<query program header>, <response type>)
        * (<query program header>, <response type>, <query program data type>)

        The types have the same requirements as the type parameter. If they are
    :param write: A string representing the *command program header*, e.g.
        `'*CLS'`. To allow for customization of the writing a 2-tuple value
        with the following requirements is valid as well.

        * (<command program header>, <response type>)

        The types have the same requirements as the type parameter.
    :param connection: A connection object, used for the communication.
    :param cfg: The configuration dictionary is used to customize the
        configuration.

    :ivar _query: The query program header.
    :ivar _response_type: The response data type.
    :ivar _query_type: The query program data type.

    :ivar _write: The command program header.
    :ivar _write_type: The command program data type.

    """
    _default_cfg = {
        'program header prefix': '',
        'program header separator': ' ',
        'program data separator': ',',
        'response header separator': ' ',
        'response data separator': ',',
    }

    def __init__(self, query=None, write=None,
                 type_=None, connection=None, cfg=None):
        def to_instance(x):
            """If x is a type class, it is converted to an instance of it."""
            if isinstance(x, slave.types.Type):
                return x
            elif isinstance(x, type) and issubclass(x, slave.types.Type):
                return x()
            else:
                raise ValueError('Invalid value.')

        def typelist(types):
            """Applies to_instance to every element of types."""
            if not isinstance(types, collections.Sequence):
                types = (types,)
            return [to_instance(t) for t in types]

        def parse_arg(x, n):
            """
            :param x: The argument to parse.
            :param n: The number of types or typelists.

            :returns: A tuple containing the header and n typelists.
            """
            if isinstance(x, basestring):
                header = x
                types = ()
            else:  # should be at least a 1-tuple
                header = x[0]
                types = x[1:]
            args = types + (n - len(types)) * ((),)
            return [header] + [typelist(x) for x in args]

        self.connection = connection

        # convert the type param to a type instance list, e.g.
        # (String(),) or (String(), Float())
        default_type = typelist(type_) if type_ else ()

        # initialize write related attributes
        if write:
            write, write_t = parse_arg(write, 1)
        else:
            write, write_t = (None, ())
        self._write = write
        self._write_type = write_t or default_type

        # initialize query related attributes
        if query:
            query, response_t, query_t = parse_arg(query, 2)
        else:
            query, response_t, query_t = (None, (), ())
        self._query = query
        self._response_type = response_t or default_type
        self._query_type = query_t

        # initialize configuration dictionary
        self._custom_cfg = dict(cfg) if cfg else {}
        self._cfg = dict(self._default_cfg)
        self._cfg.update(self._custom_cfg)

        _logger.debug('created {0}'.format(self))

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        if isinstance(value, SimulatedConnection):
            self._buffer = None
            self.query = self.__simulate_query
            self.write = self.__simulate_write
        self._connection = value

    def program_message_unit(self, header, datas, types):
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
        if (not isinstance(datas, collections.Sequence) or
            isinstance(datas, basestring)):
            datas = (datas,)
        if len(datas) != len(types):
            raise ValueError('Number of datas must match the number of types.')

        php = self._cfg['program header prefix']
        phs = self._cfg['program header separator']
        pds = self._cfg['program data separator']
        program_data = [t.dump(v) for v, t in izip(datas, types)]
        return php + header + phs + pds.join(program_data)

    def write(self, datas=None):
        """Generates and sends a command message unit.

        :param datas: The program data or an iterable of program datas.

        """
        if not self._write:
            raise AttributeError('Command is not writeable')
        # construct the command message unit
        if not datas:
            cmu = self._write
        else:
            cmu = self.program_message_unit(self._write, datas,
                                        self._write_type)
        # Send command message unit
        _logger.info('command message unit: "{0}"'.format(cmu))
        self.connection.write(cmu)

    def query(self, datas=None):
        """Generates and sends a query message unit.

        :param datas: The program data or an iterable of program datas.

        """
        if not self._query:
            raise AttributeError('Command is not queryable')
        # construct the query message unit
        if datas is None:
            qmu = self._query
        else:
            if not self._query_type:
                raise ValueError('Query type missing')
            qmu = self.program_message_unit(self._query, datas,
                                            self._query_type)
        # Send query message unit.
        _logger.info('query message unit: "{0}"'.format(qmu))
        response = self.connection.ask(qmu)

        # Parse response
        _logger.info('response:"{0}"'.format(response))
        header, parsed_data = self.parse_response(response)
        # TODO handle the response header

        # Return single value instead of 1-tuple
        if len(parsed_data) == 1:
            return parsed_data[0]
        else:
            return parsed_data

    def parse_response(self, response):
        """Parses the response."""
        rhs = self._cfg['response header separator']
        rds = self._cfg['response data separator']

        response = response.split(rhs)
        if len(response) == 2:
            header = response[0]
            data = response[1]
        else:
            header = None
            data = response[0]
        parsed_data = []
        for val, typ in izip_longest(data.split(rds), self._response_type):
            if typ:
                val = typ.load(val)
            parsed_data.append(val)
        return header, tuple(parsed_data)

    def __simulate_query(self, datas=None):
        if not self._query:
            raise AttributeError('Command is not queryable')
        # TODO: validate datas
        if self._buffer is None or self._write is None:
            # generate values from response type
            self._buffer = tuple(t.dump(t.simulate()) for t in self._response_type)
        res = tuple(t.load(v) for v, t in izip(self._buffer, self._response_type))
                # Return single value instead of 1-tuple
        if len(res) == 1:
            return res[0]
        else:
            return res

    def __simulate_write(self, datas=None):
        if (not isinstance(datas, collections.Sequence) or
            isinstance(datas, basestring)):
            datas = (datas,)
        if len(datas) != len(self._write_type):
            raise ValueError('Number of datas must match the number of types.')

        self._buffer = [t.dump(v) for v, t in izip(datas, self._write_type)]

    def __repr__(self):
        """The commands representation."""
        query = 'query=({0!r}, {1!r}, {2!r})'.format(self._query,
                                                     self._response_type,
                                                     self._query_type)
        write = 'write=({0!r}, {1!r})'.format(self._write, self._write_type)
        connection = 'connection={0!r}'.format(self.connection)
        cfg = 'cfg={0!r}'.format(self._cfg)
        return 'Command({0}, {1}, {2}, {3})'.format(query, write,
                                                    connection, cfg)


class InstrumentBase(object):
    """Base class of all instruments.

    The InstrumentBase class applies some *magic* to simplify the Command
    interaction. Read access on :class:`~.Command` attributes is redirected to
    the :class:`Command.query`, write access to the :class:`Command.write`
    member function.

    When a Command is added to a subclass of :class:`~.InstrumentBase`, the
    connection is automatically injected into the object unless the connection
    of the Command is already set. If all Commands of a Instrument need a non
    standard configuration, it is more convenient to inject it as well. This is
    done via the cfg parameter.
    """
    def __init__(self, connection, cfg=None, *args, **kw):
        """Constructs a InstrumentBase instance."""
        super(InstrumentBase, self).__init__(*args, **kw)
        self.connection = connection
        self._cfg = cfg

    def __getattribute__(self, name):
        """Redirects read access of command attributes to
        the :class:`~Command.query` function.
        """
        attr = object.__getattribute__(self, name)
        if isinstance(attr, Command):
            return attr.query()
        return attr

    def __setattr__(self, name, value):
        """Redirects write access of command attributes to the
        :class:`~Command.write` function and injects connection, and command
        config into commands.
        """
        # Redirect write access
        if hasattr(self, name):
            attr = object.__getattribute__(self, name)
            if isinstance(attr, Command):
                attr.write(value)
                return
        # Inject connection
        elif isinstance(value, Command):
            if value.connection is None:
                value.connection = self.connection
            if self._cfg:
                # TODO doesn't feel right...
                cfg = dict(value._default_cfg)
                cfg.update(self._cfg)
                cfg.update(value._custom_cfg)
                value._cfg = cfg

        object.__setattr__(self, name, value)
