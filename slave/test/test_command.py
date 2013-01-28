#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import unittest
import re
import collections
import itertools

from slave.core import Command, InstrumentBase, _Message, _to_instance
from slave.types import Boolean, String, Float, Integer, Mapping


class MockConnection(object):
    def __init__(self):
        self._state = {
            'STRING': '1337',
            'INTEGER': 1337,
            'FLOAT': 1.337,
            'MAPPING': 1337,
            'FN': '0',
            'LIST': (1337, 1337),
        }

    def ask(self, cmd):
        state = self._state[cmd[:-1]]
        if (isinstance(state, collections.Iterable) and
            not isinstance(state, basestring)):
            return ','.join(map(str, state))
        else:
            return str(state)

    def write(self, cmd):
        tokens = re.split('[\s,]+', cmd)
        key = tokens.pop(0)
        # TODO check if args are valid
        self._state[key] = ','.join(tokens) or '1'


class MockInstrument(InstrumentBase):
    def __init__(self):
        super(MockInstrument, self).__init__(MockConnection())
        self.string = Command('STRING?', 'STRING', String)
        self.integer = Command('INTEGER?', 'INTEGER', Integer)
        self.float = Command('FLOAT?', 'FLOAT', Float)
        self.mapping = Command('MAPPING?', 'MAPPING',
                               Mapping({'elite': 1337, 'notelite': 1338}))
        self.read_only = Command(('STRING?', String))
        self.write_only = Command(write=('STRING', String))
        self.list = Command('LIST?', 'LIST', [Integer, Integer])

    def write_fn(self):
        cmd = Command(write='FN', connection=self.connection)
        cmd.write()

    def ask_fn(self):
        cmd = Command(('FN?', Boolean), connection=self.connection)
        return cmd.query()


class TestCommand(unittest.TestCase):
    def setUp(self):
        self.instrument = MockInstrument()

    def test_to_instance_helper(self):
        self.assertTrue(isinstance(_to_instance(object), object))
        self.assertTrue(isinstance(_to_instance(object()), object))

    def test_constructor(self):
        types = [
            Integer,
            Integer(),
            (Integer,),
            (Integer(),),
            (Integer, Integer),
            (Integer(), Integer()),
        ]
        type_ = [Integer()]
        result = [
            type_,
            type_,
            type_,
            type_,
            type_ + type_,
            type_ + type_,
        ]

        # All these commands should be equal.
        for type_, result in itertools.izip(types, result):
            query = _Message('QUERY?', None, result)
            write = _Message('WRITE', result, None)

            self.assertEqual(_Message('QUERY?', None, result), query)

            commands = [
                Command('QUERY?', 'WRITE', type_),
                Command(('QUERY?', type_), ('WRITE', type_)),
                Command(('QUERY?', type_), ('WRITE', type_), Float),
            ]
            for cmd in commands:
                print 'QUERY: {0}; {1}; {2}'.format(query.header, cmd._query.header, query.header == cmd._query.header)
                print 'QUERY: {0}; {1}; {2}'.format(query.data_type, cmd._query.data_type, query.data_type == cmd._query.data_type)
                print 'QUERY: {0}; {1}; {2}'.format(query.response_type, cmd._query.response_type, query.response_type == cmd._query.response_type)

                self.assertEqual(query, cmd._query)
                self.assertEqual(write, cmd._write)

    def test_query_and_write(self):
        state = self.instrument.connection._state
        self.assertEqual(state['STRING'], self.instrument.string)
        self.assertEqual(state['INTEGER'], self.instrument.integer)
        self.assertEqual(state['FLOAT'], self.instrument.float)
        self.assertEqual('elite', self.instrument.mapping)
        self.assertEqual(False, self.instrument.ask_fn())
        self.assertEqual(state['LIST'], self.instrument.list)

        # Test writing
        self.instrument.string = value = '1338'
        self.assertEqual(value, self.instrument.string)
        self.instrument.integer = value = 1338
        self.assertEqual(value, self.instrument.integer)
        self.instrument.float = value = 1.338
        self.assertEqual(value, self.instrument.float)
        self.instrument.mapping = value = 'notelite'
        self.assertEqual(value, self.instrument.mapping)
        self.instrument.list = value = 1338, 1338
        self.assertEqual(value, self.instrument.list)

        self.instrument.write_fn()
        self.assertEqual(True, self.instrument.ask_fn())

        # Try to write read only value
        with self.assertRaises(AttributeError):
            self.instrument.read_only = 'write me'

        # Try to read write only value
        with self.assertRaises(AttributeError):
            self.instrument.write_only

if __name__ == '__main__':
    unittest.main()
