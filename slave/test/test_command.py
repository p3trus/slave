#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import unittest
import re

from slave.core import Command, InstrumentBase
from slave.types import Boolean, String, Float, Integer, Mapping


class MockConnection(object):
    def __init__(self):
        self._state = {
            'STRING': '1337',
            'INTEGER': 1337,
            'FLOAT': 1.337,
            'MAPPING': 1337,
            'FN': '0',
        }

    def ask(self, cmd):
        return str(self._state[cmd[:-1]])

    def write(self, cmd):
        tokens = re.split('[\s,]+', cmd)
        print tokens
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

    def write_fn(self):
        cmd = Command(write='FN', connection=self.connection)
        cmd.write()

    def ask_fn(self):
        cmd = Command(('FN?', Boolean), connection=self.connection)
        return cmd.query()

class TestCommand(unittest.TestCase):
    def setUp(self):
        self.instrument = MockInstrument()

    def test_query_and_write(self):
        state = self.instrument.connection._state
        self.assertEqual(state['STRING'], self.instrument.string)
        self.assertEqual(state['INTEGER'], self.instrument.integer)
        self.assertEqual(state['FLOAT'], self.instrument.float)
        self.assertEqual('elite', self.instrument.mapping)
        self.assertEqual(False, self.instrument.ask_fn())

        # Test writing
        self.instrument.string = value = '1338'
        self.assertEqual(value, self.instrument.string)
        self.instrument.integer = value = 1338
        self.assertEqual(value, self.instrument.integer)
        self.instrument.float = value = 1.338
        self.assertEqual(value, self.instrument.float)
        self.instrument.mapping = value = 'notelite'
        self.assertEqual(value, self.instrument.mapping)

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
