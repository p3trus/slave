#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import unittest
import re

from slave.core import Command, InstrumentBase
from slave.types import String, Float, Integer, Mapping


class MockConnection(object):
    def __init__(self):
        self._state = {
            'STRING': '1337',
            'INTEGER': 1337,
            'FLOAT': 1.337,
            'MAPPING': 1337
        }

    def ask(self, cmd):
        return str(self._state[cmd[:-1]])

    def write(self, cmd):
        tokens = re.split('[\s,]+', cmd)
        key = tokens.pop(0)
        # TODO check if args are valid
        self._state[key] = ','.join(tokens)


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


class TestCommand(unittest.TestCase):
    def setUp(self):
        self.instrument = MockInstrument()

    def test_query_and_write(self):
        state = self.instrument.connection._state
        self.assertEqual(state['STRING'], self.instrument.string)
        self.assertEqual(state['INTEGER'], self.instrument.integer)
        self.assertEqual(state['FLOAT'], self.instrument.float)
        self.assertEqual('elite', self.instrument.mapping)

        # Test writing
        self.instrument.string = value = '1338'
        self.assertEqual(value, self.instrument.string)
        self.instrument.integer = value = 1338
        self.assertEqual(value, self.instrument.integer)
        self.instrument.float = value = 1.338
        self.assertEqual(value, self.instrument.float)
        self.instrument.mapping = value = 'notelite'
        self.assertEqual(value, self.instrument.mapping)

        # Try to write read only value
        with self.assertRaises(AttributeError):
            self.instrument.read_only = 'write me'

        # Try to read write only value
        with self.assertRaises(AttributeError):
            self.instrument.write_only

if __name__ == '__main__':
    unittest.main()
