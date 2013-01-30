# -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS. Licensed under the GNU GPL.
from slave.core import Command
from slave.types import Enum, Float, Integer
from slave.iec60488 import IEC60488


class PPMS(IEC60488):
    """A Quantum Design Model 6000 PPMS.

    .. note::

        The ppms needs a newĺine '\\\\n' character as message terminator. Using
        delay between read and write operations is recommended as well.

    :ivar advisory_number: The advisory code number, a read only integer in the
        range 0 to 999.
    :ivar chamber: The configuration of the sample chamber. Valid entries are
        'seal', 'purge seal', 'vent seal', 'pump' and 'vent', where

        * 'seal' seals the chamber immediately.
        * 'purge seal' purges and then seals the chamber.
        * 'vent seal' ventilates and then seals the chamber.
        * 'pump' pumps the chamber continuously.
        * 'vent' ventilates the chamber continuously.

    :ivar field: The magnetic field configuration, represented by the following
        tuple *(<field>, <rate>, <approach mode>, <magnet mode>)*, where

        * *<field>* is the magnetic field setpoint in Oersted with a
          resolution of 0.01 Oersted. The min and max fields depend on the
          magnet used.
        * *<rate>* is the ramping rate in Oersted/second with a resolution of
          0.1 Oersted/second. The min and max values depend on the magnet
          used.
        * *<approach mode>* is the approach mode, either 'linear',
          'no overshoot' or 'oscillate'.
        * *<magnet mode>* is the state of the magnet at the end of the
          charging process, either 'persistent' or 'driven'.

    :ivar temperature: The temperature configuration, a tuple consisting of
        *(<temperature>, <rate>, <approach mode>)*, where

        * *<temperature>* The temperature settpoint in kelvin in the range 1.9
          to 350.
        * *<rate>* The sweep rate in kelvin per minute in the range 0 to 20.
        * *<approach mode>* The approach mode, either 'fast' or 'no overshoot'.

    """
    def __init__(self, connection):
        super(PPMS, self).__init__(connection)
        self.advisory_number = Command(('ADVNUM?', Integer(min=0, max=999)))
        self.chamber = Command(
            'CHAMBER?',
            'CHAMBER',
            Enum('seal', 'purge seal', 'vent seal', 'pump', 'vent')
        )
        # TODO Allow for configuration of the ranges
        self.field = Command(
            'FIELD?',
            'FIELD',
            (
                Float(min=-9e4, max=9e4, fmt='{0:.2f}'),
                Float(min=10.5, max=196., fmt='{0:.1f}'),
                Enum('linear', 'no overshoot', 'oscillate'),
                Enum('persistent', 'driven')
            )
        )
        self.temperature = Command(
            'TEMP?',
            'TEMP',
            (
                Float(min=1.9, max=350.),
                Float(min=0., max=20),
                Enum('fast', 'no overshoot')
            )
        )

    def beep(self, duration, frequency):
        """Generates a beep.

        :param duration: The duration in seconds, in the range 0.1 to 5.
        :param frequency: The frequency in Hz, in the range 500 to 5000.

        """
        cmd = 'BEEP', [Float(min=0.1, max=5.0), Integer(min=500, max=5000)]
        self._write(cmd, duration, frequency)

    def shutdown(self):
        """The temperature controller shutdown.

        Invoking this method puts the PPMS in standby mode, both drivers used
        to control the system temperature are turned off and helium flow is set
        to a minimum value.

        """
        self._write('SHUTDOWN')
