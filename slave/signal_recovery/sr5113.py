#  -*- coding: utf-8 -*-
#
# Slave, (c) 2015, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

from slave.driver import Command, CommandSequence, Driver
from slave.types import Boolean, Enum, Integer, String, Register
import slave.protocol


class SR5113(Driver):
    """The signal recovery model 5113 low noise preamp driver.

    :param transport: A transport object.

    :ivar bool backlight: The LCD backlight status.
    :ivar int contrast: The LCD contrast. An integer in the range [0, 15].
    :ivar str identification: Causes the unit to respond with '5113' (read only)
    :ivar str version: The firmware version. (read only)
    :ivar bool remote: The remote lock mode. If `True` the front panel is
        disabled and the unit can only be controlled remotely.
    :ivar status: The system status. A dict with the following keys
        'command done', 'invalid command', 'parameter error', 'overload',
        'low battery' and boolean values. (read only)
    :ivar line: A sequence with two items representing the two lines displayed
        at startup.

    :ivar coarse_gain: The coarse gain setting, see
        :attr:`~SR5113.COARSE_GAIN` for correct values.
    :ivar fine_gain: The fine gain setting, see
        :attr:`~SR5113.FINE_GAIN` for correct values.
    :ivar int gain_vernier: The uncalibrated vernier icreases the gain by a
        maximum of 20% in 15 steps. Valid entries are integers in the range
        [0, 15].
    :ivar input_coupling: The input coupling. Either 'ac' or 'dc'.
    :ivar dynamic_reserve: Configures the dynamic reserve. Either 'low noise' or
        'high reserve'.
    :ivar input_mode: The input mode, either 'A' or 'A-B'.
    :ivar time_constant: The coupling mode time constant, either '1 s' or '10 s'.
    :ivar filter_mode: The filter mode control. See
        :attr:`~SR5113.FILTER_MODE` for valid values.
    :ivar filter_frequency: Defines the cutoff frequencies. A tuple of the form
        *(<mode>, <frequency>)*, where *<mode>* is either 'low' or 'high' and
        *<frequency>* is one of :attr:`~SR5113.FREQUENCIES`.

    """
    #: Allowed coarse gain values.
    COARSE_GAIN = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000]
    #: Allowed fine gain multiplier values
    FINE_GAIN = [0.2, 0.4, 0.6, 0.8, 1., 1.2, 1.4, 1.6, 1.8, 2., 2.2, 2.4, 2.6, 2.8, 3.]
    #: Available filter modes.
    FILTER_MODE = [
        'flat', 'bandpass', 'lowpass 6dB', 'lowpass 12dB', 'lowpass 6/12dB',
        'highpass 6dB', 'highpass 12dB', 'highpass 6/12dB'
    ]
    #: Available cutoff frequencies.
    FREQUENCIES = [
        '0.03 Hz', '0.1 Hz', '0.3 Hz', '1 Hz', '3 Hz', '10 Hz', '30 Hz',
        '100 Hz', '300 Hz', '1 kHz', '3 kHz', '10 kHz', '30 kHz', '100 kHz',
        '300 kHz'
    ]
    STATUS = {
        0: 'command done',
        1: 'invalid command',
        2: 'parameter error',
        3: 'overload',
        4: 'low battery'
    }

    def __init__(self, transport):
        protocol = slave.protocol.IEC60488(
            msg_data_sep=' ', msg_term='\r', resp_data_sep=' ', resp_term='\r'
        )
        super(SR5113, self).__init__(transport, protocol)

        self.backlight = Command('BL', 'BL', Boolean)
        self.contrast = Command('LCD', 'LCD', Integer(min=0, max=15))
        self.identification = Command(query=('ID',  String))
        self.version = Command(query=('VER', String))
        self.remote = Command('REMOTE', 'REMOTE', Enum(True, False))
        self.status = Command(query=('ST', Register(SR5113.STATUS)))
        # TODO check if lines are readable. Check 40 character limit.
        self.line = CommandSequence(
            self._transport,
            self._protocol,
            [
                Command('LINE 1', 'LINE 1\r', String(max=40)),
                Command('LINE 2', 'LINE 2\r', String(max=40)),
            ]
        )

        self.coarse_gain = Command('CG', 'CG', Enum(*SR5113.COARSE_GAIN))
        self.fine_gain = Command('FG', 'FG', Enum(*SR5113.FINE_GAIN))
        self.gain_vernier = Command('GV', 'GV', Integer(min=0, max=15))
        self.input_coupling = Command('CP', 'CP', Enum('ac', 'dc'))
        self.dynamic_reserve = Command(
            'DR',
            'DR',
            Enum('low noise', 'high reserve')
        )
        self.input_mode = Command('IN', 'IN', Enum('A', 'A-B'))
        self.time_constant = Command('TC', 'TC', Enum('1 s', '10 s'))
        self.filter_mode = Command('FLT', 'FLT', Enum(*SR5113.FILTER_MODE))
        self.filter_frequency = Command(
            'FF',
            'FF',
            [Enum('low', 'high'), Enum(*SR5113.FREQUENCIES)]
        )

    def overload_recover(self):
        """Performs an overload recover operation."""
        self._write('OR')

    def sleep(self):
        """Deactivates the digital circuitry."""
        self._write('SLEEP')

    def disable(self):
        """Turns off power to all but the battery charging circuitry.

        .. note:: It's not possible to remotely turn on the device.

        """
        self._write('OFF')
