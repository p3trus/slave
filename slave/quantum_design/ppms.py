# -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS. Licensed under the GNU GPL.
import datetime
import time

from slave.core import Command
from slave.types import Enum, Float, Integer
from slave.iec60488 import IEC60488

# Temperature controller status code.
STATUS_TEMPERATURE = {
    0x0: 'unknown',
    0x1: 'normal stability at target temperature',
    0x2: 'stable',
    0x5: 'within tolerance, waiting for equilibrium',
    0x6: 'temperature not in tolerance, not valid',
    0x7: 'filling/emptying reservoir',
    0xa: 'standby mode invoked',
    0xd: 'temperature control disabled',
    0xe: 'request cannot complete, impedance not functioning',
    0xf: 'failure',
}

#: Magnet status codes.
STATUS_MAGNET = {
    0x0: 'unknown',
    0x1: 'persistent, stable',
    0x2: 'persist switch warming',
    0x3: 'persist switch cooling',
    0x4: 'driven, stable',
    0x5: 'driven, final approach',
    0x6: 'charging',
    0x7: 'discharging',
    0x8: 'current error',
    0xf: 'failure',
}

#: Chamber status codes.
STATUS_CHAMBER = {
    0x0: 'unknown',
    0x1: 'purged, sealed',
    0x2: 'vented, sealed',
    0x3: 'sealed, condition unknown',
    0x4: 'performing purge/seal',
    0x5: 'performing vent/seal',
    0x8: 'pumping continuously',
    0x9: 'venting continuously',
    0xf: 'failure',
}

#: Sample Position status codes.
STATUS_SAMPLE_POSITION = {
    0x0: 'unknown',
    0x1: 'stopped',
    0x5: 'moving',
    0x8: 'limit',
    0x9: 'index',
    0xf: 'failure',
}


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

    :ivar system_status: The general system status.

    .. rubric:: Magnet Control

    :ivar field: The current magnetic field in Oersted(read only).
    :ivar target_field: The magnetic field configuration, represented by the following
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

    .. rubric:: Temperature Control

    :ivar temperature: The temperature at the sample position in Kelvin
        (read only).
    :ivar target_temperature: The temperature configuration, a tuple consisting of
        *(<temperature>, <rate>, <approach mode>)*, where

        * *<temperature>* The temperature setpoint in kelvin in the range 1.9
          to 350.
        * *<rate>* The sweep rate in kelvin per minute in the range 0 to 20.
        * *<approach mode>* The approach mode, either 'fast' or 'no overshoot'.

    .. rubric:: Sample Position

    :ivar move_config: The move configuration, a tuple consisting of
        *(<unit>, <unit/step>, <range>)*, where

        * *<unit>* The unit, valid are 'steps', 'degree', 'radian', 'mm', 'cm',
          'mils' and 'inch'.
        * *<unit/step>* the units per step.
        * *<range>* The allowed travel range.

    :ivar move_limits: The position of the limit switch and the max travel
        limit, represented by the following tuple
        *(<lower limit>, <upper limit>)*, where

        * *<lower limit>* The lower limit represents the position of the limit
          switch in units specified by the move configuration.
        * *<upper limit>* The upper limit in units specified by the move
          configuration. It is defined by the position of the limit switch and
          the configured travel range.

        (read only)

    :ivar position: The current sample position.

    """
    def __init__(self, transport):
        super(PPMS, self).__init__(transport)
        self.advisory_number = Command(('ADVNUM?', Integer(min=0, max=999)))
        self.chamber = Command(
            'CHAMBER?',
            'CHAMBER',
            Enum('seal', 'purge seal', 'vent seal', 'pump', 'vent')
        )
        self.move_config = Command(
            'MOVECFG?',
            'MOVECFG',
            (
                Enum('steps', 'degree', 'radian', 'mm', 'cm', 'mils', 'inch'),
                Float,  # Units per step
                Float  # The total range
            )
        )
        self.sample_position = Command(('GETDAT? 8', Float))
        # TODO Allow for configuration of the ranges
        self.target_field = Command(
            'FIELD?',
            'FIELD',
            (
                Float(min=-9e4, max=9e4, fmt='{0:.2f}'),
                Float(min=10.5, max=196., fmt='{0:.1f}'),
                Enum('linear', 'no overshoot', 'oscillate'),
                Enum('persistent', 'driven')
            )
        )
        # TODO Allow for the configuration of the ranges
        self.target_temperature = Command(
            'TEMP?',
            'TEMP',
            (
                Float(min=1.9, max=350.),
                Float(min=0., max=20),
                Enum('fast', 'no overshoot')
            )
        )

    @property
    def field(self):
        """The field at sample position."""
        # omit dataflag and timestamp
        return self._query(('GETDAT? 4', (Integer, Float, Float)))[2]

    @property
    def system_status(self):
        """The system status codes."""
        flag, timestamp, status = self._query(('GETDAT? 1', (Integer, Float, Integer)))
        return {
            # convert unix timestamp to datetime object
            'timestamp': datetime.datetime.fromtimestamp(timestamp),
            # bit 0-3 represent the temperature controller status
            'temperature': STATUS_TEMPERATURE[status & 0xf],
            # bit 4-7 represent the magnet status
            'magnet': STATUS_MAGNET[(status >> 4) & 0xf],
            # bit 8-11 represent the chamber status
            'chamber': STATUS_CHAMBER[(status >> 8) & 0xf],
            # bit 12-15 represent the sample position status
            'sample_position': STATUS_SAMPLE_POSITION[(status >> 12) & 0xf],
        }

    @property
    def temperature(self):
        "The current temperature at the sample position."
        # omit dataflag and timestamp
        return self._query(('GETDAT? 2', (Integer, Float, Float)))[2]

    def beep(self, duration, frequency):
        """Generates a beep.

        :param duration: The duration in seconds, in the range 0.1 to 5.
        :param frequency: The frequency in Hz, in the range 500 to 5000.

        """
        cmd = 'BEEP', [Float(min=0.1, max=5.0), Integer(min=500, max=5000)]
        self._write(cmd, duration, frequency)

    def move(self, position, slowdown=0):
        """Move to the specified sample position.

        :param position: The target position.
        :param slowdown: The slowdown code, an integer in the range 0 to 14,
            used to scale the stepper motor speed. 0, the default, is the
            fastest rate and 14 the slowest.

        """
        cmd = 'MOVE', [Float, Integer, Integer(min=0, max=14)]
        self._write(cmd, position, 0, slowdown)

    def move_to_limit(self, position):
        """Move to limit switch and define it as position.

        :param position: The new position of the limit switch.

        """
        cmd = 'MOVE', [Float, Integer]
        self._write(cmd, position, 1)

    def redefine_position(self, position):
        """Redefines the current position to the new position.

        :param position: The new position.

        """
        cmd = 'MOVE', [Float, Integer]
        self._write(cmd, position, 2)

    def scan_temperature(self, measure, temperature, rate, delay=1):
        """Performs a temperature scan.

        :param measure: A callable called repeatedly until stability at target
            temperature is reached.
        :param temperature: The target temperature in kelvin.
        :param rate: The sweep rate in kelvin per minute.
        :param delay: The time delay between each call to measure in seconds.

        """
        if not hasattr(measure, '__call__'):
            raise TypeError('measure parameter not callable.')

        self.set_temperature(temperature, rate, 'no overshoot', wait_for_stability=False)
        while True:
            if self.system_status['temperature'] == 'normal stability at target temperature':
                break
            measure()
            time.sleep(delay)

    def set_field(self, field, rate, approach='linear', mode='persistent',
                  wait_for_stability=True, delay=1):
        """Sets the magnetic field.

        :param field: The target field in Oersted.

            .. note:: The conversion is 1 Oe = 0.1 mT.

        :param rate: The field rate in Oersted per minute.
        :param approach: The approach mode, either 'linear', 'no overshoot' or
            'oscillate'.
        :param mode: The state of the magnet at the end of the charging
            process, either 'persistent' or 'driven'.
        :param wait_for_stability: If `True`, the function call blocks until
            the target field is reached and stable.
        :param delay: Specifies the frequency in seconds how often the magnet
            status is checked. (This has no effect if wait_for_stability is
            `False`).

        """
        self.target_field = field, rate, approach, mode
        if wait_for_stability and (mode == 'persistent'):
            # Wait a few seconds because the ppms does not update the field
            # status fast enough.
            time.sleep(10)
        while wait_for_stability:
            if self.system_status['magnet'] == 'persistent, stable':
                break
            time.sleep(delay)

    def set_temperature(self, temperature, rate, mode='fast', wait_for_stability=True, delay=1):
        """Sets the temperature.

        :param temperature: The target temperature in kelvin.
        :param rate: The sweep rate in kelvin per minute.
        :param mode: The sweep mode, either 'fast' or 'no overshoot'.
        :param wait_for_stability: If wait_for_stability is `True`, the function call blocks
            until the target temperature is reached and stable.
        :param delay: The delay specifies the frequency how often the status is checked.

        """
        self.target_temperature = temperature, rate, mode
        while wait_for_stability:
            status = self.system_status['temperature']
            if status == 'normal stability at target temperature':
                break
            time.sleep(delay)

    def shutdown(self):
        """The temperature controller shutdown.

        Invoking this method puts the PPMS in standby mode, both drivers used
        to control the system temperature are turned off and helium flow is set
        to a minimum value.

        """
        self._write('SHUTDOWN')
