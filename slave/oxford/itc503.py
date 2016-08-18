#  -*- coding: utf-8 -*-
#
# Slave, (c) 2015, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

from slave.driver import Command, Driver
from slave.types import Boolean, Enum, Float, Integer, Register, String
from slave.protocol import OxfordIsobus

import re
import time


class ITC503(Driver):
    """An oxford instruments ITC503 temperature controller driver.

    E.g.::

        from slave.transport import Serial

        # Connect to an ITC503 Temperature controller with the isobus address 1.
        #
        # Note: Oxford Instruments serial devices need two stopbits.
        itc = ITC503(Serial(0, stopbits=2), address=1)

        itc.access_mode = 'remote unlocked'

        # Use sensor2 as control sensor
        itc.control_sensor = 2



    :param transport: A transport object.

        .. note:: When using the serial interface, two stopbits must be used.

    :param address: The isobus address. Use `None` if no isobus address is
        configured.

    :ivar access_mode: Controls the front panel access mode. Valid are
        'local locked', 'remote locked', 'local unlocked' and 'remote unlocked'.
    :ivar activity: Defines wether the itc is sweeping or holding.
    :ivar auto: Returns a dict with the keys 'gas' and 'heater' and boolean
        values corresponding to the state of each auto control mode.

        >>> itc.auto
        {'gas': False, 'heater': False}
    :ivar bool auto_pid: Enables/Disables the auto_pid feature. When enabled,
        the internal pid table is used.
    :ivar float gas_flow: The gas flow in percent with a resolution of 0.1%.
    :ivar float heater: The heater output in percent with a resolution of 0.1%.

    :ivar float target_temperature: The target temperature.
    :ivar float temperature1: The temperature of sensor 1. (read-only)
    :ivar float temperature2: The temperature of sensor 2. (read-only)
    :ivar float temperature3: The temperature of sensor 3. (read-only)

    :ivar str version: Returns the version and firmware number as a string.
        (read-only)

    """
    ACCESS_MODE = [
        'local locked', 'remote locked', 'local unlocked', 'remote unlocked',
    ]
    ACTIVITY = ['hold', 'sweep']
    AUTO = {
        0: 'heater',
        1: 'gas'
    }

    def __init__(self, transport, address=None):
        super(ITC503, self).__init__(transport, OxfordIsobus(address=address))

        self.gas_flow = Command('R7', 'G', Float(min=0, max=99.9))
        self.heater = Command('R5', 'O', Float(min=0, max=99.9))

        self.sweep_table = SweepTable(self._transport, self._protocol)

        self.target_temperature = Command('R0', 'T', Float)

        self.temperature1 = Command(('R1', Float))
        self.temperature2 = Command(('R2', Float))
        self.temperature3 = Command(('R3', Float))

        # TODO: The ITC does not echo the 'V' for this command. This leads to a
        # parsing error.
        self.version = Command(('V', String))

    @property
    def access_mode(self):
        return self.status['access_mode']

    @access_mode.setter
    def access_mode(self, mode):
        cmd = 'C', Enum(*self.ACCESS_MODE)
        self._write(cmd, mode)

    @property
    def activity(self):
        try:
            return self.ACTIVITY[self.status['activity'] % 2]
        except ValueError:
            return 'ERROR'

    @activity.setter
    def activity(self, mode):
        cmd = 'S', Enum(*self.ACTIVITY)
        self._write(cmd, mode)

    @property
    def auto(self):
        return self.status['auto']

    @auto.setter
    def auto(self, mode):
        cmd = 'A', Register(self.AUTO)
        self._write(cmd, mode)

    @property
    def auto_pid(self):
        return self.status['auto_pid']

    @auto_pid.setter
    def auto_pid(self, value):
        cmd = 'L', Boolean
        self._write(cmd, value)

    @property
    def control_temperature(self):
        control_sensor = self.status['control_sensor']
        if control_sensor == 1:
            return self.temperature1
        if control_sensor == 2:
            return self.temperature2
        if control_sensor == 3:
            return self.temperature3

    @property
    def control_sensor(self):
        return self.status['control_sensor']

    @control_sensor.setter
    def control_sensor(self, value):
        cmd = 'H', Integer(min=1, max=3)
        self._write(cmd, value)

    @property
    def status(self):
        response = self._protocol.query(self._transport, 'X')[0]
        x, auto, access_mode, activity, control_sensor, auto_pid = re.split('[XACSHL]', response)
        return {
            'auto': Register(self.AUTO).load(auto),
            'access_mode': Enum(*self.ACCESS_MODE).load(access_mode),
            'activity': int(activity) if activity != 'O' else -1,
            'control_sensor': int(control_sensor),
            'auto_pid': bool(int(auto_pid)),
        }

    def scan_temperature(self, measure, temperature, rate, delay=1):
        """Performs a temperature scan.

        Measures until the target temperature is reached.

        :param measure: A callable called repeatedly until stability at target
            temperature is reached.
        :param temperature: The target temperature in kelvin.
        :param rate: The sweep rate in kelvin per minute.
        :param delay: The time delay between each call to measure in seconds.

        """
        self.activity = 'hold'
        # Clear old sweep table
        self.sweep_table.clear()

        # Use current temperature as target temperature
        # and calculate sweep time.
        current_temperature = self.control_temperature
        sweep_time = abs((temperature - current_temperature) / rate)

        self.sweep_table[0] = temperature, sweep_time, 0.
        self.sweep_table[-1] = temperature, 0., 0.

        self.activity = 'sweep'
        while self.activity == 'sweep':
            measure()
            time.sleep(delay)

    def set_temperature(self, temperature, rate, wait_for_stability=True, delay=1):
        """Sets the temperature.

        .. note::

            For complex sweep sequences, checkout :attr:`ITC503.sweep_table`.

        :param temperature: The target temperature in kelvin.
        :param rate: The sweep rate in kelvin per minute.
        :param wait_for_stability: If wait_for_stability is `True`, the function
            call blocks until the target temperature is reached and stable.
        :param delay: The delay specifies the frequency how often the status is
            checked.

        """
        self.activity = 'hold'
        # Clear old sweep table
        self.sweep_table.clear()

        # Use current temperature as target temperature
        # and calculate sweep time.
        current_temperature = self.control_temperature
        sweep_time = abs((temperature - current_temperature) / rate)

        self.sweep_table[0] = temperature, sweep_time, 0.
        self.sweep_table[-1] = temperature, 0., 0.

        self.activity = 'sweep'
        if wait_for_stability:
            while self.activity == 'sweep':
                time.sleep(delay)


class Table(Driver):
    """Abstract table implementation for Oxford itc503 internal tables.

    Inheriting classes need to implement a `_item` command used
    to read and write the table.

    """
    def __init__(self, transport, protocol, shape):
        super(Table, self).__init__(transport, protocol)
        self._shape = shape

    @property
    def shape(self):
        return self._shape

    def _read_item(self, x, y):
        # recursively build a list of items if x is a slice
        if isinstance(x, slice):
            return [self._read_item(xi, y) for xi in range(*x.indices(self.shape[0]))]
        if isinstance(y, slice):
            return [self._read_item(x, yi) for yi in range(*y.indices(self.shape[1]))]
        # The ITC uses one based indexing, therefore we increase x and y
        # by one
        x, y = x % self.shape[0] + 1, y % self.shape[1] + 1
        # Direct pointer to table entry.
        self._write(('x', Integer), x)
        self._write(('y', Integer), y)
        return self._item

    def _write_item(self, x, y, value):
        # recursively walk through a list of items if x is a slice
        if isinstance(x, slice):
            # TODO assign complete table
            for xi in range(*x.indices(self.shape[0])):
                self._write_item(xi, y, value)
        elif isinstance(y, slice):
            # Check if sizes match
            y_values = range(*y.indices(self.shape[1]))
            try:
                if len(y_values) == len(value):
                    for yi, vi in zip(y_values, value):
                        self._write_item(x, yi, vi)
                else:
                    raise ValueError('Size missmatch: {} != {}'.format(len(y_values), len(value)))
            except TypeError:
                for yi in y_values:
                    self._write_item(x, yi, value)
        else:
            # The ITC uses one based indexing, therefore we increase x and y
            # by one
            x, y = x % self.shape[0] + 1, y % self.shape[1] + 1
            # Direct pointer to table entry.
            self._write(('x', Integer), x)
            self._write(('y', Integer), y)
            self._item = value

    def __len__(self):
        return self.shape[0]

    def __getitem__(self, item):
        if isinstance(item, tuple):
            # Both rows and columns are given
            x, y = item
        else:
            # Only rows are given
            x, y = item, slice(0, self.shape[1])
        return self._read_item(x, y)

    def __setitem__(self, item, value):
        if isinstance(item, tuple):
            # Both rows and columns are given
            x, y = item
        else:
            # Only rows are given
            x, y = item, slice(0, self.shape[1])
        return self._write_item(x, y, value)


class SweepTable(Table):
    """

    The itc sweep table subsystem uses slicing notation to access the table.

    E.g.::
        # read complete table
        table = itc.sweep_table[:]

        # reads the first row
        row = itc.sweep_table[0]

        # reads the first element of the first row
        element = itc.sweep_table[0, 0]

        # Reads every second row
        row = itc.sweep_table[::2]

    """
    def __init__(self, transport, protocol):
        super(SweepTable, self).__init__(transport, protocol, shape=(16, 3))
        self._item = Command('r', 's', Float)

    def clear(self):
        """Clears the sweep table."""
        try:
            self._write('w')
        except OxfordIsobus.InvalidRequestError:
            # Wipe command was not recognized. Try manual wiping
            self[:] = 0