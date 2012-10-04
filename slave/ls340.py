#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The ls340 module implements an interface for the Lakeshore model LS340
temperature controller.
"""

from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488
from slave.types import Boolean, Enum, Float, Integer, Set


__all__ = ['scanner', 'LS340']


class Input(InstrumentBase):
    """Represents a LS340 input channel.

    :param connection: A connection object.
    :param name: A string value indicating the input in use.
    :ivar alarm: The alarm configuration, represented by the following list
        *[<enabled>, <source>, <high value>, <low value>, <latch>, <relay>]*,
        where:
        * *<enabled>* Enables or disables the alarm.
        * *<source>* Specifies the input data to check.
        * *<high value>* Sets the upper limit, where the high alarm sets off.
        * *<low value>* Sets the lower limit, where the low alarm sets off.
        * *<latch>* Enables or disables a latched alarm.
        * *<relay>* Specifies if the alarm can affect the relays.
    :ivar alarm_status: The high and low alarm status, represented by the
        following list: *[<high status>, <low status>]*.
    :ivar celsius: The input value in celsius.
    :ivar filter: The input filter parameters, represented by the following
        list: *[<enable>, <points>, <window>]*.
    :ivar set: The input setup parameters, represented by the following list:
        *[<enable>, <compensation>]*
    :ivar curve: The input curve number. An Integer in the range [0-60].
    :ivar input_type: The input type configuration, represented by the
        list: *[<type>, <units>, <coefficient>, <excitation>, <range>]*, where
        * *<type>* Is the input sensor type.
        * *<units>* Specifies the input sensor units.
        * *<coefficient>* The input coefficient.
        * *<excitation>* The input excitation.
        * *<range>* The input range.
    :ivar kelvin: The kelvin reading.
    :ivar linear: The linear equation data.
    :ivar linear_status: The linear status register.

    """
    def __init__(self, connection, name):
        super(Input, self).__init__(connection)
        self.name = name = str(name)
        self.alarm = Command('ALARM? {0}'.format(name),
                             'ALARM {0}'.format(name),
                             [Boolean,
                              Enum('kelvin', 'celsius', 'sensor', 'linear'),
                              Float, Float, Boolean, Boolean])
        self.alarm_status = Command(('ALARMST?', [Boolean, Boolean]))
        self.celsius = Command(('CRDG? {0}'.format(name), Float))
        self.filter = Command('FILTER? {0}'.format(name),
                              'FILTER {0}'.format(name),
                              [Boolean, Integer(min=0),
                               Integer(min=0, max=100)])
        self.set = Command('INSET? {0}'.format(name),
                           'INSET {0}'.format(name),
                           [Boolean, Enum('off', 'on', 'pause')])
        self.curve = Command('INCRV? {0}'.format(name),
                             'INCRV {0}'.format(name),
                             Integer(min=0, max=60))
        self.input_type = Command('INTYPE? {0}'.format(name),
                                  'INTYPE {0}'.format(name),
                                  [Enum('special', 'Si', 'GaAlAs',
                                        'Pt100 250 Ohm', 'Pt100 500 Ohm',
                                        'Pt1000', 'RhFe', 'Carbon-Glass',
                                        'Cernox', 'RuOx', 'Ge', 'Capacitor',
                                        'Thermocouple'),
                                   Enum('special', 'volt', 'ohm'),
                                   Enum('special', '-', '+'),
                                   # XXX Volt and Ampere?
                                   Enum('off', '30nA', '100nA', '300nA', '1uA',
                                        '3uA', '10uA', '30uA', '100uA',
                                        '300uA', '1mA', '10mV', '1mV'),
                                   Enum('1mV', '2.5mV', '5mV', '10mV', '25mV',
                                        '50mV', '100mV', '250mV', '500mV',
                                        '1V', '2.5V', '5V', '7.5V', start=0)])
        self.kelvin = Command(('KRDG? {0}'.format(name), Float))
        self.linear = Command(('LDAT? {0}'.format(name), Float))
        # TODO use register instead of Integer
        self.linear_status = Command(('LDATST? {0}'.format(name), Integer))


class Output(InstrumentBase):
    """Represents a LS340 analog output.

    :param connection: A connection object.
    :param channel: The analog output channel. Valid are either 1 or 2.

    :ivar analog: The analog output parameters, represented by the following
        list: *[<bipolar>, <mode>, <input>, <source>, <high>, <low>, <manual>]*
        where:
        * *<bipolar>* Enables bipolar output.
        * *<mode>* Valid entries are `'off'`, `'input'`, `'manual'`, `'loop'`.
          `'loop'` is only valid for the output channel 2.
        * *<input>* Selects the input to monitor. (Has no effect if mode is not
          `'input'`)
        * *<source>* Selects the input data, either `'kelvin'`, `'celsius'`,
          `'sensor'` or `'linear'`.
        * *<high>* Represents the data value at which 100% is reached.
        * *<low>* Represents the data value at which the minimum value is
            reached (-100% for bipolar, 0% otherwise).
        * *<manual>* Represents the data value of the analog output in manual
            mode.

    """
    def __init__(self, connection, channel):
        super(Output, self).__init__(connection)
        if not channel in (1, 2):
            raise ValueError('Invalid Channel number. Valid are either 1 or 2')
        self.channel = channel
        self.analog = Command('ANALOG? {0}'.format(channel),
                              'ANALOG {0}'.format(channel),
                              [Boolean,
                               Enum('off', 'input', 'manual', 'loop'),
                               #INPUT,
                               Enum('kelvin', 'celsius', 'sensor', 'linear',
                                    start=1),
                               Float, Float, Float])
        self.value = Command(('AOUT? {0}'.format(channel), Float))


class Loop(InstrumentBase):
    """Represents a LS340 control loop.

    :ivar filter: The loop filter state.
    :ivar limit: The limit configuration, represented by the following list
        *[<limit>, <pos slope>, <neg slope>, <max current>, <max range>]*
    :ivar manual_output: The manual output value.
    :ivar mode: The control-loop mode. Valid entries are
        *'manual', 'zone', 'open', 'pid', 'pi', 'p'*
    :ivar parameters: The control loop parameters, a list containing
        *[<input('A', 'B')>, <units('kelvin', 'celsius', 'sensor')>, <enabled>,
        <powerup>]*.
    :ivar pid: The PID values.
    :ivar ramp: The control-loop ramp parameters, represented by the following
        list *[<enabled>, <rate>]*, where
         * *<enabled>*  Enables, disables the ramping.
         * *<rate>* Specifies the ramping rate in kelvin/minute.
    :ivar ramping: The ramping status. `True` if ramping and `False` otherwise.
    :ivar setpoint: The control-loop setpoint in its configured units.

    """
    def __init__(self, connection, idx):
        super(Loop, self).__init__(connection)
        self.idx = idx = int(idx)
        self.filter = Command('CFILT? {0}'.format(idx),
                              'CFILT {0}'.format(idx),
                              Boolean)
        self.limit = Command('CLIMIT? {0}'.format(idx),
                             'CLIMIT {0}'.format(idx),
                             [Float, Float, Float,
                              Enum(0.25, 0.5, 1., 2., start=1),
                              Integer(min=0, max=5)])
        # TODO: check limits.
        self.manual_output = Command('MOUT? {0}'.format(idx),
                                     'MOUT {0}'.format(idx),
                                     Float(min=0, max=100))
        self.mode = Command('CMODE? {0}'.format(idx), 'CMODE {0}'.format(idx),
                            Enum('manual', 'zone', 'open', 'pid', 'pi', 'p',
                                 start=1))

        self.parameters = Command('CSET? {0}'.format(idx),
                                  'CSET {0}'.format(idx),
                                  [Set('A', 'B'),
                                   Enum('kelvin', 'celsius', 'sensor',
                                        start=1),
                                   Boolean,
                                   Boolean])
        self.pid = Command('PID? {0}'.format(idx), 'PID {0}'.format(idx),
                           [Float, Float, Float])
        self.ramp = Command('RAMP? {0}'.format(idx), 'RAMP {0}'.format(idx),
                            [Boolean, Float])
        self.ramping = Command(('RAMPST? {0}'.format(idx), Boolean))
        self.setpoint = Command('SETP? {0}'.format(idx),
                                'SETP {0}'.format(idx), Float)


class Scanner(InstrumentBase):
    """Represents a scanner option for the ls340 temperature controller.

    :ivar channels: A tuple with all channel names.

    """
    def __init__(self, connection, channels):
        super(Scanner, self).__init__(connection)
        self.channels = tuple(channels)
        for channel in channels:
            setattr(self, channel.lower(), Input(connection, channel))


def scanner(model):
    """A factory function used to create the different scanner instances.

    :param model: A string representing the different scanner models supported
        by the ls340 temperature controller. Valid entries are:

        * `"3462"`, The dual standard input option card.
        * `"3464"`, The dual thermocouple input option card.
        * `"3465"`, The single capacitance input option card.
        * `"3468"`, The eight channel input option card.

    """
    channels = {
        '3462': ('C', 'D'),
        '3464': ('C', 'D'),
        '3465': ('C'),
        '3468': ('C1', 'C2', 'C3', 'C4', 'D1', 'D2', 'D3', 'D4')
    }
    return Scanner(channels[model])


class LS340(IEC60488):
    """
    Represents a Lakeshore model LS340 temperature controller.

    The LS340 class implements an interface to the Lakeshore model LS340
    temperature controller.

    :param connection: An object, modeling the connection interface, used to
        communicate with the real instrument.
    :param scanner: Sets a scanner option. See :meth:`~slave.ls340.scanner` for
        the available scanner options.

    :ivar a: Input channel a.
    :ivar b: Input channel b.
    :ivar output1: First output channel.
    :ivar output2: Second output channel.
    :ivar beeper: A boolean value representing the beeper mode. `True` means
        enabled, `False` means disabled.
    :ivar beeping: A Integer value representing the current beeper status.
    :ivar busy: A Boolean representing the instrument busy status.
    :ivar com: The serial interface configuration, represented by the following
        list: *[<terminator>, <baud rate>, <parity>]*.

        * *<terminator>* valid entries are `"CRLF"`, `"LFCR"`, `"CR"`, `"LF"`
        * *<baud rate>* valid entries are 300, 1200, 2400, 4800, 9600, 19200
        * *<parity>* valid entries are 1, 2, 3. See LS340 manual for meaning.

    :ivar idn: A list of strings representing the manufacturer, model number,
        serial number and firmware date in this order.
    :ivar mode: Represents the interface mode. Valid entries are
        `"local"`, `"remote"`, `"lockout"`.
    :ivar range: The heater range.
    :ivar loop1: An instance of the Loop class, representing the first control
        loop.
    :ivar loop2: Am instance of the Loop class, representing the second control
        loop.
    :ivar logging: A Boolean value, enabling or disabling data logging.
    :ivar program_status: The status of the currently running program
        represented by the following tuple: *(<program>, <status>)*. If
        program is zero, it means that no program is running.

    """
    PROGRAM_STATUS = [
        'No errors',
        'Too many call commands',
        'Too many repeat commands',
        'Too many end repeat commands',
        'The control channel setpoint is not in temperature',
    ]

    def __init__(self, connection, scanner=None):
        super(LS340, self).__init__(connection)
        self.scanner = scanner
        self.a = Input(connection, 'A')
        self.b = Input(connection, 'B')
        self.output1 = Output(connection, 1)
        self.output2 = Output(connection, 2)
        # Control Commands
        # ================
        self.loop1 = Loop(connection, 1)
        self.loop2 = Loop(connection, 2)
        self.range = Command('RANGE?', 'RANGE', Integer(min=0, max=5))
        # System Commands
        # ===============
        self.beeper = Command('BEEP?', 'BEEP', Boolean)
        self.beeping = Command(('BEEPST?', Integer))
        self.busy = Command(('BUSY?', Boolean))
        self.com = Command('COMM?', 'COMM',
                            [Enum('CRLF', 'LFCR', 'CR', 'LF', start=1),
                             Enum(300, 1200, 2400, 4800, 9600, 19200, start=1),
                             Set(1, 2, 3)])
        self.mode = Command('MODE?', 'MODE',
                            Enum('local', 'remote', 'lockout', start=1))
        # Data Logging Commands
        # =====================
        self.logging = Command('LOG?', 'LOG', Boolean)

        self.program_status = Command(('PGMRUN?',
                                       [Integer, Enum(self.PROGRAM_STATUS)]))

    def clear_alarm(self):
        """Clears the alarm status for all inputs."""
        self.connection.write('ALMRST')
