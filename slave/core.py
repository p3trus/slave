#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import collections
from itertools import izip_longest

import types


class Command(object):
    def __init__(self, connection, query=None, write=None, type=None, **cfg):
        """
        Construct a new Command object

        :param connection: Represents a connection object, used to query and
          write the command. It may be the first positional argument or
          specified via keyword.

        :param query: Represents the query command. It may be the second
          positional argument or specified via keyword.

        :type query: Either a command string or a tuple, where the first item
          is the command string and the second is the result type of the query.

        :param write: Represents the write command. It may be the third
          positional argument.

        :type write: Either a command string or a tuple, where the first item
          is the command string and the second is the parameter type of the
          write command.

        :param type: Represents the type of the query result and the write
          argument, indicated using an instance or class inheriting from
          :class:`~tucold.types.Type`, e.g.::

          # A type with no arguments
          a = Command('QUERY?', 'WRITE', Integer)

          # A type with two arguments
          b = Command('QUERY?', 'WRITE', Integer(min=0, max=255))

          Multiple return values are indicated using an iterable, e.g. a list
          or tuple, holding type instances or classes, e.g.::

            # A command returning an Integer and a Float on query
            c = Command('QUERY?', type=[Integer, Float(min=12.)])

          If the query result type or the write parameter type is set, it is
          preferred.

        """
        self._connection = connection
        self._query, self._result_type = self.__init_cmd__(query, type)
        self._write, self._write_parms = self.__init_cmd__(write, type)

        self._cfg = {
            'separator': ','
        }
        self._cfg.update(cfg)

    def __init_cmd__(self, cmd, default_type):
        def init_cmd(value):
            if isinstance(value, basestring):
                return value
            else:
                raise ValueError()

        def to_instance(value):
            if isinstance(value, types.Type):
                return value
            elif isinstance(value, type) and issubclass(value, types.Type):
                return value()
            else:
                raise ValueError('Invalid value.')

        def init_type(value):
            if not isinstance(value, collections.Sequence):
                value = [value]
            else:
                value = list(value)
            value = map(to_instance, value)
            return value

        if cmd is None:
            return None, None

        if isinstance(cmd, basestring):
            cmd_ = init_cmd(cmd)
            type_ = init_type(default_type)
        else:
            cmd = list(cmd)
            cmd_ = init_cmd(cmd.pop(0))
            if cmd:
                type_ = init_type(cmd.pop(0))
            else:
                type_ = init_type(default_type)
        return cmd_, type_

    def query(self):
        if self._query is None:
            raise AttributeError('Command is not queryable.')
        result = self._connection.ask(self._query)
        return self._parse_result(result)

    def _parse_result(self, result):
        sep = self._cfg['separator']
        result = [i.strip() for i in result.split(sep)]
        parsed = []
        for (val, typ) in izip_longest(result, self._result_type):
            if typ:
                val = typ.load(val)
            parsed.append(val)

        if len(parsed) == 1:
            return parsed[0]
        return parsed

    def write(self, value):
        if self._write is None:
            raise AttributeError('Command is not writeable.')
        if (isinstance(value, basestring)
        or not isinstance(value, collections.Sequence)):
            value = [value]
        if len(self._write_parms) != len(value):
            raise ValueError('Mismatch in argument number. Required:{}, Received:{}'.format(len(self._write_parms), len(value)))

        args = map(lambda t, v: t.dump(v), self._write_parms, value)
        cmd = self._write + ' ' + ','.join(args)
        self._connection.write(cmd)


class InstrumentBase(object):
    """Base class of all instruments."""
    def __getattribute__(self, name):
        """Redirects read access of command attributes to
        the :class:`~.Command.query` function.
        """
        attr = object.__getattribute__(self, name)
        if isinstance(attr, Command):
            return attr.query()
        return attr

    def __setattr__(self, name, value):
        """Redirects write access of command attributes to the
        :class:`~.Command.write` function.
        """
        if hasattr(self, name):
            attr = object.__getattribute__(self, name)
            if isinstance(attr, Command):
                attr.write(value)
                return
        object.__setattr__(self, name, value)
