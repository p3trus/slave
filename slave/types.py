#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
import random
import string


class Type(object):
    """Type factory base class."""
    def dump(self, value):
        value = self._convert(value)
        self._validate(value)
        return self._serialize(value)

    def load(self, value):
        return self._convert(value)

    def simulate(self):
        """Calculates a valid value, represented by this class."""
        raise NotImplementedError()

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

    def __repr__(self):
        return '{0}()'.format(type(self).__name__)


class Boolean(Type):
    """Represents a boolean type. It is serialized in decimal form."""
    def _convert(self, value):
        return bool(int(value))

    def _serialize(self, value):
        return '{0:d}'.format(self._convert(value))

    def simulate(self):
        """Costructs a random boolean and returns it."""
        return random.randint(0, 1)


class Number(Type):
    """Represents a abstract number type, allowing range checks."""
    def __init__(self, min=None, max=None):
        """
        Constructs a Number type factory.

        :param min: Minimal value a constructed object can have.
        :param max: Maximal value a constructed object can have.

        """
        super(Number, self).__init__()
        # evaluates to min/max if min/max is None and to it's conversion
        # otherwise.
        self.min = min and self._convert(min)
        self.max = max and self._convert(max)

    def _validate(self, value):
        if self.min is not None and value < self.min:
            raise ValueError('Value:{0}<Min:{0}'.format(value, self.min))
        if self.max is not None and value > self.max:
            raise ValueError('Value:{0}>Max:{0}'.format(value, self.max))

    def __repr__(self):
        return '{0}(min={1!r}, max={2!r})'.format(type(self).__name__,
                                                  self.min, self.max)


class Integer(Number):
    """Represents an integer type."""
    def _convert(self, value):
        return int(value)

    def simulate(self):
        min_ = -999 if self.min is None else self.min
        max_ = 1000 if self.max is None else self.max
        return random.randint(min_, max_)


class Float(Number):
    """Represents a floating point type."""
    def _convert(self, value):
        return float(value)

    def simulate(self):
        min_ = -999. if self.min is None else self.min
        max_ = 1000. if self.max is None else self.max
        return random.uniform(min_, max_)


class Mapping(Type):
    """
    Represents a one to one mapping of keys and values.

    The Mapping represents a one to one mapping of keys and values. The keys
    represent the value on the user side, and the values represent the value on
    the instrument side.

    """
    def __init__(self, mapping):
        super(Mapping, self).__init__()
        self._map = dict((k, str(v)) for k, v in mapping.items())
        self._inv = dict((v, k) for k, v in self._map.items())

    def _convert(self, value):
        return self._map[value]

    def load(self, value):
        return self._inv[value]

    def simulate(self):
        """Returns a randomly chosen key of the mapping."""
        return random.choice(self._map.keys())

    def __repr__(self):
        return '{0}({1!r})'.format(type(self).__name__, self._map)


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
    """Represents python's string type."""
    def __init__(self, min=None, max=None):
        """
        Constructs a Number type factory.

        :param min: Minimal length a string object can have.
        :param max: Maximal length a string object can have.

        """
        super(String, self).__init__()
        # evaluates to min/max if min/max is None and to it's conversion
        # otherwise.
        self.min = min and self._convert(min)
        self.max = max and self._convert(max)

    def _convert(self, value):
        return str(value)

    def _validate(self, value):
        if self.min is not None and len(value) < self.min:
            raise ValueError('len({0})<Min:{0}'.format(value, self.min))
        if self.max is not None and len(value) > self.max:
            raise ValueError('len({0})>Max:{0}'.format(value, self.max))

    def simulate(self):
        """Returns a randomly constructed string.

        Simulate randomly constructs a string with a length between min and
        max. If min is not present, a minimum length of 1 is assumed, if max
        is not present a maximum length of 10 is used.
        """
        min_ = 1 if self.min is None else self.min
        max_ = 10 if self.max is None else self.max
        # XXX What if self.min > 10 and self.max == None?
        n = random.randint(min_, max_)
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for x in range(n))


class Register(Type):
    """Represents a binary register, where bits are mapped with a name."""
    def __init__(self, mapping):
        super(Register, self).__init__()
        self.__map = dict((str(k), int(v)) for k, v in mapping.iteritems())

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

    def simulate(self):
        """Returns a dictionary representing the mapped register with random
        values.
        """
        return dict((k, random.randint(0, 1)) for k in self.__map)

    def __repr__(self):
        return 'Register({0!r})'.format(self.__map)
