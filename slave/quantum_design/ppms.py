# -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS. Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

import datetime
import time

from slave.driver import Command, CommandSequence, Driver
from slave.types import Enum, Float, Integer, Register, String
from slave.iec60488 import IEC60488
import slave.protocol

#: Temperature controller status code.
STATUS_TEMPERATURE = {
    0x0: 'unknown',
    0x1: 'normal stability at target temperature',
    0x2: 'tracking',
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
    0x6: 'pre pump',
    0x7: 'high vacuum',
    0x8: 'pumping continuously',
    0x9: 'venting continuously',
    0xe: 'high vacuum error',
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

#: Status of digital input lines.
STATUS_DIGITAL_INPUT = {
    0x1: 'Motor Port - Limit 1',
    0x2: 'Motor Port - Limit 2',
    0x3: 'Aux Port - Sense 1',
    0x4: 'Aux Port - Sense 2',
    0x5: 'Ext Port - Busy',
    0x6: 'Ext Port - User',
}

#: Status of the digital output lines.
STATUS_DIGITAL_OUTPUT = {
    0x0: 'Drive Line 1',
    0x1: 'Drive Line 2',
    0x2: 'Drive Line 3',
    0x3: 'Actuator Drive'
}

#: Status of the external select lines.
STATUS_EXTERNAL_SELECT = {
    0x0: 'Select 1',
    0x1: 'Select 2',
    0x2: 'Select 3',
}

#: The linking status.
STATUS_LINK = {
    0: None,
    1: 'Temperature',
    2: 'Tield',
    3: 'Position',
    4: 'User Bridge CH1 Ohm',
    5: 'User Bridge CH1 A',
    6: 'User Bridge CH2 Ohm',
    7: 'User Bridge CH2 A',
    8: 'User Bridge CH3 OHM',
    9: 'User Bridge CH3 A',
    10: 'User Bridge CH4 Ohm',
    11: 'User Bridge CH4 A',
    12: 'Signal Input CH1',
    13: 'Signal Input CH2',
    14: 'Digital Input Aux, Ext',
    15: 'User Driver CH1 mA',
    16: 'User Driver CH1 W',
    17: 'User Driver CH2 mA',
    18: 'User Driver CH2 W',
    19: 'Sample Space Pressure',
    20: 'User Mapped Item',
    21: 'User Mapped Item',
    22: 'User Mapped Item',
    23: 'User Mapped Item',
    24: 'User Mapped Item',
    25: 'User Mapped Item',
    26: 'User Mapped Item',
    27: 'User Mapped Item',
    28: 'User Mapped Item',
    29: 'User Mapped Item',
}


class PPMS(IEC60488):
    """A Quantum Design Model 6000 PPMS.

    :param transport: A transport object.
    :param max_field: The maximum magnetic field allowed in Oersted. If `None`,
        the default, it's read back from the ppms.

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

    :ivar sample_space_pressure: The pressure of the sample space in user units.
        (read only)
    :ivar system_status: The general system status.

    .. rubric:: Configuration

    :ivar bridges: A list of :class:`~.BridgeChannel` instances representing all
        four user bridges.

        .. note::

            Python indexing starts at 0, so the first bridge has the index 0.


    :ivar date: The configured date of the ppms computer represented by a python
        `datetime.date` object.
    :ivar time: The configured time of the ppms computer, represented by a python
        `datetime.time` object.
    :ivar analog_output: A tuple of :class:`~.AnalogOutput` instances
        corresponding to the four analog outputs.
    :ivar digital_input: The states of the digital input lines.
        A dict with the following keys

        ====================== ========
        Keys                   Pinouts
        ====================== ========
        'Motor Port - Limit 1' P10-4,5
        'Motor Port - Limit 2' P10-9,5
        'Aux Port - Sense 1'   P8-18,19
        'Aux Port - Sense 2'   P8-6,19
        'Ext Port - Busy'      P11-9
        'Ext Port - User'      P11-5
        ====================== ========

        A dict value of True means the line is asserted.

        (read only)

    :ivar digital_output: The state of the digital output lines. A dict with
        the following keys

        ================ ============== =======
        Keys             Connector Port Pinouts
        ================ ============== =======
        'Drive Line 1'   Auxiliary Port P8-1,14
        'Drive Line 2'   Auxiliary Port P8-2,15
        'Drive Line 3'   Auxiliary Port P8-3,16
        'Actuator Drive' Motor Port     P10-3,8
        ================ ============== =======

        A dict value of `True` means the line is set to -24 V output.
        Setting it with a dict containing only some keys will only change these.
        The other lines will be left unchanged.

    :ivar driver_output: A :class:`CommandSequence` representing the driver
        outputs of channel 1 and 2. Each channel is represented by a tuple of
        the form *(<current>, <power limit>)*, where

         * *<current>* is the current in mA, in the range 0 to 1000.
         * *<power limit>* is the power limit in W, in the range 0 to 20.

         .. note::

            Python indexing starts with 0. Therefore channel 1 has the index 0.

    :ivar external_select: The state of the external select lines. A dict with
        the following keys

        ====== =============== =======
        Key    Connector Port  Pinouts
        ====== =============== =======
        Select 1 External Port P11-1,6
        Select 2 External Port P11-2,7
        Select 3 External Port P11-3,8
        ====== =============== =======

        A dict value of `True` means the line is asserted (switch closed).
        Setting it with a dict containing only some keys will only change these.
        The other lines will be left unchanged.

    :ivar revision: The revision number. (read only)

    .. rubric:: Helium Level Control

    :ivar level: The helium level, represented by a tuple of the form
        *(<level>, <age>)*, where

        * *<level>* The helium level in percent.
        * *<age>* is the age of the reading. Either '>1h', '<1h' or
          'continuous'.

    .. rubric:: Magnet Control

    :ivar field: The current magnetic field in Oersted(read only).
    :ivar target_field: The magnetic field configuration, represented by the
        following tuple *(<field>, <rate>, <approach mode>, <magnet mode>)*,
        where

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

    :ivar magnet_config: The magnet configuration represented by the following
        tuple *(<max field>, <B/I ratio>, <inductance>, <low B charge volt>,*
        *<high B charge volt>, <switch heat time>, <switch cool time>)*, where

        * *<max field>* is the max field of the magnet in Oersted.
        * *<B/I ratio>* is the field to current ratio in Oersted/A.
        * *<inductance>* is the inductance in Henry.
        * *<low B charge volt>* is the charging voltage at low B fields in volt.
        * *<high B charge volt>* is the chargin voltage at high B fields in
          volt.
        * *<switch heat time>* is the time it takes to open the persistent
          switch in seconds.
        * *<switch cool time>* is the time it takes to close the persistent
          switch in seconds.

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

    .. rubric:: Temperature Control

    :ivar temperature: The temperature at the sample position in Kelvin
        (read only).
    :ivar target_temperature: The temperature configuration, a tuple consisting of
        *(<temperature>, <rate>, <approach mode>)*, where

        * *<temperature>* The temperature setpoint in kelvin in the range 1.9
          to 350.
        * *<rate>* The sweep rate in kelvin per minute in the range 0 to 20.
        * *<approach mode>* The approach mode, either 'fast' or 'no overshoot'.

    """
    def __init__(self, transport, max_field=None):
        # The PPMS uses whitespaces to separate data and semicolon to terminate
        # a message.
        protocol = slave.protocol.IEC60488(
            msg_data_sep=',',
            msg_term=';',
            resp_data_sep=',',
            resp_term=';'
        )
        super(PPMS, self).__init__(transport, protocol)
        self.advisory_number = Command(('ADVNUM?', Integer(min=0, max=999)))
        self.chamber = Command(
            'CHAMBER?',
            'CHAMBER',
            Enum('seal', 'purge seal', 'vent seal', 'pump', 'vent')
        )
        self.sample_space_pressure = Command(('GETDAT? 524288', Float))
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
        self.magnet_config = Command(
            'MAGCNF?',
            'MAGCNF',
            [Float] * 5 + [Integer, Integer]
        )
        if max_field is None:
            max_field = self.magnet_config[0]

        self.target_field = Command(
            'FIELD?',
            'FIELD',
            (
                Float(min=-max_field, max=max_field, fmt='{0:.2f}'),
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
        self.digital_input = Command(('DIGIN?', Register(STATUS_DIGITAL_INPUT)))
        cmds = [
            Command(
                'DRVOUT? {}'.format(i),
                'DRVOUT {} '.format(i),
                [Float(min=0, max=1000.), Float(min=0., max=20.)])
            for i in range(1, 3)
        ]
        self.driver_output = CommandSequence(
            self._transport,
            self._protocol,
            [
                Command(
                    'DRVOUT? {}'.format(i),
                    'DRVOUT {} '.format(i),
                    [Float(min=0, max=1000.), Float(min=0., max=20.)]
                ) for i in range(1, 3)
            ]
        )
        self.bridge = [
            BridgeChannel(self._transport, self._protocol, i) for i in range(1, 5)
        ]
        self.level = Command((
            'LEVEL?',
            [Float, Enum('>1h', '<1h', 'continuous')]
        ))
        self.revision = Command(('REV?', [String, String]))

    def levelmeter(self, rate):
        """Changes the measuring rate of the levelmeter.

        :param rate: Valid are 'on', 'off', 'continuous' and 'hourly'. 'on'
            turns on the level meter, takes a reading and turns itself off.
            In 'continuous' mode, the readings are constantly updated. If no
            reading is requested within 60 seconds, the levelmeter will be
            turned off. 'off' turns off hourly readings.

        .. note::
            It takes approximately 10 seconds until a measured level is
            available.

        """
        # TODO: Check what 'off' actually does. Manual says it just deactivates
        # hourly readings and opcode 0 should be used to deactivate.
        self._write(('LEVELON', Enum('on', 'continuous', 'hourly', 'off')), rate)

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

    @property
    def digital_output(self):
        return self._query(('DIGSET', Register(STATUS_DIGITAL_OUTPUT)))

    @digital_output.setter
    def digital_output(self, value):
        # Constructs a mask, where the values are False if the key is missing.
        mask = {k: k not in value for k in STATUS_DIGITAL_OUTPUT.values()}
        type = Register(STATUS_DIGITAL_OUTPUT)
        self._write(('DIGSET', [type, type]), value, mask)

    @property
    def external_select(self):
        return self._query(('EXTSET?', Register(STATUS_EXTERNAL_SELECT)))

    @external_select.setter
    def external_select(self, value):
        # Constructs a mask, where the values are False if the key is missing.
        mask = {k: k not in value for k in STATUS_EXTERNAL_SELECT.values()}
        type = Register(STATUS_EXTERNAL_SELECT)
        self._write(('DIGSET', [type, type]), value, mask)

    @property
    def date(self):
        month, day, year = self._query(('DATE?', [Integer, Integer, Integer]))
        return datetime.date(2000 + year, month, day)

    @date.setter
    def date(self, date):
        # The ppms only accepts the last two digits of the year.
        month, date, year = date.month, date.day, date.year % 100
        self._write(('DATE', [Integer, Integer, Integer]), month, date, year)

    @property
    def time(self):
        hour, minutes, seconds = self._query(('TIME?', [Integer, Integer, Integer]))
        return datetime.time(hour, minutes, seconds)

    @time.setter
    def time(self, time):
        self._write(
            ('TIME', [Integer, Integer, Integer]),
            time.hour, time.minute, time.second
        )

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

        Measures until the target temperature is reached.

        :param measure: A callable called repeatedly until stability at target
            temperature is reached.
        :param temperature: The target temperature in kelvin.
        :param rate: The sweep rate in kelvin per minute.
        :param delay: The time delay between each call to measure in seconds.

        """
        if not hasattr(measure, '__call__'):
            raise TypeError('measure parameter not callable.')

        self.set_temperature(temperature, rate, 'no overshoot', wait_for_stability=False)
        start = datetime.datetime.now()
        while True:
            # The PPMS needs some time to update the status code, we therefore ignore it for 10s.
            if (self.system_status['temperature'] == 'normal stability at target temperature' and
                (datetime.datetime.now() - start > datetime.timedelta(seconds=10))):
                break
            measure()
            time.sleep(delay)

    def scan_field(self, measure, field, rate, mode='persistent', delay=1):
        """Performs a field scan.

        Measures until the target field is reached.

        :param measure: A callable called repeatedly until stability at the
            target field is reached.
        :param field: The target field in Oersted.

            .. note:: The conversion is 1 Oe = 0.1 mT.

        :param rate: The field rate in Oersted per minute.
        :param mode: The state of the magnet at the end of the charging
            process, either 'persistent' or 'driven'.
        :param delay: The time delay between each call to measure in seconds.

        :raises TypeError: if measure parameter is not callable.

        """
        if not hasattr(measure, '__call__'):
            raise TypeError('measure parameter not callable.')
        self.set_field(field, rate, approach='linear', mode=mode, wait_for_stability=False)
        if self.system_status['magnet'].startswith('persist'):
            # The persistent switch takes some time to open. While it's opening,
            # the status does not change.
            switch_heat_time = datetime.timedelta(seconds=self.magnet_config[5])
            start = datetime.datetime.now()
            while True:
                now = datetime.datetime.now()
                if now - start > switch_heat_time:
                    break
                measure()
                time.sleep(delay)
        while True:
            status = self.system_status['magnet']
            if status in ('persistent, stable', 'driven, stable'):
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
        if wait_for_stability and self.system_status['magnet'].startswith('persist'):
            # Wait until the persistent switch heats up.
            time.sleep(self.magnet_config[5])

        while wait_for_stability:
            status = self.system_status['magnet']
            if status in ('persistent, stable', 'driven, stable'):
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
        start = datetime.datetime.now()
        while wait_for_stability:
            # The PPMS needs some time to update the status code, we therefore ignore it for 10s.
            if (self.system_status['temperature'] == 'normal stability at target temperature' and
                (datetime.datetime.now() - start > datetime.timedelta(seconds=10))):
                break
            time.sleep(delay)

    def shutdown(self):
        """The temperature controller shutdown.

        Invoking this method puts the PPMS in standby mode, both drivers used
        to control the system temperature are turned off and helium flow is set
        to a minimum value.

        """
        self._write('SHUTDOWN')


class AnalogOutput(Driver):
    """Represents an analog output.

    :ivar id: The analog output id.
    :ivar voltage: The voltage present at the analog output channel.

        .. note:: Setting the voltage removes any linkage.

    :ivar link: Links a parameter to this analog output. It has the form
        *(<link>, <full>, <mid>)*, where

        * *<link>* is the parameter to link. See :data:`~.STATUS_LINK` for
          valid links.
        * *<full>* the value of the parameter corresponding to full scale output
          (10 V).
        * *<mid>* the value of the parameter corresponding to mid sclae output
          (0 V).

    """
    def __init__(self, transport, protocol, id):
        super(AnalogOutput, self).__init__(transport, protocol)
        self.id = id
        self.voltage = Command(
            'SIGOUT? {}'.format(self.id),
            'SIGOUT {} '.format(self.id),
            Float(min=-10., max=10.)
        )

    @property
    def link(self):
        link, full, mid = self._query((
            'LINK? {}'.format(self.id),
            [Register(STATUS_LINK), Float, Float]
        ))
        for kex, value in link.items():
            if value is True:
                return key, full, mid

    @link.setter
    def link(self, link, full, mid):
        self._write(
            ('LINK {} '.format(self.id), [Register(STATUS_LINK), Float, Float]),
            {link: True},
            full,
            mid
        )

class BridgeChannel(Driver):
    """Represents the user bridge configuration.

    :ivar id: The user bridge channel id.
    :ivar config: The bridge configuration, represented by a tuple of the form
        *(<excitation>, <power limit>, <dc flag>, <mode>, <unknown>)*, where

        * *<excitation>* The excitation current in microamps from 0.01 to 5000.
        * *<power limit>* The maximum power to be applied in microwatts from
            0.001 to 1000.
        * *<dc flag>* Selects the excitation type. Either 'AC' or 'DC'. 'AC'
            corresponds to a square wave excitation of 7.5 Hz.
        * *<mode>* Configures how often the internal analog-to-digital converter
            recalibrates itself. Valid are 'standart', 'fast' and 'high res'.

    :ivar resistance: The resistance of the user channel in ohm.
    :ivar current: The current of the user channel in microamps.

    """
    def __init__(self, transport, protocol, id):
        super(BridgeChannel, self).__init__(transport, protocol)
        self.idx = id
        
        config_type = [
          Float(min=0.01, max=5000.), Float(min=0.001, max=1000.),
          Enum('AC', 'DC'), Enum('standart', 'fast', 'high res')
        ]
        self.config = Command(
            query=('BRIDGE? {}'.format(id), [Integer] + config_type + [Float]),
            write=('BRIDGE {} '.format(id), config_type)
        )
        bit = 2 * (id + 1)
        self.current = Command(('GETDAT? {}'.format(2**(bit + 1), Float)))
        self.resistance = Command(('GETDAT? {}'.format(2**bit), Float))
