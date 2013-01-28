#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
import itertools
import unittest

from slave.types import Boolean, Integer, Float, Mapping, Register, Set


class TypeCheck(object):
    def test_dump(self):
        for val, ser in itertools.izip(self._values, self._serialized):
            self.assertEqual(ser, self._type.dump(val))

    def test_load(self):
        for val, ser in itertools.izip(self._values, self._serialized):
            self.assertEqual(val, self._type.load(ser))


class RangeCheck(TypeCheck):
    def test_limit(self):
        with self.assertRaises(ValueError):
            self._type.dump(self._to_low)
        with self.assertRaises(ValueError):
            self._type.dump(self._to_big)


class TestBoolean(unittest.TestCase, TypeCheck):
    def setUp(self):
        self._values = (True, False)
        self._serialized = ('1', '0')
        self._type = Boolean()


class TestFloat(unittest.TestCase, RangeCheck):
    def setUp(self):
        self._to_low = -11.
        self._to_big = 11.
        self._values = (1.,)
        self._serialized = map(str, self._values)
        self._type = Float(min=-10., max=10.)


class TestInteger(unittest.TestCase, RangeCheck):
    def setUp(self):
        self._to_low = -11
        self._to_big = 11
        self._values = range(-10, 10)
        self._serialized = map(str, self._values)
        self._type = Integer(min=-10, max=10)


class TestString(unittest.TestCase):
    pass


class TestMapping(unittest.TestCase, TypeCheck):
    def setUp(self):
        class TestObject(object):
            def __eq__(self, other):
                return type(self) == type(other)

        mapping = {'foobar': 'string', 1337: 'number', TestObject(): 'object'}
        self._values = tuple(mapping.iterkeys())
        self._serialized = tuple(mapping.itervalues())
        self._type = Mapping(mapping)


class TestSet(unittest.TestCase, TypeCheck):
    def setUp(self):
        self._values = ('string', 1337, )
        self._serialized = tuple(str(v) for v in self._values)
        self._type = Set(*self._values)


class TestRegister(unittest.TestCase, TypeCheck):
    def setUp(self):
        self._values = ({'first': True, 'second': False,
                       'third': False, 'fourth': True},)
        self._serialized = ('9',)
        self._type = Register({'first': 0, 'second': 1,
                               'third': 2, 'fourth': 3})

if __name__ == '__main__':
    unittest.main()
