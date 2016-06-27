#  -*- coding: utf-8 -*-
#
# E21, (c) 2012-2015, see AUTHORS.  Licensed under the GNU GPL.
from slave.driver import Command, Driver
import slave.iec60488 as iec
from slave.types import Boolean, Float, Integer, Mapping, Set


class Initiate(Driver):
    """The initiate command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar continuous: A boolean representing the continuous initiation mode.

    """
    def __init__(self, transport, protocol):
        super(Initiate, self).__init__(transport, protocol)
        self.continuous_mode = Command(
            ':INIT:CONT?',
            ':INIT:CONT',
            Boolean
        )

    def __call__(self):
        """Initiates one measurement cycle."""
        self._write(':INIT')


class Output(Driver):
    """The Output command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar gain: The analog output gain. A float between -100e6 and 100e6.
    :ivar offset: The analog output offset. -1.2 to 1.2.
    :ivar state: The analog output state. A boolean, `True` equals to on,
        `False` to off.
    :ivar relative: If `True`, the present analog output voltage is used as the
        relative value.

    """
    def __init__(self, transport, protocol):
        super(Output, self).__init__(transport, protocol)
        self.gain = Command(
            'OUTP:GAIN?',
            'OUTP:GAIN',
            Float(min=-100e6, max=100e6)
        )
        self.offset = Command(
            'OUTP:OFFS?',
            'OUTP:OFFS',
            Float(min=-1.2, max=1.2)
        )
        self.relative = Command(
            'OUTP:REL?',
            'OUTP:REL',
            Boolean
        )
        self.state = Command(
            'OUTP:STAT?',
            'OUTP:STAT',
            Boolean
        )


class Sense(Driver):
    """The Sense command layer.

    :param transport: A transport object.

    :ivar delta_mode: Enables/Disables the delta measurement mode.
    :ivar function: The sense function, either 'temperature' or 'voltage' (dc).
    :ivar nplc: Set integration rate in line cycles (0.01 to 60).
    :ivar auto_range: Enable/Disable auto ranging
    :ivar range: Set the measurement range (0 to 120 Volt)

    """
    def __init__(self, transport, protocol):
        super(Sense, self).__init__(transport, protocol)
        self.delta_mode = Command(
            ':SENS:VOLT:DELT?',
            ':SENS:VOLT:DELT',
            Boolean
        )
        self.function = Command(
            ':SENS:FUNC?',
            ':SENS:FUNC',
            Mapping({'voltage': '"VOLT:DC"', 'temperature': '"TEMP"'})
        )
        self.nplc = Command(
            ':SENS:VOLT:NPLC?',
            ':SENS:VOLT:NPLC',
            Float(min=0.01, max=50)
        )
        self.auto_range = Command(
            ':SENS:VOLT:RANG:AUTO?',
            ':SENS:VOLT:RANG',
            Boolean
        )
        self.range = Command(
            ':SENS:VOLT:RANG?',
            ':SENS:VOLT:RANG',
            Float(min=0, max=120)
        )


class System(Driver):
    """The System command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar autozero: Enable/Disable autozero.
    :ivar front_autozero: Enable/Disable front autozero (disable to speed
                          up delta measurements)
    """
    def __init__(self, transport, protocol):
        super(System, self).__init__(transport, protocol)
        self.autozero = Command(
            ':SYST:AZER?',
            ':SYST:AZER',
            Boolean
        )
        self.front_autozero = Command(
            ':SYST:FAZ?',
            ':SYST:FAZ',
            Boolean
        )

    def preset(self):
        """Return to system preset defaults."""
        self._write(':SYST:PRES')


class Trace(Driver):
    """The Trace command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar points: Specify number of readings to store (2-1024).
    :ivar feed:   Source of readings ('sense', 'calculate' or `None`).
    :ivar feed_control: Buffer control mode ('never' or 'next')

    """
    def __init__(self, transport, protocol):
        super(Trace, self).__init__(transport, protocol)
        self.points = Command(
            ':TRAC:POIN?',
            ':TRAC:POIN',
            Integer(min=2, max=1024)
        )
        self.feed = Command(
            ':TRAC:FEED?',
            ':TRAC:FEED',
            Mapping({'sense': 'SENS', 'calculate': 'CALC', None: 'NONE'})
        )
        self.feed_control = Command(
            ':TRAC:FEED:CONT?',
            ':TRAC:FEED:CONT?',
            Mapping({'next': 'NEXT', 'never': 'NEV'})
        )

    def clear(self):
        """Clear readings from buffer."""
        self._write(':TRAC:CLEAR')

    def free(self):
        """Query bytes available and bytes in use."""
        return self._query((':TRAC:FREE?', [Float, Float]))


class Trigger(Driver):
    """The Trigger command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar auto_delay: The state of the auto delay.
    :ivar delay: The trigger delay, between 0 to 999999.999 seconds.
    :ivar source: The trigger source, either 'immediate', 'timer', 'manual',
        'bus' or 'external'.
    :ivar timer: The timer interval, between 0 to 999999.999 seconds.

    """
    def __init__(self, transport, protocol):
        super(Trigger, self).__init__(transport, protocol)
        self.auto_delay = Command(
            ':TRIG:DEL:AUTO?',
            ':TRIG:DEL:AUTO',
            Boolean
        )
        # TODO count has a max value of 9999 but supports infinity as well.
        self.count = Command(
            ':TRIG:COUN?',
            ':TRIG:COUN',
            Float(min=0.)
        )
        self.delay = Command(
            ':TRIG:DEL?',
            ':TRIG:DEL',
            Float(min=0., max=999999.999)
        )
        self.source = Command(
            ':TRIG:SOUR?',
            ':TRIG:SOUR',
            Mapping({'immediate': 'IMM', 'timer': 'TIM', 'manual': 'MAN',
                     'bus': 'BUS', 'external': 'EXT'})
        )
        self.timer = Command(
            ':TRIG:TIM?',
            ':TRIG:TIM',
            Float(min=0., max=999999.999)
        )

    def signal(self):
        """Generates an event, to bypass the event detector block.

        If the trigger system is waiting for an event (specified by the
        :attr:.`source` attribute), the event detection block is immediately
        exited.

        """
        self._write(':TRIG:SIGN')


class Unit(Driver):
    """The unit command layer.

    :param transport: A transport object.
    :param protocol: A protocol object.

    :ivar temperature: The unit of the temperature, either 'C', 'F', or 'K'.

    """
    def __init__(self, transport, protocol):
        super(Unit, self).__init__(transport, protocol)
        self.temperature = Command(
            ':UNIT:TEMP?',
            ':UNIT:TEMP',
            Set('C', 'F', 'K')
        )


class K2182(iec.IEC60488, iec.StoredSetting, iec.Trigger):
    """A keithley model 2182/A nanovoltmeter.

    :param transport: A transport object.

    :ivar initiate: An instance of :class:`.Initiate`.
    :ivar output: An instance of :class:`.Output`.
    :ivar sample_count: The sample count. Valid entries are 1 to 1024.
    :ivar temperature: Performs a single-shot measurement of the temperature.

        ..note:: This Command is much slower than :meth:`.read`.

    :ivar triggering: An instance of :class:`.Trigger`.
    :ivar unit: An instance of :class:`.Unit`.
    :ivar voltage: Performs a single-shot measurement of the voltage.

        ..note:: This Command is much slower than :meth:`.read`.

    """
    def __init__(self, transport, protocol=None):
        super(K2182, self).__init__(transport, protocol)
        self.initiate = Initiate(self._transport, self._protocol)
        self.output = Output(self._transport, self._protocol)
        self.sample_count = Command(
            ':SAMP:COUN?',
            ':SAMP:COUN',
            Integer(min=1, max=1024)
        )
        self.sense = Sense(self._transport, self._protocol)
        self.system = System(self._transport, self._protocol)
        self.temperature = Command((':MEAS:TEMP?', Float))
        self.trace = Trace(self._transport, self._protocol)
        self.triggering = Trigger(self._transport, self._protocol)
        self.unit = Unit(self._transport, self._protocol)
        self.voltage = Command((':MEAS:VOLT?', Float))

    def abort(self):
        """Resets the trigger system, it put's the device in idle mode."""
        self._write(':ABOR')

    def fetch(self):
        """Returns the latest available reading

        .. note:: It does not perform a measurement.

        """
        # TODO check if it can return multiple values.
        return self._query((':FETC?', Float))

    def read(self):
        """A high level command to perform a singleshot measurement.

        It resets the trigger model(idle), initiates it, and fetches a new
        value.

        """
        return self._query((':READ?', Float))
