#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.


class Type(object):
    """Type factory base class."""
    def validate(self, value):
        return True

    def __call__(self, value):
        value = self.convert(value)
        value = self.validate(value)
        return value


class Boolean(Type):
    def convert(self, value):
        return bool(value)


class Number(Type):
    def __init__(self, min=None, max=None):
        """
        Constructs a Number type factory.

        :param min: Minimal value a constructed object can have.
        :param max: Maximal value a constructed object can have.

        """
        self.min = self.convert(min)
        self.max = self.convert(max)

    def validate(self, value):
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value > self.max:
            return False
        return True


class Integer(Number):
    def convert(self, value):
        return int(value)


class Float(Number):
    def convert(self, value):
        return float(value)


class Mapping(Type):
    def __init__(self, map=None, **kw):
        self._map = {} if map is None else dict(map)
        self._map.update(kw)

    def convert(self, value):
        return self._map[value]


class String(Type):
    def convert(self, value):
        return str(value)