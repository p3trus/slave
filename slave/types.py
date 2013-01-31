#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""Contains the type factory classes used to load and dump values to string.

The type module contains several type classes used by the :class:`~.Command`
class to load and dump values.

Custom Types
------------

The :class:`~.Command` class needs an object with three methods:

 * :meth:`.load(value)`, takes the value and returns the userspace representation.
 * :meth:`.dump(value)`, returns the device space representation of value.
 * :meth:`.simulate()`, generates a valid user space value.

The abstract :class:`~.Type` class implements this interface but most of the
time it is sufficient to inherit from :class:`~.SingleType`. 

:class:`~.SingleType` provides a default implementation, as well as three hooks
to modify the behaviour.

"""
import random
import string
import sys


class Type(object):
    """The type class defines the interface for all type factory classes."""
    def dump(self, value):
        raise NotImplementedError()

    def load(self, value):
        raise NotImplementedError()

    def simulate(self):
        """Return a valid, randomly calculated value."""
        raise NotImplementedError()

    def __repr__(self):
        return '{0}()'.format(type(self).__name__)


class SingleType(Type):
    """A simple yet easily customizable implementation of the Type interface

    :param fmt: A format string used in :meth:`.__serialize__()` to convert the
        value to string. Advanced string formatting syntax is used.
        Default: `'{0}'`

    The SingleType provides a default implementation of the :class:`~.Type`
    interface. It provides three hooks to modify it's behavior.

    * :meth:`.__convert__()`
    * :meth:`.__serialize__()`
    * :meth:`.__validate__()`

    Only :meth:`.__convert__()` is required. It should convert the value to the
    represented python type. Both :meth:`.__serialize__()` and
    :meth:`.__validate__()` have a default implementation, which can be
    overwritten to provide custom behaviour.

    """
    def __init__(self, fmt=None):
        super(SingleType, self).__init__()
        self._fmt = fmt or '{0}'

    def __convert__(self, value):
        """Convert and return the value to the represented type.

        :raises: TypeError, ValueError

        """
        raise NotImplementedError()

    def __serialize__(self, value):
        """Converts the value to string."""
        return self._fmt.format(value)

    def __validate__(self, value):
        """Validates the value.

        :raises: ValueError

        """
        pass

    def dump(self, value):
        """Dumps the value to string.

        :returns: Returns the stringified version of the value.
        :raises: TypeError, ValueError

        """
        value = self.__convert__(value)
        self.__validate__(value)
        return self.__serialize__(value)

    def load(self, value):
        """Create the value from a string.

        :returns: The value loaded from a string.
        :raises: TypeError

        """
        return self.__convert__(value)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)


class Range(SingleType):
    """Abstract base class for types representing ranges.

    :param min: The minimal included value.
    :param max: The maximal included value.

    The Range base class extends the :class:`~.SingleType` class with a range
    checking validation.

    """
    def __init__(self, min=None, max=None, *args, **kw):
        super(Range, self).__init__(*args, **kw)
        self._min = min and self.__convert__(min)
        self._max = max and self.__convert__(max)

    def __validate__(self, value):
        if self._min is not None and value < self._min:
            raise ValueError('Value:{0}<Min:{1}'.format(value, self._min))
        if self._max is not None and value > self._max:
            raise ValueError('Value:{0}>Max:{1}'.format(value, self._max))

    def __repr__(self):
        return '{0}(min={1!r}, max={2!r})'.format(type(self).__name__,
                                                  self._min, self._max)


class Boolean(SingleType):
    """Represents a Boolean type.

    :param fmt: Boolean uses a default format string of `'{0:d}'`. This means
        `True` will get serialized to `'1'` and `False` to `'0'`.

    """
    def __init__(self, fmt=None):
        super(Boolean, self).__init__(fmt=fmt or '{0:d}')

    def __convert__(self, value):
        return bool(int(value))

    def simulate(self):
        return bool(random.randint(0, 1))


class Integer(Range):
    """Represents an integer type."""
    def __convert__(self, value):
        return int(value)

    def simulate(self):
        """Generates a random integer in the available range."""
        min_ = (-sys.maxint - 1) if self._min is None else self._min
        max_ = sys.maxint if self._max is None else self._max
        return random.randint(min_, max_)


class Float(Range):
    """Represents a floating point type."""
    def __convert__(self, value):
        return float(value)

    def simulate(self):
        min_ = sys.float_info.min if self._min is None else self._min
        max_ = sys.float_info.max if self._max is None else self._max
        return random.uniform(min_, max_)


class String(SingleType):
    """Represents a string type.

    :param min: Minimum number of characters required.
    :param max: Maximum number of characters allowed.

    """
    def __init__(self, min=None, max=None, *args, **kw):
        super(String, self).__init__(*args, **kw)
        self._min = min = min and self.__convert__(min)
        self._max = max = max and self.__convert__(max)
        if (min is not None) and (max is not None):
            if (min > max):
                raise ValueError('min > max')

    def __convert__(self, value):
        return str(value)

    def __validate__(self, value):
        if self._min and len(value) < self._min:
            raise ValueError('String too short.')
        if self._max and self._max < len(value):
            raise ValueError('String too long.')

    def simulate(self):
        """Returns a randomly constructed string.

        Simulate randomly constructs a string with a length between min and
        max. If min is not present, a minimum length of 1 is assumed, if max
        is not present a maximum length of 10 is used.
        """
        min_ = 1 if self._min is None else self._min
        max_ = 10 if self._max is None else self._max
        n = min_ if (min_ >= max_) else random.randint(min_, max_)
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for x in range(n))


class Mapping(SingleType):
    """
    Represents a one to one mapping of keys and values.

    The Mapping represents a one to one mapping of keys and values. The keys
    represent the value on the user side, and the values represent the value on
    the instrument side, e.g::

        type_ = Mapping({'UserValue': 'DeviceValue'})
        print type_.load('DeviceValue')  # prints 'UserValue'
        print type_.dump('UserValue')  # prints 'DeviceValue'

    .. note::

        1. Keys do not need to be strings, they just need to be hashable.
        2. Values will be converted to strings using `str()`.

    """
    def __init__(self, mapping):
        super(Mapping, self).__init__()
        self._map = dict((k, str(v)) for k, v in mapping.items())
        self._inv = dict((v, k) for k, v in self._map.items())

    def __convert__(self, value):
        try:
            return self._map[value]
        except KeyError:
            raise ValueError()

    def load(self, value):
        try:
            return self._inv[value]
        except KeyError:
            raise TypeError()

    def simulate(self):
        """Returns a randomly chosen key of the mapping."""
        return random.choice(self._map.keys())

    def __repr__(self):
        return '{0}({1!r})'.format(type(self).__name__, self._map)


class Set(Mapping):
    """
    Represents a one to one mapping of each value to its string representation.
    """
    def __init__(self, *args, **kw):
        super(Set, self).__init__(dict((k, str(k)) for k in args), **kw)


class Enum(Mapping):
    """Represents a one to one mapping to an integer range."""
    def __init__(self, *args, **kw):
        """Constructs an Enum type factory.

        :param start: The first integer value of the enumerated sequence.
        :param step: The step size used in the enumeration.

        """
        start = int(kw.pop('start', 0))
        step = int(kw.pop('step', 1))
        stop = len(args) * step + start
        map_ = dict((k, v) for k, v in zip(args, range(start, stop, step)))
        super(Enum, self).__init__(map_, **kw)

    def load(self, value):
        # XXX Nasty hack so that device values '4', '04' return the same
        # user value.
        return super(Enum, self).load(str(int(value)))


class Register(SingleType):
    """Represents a binary register, where bits are mapped with a name."""
    def __init__(self, mapping):
        super(Register, self).__init__()
        self._map = dict((str(k), int(v)) for k, v in mapping.iteritems())

    def __convert__(self, value):
        x = 0
        for k, v in value.iteritems():
            if v:  # set bit
                x |= 1 << self._map[k]
        return x

    def load(self, value):
        bit = lambda x, i: bool(x & (1 << i))
        value = int(value)
        return dict((k, bit(value, i)) for k, i in self._map.iteritems())

    def simulate(self):
        """Returns a dictionary representing the mapped register with random
        values.
        """
        return dict((k, random.randint(0, 1)) for k in self._map)

    def __repr__(self):
        return 'Register({0!r})'.format(self._map)
