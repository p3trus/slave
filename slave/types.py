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
        return bool(int(value))

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
            raise ValueError('Value:{0}<Min:{0}'.format(value, self.min))
        if self.max is not None and value > self.max:
            raise ValueError('Value:{0}>Max:{0}'.format(value, self.max))


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
        self._map = dict((k, str(v)) for k, v in map.items()) if map else {}
        self._inv = dict((v, k) for k, v in self._map.items())
        print '\nMAP', self._map, 'X'
        print '\nINV', self._inv, 'X'

    def _convert(self, value):
        return self._map[value]

    def load(self, value):
        return self._inv[value]


class Set(Mapping):
    """
    Represents a one to one mapping of each value to its string representation.
    """
    def __init__(self, *args):
        super(Set, self).__init__(dict((k, str(k)) for k in args))


class Enum(Mapping):
    """Represents a one to one mapping to an integer range."""
    def __init__(self, *args, **kw):
        """Constructs an Enum type factory.

        :param start: The first integer value of the enumerated sequence.
        :param step: The step size used in the enumeration.

        """
        start = int(kw.pop('start', 0))
        step = int(kw.pop('step', 1))
        stop = len(args) * step
        map_ = dict((k, v) for k, v in zip(args, range(start, stop, step)))
        super(Enum, self).__init__(map_)


class String(Type):
    def _convert(self, value):
        return str(value)


class Register(Type):
    """Represents a binary register, where bits are mapped with a name."""
    def __init__(self, map):
        self.__map = dict((str(k), int(v)) for k, v in map.iteritems())

    def _convert(self, value):
        x = 0
        for k, v in value.iteritems():
            if v:  # set bit
                x |= 1 << self.__map[k]
        return x

    def load(self, value):
        bit = lambda x, i: bool(x & (1 << i))
        value = int(value)
        return dict((k, bit(value, i)) for k, i in self.__map.iteritems())
