#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The ls340 module implements an interface for the Lakeshore model LS340
temperature controller.

The :class:`~.LS340` class models the excellent `Lakeshore model LS340`_
temperature controller. Using it is simple::

    # We use pyvisa to connect to the controller.
    import visa
    from slave.ls340 import LS340

    # We assume the LS340 is listening on GPIB channel.
    ls340 = LS340(visa.instrument('GPIB::08'))
    # Show kelvin reading of channel A.
    print ls340.a.kelvin

    # Filter channel 'B' data through 10 readings with 2% of full scale window.
    ls340.b.filter = True, 10, 2

Since the :class:`~.LS340` supports different scanner options, these are
supported as well. They extend the available input channels. To use them one
simply passes the model name at construction, e.g.::

    import visa
    from slave.ls340 import LS340

    # We assume the LS340 is equipped with the 3468 eight channel input option
    # card.
    ls340 = LS340(visa.instrument('GPIB::08'), scanner='3468')

    # Show sensor reading of channel D2.
    print ls340.scanner.d2.sensor_units

.. _Lakeshore model LS340: http://www.lakeshore.com/products/cryogenic-tempera\
ture-controllers/model-340/Pages/Overview.aspx

"""

from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488
from slave.types import Boolean, Enum, Float, Integer, Register, Set, String


class Curve(InstrumentBase):
    """Represents a LS340 curve.

    :param connection: A connection object.
    :param idx: The curve index.
    :param writeable: Specifies if the represented curve is read-only or
        writeable as well. User curves are writeable in general.
    :param length: The maximum number of points. Default: 200.

    :ivar header: The curve header configuration.
        *(<name><serial><format><limit><coefficient>)*, where

        * *<name>* The name of the curve, a string limited to 15 characters.
        * *<serial>* The serial number, a string limited to 10 characters.
        * *<format>* Specifies the curve data format. Valid entries are
          `'mV/K'`, `'V/K'`, `'Ohm/K'`, `'logOhm/K'`, `'logOhm/logK'`.
        * *<limit>* The curve temperature limit in Kelvin.
        * *<coefficient>* The curves temperature coefficient. Valid entries are
          `'negative'` and `'positive'`.
    :ivar point: The curve data point

    Points are tuples with the following structure
    *(<units value>, <temp value>)*, where

    * *<units value>* specifies the sensor units for this point.
    * *<temp value>* specifies the corresponding temperature in kelvin.

    To access the points of this curve, use slicing operations, e.g.::

        # assuming an LS340 instance named ls340, the following will print the
        # sixth point.
        print ls340.curve4[5]

        # You can use negative indices. This will print the last point.
        print ls340.curve4[-1]

        # You can use the builtin function `len()` to get the number of points.
        print len(ls340.curve4)

        #Extended slicing is available too. This will print every second point.
        print ls340.curve4[::2]

        # Set this curves data point to 0.10191 sensor units and 470.000 K.
        ls340.curve21[5] = 0.10191, 470.000

    .. warning ::

        In contrast to the LS340 device, point indices start at 0 **not** 1.

    """
    def __init__(self, connection, idx, writeable, length=None):
        super(Curve, self).__init__(connection)
        self.idx = idx = int(idx)
        self.__length = length or 200
        # curves 1-20 are internal and not writeable.
        self._writeable = writeable
        self.header = Command('CRVHDR? {0}'.format(idx),
                              'CRVHDR {0},'.format(idx) if writeable else None,
                              [String(max=15),
                               String(max=10),
                               Enum('mV/K', 'V/K', 'Ohm/K',
                                    'logOhm/K', 'logOhm/logK', start=1),
                               Float(min=0.),
                               Enum('negative', 'positive', start=1)])

    def __len__(self):
        return self.__length

    def __make_index(self, index):
        index = int(index)
        if index < 0:
            index += len(self)
        if 0 <= index < len(self):
            return index
        else:
            raise IndexError()

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return [self[i] for i in range(*indices)]
        # Simple index
        item = self.__make_index(item)
        response_t = [Float, Float]
        data_t = [Integer(min=1), Integer(min=1, max=200)]
        cmd = Command(('CRVPT?', response_t, data_t),
                      connection=self.connection, cfg=self._cfg)
        # Since indices in LS304 start at 1, it must be added.
        return cmd.query((self.idx, item + 1))

    def __setitem__(self, item, value):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            for i in range(*indices):
                self[i] = value[i]
        else:
            item = self.__make_index(item)
            unit, temp = value
            data_t = [Integer(min=1), Integer(min=1, max=200), Float, Float]
            cmd = Command(write=('CRVPT', data_t),
                          connection=self.connection, cfg=self._cfg)
            # Since indices in LS304 start at 1, it must be added.
            cmd.write((self.idx, item + 1, unit, temp))

    def delete(self):
        """Deletes the current curve.

        .. note:: Only writeable curves are deleteable.

        """
        if self._writeable:
            self.connection.write('CRVDEL {0}'.format(self.idx))


class Heater(InstrumentBase):
    """Represents the LS340 heater.

    :param connection: The connection object.

    :ivar output: The heater output in percent.
    :ivar range: The heater range. An integer between 0 and 5, where 0
        deactivates the heater.
    :ivar status: The heater error status.

    """
    ERROR_STATUS = [
        'no error',
        'power supply over voltage',
        'power supply under voltat',
        'output digital-to-analog converter error',
        'current limit digital-to-analog converter error',
        'open heater load',
        'heater load less than 10 ohms',
    ]

    def __init__(self, connection):
        super(Heater, self).__init__(connection)
        self.output = Command(('HTR?', Float))
        self.range = Command('RANGE?', 'RANGE', Integer(min=0, max=5))
        self.status = Command(('HTRST?', Enum(*self.ERROR_STATUS)))


class Input(InstrumentBase):
    """Represents a LS340 input channel.

    :param connection: A connection object.
    :param name: A string value indicating the input in use.

    :ivar alarm: The alarm configuration, represented by the following tuple
        *(<enabled>, <source>, <high value>, <low value>, <latch>, <relay>)*,
        where:

         * *<enabled>* Enables or disables the alarm.
         * *<source>* Specifies the input data to check.
         * *<high value>* Sets the upper limit, where the high alarm sets off.
         * *<low value>* Sets the lower limit, where the low alarm sets off.
         * *<latch>* Enables or disables a latched alarm.
         * *<relay>* Specifies if the alarm can affect the relays.
    :ivar alarm_status: The high and low alarm status, represented by the
        following list: *(<high status>, <low status>)*.
    :ivar celsius: The input value in celsius.
    :ivar curve: The input curve number. An Integer in the range [0-60].
    :ivar filter: The input filter parameters, represented by the following
        tuple: *(<enable>, <points>, <window>)*.
    :ivar input_type: The input type configuration, represented by the
        tuple: *(<type>, <units>, <coefficient>, <excitation>, <range>)*, where

         * *<type>* Is the input sensor type.
         * *<units>* Specifies the input sensor units.
         * *<coefficient>* The input coefficient.
         * *<excitation>* The input excitation.
         * *<range>* The input range.
    :ivar kelvin: The kelvin reading.
    :ivar linear: The linear equation data.
    :ivar linear_equation: The input linear equation parameters.
        *(<equation>, <m>, <x source>, <b source>, <b>)*, where

         * *<equation>* is either `'slope-intercept'` or `'point-slope'`,
           meaning 'y = mx + b' or 'y = m(x + b)'.
         * *<m>* The slope.
         * *<x source>* The input data to use, either 'kelvin', 'celsius' or
           'sensor units'.
         * *<b source>* Either 'value', '+sp1', '-sp1', '+sp2' or '-sp2'.
         * *<b>* The b value if *<b source>* is set to 'value'.
    :ivar linear_status: The linear status register.
    :ivar minmax: The min max data, *(<min>, <max>)*, where

         * *<min>* Is the minimum input data.
         * *<max>* Is the maximum input data.
    :ivar minmax_parameter: The minimum maximum input function parameters.
        *(<on/pause>, <source>)*, where

         * *<on/pause>* Starts/pauses the min/max function. Valid entries are
           `'on'`, `'pause'`.
         * *<source>* Specifies the input data to process. Valid entries are
           `'kelvin'`, `'celsius'`, `'sensor units'` and `'linear'`.
    :ivar minmax_status: The min/max reading status.
        *(<min status>, <max status>)*, where

         * *<min status>* is the reading status register of the min value.
         * *<max status>* is the reading status register of the max value.
    :ivar reading_status: The reading status register.
    :ivar sensor_units: The sensor units reading of the input.
    :ivar set: The input setup parameters, represented by the following tuple:
        *(<enable>, <compensation>)*

    """
    READING_STATUS = {
                      0: 'invalid reading',
                      1: 'old reading',
                      4: 'temp underrange',
                      5: 'temp overrange',
                      6: 'units zero',
                      7: 'units overrange',
    }

    def __init__(self, connection, name):
        super(Input, self).__init__(connection)
        self.name = name = str(name)
        # The reading status register, used in linear_status, reading_status
        # and minmax_status.
        rds = Register(dict((v, k) for k, v in self.READING_STATUS.items()))

        self.alarm = Command('ALARM? {0}'.format(name),
                             'ALARM {0},'.format(name),
                             [Boolean,
                              Enum('kelvin', 'celsius', 'sensor', 'linear'),
                              Float, Float, Boolean, Boolean])
        self.alarm_status = Command(('ALARMST?', [Boolean, Boolean]))
        self.celsius = Command(('CRDG? {0}'.format(name), Float))
        self.filter = Command('FILTER? {0}'.format(name),
                              'FILTER {0},'.format(name),
                              [Boolean, Integer(min=0),
                               Integer(min=0, max=100)])
        self.set = Command('INSET? {0}'.format(name),
                           'INSET {0},'.format(name),
                           [Boolean, Enum('off', 'on', 'pause')])
        self.curve = Command('INCRV? {0}'.format(name),
                             'INCRV {0},'.format(name),
                             Integer(min=0, max=60))
        self.input_type = Command('INTYPE? {0}'.format(name),
                                  'INTYPE {0},'.format(name),
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
        self.sensor_units = Command(('SRDG? {0}'.format(name), Float))
        self.linear = Command(('LDAT? {0}'.format(name), Float))
        leq = [
            Enum('slope-intercept', 'point-slope'),
            Float,  # m value
            Enum('kelvin', 'celsius', 'sensor units', start=1),
            Enum('value', '+sp1', '-sp1', '+sp2', '-sp2', start=1),
            Float,  # b value
        ]
        self.linear_equation = Command('LINEAR? {0}'.format(name),
                                       'LINEAR {0},'.format(name), leq)
        self.linear_status = Command(('LDATST? {0}'.format(name), rds))
        self.reading_status = Command(('RDGST? {0}'.format(name), rds))
        self.minmax = Command(('MDAT? {0}'.format(name), [Float, Float]))
        self.minmax_parameter = Command('MNMX? {0}'.format(name),
                                        'MNMX {0},'.format(name),
                                        [Enum('on', 'pause'),
                                         Enum('kelvin', 'celsius',
                                              'sensor units', 'linear')])
        self.minmax_status = Command(('MDATST? {0}'.format(name), rds, rds))


class Output(InstrumentBase):
    """Represents a LS340 analog output.

    :param connection: A connection object.
    :param channel: The analog output channel. Valid are either 1 or 2.

    :ivar analog: The analog output parameters, represented by the tuple
        *(<bipolar>, <mode>, <input>, <source>, <high>, <low>, <manual>)*,
        where:

         * *<bipolar>* Enables bipolar output.
         * *<mode>* Valid entries are `'off'`, `'input'`, `'manual'`, `'loop'`.
           `'loop'` is only valid for the output channel 2.
         * *<input>* Selects the input to monitor (Has no effect if mode is
           not `'input'`).
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
                              'ANALOG {0},'.format(channel),
                              [Boolean,
                               Enum('off', 'input', 'manual', 'loop'),
                               #INPUT,
                               Enum('kelvin', 'celsius', 'sensor', 'linear',
                                    start=1),
                               Float, Float, Float])
        self.value = Command(('AOUT? {0}'.format(channel), Float))


class Program(InstrumentBase):
    """Represents a LS340 program.

    :param connection: A connection object.
    :param idx: The program index.

    .. note::

        There is currently no parsing done on program lines. Lines are read and
        written as strings according to the LS340 manual.

    """
    def __init__(self, connection, idx):
        super(Program, self).__init__(connection)
        self.idx = idx = int(idx)

    def line(self, idx):
        """Return the i'th program line.

        :param i: The i'th program line.

        """
        return self.connection.ask('PGM? {0}, {1}'.format(self.idx, int(idx)))

    def append_line(self, new_line):
        """Appends the new_line to the LS340 program."""
        self.connection.write('PGM {0},'.format(self.idx) + new_line)

    def run(self):
        """Runs this program."""
        self.connection.write('PGMRUN {0}'.format(self.idx))

    def delete(self):
        """Deletes this program."""
        self.connection.write('PGMDEL {0}'.format(self.idx))


class Loop(InstrumentBase):
    """Represents a LS340 control loop.

    :param connection: A connection object.
    :param idx: The loop index.

    :ivar display_parameters: The display parameter of the loop.
        *(<loop>, <resistance>, <current/power>, <large output enable>)*, where

         * *<loop>* specifies how many loops should be displayed. Valid entries
           are `'none'`, `'loop1'`, `'loop2'`, `'both'`.
         * *<resistance>* The heater load resistance, an integer between 0 and
           1000.
         * *<current/power>* Specifies if the heater output should be displayed
           as current or power. Valid entries are `'current'` and `'power'`.
         * *<large output enable>* Disables/Enables the large output display.
    :ivar filter: The loop filter state.
    :ivar limit: The limit configuration, represented by the following tuple
        *(<limit>, <pos slope>, <neg slope>, <max current>, <max range>)*
    :ivar manual_output: The manual output value in percent of full scale.
        Valid entries are floats in the range -100.00 to 100.00 with a
        resolution of 0.01.
    :ivar mode: The control-loop mode. Valid entries are
        *'manual', 'zone', 'open', 'pid', 'pi', 'p'*
    :ivar parameters: The control loop parameters, a tuple containing
        *(<input>, <units>, <enabled>, <powerup>)*, where

         * *<input>* specifies the input channel. Valid entries are `'A'` and
           `'B'`.
         * *<units>* The setpoint units. Either `'kelvin'`, `'celsius'` or
           `'sensor'`.
         * *<enabled>* A boolean enabling/disabling the control loop.
         * *<powerup>* Specifies if the control loop is enabled/disabled after
           powerup.

    :ivar pid: The PID values.
    :ivar ramp: The control-loop ramp parameters, represented by the following
        tuple *(<enabled>, <rate>)*, where

         * *<enabled>*  Enables, disables the ramping.
         * *<rate>* Specifies the ramping rate in kelvin/minute.

    :ivar ramping: The ramping status. `True` if ramping and `False` otherwise.
    :ivar setpoint: The control-loop setpoint in its configured units.
    :ivar settle: The settle parameters. *(<threshold>, <time>)*, where

        * *<threshold>* Specifies the allowable band around the setpoint. Must
            be between 0.00 and 100.00.
        * *<time>* The time in seconds, the reading must stay within the band.
          Valid entries are 0-86400.

        .. note:: This command is only available for loop1.

    :ivar tuning_status: A boolean representing the tuning status, `True` if
        tuning `False` otherwise.
        .. note:: This attribute is only available for loop1.
    :ivar zonex: There are 11 zones, zone1 is the first. The zone attribute
        represents the control loop zone table parameters.
        *(<top>, <p>, <i>, <d>, <mout>, <range>)*.

    """
    def __init__(self, connection, idx):
        super(Loop, self).__init__(connection)
        self.idx = idx = int(idx)
        self.filter = Command('CFILT? {0}'.format(idx),
                              'CFILT {0},'.format(idx),
                              Boolean)
        self.limit = Command('CLIMIT? {0}'.format(idx),
                             'CLIMIT {0},'.format(idx),
                             [Float, Float, Float,
                              Enum(0.25, 0.5, 1., 2., start=1),
                              Integer(min=0, max=5)])
        self.manual_output = Command('MOUT? {0}'.format(idx),
                                     'MOUT {0},'.format(idx),
                                     Float(min=-100., max=100.))
        self.mode = Command('CMODE? {0}'.format(idx), 'CMODE {0},'.format(idx),
                            Enum('manual', 'zone', 'open', 'pid', 'pi', 'p',
                                 start=1))

        self.parameters = Command('CSET? {0}'.format(idx),
                                  'CSET {0},'.format(idx),
                                  [Set('A', 'B'),
                                   Enum('kelvin', 'celsius', 'sensor',
                                        start=1),
                                   Boolean,
                                   Boolean])
        self.pid = Command('PID? {0}'.format(idx), 'PID {0},'.format(idx),
                           [Float, Float, Float])
        self.ramp = Command('RAMP? {0}'.format(idx), 'RAMP {0},'.format(idx),
                            [Boolean, Float])
        self.ramping = Command(('RAMPST? {0}'.format(idx), Boolean))
        self.setpoint = Command('SETP? {0}'.format(idx),
                                'SETP {0},'.format(idx), Float)
        for z in range(1, 11):
            type_ = [
                Float(min=0),  # top value
                Float(min=0),  # P value
                Float(min=0),  # I value
                Float(min=0),  # D value
                Float(min=0),  # manual output
                Integer(min=0, max=5),  # heater range
            ]
            cmd = Command('ZONE? {0}, {1},'.format(idx, z),
                          'ZONE {0}, {1},'.format(idx, z),
                          type_)
            setattr(self, 'zone{0}'.format(z), cmd)
        if idx == 1:
            self.tuning_status = Command(('TUNEST?', Boolean))
            self.settle = Command('SETTLE?', 'SETTLE',
                                  [Float(min=0., max=100.),
                                   Integer(min=0, max=86400)])
        cdisp = [
            Enum('none', 'loop1', 'loop2', 'both'),
            Integer(min=0, max=1000),
            Enum('current', 'power', start=1),
            Boolean,
        ]
        self.display_parameters = Command('CDISP? {0}'.format(idx),
                                          'CDISP {0},'.format(idx), cdisp)


class Scanner(InstrumentBase):
    """Represents a scanner option for the ls340 temperature controller.

    :ivar channels: A tuple with all channel names.

    """
    def __init__(self, connection, channels):
        super(Scanner, self).__init__(connection)
        self.channels = tuple(channels)
        for channel in channels:
            setattr(self, channel.lower(), Input(connection, channel))


def _get_scanner(connection, model):
    """A factory function used to create the different scanner instances.

    :param connection: A connection object.
    :param model: A string representing the different scanner models supported
        by the ls340 temperature controller. Valid entries are:

        * `"3462"`, The dual standard input option card.
        * `"3464"`, The dual thermocouple input option card.
        * `"3465"`, The single capacitance input option card.
        * `"3468"`, The eight channel input option card.

    The different scanner options support a different number of input channels.

    """
    channels = {
        '3462': ('C', 'D'),
        '3464': ('C', 'D'),
        '3465': ('C'),
        '3468': ('C1', 'C2', 'C3', 'C4', 'D1', 'D2', 'D3', 'D4')
    }
    return Scanner(connection, channels[model])


class LS340(IEC60488):
    """
    Represents a Lakeshore model LS340 temperature controller.

    The LS340 class implements an interface to the Lakeshore model LS340
    temperature controller.

    :param connection: An object, modeling the connection interface, used to
        communicate with the real instrument.
    :param scanner: A string representing the scanner in use. Valid entries are

        * `"3462"`, The dual standard input option card.
        * `"3464"`, The dual thermocouple input option card.
        * `"3465"`, The single capacitance input option card.
        * `"3468"`, The eight channel input option card.

    :ivar a: Input channel a.
    :ivar b: Input channel b.
    :ivar beeper: A boolean value representing the beeper mode. `True` means
        enabled, `False` means disabled.
    :ivar beeping: A Integer value representing the current beeper status.
    :ivar busy: A Boolean representing the instrument busy status.
    :ivar com: The serial interface configuration, represented by the following
        tuple: *(<terminator>, <baud rate>, <parity>)*.

        * *<terminator>* valid entries are `"CRLF"`, `"LFCR"`, `"CR"`, `"LF"`
        * *<baud rate>* valid entries are 300, 1200, 2400, 4800, 9600, 19200
        * *<parity>* valid entries are 1, 2, 3. See LS340 manual for meaning.

    :ivar curvex: An instance of :class:`~.Curve`. x is just a placeholder for
        an integer between 1 and 60, e.g. `.curve2` is the second curve.
    :ivar datetime: The configured date and time.
        *(<MM>, <DD>, <YYYY>, <HH>, <mm>, <SS>, <sss>)*, where

        * *<MM>* represents the month, an Integer in the range 1-12.
        * *<DD>* represents the day, an Integer in the range 1-31.
        * *<YYYY>* represents the year.
        * *<mm>* represents the minutes, an Integer in the range 0-59.
        * *<SS>* represents the seconds, an Integer in the range 0-59.
        * *<sss>* represents the miliseconds, an Integer in the range 0-999.

    :ivar digital_io_status: The digital input/output status.
        *(<input status>, <output status>)*, where

        * *<input status>* is a Register representing the state of the 5 input
          lines DI1-DI5.
        * *<output status>* is a Register representing the state of the 5
          output lines DO1-DO5.

    :ivar digital_output_param: The digital output parameters.
        *(<mode>, <digital output>)*, where:

        * *<mode>* Specifies the mode of the digital output, valid entries are
          `'off'`, `'alarms'`, `'scanner'`, `'manual'`,
        * *<digital output>* A register to enable/disable the five digital
          outputs DO1-DO5, if *<mode>* is `'manual'`.

    :ivar display_fieldx: The display field configuration values. x is just a
        placeholder and varies between 1 and 8, e.g. `.display_field2`.
        *(<input>, '<source>')*, where

        * *<input>* Is the string name of the input to display.
        * *<source>* Specifies the data to display. Valid entries are
          `'kelvin'`, `'celsius'`, , `'sensor units'`, `'linear'`, `'min'` and
          `'max'`.

    :ivar heater: An instance of the :class:`~.Heater` class.
    :ivar high_relay: The configuration of the high relay, represented by the
        following tuple *(<mode>, <off/on>)*, where

        * *<mode>* specifies the relay mode, either `'off'` , `'alarms'` or
          `'manual'`.
        * *<off/on>* A boolean enabling disabling the relay in manual mode.

    :ivar high_relay_status: The status of the high relay, either `'off'` or
        `'on'`.
    :ivar ieee: The IEEE-488 interface parameters, represented by the following
        tuple *(<terminator>, <EOI enable>, <address>)*, where

        * *<terminator>* is `None`, `\\\\r\\\\n`, `\\\\n\\\\r`, `\\\\r` or
          `\\\\n`.
        * *<EOI enable>* A boolean.
        * *<address>* The IEEE-488.1 address of the device, an integer between
          0 and 30.

    :ivar key_status: A string representing the keypad status, either
        `'no key pressed'` or `'key pressed'`.
    :ivar lock: A tuple representing the keypad lock-out and the lock-out code.
        *(<off/on>, <code>)*.
    :ivar logging: A Boolean value, enabling or disabling data logging.
    :ivar logging_params: The data logging parameters.
        *(<type>, <interval>, <overwrite>, <start mode>)*, where

        * *<type>* Valid entries are `'readings'` and `'seconds'`.
        * *<interval>* The number of readings between each record if *<type>*
            is readings and number of seconds between each record otherwise.
            Valid entries are 1-3600.
        * *<overwrite>* `True` if overwrite is enabled, `False` otherwise.
        * *<start mode>* The start mode, either `clear` or `continue`.

        .. note::

            If no valid SRAM data card is installed, queriing returns
            `('invalid', 0, False, 'clear')`.

    :ivar loop1: An instance of the Loop class, representing the first control
        loop.
    :ivar loop2: Am instance of the Loop class, representing the second control
        loop.
    :ivar low_relay: The configuration of the low relay, represented by the
        following tuple *(<mode>, <off/on>)*, where

        * *<mode>* specifies the relay mode, either `'off'` , `'alarms'` or
          `'manual'`.
        * *<off/on>* A boolean enabling disabling the relay in manual mode.

    :ivar low_relay_status: The status of the low relay, either `'off'` or
        `'on'`.
    :ivar mode: Represents the interface mode. Valid entries are
        `"local"`, `"remote"`, `"lockout"`.
    :ivar output1: First output channel.
    :ivar output2: Second output channel.
    :ivar programx: A Program instance, x denotes a placeholder for an integer
        between 1 and 10.
    :ivar program_status: The status of the currently running program
        represented by the following tuple: *(<program>, <status>)*. If
        program is zero, it means that no program is running.
    :ivar revision: A tuple representing the revision information.
        *(<master rev date>, <master rev number>, <master serial number>,*
        *<switch setting SW1>, <input rev date>, <input rev number>,*
        *<option ID>, <option rev date>, <option rev number>)*.
    :ivar scanner_parameters: The scanner parameters.
        *(<mode>, <channel>, <intervall>)*, where

         * *<mode>* represents the scan mode. Valid entries are `'off'`,
           `'manual'`, `'autoscan'`, `'slave'`.
         * *<channel>* the input channel to use, an integer in the range 1-16.
         * *<interval>* the autoscan intervall in seconds, an integer in the
           range 0-999.

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
        self.scanner = _get_scanner(connection, scanner) if scanner else None
        self.a = Input(connection, 'A')
        self.b = Input(connection, 'B')
        self.output1 = Output(connection, 1)
        self.output2 = Output(connection, 2)
        # Control Commands
        # ================
        self.loop1 = Loop(connection, 1)
        self.loop2 = Loop(connection, 2)
        self.heater = Heater(connection)
        # System Commands
        # ===============
        self.beeper = Command('BEEP?', 'BEEP', Boolean)
        self.beeping = Command(('BEEPST?', Integer))
        self.busy = Command(('BUSY?', Boolean))
        self.com = Command('COMM?', 'COMM',
                            [Enum('CRLF', 'LFCR', 'CR', 'LF', start=1),
                             Enum(300, 1200, 2400, 4800, 9600, 19200, start=1),
                             Set(1, 2, 3)])
        self.datetime = Command('DATETIME?', 'DATETIME',
                                [Integer(min=1, max=12),
                                 Integer(min=1, max=31),
                                 Integer,
                                 Integer(min=0, max=23),
                                 Integer(min=0, max=59),
                                 Integer(min=0, max=59),
                                 Integer(min=0, max=999)])
        dispfld = [
            String,
            Enum('kelvin', 'celsius', 'sensor units', 'linear', 'min', 'max'),
        ]
        for i in range(1, 9):
            cmd = Command('DISPFLD? {0}'.format(i),
                          'DISPFLD {0},'.format(i),
                          dispfld)
            setattr(self, 'display_field{0}'.format(i), cmd)
        self.mode = Command('MODE?', 'MODE',
                            Enum('local', 'remote', 'lockout', start=1))
        self.key_status = Command(('KEYST?',
                                   Enum('no key pressed', 'key pressed')))
        self.high_relay = Command('RELAY? 1', 'RELAY 1',
                                  [Enum('off', 'alarms', 'manual'),
                                   Boolean])
        self.low_relay = Command('RELAY? 2', 'RELAY 2',
                                  [Enum('off', 'alarms', 'manual'),
                                   Boolean])
        self.high_relay_status = Command(('RELAYST? 1', Enum('off', 'on')))
        self.low_relay_status = Command(('RELAYST? 2', Enum('off', 'on')))
        self.revision = Command(('REV?', [Integer for _ in range(9)]))
        self.lock = Command('LOCK?', 'LOCK',
                            [Boolean, Integer(min=0, max=999)])
        self.ieee = Command('IEEE?', 'IEEE',
                            [Enum(None, '\r\n', '\n\r', '\r', '\n'),
                             Boolean,
                             Integer(min=0, max=30)])
        dout = [
            Enum('off', 'alarms', 'scanner', 'manual'),
            Register({'DO1': 0, 'DO2': 1, 'DO3': 2, 'DO4': 3, 'DO5': 4})
        ]
        self.digital_output_param = Command('DOUT?', 'DOUT',
                                            dout)
        diost = [
            Register({'DI1': 0, 'DI2': 1, 'DI3': 2, 'DI4': 3, 'DI5': 4}),
            Register({'DO1': 0, 'DO2': 1, 'DO3': 2, 'DO4': 3, 'DO5': 4}),
        ]
        self.digital_io_status = Command(('DIOST?', diost))
        xscan = [
            Enum('off', 'manual', 'autoscan', 'slave'),
            Integer(min=1, max=16),
            Integer(min=0, max=999)
        ]
        self.scanner_parameters = Command('XSCAN?', 'XSCAN', xscan)
        # Curve Commands
        # ==============
        for i in range(1, 61):
            setattr(self, 'curve{0}'.format(i),
                    Curve(connection, i, writeable=(i > 20)))
        # Data Logging Commands
        # =====================
        self.logging = Command('LOG?', 'LOG', Boolean)
        logset_query_t = [
            Enum('invalid', 'readings', 'seconds', start=0),
            Integer(min=0, max=3600),
            Boolean,
            Enum('clear', 'continue')
        ]
        logset_write_t = [
            Enum('readings', 'seconds', start=1),
            Integer(min=1, max=3600),
            Boolean,
            Enum('clear', 'continue')
        ]
        self.logging_params = Command(('LOGSET?', logset_query_t),
                                      ('LOGSET', logset_write_t))
        self.program_status = Command(('PGMRUN?',
                                       [Integer, Enum(*self.PROGRAM_STATUS)]))
        for i in range(1, 11):
            setattr(self, 'program{0}'.format(i), Program(connection, i))

    def clear_alarm(self):
        """Clears the alarm status for all inputs."""
        self.connection.write('ALMRST')

    def lines(self):
        """The number of program lines remaining."""
        return int(self.connection.ask('PGMMEM?'))

    def reset_minmax(self):
        """Resets Min/Max functions for all inputs."""
        self.connection.write('MNMXRST')

    def save_curves(self):
        """Updates the curve flash with the current user curves."""
        self.connection.write('CRVSAV')

    def softcal(self, std, dest, serial, T1, U1, T2, U2, T3=None, U3=None):
        """Generates a softcal curve.

        :param std: The standard curve index used to calculate the softcal
            curve. Valid entries are 1-20
        :param dest: The user curve index where the softcal curve is stored.
            Valid entries are 21-60.
        :param serial: The serial number of the new curve. A maximum of 10
            characters is allowed.
        :param T1: The first temperature point.
        :param U1: The first sensor units point.
        :param T2: The second temperature point.
        :param U2: The second sensor units point.
        :param T3: The third temperature point. Default: `None`.
        :param U3: The third sensor units point. Default: `None`.

        """
        std = int(std)
        if not (0 <= std <= 20):
            raise ValueError('Standard curve index out of range.')
        dest = int(dest)
        if not (20 < std <= 60):
            raise ValueError('User curve index out of range.')
        serial = str(serial)
        if len(serial) > 10:
            raise ValueError('Serial number too large.')
        args = [std, dest, serial, T1, U1, T2, U2]
        if (T3 is not None) and (U3 is not None):
            args.extend([T3, U3])
        self.connection.write('SCAL ' + ','.join(args))

    def stop_program(self):
        """Terminates the current program, if one is running."""
        self.connection.write('PGMRUN 0')

    def _factory_default(self, confirm=False):
        """Resets the device to factory defaults.

        :param confirm: This function should not normally be used, to prevent
            accidental resets, a confirm value of `True` must be used.

        """
        if confirm is True:
            self.connection.write('DFLT 99')
        else:
            raise ValueError('Reset to factory defaults was not confirmed.')
