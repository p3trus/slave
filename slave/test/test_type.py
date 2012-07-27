#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
import unittest

from slave.types import Integer, Float


class TypeCheck(object):
    def test_dump(self):
        self.assertEqual(self._serialized, self._type.dump(self._value))

    def test_load(self):
        self.assertEqual(self._value, self._type.load(self._serialized))


class NumberCheck(TypeCheck):
    def test_limit(self):
        with self.assertRaises(ValueError):
            self._type.dump(self._to_low)
        with self.assertRaises(ValueError):
            self._type.dump(self._to_big)


class TestFloat(unittest.TestCase, NumberCheck):
    def setUp(self):
        self._to_low = -11.
        self._to_big = 11.
        self._value = 1.
        self._serialized = str(self._value)
        self._type = Float(min=-10., max=10.)


class TestInteger(unittest.TestCase, NumberCheck):
    def setUp(self):
        self._to_low = -11
        self._to_big = 11
        self._value = 1
        self._serialized = str(self._value)
        self._type = Integer(min=-10, max=10)


if __name__ == '__main__':
    unittest.main()
