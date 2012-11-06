#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""

"""

from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488
from slave.types import Boolean, Enum, Float, Integer, Register, Set, String


class Heater(InstrumentBase):
    """An LS370 Heater.

    :param output: The heater output in percent of current or actual power
        dependant on the heater output selection.
    :param range: The heater current range. Valid entries are 'off',
        '31.6 uA', '100 uA', '316 uA', '1 mA', '3.16 mA', '10 mA', '31.6 mA',
        and '100 mA'
    :param status: The heater status, either 'no error' or 'heater open error'.

    """
    def __init__(self, connection):
        super(Heater, self).__init__(connection)
        self.output = Command(('HTR?', Float))
        self.range = Command(
            'HTRRNG?',
            'HTRRNG',
            Enum('off', '31.6 uA', '100 uA', '316 uA', '1 mA',
                 '3.16 mA', '10 mA', '31.6 mA', '100 mA')
        )
        self.status = Command(
            ('HTRST?', Enum('no error', 'heater open error'))
        )

class Output(InstrumentBase):
    """Represents a LS370 analog output.

    :param connection: A connection object.
    :param channel: The analog output channel. Valid are either 1 or 2.

    :ivar analog: The analog output parameters, represented by the tuple
        *(<bipolar>, <mode>, <input>, <source>, <high>, <low>, <manual>)*,
        where:

         * *<bipolar>* Enables bipolar output.
         * *<mode>* Valid entries are 'off', 'channel', 'manual', 'zone',
            'still'. 'still' is only valid for the output channel 2.
         * *<input>* Selects the input to monitor (Has no effect if mode is
           not `'input'`).
         * *<source>* Selects the input data, either 'kelvin', 'ohm', 'linear'.
         * *<high>* Represents the data value at which 100% is reached.
         * *<low>* Represents the data value at which the minimum value is
           reached (-100% for bipolar, 0% otherwise).
         * *<manual>* Represents the data value of the analog output in manual
           mode.
    :ivar value: The value of the analog output.

    """
    def __init__(self, connection, channel):
        super(Output, self).__init__(connection)
        if not channel in (1, 2):
            raise ValueError('Invalid Channel number. Valid are either 1 or 2')
        self.channel = channel
        mode = 'off', 'channel', 'manual', 'zone'
        mode = mode + ('still',) if channel == 2 else mode
        self.analog = Command('ANALOG? {0}'.format(channel),
                              'ANALOG {0},'.format(channel),
                              [Enum('unipolar', 'bipolar'),
                               Enum(*mode),
                               Enum('kelvin', 'ohm', 'linear', start=1),
                               Float, Float, Float])
        self.value = Command(('AOUT? {0}'.format(channel), Float))

class LS370(IEC60488):
    """A lakeshore mode ls370 resistance bridge.

    Represents a Lakeshore model ls370 ac resistance bridge.

    :param connection: A connection object.

    :ivar beeper: A boolean value representing the beeper mode. `True` means
        enabled, `False` means disabled.
    :ivar brightness: The brightness of the frontpanel display in percent.
        Valid entries are `25`, `50`, `75` and `100`.
    :ivar common_mode_reduction: The state of the common mode reduction.
    :ivar control_mode: The temperature control mode, valid entries are
        'closed', 'zone', 'open' and 'off'.
    :ivar digital_output: A register enabling/disabling the digital output
        lines.
    :ivar frequency: The excitation frequency. Valid entries are '9.8 Hz',
        '13.7 Hz' and '16.2 Hz'.

        .. note:: This commands takes several seconds to complete

    :ivar heater: An instance of the :class:`.Heater` class.
    :ivar ieee: The IEEE-488 interface parameters, represented by the following
        tuple *(<terminator>, <EOI enable>, <address>)*, where

        * *<terminator>* is `None`, `\\\\r\\\\n`, `\\\\n\\\\r`, `\\\\r` or
          `\\\\n`.
        * *<EOI enable>* A boolean.
        * *<address>* The IEEE-488.1 address of the device, an integer between
          0 and 30.

    :ivar mode: Represents the interface mode. Valid entries are
        `"local"`, `"remote"`, `"lockout"`.
    :ivar output1: First output channel.
    :ivar output2: Second output channel.
    :ivar polarity: The polarity of the temperature control. Valid entries are
        'unipolar' and 'bipolar'.

    """
    def __init__(self, connection):
        super(LS370, self).__init__(connection)
        self.beeper = Command('BEEP?', 'BEEP', Boolean)
        self.brightness = Command('BRIGT?', 'BRIGT', Enum(25, 50, 75, 100))
        self.common_mode_reduction = Command('CMR?', 'CMR', Boolean)
        self.control_mode = Command(
            'CMODE?',
            'CMODE',
            Enum('closed', 'zone', 'open', 'off', start=1)
        )
        # TODO disable if 3716 scanner option is used.
        self.digital_output = Command(
            'DOUT?',
            'DOUT',
            Register({'DO1': 0, 'DO2': 1, 'DO3': 2, 'DO4': 3, 'DO5': 4}),
        )
        self.frequency = Command(
            'FREQ?',
            'FREQ',
            Enum('9.8 Hz', '13.7 Hz', '16.2 Hz', start=1)
        )
        self.guard = Command('GUARD?', 'GUARD', Boolean)
        self.ieee = Command('IEEE?', 'IEEE',
                            [Enum(None, '\r\n', '\n\r', '\r', '\n'),
                             Boolean,
                             Integer(min=0, max=30)])
        self.mode = Command('MODE?', 'MODE',
                            Enum('local', 'remote', 'lockout', start=1))
        self.output1 = Output(connection, 1)
        self.output2 = Output(connection, 2)
        self.polarity = Command('CPOL?', 'CPOL', Enum('unipolar', 'bipolar'))

    def clear_alarm(self):
        """Clears the alarm status for all inputs."""
        self.connection.write('ALMRST')

    def _factory_default(self, confirm=False):
        """Resets the device to factory defaults.

        :param confirm: This function should not normally be used, to prevent
            accidental resets, a confirm value of `True` must be used.

        """
        if confirm is True:
            self.connection.write('DFLT 99')
        else:
            raise ValueError('Reset to factory defaults was not confirmed.')

    def reset_minmax(self):
        """Resets Min/Max functions for all inputs."""
        self.connection.write('MNMXRST')

