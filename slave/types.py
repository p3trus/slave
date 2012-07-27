#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.


class Type(object):
    """Type factory base class."""
    def dump(self, value):
        value = self._convert(value)
        self._validate(value)
        return self._serialize(value)

    def load(self, value):
        return self._convert(value)

    def _convert(self, value):
        """Converts value to the type represented by this class."""
        raise NotImplementedError()

    def _validate(self, value):
        """Validates the value.

        This member function can be overwritten by subclasses to provide
        validation. Per default it does nothing.

        """
        pass

    def _serialize(self, value):
        """Converts the value to a string.

        The serialize function converts the value to a string. It can be
        overwritten if custom serialisation behaviour is needed.

        """
        return str(value)


class Boolean(Type):
    """Represents a boolean type. It is serialized in decimal form."""
    def _convert(self, value):
        return bool(value)

    def _serialize(self, value):
        return '{:d}'.format(self.convert(value))


class Number(Type):
    def __init__(self, min=None, max=None):
        """
        Constructs a Number type factory.

        :param min: Minimal value a constructed object can have.
        :param max: Maximal value a constructed object can have.

        """
        # evaluates to min/max if min/max is None and to it's conversion
        # otherwise.
        self.min = min and self._convert(min)
        self.max = max and self._convert(max)

    def _validate(self, value):
        if self.min is not None and value < self.min:
            raise ValueError('Value:{}<Min:{}'.format(value, self.min))
        if self.max is not None and value > self.max:
            raise ValueError('Value:{}>Max:{}'.format(value, self.max))


class Integer(Number):
    """Represents an integer type."""
    def _convert(self, value):
        return int(value)


class Float(Number):
    """Represents a floating point type."""
    def _convert(self, value):
        return float(value)


class Mapping(Type):
    """
    Represents a one to one mapping of keys and values.
    """
    def __init__(self, map=None):
        # Note: dict comprehension needs at least python 2.7
        self._map = {k: str(v) for k, v in map.items()} if map else {}
        self._inv = {v: k for k, v in self._map.items()}
        print '\nMAP', self._map, 'X'
        print '\nINV', self._inv, 'X'

    def _convert(self, value):
        return self._map[value]

    def load(self, value):
        return self._inv[value]


class String(Type):
    def _convert(self, value):
        return str(value)
