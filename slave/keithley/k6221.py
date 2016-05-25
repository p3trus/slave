#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""The k6221 module implements a complete programmable interface of the Keithley
:class:`~.K6221` ac/dc current source.

"""
import itertools
from slave.driver import Command, Driver
from slave.iec60488 import (IEC60488, Trigger, ObjectIdentification,
    StoredSetting)
from slave.types import (Boolean, Enum, Float, Integer, Mapping, String, Set,
    Stream, Register)


class K6221(IEC60488, Trigger, ObjectIdentification):
    """The Keithley K6221 ac/dc current source.

    The programmable interface is grouped into several layers and builts a tree
    like structure.

    .. rubric: The calculate Command layer

    :ivar math: The math command subgroup, an instance of
        :class:`~.Math`.
    :ivar buffer_statistics: The buffer statistics command subgroup, an instance of
        :class:`~.BufferStatistics`.
    :ivar digital_io: The limit testing and digital IO command subgroup, an instance of
        :class:`~.DigitalIO`.

    .. rubric: The display command layer

    :ivar display: The display command subgroup, an instance of
        :class:`~.Display`.

    .. rubric: The format command layer

    :ivar format: The format command subgroup, an instance of
        :class:`~.Format`.

    .. rubric: The output command layer

    :ivar output: The output command subgroup, an instance of
        :class:`~.Output`.

    .. rubric: The sense command layer

    :ivar sense: The sense command subgroup, an instance of
        :class:`~.Sense`.

    .. rubric: The source command layer

    :ivar source: The source command subgroup, an instance of
        :class:`~.Source`.

    .. rubric: The status command layer

    :ivar status_cmds: The status command subgroup, an instance of
        :class:`~.Status`.

    .. rubric: The system command layer

    :ivar system: The system command subgroup, an instance of
        :class:`~.System`.

    .. rubric: The trace command layer

    :ivar trace: The trace command subgroup, an instance of
        :class:`~.Trace`.

    .. rubric: The trigger command layer

    :ivar arm: The arm command subgroup, an instance of :class:`~.Arm`.
    :ivar triggering: The triggering command subgroup, an instance of
        :class:`~.Trigger`.

    .. rubric: The units command layer

    :ivar units: The units command subgroup, an instance of
        :class:`~.Units`.

    """
    def __init__(self, transport):
        super(K6221, self).__init__(transport)
        # The command subgroups
        self.math = Math(self._transport, self._protocol)
        self.buffer_statistics = BufferStatistics(self._transport, self._protocol)
        self.digital_io = DigitalIO(self._transport, self._protocol)
        self.display = Display(self._transport, self._protocol)
        self.format = Format(self._transport, self._protocol)
        self.output = Output(self._transport, self._protocol)
        self.sense = Sense(self._transport, self._protocol)
        self.source = Source(self._transport, self._protocol)
        self.status_cmds = Status(self._transport, self._protocol)
        self.system = System(self._transport, self._protocol)
        self.trace = Trace(self._transport, self._protocol)
        # The trigger command layer
        self.arm = Arm(self._transport, self._protocol)
        self.triggering = Trigger(self._transport, self._protocol)
        self.units = Units(self._transport, self._protocol)


    # TODO list method in trigger rubric
    def initiate(self):
        """Initiates the trigger system."""
        self._write(':INIT')

    # TODO list method in trigger rubric
    def abort(self):
        """Resets the trigger system."""
        self._write(':ABOR')


# -----------------------------------------------------------------------------
# Calculate Command Layer
# -----------------------------------------------------------------------------
class Math(Driver):
    """The math command subgroup.

    :ivar format: The math format. Valid are `None`, 'linear' or 'reciprocal'.

        ============  ==============================================
        Value         Description
        ============  ==============================================
        `None`        No math calculation is used.
        'linear'      Uses a linear equation of the form `m * X + b`
        'reciprocal'  Uses an equation of the form `m / X + b`
        ============  ==============================================

    :ivar float m: The m factor used in the equation. [-9.99999e20, 9.99999e20].
    :ivar float b: The b factor used in the equation. [-9.99999e20, 9.99999e20].
    :ivar bool enabled: The state of the math calculation.
    :ivar float latest: The latest math calculation. (read-only).
    :ivar float fresh: The latest math calculation. It can only be read once.
        (read-only).

    """
    def __init__(self, transport, protocol):
        super(Math, self).__init__(transport, protocol)
        self.format = Command(
            ':CALC:FORM?',
            ':CALC:FORM',
            Mapping({None: 'NONE', 'linear': 'MXB', 'reciprocal': 'REC'})
        )
        self.m = Command(
            ':CALC:KMAT:MMF?',
            ':CALC:KMAT:MMF',
            Float(min=-9.99999e20, max=9.99999e20)
        )
        self.b = Command(
            ':CALC:KMAT:MBF?',
            ':CALC:KMAT:MBF',
            Float(min=-9.99999e20, max=9.99999e20)
        )
        self.enabled = Command(':CALC:STAT?', ':CALC:STAT', Boolean)
        self.latest = Command((':CALC:DATA?', Float))
        self.fresh = Command((':CALC:DATA:FRESH', Float))


class BufferStatistics(Driver):
    """The buffer statistics command subgroup.

    :ivar format: The selected buffer statistics.

        ======  =============================================
        Value   Description
        ======  =============================================
        'mean'  The mean value of the buffer readings
        'sdev'  The standard deviation of the buffer readings
        'max'   The max value of the buffer readings.
        'min'   The min value of the buffer readings.
        'peak'  The difference of the max and min values.
        ======  =============================================
    :ivar bool enabled: The state of the buffer statistics.
    :ivar float data: The calculated value.(read-only).

    """
    def __init__(self, transport, protocol):
        super(BufferStatistics, self).__init__(transport, protocol)
        self.format = Command(
            ':CALC2:FORM?',
            ':CALC2:FORM',
            Mapping({
                'mean': 'MEAN', 'sdev': 'SDEV', 'max': 'MAX',
                'min': 'MIN', 'peak': 'PKPK'
            })
        )
        self.enabled = Command(':CALC2:STAT?', ':CALC2:STAT', Boolean)
        self.data = Command((':CALC2:DATA?', Float))

    def immediate(self):
        """Perform the calculation on the buffer content."""
        self._write(':CALC2:IMM')


class DigitalIO(Driver):
    """The limit testing and digital IO command subgroup.

    Activating limit testing and enable the output on lines 2 and 3 in case
    of limit failure, would look like this::

        k6221.digital_io.limit_pattern = dict(out1=False, out2=True, out3=True, out4=False)
        k6221.digital_io.test_limit = True

    :ivar bool test_limit: The state of the limit testing circuit.
    :ivar bool force_output: The state of the force overwrite. If `True`, the
        limit testing circuit is overwritten and the force pattern is used.
    :ivar limit_pattern: The limit pattern, a register represented by a
        dictionairy with the following four keys and a boolean value
        enabling/disabling the digital output.

        Keys: 'out1', 'out2', 'out3', 'out4'
    :ivar force_pattern: The force pattern, a register dictionary with the
        same form as the limit_pattern.

    """
    def __init__(self, transport, protocol):
        super(DigitalIO, self).__init__(transport, protocol)
        self.force_output = Command(
            ':CALC3:FORC:STAT?',
            ':CALC3:FORC:STAT',
            Boolean
        )
        self.test_limit = Command(':CALC3:LIM?', ':CALC3:LIM', Boolean)
        pattern = Register({
            0: 'out1',
            1: 'out2',
            2: 'out3',
            3: 'out4'
        })
        self.limit_pattern = Command(
            ':CALC3:LIM:SOUR?',
            ':CALC3:LIM:SOUR',
            pattern
        )
        self.force_pattern = Command(
            ':CALC3:FORC:PATT?',
            ':CALC3:FORC:PATT',
            pattern
        )

    def limit_test_failed(self):
        """Returns a boolean value, showing if the limit test has failed"""
        self._query((':CALC3:LIM:FAIL?', Boolean))


# -----------------------------------------------------------------------------
# Display Command Layer
# -----------------------------------------------------------------------------
class Display(Driver):
    """The display command subgroup.

    :ivar enabled: A boolean representing the state of the frontpanel display
        and controls.
    :ivar top: The top line display. An instance of :class:`~.Window`.
    :ivar bottom: The bottom line display. An instance of :class:`~.Window`.

    """
    def __init__(self, transport, protocol):
        super(Display, self).__init__(transport, protocol)
        self.enabled = Command(':DISP:ENAB?', ':DISP:ENAB', Boolean)
        self.top = DisplayWindow(1, self._transport, self._protocol)
        self.bottom = DisplayWindow(2, self._transport, self._protocol)


class DisplayWindow(Driver):
    """The window command subgroup of the Display node.

    :ivar text: The window text. An instance of :class:`~.DisplayWindowText`.
    :ivar blinking: A boolean representing the blinking state of the message
        characters.

    """
    def __init__(self, id, transport, protocol):
        super(DisplayWindow, self).__init__(transport, protocol)
        self.id = int(id)
        self.text = DisplayWindowText(self.id, self._transport, self._protocol)
        self.blinking = Command(
            ':DISP:WIND{}:ATTR?'.format(id),
            ':DISP:WIND{}:ATTR'.format(id),
            Boolean
        )


class DisplayWindowText(Driver):
    """The text command subgroup of the Window node.

    :ivar data: An ascii encoded message with up to 20 characters.
    :ivar bool enabled: The state of the text message.

    """
    def __init__(self, id, transport, protocol):
        super(DisplayWindowText, self).__init__(transport, protocol)
        # TODO check encoding.
        self.text = Command(
            ':DISP:WIND{0}:TEXT:DATA?'.format(id),
            ':DISP:WIND{0}:TEXT:DATA'.format(id),
            String(max=20)
        )
        self.enabled = Command(
            ':DISP:WIND{0}:TEXT:STAT?'.format(id),
            ':DISP:WIND{0}:TEXT:STAT'.format(id),
            Boolean
        )


# -----------------------------------------------------------------------------
# Format Command Layer
# -----------------------------------------------------------------------------
class Format(Driver):
    """The format command subgroup.

    :ivar data: Specifies the data format. Valid are 'ascii', 'real32',
        'real64', sreal' and dreal'.
    :ivar elements: A tuple of data elements configuring what should be stored
        in the buffer. Valid elements are 'reading', 'timestamp', 'units',
        'rnumber', 'source', 'compliance' 'avoltage', 'all' and 'default'.
        E.g.::

            k6221.format.elements = 'reading', 'source', 'timestamp'

    :ivar byte_order: The byte order. Valid are 'normal' and 'swapped'.

        .. note::

            After a reset, it defaults to 'normal' but the system preset
            is 'swapped'.

    :ivar status_register: The format of the status register. Valid are
        'ascii', 'octal', 'hex' and 'binary'.

    """
    DATA = {
        'ascii': 'ASC',
        'real32': 'REAL,32', # TODO might break due to the , in the response.
        'real64': 'REAL,64',
        'sreal': 'SRE',
        'dreal': 'DRE'
    }
    ELEMENTS = {
        'reading': 'READ',
        'timestamp': 'TST',
        'units': 'UNIT',
        'rnumber': 'RNUM',
        'source': 'SOUR',
        'compliance': 'COMP',
        'avoltage': 'AVOL',
        'all': 'ALL',
        'default': 'DEF',
    }
    def __init__(self, transport, protocol):
        super(Format, self).__init__(transport, protocol)
        self.data = Command(
            ':FORM?',
            ':FORM',
            Mapping(Format.DATA)
        )
        self.elements = Command(
            ':FORM:ELEM?',
            ':FORM:ELEM',
            # We use itertools here because we don't know the number of data
            # types. E.g. a response could be 'READ' or 'READ,TST'.
            itertools.repeat(Mapping(Format.ELEMENTS))
        )
        self.byte_order = Command(
            ':FORM:BORD?',
            ':FORM:BORD',
            Mapping({'normal': 'NORM', 'swapped': 'SWAP'})
        )
        self.status_register = Command(
            ':FORM:SREG?',
            ':FORM:SREG',
            Mapping({'ascii': 'ASC', 'hex': 'HEX', 'octal': 'OCT', 'binary': 'BIN'})
        )


# -----------------------------------------------------------------------------
# Output Command Layer
# -----------------------------------------------------------------------------
class Output(Driver):
    """The output command subsystem.

    :ivar enabled: A boolean representing the state of the output.
    :ivar low_to_earth: A boolean representing the state of the low to earth
        ground transport.
    :ivar inner_shield: The transport of the triax inner shield, either
        'output low' or 'guard'.
    :ivar response: The output response. Valid are 'fast' or 'slow'.
    :ivar interlock: A boolean representing the state of the interlock.
        `False` if the interlock is tripped (output is disabled) and `True` if
        the interlock is closed.

    """
    def __init__(self, transport, protocol):
        super(Output, self).__init__(transport, protocol)
        self.enabled = Command(':OUTP?', ':OUTP', Boolean)
        self.low_to_earth = Command(':OUTP:LTE?', ':OUTP:LTE', Boolean)
        self.inner_shield = Command(
            ':OUTP:ISH?',
            ':OUTP:ISH',
            Mapping({'output low': 'OLOW', 'guard': 'GUAR'})
        )
        self.response = Command(
            ':OUTP:RESP?',
            ':OUTP:RESP',
            Mapping({'fast': 'FAST', 'slow': 'SLOW'})
        )
        self.interlock = Command(
            (':OUTP:INT:TRIP?', Boolean)
        )


# -----------------------------------------------------------------------------
# Sense Command Layer
# -----------------------------------------------------------------------------
class Sense(Driver):
    """The Sense command subsystem.

    :ivar data: The sense data subsystem, an instance of :class:`~.SenseData`.
    :ivar average: The sense average subsystem, an instance of
        :class:`~.SenseAverage`.

    """
    def __init__(self, transport, protocol):
        super(Sense, self).__init__(transport, protocol)
        self.data = SenseData(self._transport, self._protocol)
        self.average = SenseAverage(self._transport, self._protocol)


class SenseData(Driver):
    """The data command subsystem of the Sense node.

    :ivar fresh: Similar to latest, but the same reading can only be returned
        once. If no fresh reading is available, a call will block. (read-only)
    :ivar latest: Represents the latest pre-math delta reading. (read-only)

    """
    def __init__(self, transport, protocol):
        super(SenseData, self).__init__(transport, protocol)
        self.fresh = Command((':SENS:DATA:FRES?', Stream(Float)))
        self.latest = Command((':SENS:DATA?', Stream(Float)))


class SenseAverage(Driver):
    """The average command subsystem of the Sense node.

    :ivar tcontrol: The filter control. Valid are 'moving', 'repeat'.
    :ivar window: The filter window in percent of the range, a float in the
        range [0.00, 10].
    :ivar count: The filter count size, an integer in the range [2, 300].
    :ivar enabled: The state of the averaging filter, either `True` or `False`.

    """
    def __init__(self, transport, protocol):
        super(SenseAverage, self).__init__(transport, protocol)
        self.tcontrol = Command(
            ':SENS:AVER:TCON?',
            ':SENS:AVER:TCON',
            Mapping({'moving': 'MOV', 'repeat': 'REP'})
        )
        self.window = Command(
            ':SENS:AVER:WIND?',
            ':SENS:AVER:WIND',
            Float(min=0., max=10)
        )
        self.count = Command(
            ':SENS:AVER:COUN?',
            ':SENS:AVER:COUN',
            Integer(min=2, max=300)
        )
        self.enabled = Command(':SENS:AVER?', ':SENS:AVER', Boolean)


# -----------------------------------------------------------------------------
# Source Command Layer
# -----------------------------------------------------------------------------
class Source(Driver):
    """The source command subsystem.

    :ivar current: The source current command subsystem, an instance of
        :class:`~.SourceCurrent`.
    :ivar float delay: The source delay in seconds, in the range
        [1e-3, 999999.999].
    :ivar sweep: The source sweep command subsystem, an instance of
        :class:`~.SourceSweep`.
    :ivar list: The source list command subsystem, an instance of
        :class:`~.SourceList`.
    :ivar delta: The source delta command subsystem, an instance of
        :class:`~.SourceDelta`.
    :ivar pulse_delta: The source pulse delta command subsystem, an instance of
        :class:`~.SourcePulseDelta`.
    :ivar differential_conductance: The source differential conductance command
        subsystem, an instance of :class:`~.SourceDifferentialConductance`.
    :ivar wave: The source wave command subsystem, an instance of
        :class:`~.SourceWave`.

    """
    def __init__(self, transport, protocol):
        super(Source, self).__init__(transport, protocol)
        self.current = SourceCurrent(self._transport, self._protocol)
        self.delay = Command(
            ':SOUR:DEL?',
            ':SOUR:DEL',
            Float(min=1e-3, max=999999.999, fmt='{0:.3f}')
        )
        self.sweep = SourceSweep(self._transport, self._protocol)
        self.list = SourceList(self._transport, self._protocol)
        self.delta = SourceDelta(self._transport, self._protocol)
        self.pulse_delta = SourcePulseDelta(self._transport, self._protocol)
        self.differential_conductance = SourceDifferentialConductance(
            self._transport,
            self._protocol
        )
        self.wave = SourceWave(self._transport, self._protocol)

    def clear(self):
        """Clears the current source."""
        self._write(':SOUR:CLE')


class SourceCurrent(Driver):
    """The current command subsystem of the Source node.

    :ivar float amplitude: The current amplitude in ampere. [-105e-3, 105e3].
    :ivar float range: The current range in ampere. [-105e-3, 105e3].
    :ivar bool auto_range: A boolean flag to enable/disable auto ranging.
    :ivar float compliance: The voltage compliance in volts. [0.1, 105].
    :ivar bool analog_filter: The state of the analog filter.
    :ivar float start: The start current. [-105e-3, 105e-3].
    :ivar float step: The step current. [-1e-13, 105e-3].
    :ivar float stop: The stop current. [-105e-3, 105e-3].
    :ivar float center: The center current. [-105e-3, 105e-3].
    :ivar float span: The span current. [2e-13, 210e-3].

    """
    def __init__(self, transport, protocol):
        super(SourceCurrent, self).__init__(transport, protocol)
        self.amplitude = Command(
            ':SOUR:CURR?',
            ':SOUR:CURR',
            Float(min=-105e-3, max=105e3)
        )
        self.range = Command(
            ':SOUR:CURR:RANG?',
            ':SOUR:CURR:RANG',
            Float(min=-105e-3, max=105e3)
        )
        self.auto_range = Command(
            ':SOUR:CURR:RANG:AUTO?',
            ':SOUR:CURR:RANG:AUTO',
            Boolean
        )
        self.compliance = Command(
            ':SOUR:CURR:COMP?',
            ':SOUR:CURR:COMP',
            Float(min=0.1, max=105)
        )
        self.analog_filter = Command(
            ':SOUR:CURR:FILT?',
            ':SOUR:CURR:FILT',
            Boolean
        )
        self.start = Command(
            ':SOUR:CURR:STAR?',
            ':SOUR:CURR:STAR',
            Float(min=-105e-3, max=105e-3)
        )
        self.step = Command(
            ':SOUR:CURR:STEP?',
            ':SOUR:CURR:STEP',
            Float(min=1e-13, max=105e-3)
        )
        self.stop = Command(
            ':SOUR:CURR:STOP?',
            ':SOUR:CURR:STOP',
            Float(min=-105e-3, max=105e-3)
        )
        self.center = Command(
            ':SOUR:CURR:CENT?',
            ':SOUR:CURR:CENT',
            Float(min=-105e-3, max=105e-3)
        )
        self.span = Command(
            ':SOUR:CURR:SPAN?',
            ':SOUR:CURR:SPAN',
            Float(min=2e-13, max=210e-3)
        )


class SourceSweep(Driver):
    """The sweep command subsystem of the Source node.

    :ivar spacing: The sweep type, valid are 'linear', 'log' and 'list'.
    :ivar int points: The number of sweep points in the range 1 to 65535.
    :ivar ranging: The sweep ranging, valid are 'auto', 'best' and 'fixed'.
    :ivar count: The sweep count, either an integer between 1 and 9999 or
        float('inf').

        .. note:: The range is not checked.

    :ivar bool compliance_abort: Enables/Disables the compliance abort function.

    """
    def __init__(self, transport, protocol):
        super(SourceSweep, self).__init__(transport, protocol)
        self.spacing = Command(
            ':SOUR:SWE:SPAC?',
            ':SOUR:SWE:SPAC',
            Mapping({'linear': 'LIN', 'log': 'LOG', 'list': 'LIST'})
        )
        self.points = Command(
            ':SOUR:SWE:POIN?',
            ':SOUR:SWE:POIN',
            Integer(min=1, max=65535)
        )
        self.ranging = Command(
            ':SOUR:SWE:RANG?',
            ':SOUR:SWE:RANG',
            Mapping({'auto': 'AUTO', 'best': 'BEST', 'fixed': 'FIXED'})
        )
        self.count = Command(
            ':SOUR:SWE:COUN?',
            ':SOUR:SWE:COUN',
            # We use a float instead of an integer because it can represent
            # infinity. E.g. float('inf') is valid python.
            Float
        )
        self.compliance_abort = Command(
            ':SOUR:SWE:CAB?',
            ':SOUR:SWE:CAB',
            Boolean
        )

    def arm(self):
        """Arms the sweep."""
        self._write(':SOUR:SWE:ARM')

    def abort(self):
        """Aborts the sweep mode."""
        self._write(':SOUR:SWE:ABOR')


class SourceList(Driver):
    """The list command subsystem of the Source node.

    It is used to define arbitrarycurrent pulse sequences. E.g. writing a
    current sequence is as simple as::

        >>> k6221.source.list.current[:] = [-0.01, -0.02, 0.0]
        >>> len(k6221.source.list.current)
        3

    To extend the list, a special member function is provided::

        >>> k6221.source.list.current.extend([0.01, 0.0, 0.0])
        >>> k6221.source.list.current[:]
        [-0.01, -0.02, 0.0, 0.01, 0.0, 0.0]

    Slicing notation can also be used to manipulate the sequence::

        >>> k6221.source.list.current[::2] = [-0.03, 0.05, 0.07]
        >>> k6221.source.list.current[:]
        [-0.03, -0.02, 0.05, 0.01, 0.07, 0.0]

    :attr:`~.SourceList.delay` and :attr:`~.SourceList.compliance` can be
    manipulated in the same manner.

    :ivar current: An instance of :class:`~.SourceListSequence`, giving access
        to the current subsystem.
    :ivar delay: An instance of :class:`~.SourceListSequence`, giving access
        to the delay subsystem.
    :ivar current: An instance of :class:`~.SourceListSequence`, giving access
        to the compliance subsystem.

    """
    def __init__(self, transport, protocol):
        super(SourceList, self).__init__(transport, protocol)
        self.current = SourceListSequence(
            transport,
            protocol,
            node='CURR',
            type=Float(min=-105e-3, max=105e-3)
        )
        self.delay = SourceListSequence(
            transport,
            protocol,
            node='DEL',
            type=Float(min=1e-3, max=999999.999)
        )
        self.current = SourceListSequence(
            transport,
            protocol,
            node='COMP',
            type=Float(min=-1e-3, max=105e-3)
        )


class SourceListSequence(Driver):
    def __init__(self, transport, protocol, node, type):
        super(SourceListSequence, self).__init__(transport, protocol)
        self._node = node
        self._extend = Command(write=(
            ':SOUR:LIST:{}:APPEND'.format(node),
            itertools.repeat(type))
        )
        self._sequence = Command(
            ':SOUR:LIST:{}?'.format(node),
            ':SOUR:LIST:{}?'.format(node),
            itertools.repeat(type)
        )

    def extend(self, iterable):
        """Extends the list."""
        self._extend = iterable

    def __getitem__(self, item):
        return self._sequence[item]

    def __setitem__(self, item, value):
        seq = self._sequence
        seq[item] = value
        self._sequence = seq

    def __len__(self):
        return self._query((':SOUR:LIST:{}:POIN?'.format(self._node), Integer))

class SourceDelta(Driver):
    """The delta command subsystem of the Source node.

    :ivar float high: The high source value, in the range 0 to 105e-3 (amps).
    :ivar float low: The low source value, in the range 0 to -105e-3 (amps).
    :ivar float delay: The delta delay in seconds from 1e-3 to 1e5.
    :ivar count: The sweep count, either an integer between 1 and 65536 or
        float('inf').

        .. note:: The range is not checked.

    :ivar bool compliance_abort: Enables/Disables the compliance abort function.
    :ivar bool cold_switching: The cold switching mode.

    """
    def __init__(self, transport, protocol):
        super(SourceDelta, self).__init__(transport, protocol)
        self.high = Command(
            ':SOUR:DELT:HIGH?',
            ':SOUR:DELT:HIGH',
            Float(min=0, max=105e-3)
        )
        self.low = Command(
            ':SOUR:DELT:LOW?',
            ':SOUR:DELT:LOW',
            Float(min=-105e-3, max=0.)
        )
        self.delay = Command(
            ':SOUR:DELT:DEL?',
            ':SOUR:DELT:DEL',
            Float(min=1e-3, max=9999.999)
        )
        self.count = Command(
            ':SOUR:DELT:COUN?',
            ':SOUR:DELT:COUN',
            # We use a float instead of an integer because it can represent
            # infinity. E.g. float('inf') is valid python.
            Float
        )
        self.compliance_abort = Command(
            ':SOUR:DELT:CAB?',
            ':SOUR:DELT:CAB',
            Boolean
        )
        self.cold_switching = Command(
            ':SOUR:DELT:CSW?',
            ':SOUR:DELT:CSW',
            # TODO check response
            Boolean
        )

    def voltmeter_connected(self):
        """The nanovoltmeter connection status."""
        return self._query((':SOUR:DELT:NVPR?', Boolean))

    def arm(self):
        """Arms the source delta mode."""
        self._write(':SOUR:DELT:ARM')

    def is_armed(self):
        """A boolean flag returning arm state."""
        return self._query((':SOUR:DELT:ARM?', Boolean))


class SourcePulseDelta(Driver):
    """The pulse delta command subsystem of the Source node.

    :ivar float high: The high source value, in the range 0 to 105e-3 (amps).
    :ivar float low: The low source value, in the range 0 to -105e-3 (amps).
    :ivar float width: Pulse width in seconds in the range 50e-6 to 12e-3.
    :ivar count: The sweep count, either an integer between 1 and 65636 or
        float('inf').

        .. note:: The range is not checked.
    :ivar float source_delay: The source delay in seconds in the range 16e-6 to
        11.966e-3.
    :ivar ranging: The pulse source ranging mode. Valid are 'best' or 'fixed'.
    :ivar interval: The interval for each pulse cycle, an integer number of
        powerline cycles in the range 5 to 999999
    :ivar bool sweep_output: The state of the sweep output.
    :ivar int low_measurements: The number of low measurements per cycle, either
        1 or 2.

    """
    def __init__(self, transport, protocol):
        super(SourcePulseDelta, self).__init__(transport, protocol)
        self.high = Command(
            ':SOUR:PDEL:HIGH?',
            ':SOUR:PDEL:HIGH',
            Float(min=0, max=105e-3)
        )
        self.low = Command(
            ':SOUR:PDEL:LOW?',
            ':SOUR:PDEL:LOW',
            Float(min=-105e-3, max=0.)
        )
        self.width = Command(
            ':SOUR:PDEL:WIDT?',
            ':SOUR:PDEL:WIDT',
            Float(min=50e-6, max=12e-3)
        )
        self.count = Command(
            ':SOUR:PDEL:COUN?',
            ':SOUR:PDEL:COUN',
            # We use a float instead of an integer because it can represent
            # infinity. E.g. float('inf') is valid python.
            Float
        )
        self.source_delay = Command(
            ':SOUR:PDEL:SDEL?',
            ':SOUR:PDEL:SDEL',
            Float(min=16e-6, max=11.966e-3)
        )
        self.ranging = Command(
            ':SOUR:PDEL:RANG?',
            ':SOUR:PDEL:RANG',
            Mapping({'best': 'BEST', 'fixed': 'FIX'})
        )
        self.interval = Command(
            ':SOUR:PDEL:INT?',
            ':SOUR:PDEL:INT',
            Integer(min=1, max=999999)
        )
        self.sweep_output = Command(
            ':SOUR:PDEL:SWE?',
            ':SOUR:PDEL:SWE',
            Boolean
        )
        self.low_measurements = Command(
            ':SOUR:PDEL:LME?',
            ':SOUR:PDEL:LME',
            Integer(min=1, max=2)
        )

    def voltmeter_connected(self):
        """The nanovoltmeter connection status."""
        return self._query((':SOUR:PDEL:NVPR?', Boolean))

    def arm(self):
        """Arms the source delta mode."""
        self._write(':SOUR:PDEL:ARM')

    def is_armed(self):
        """A boolean flag returning arm state."""
        return self._query((':SOUR:PDEL:ARM?', Boolean))


class SourceDifferentialConductance(Driver):
    """The differential conductance command subsystem of the Source node.

    :ivar float zero_voltage: The zero voltage of the nanovoltmeter 2182/2182A.
    :ivar float start: The starting current (amps) in the range -105e-3 to
        105e-3.
    :ivar float step: The current step (amps) in the range 0 to 105e-3.
    :ivar float stop: The stop current (amps) in the range -105e-3 to 105e-3.
    :ivar float delta: The delta value in the range 0 to 105-e3.
    :ivar float delay: The delay (seconds) in the range 1e-3 to 1e5.
    :ivar bool compliance_abort: Enables/Disables the compliance abort function.

    """
    def __init__(self, transport, protocol):
        super(SourceDifferentialConductance, self).__init__(transport, protocol)
        self.zero_voltage = Command((':SOUR:DCON:NVZ?', Float))
        self.start = Command(
            ':SOUR:DCON:STAR?',
            ':SOUR:DCON:STAR',
            Float(min=-105e-3, max=105e-3)
        )
        self.step = Command(
            ':SOUR:DCON:STEP?',
            ':SOUR:DCON:STEP',
            Float(min=0, max=105e-3)
        )
        self.stop = Command(
            ':SOUR:DCON:STOP?',
            ':SOUR:DCON:STOP',
            Float(min=-105e-3, max=105e-3)
        )
        self.delta = Command(
            ':SOUR:DCON:DELT?',
            ':SOUR:DCON:DELT',
            Float(min=0., max=105e-3)
        )
        self.delay = Command(
            ':SOUR:DCON:DEL?',
            ':SOUR:DCON:DEL',
            Float(min=1e-3, max=9999.999)
        )
        self.compliance_abort = Command(
            ':SOUR:DCON:CAB?',
            ':SOUR:DCON:CAB',
            Boolean
        )

    def voltmeter_connected(self):
        """The nanovoltmeter connection status."""
        return self._query((':SOUR:DCON:NVPR?', Boolean))

    def arm(self):
        """Arms the source delta mode."""
        self._write(':SOUR:DCON:ARM')

    def is_armed(self):
        """A boolean flag returning arm state."""
        return self._query((':SOUR:DCON:ARM?', Boolean))


class SourceWave(Driver):
    """The wave command subsystem of the Source node.

    :ivar function: The wave function. Valid are 'sin', 'square', 'ramp',
        'arbitrary0', 'arbitrary1', 'arbitrary2', 'arbitrary3' or 'arbitrary4'.
    :ivar int duty_cycle: The duty cycle of the wave function in percent.
        [0, 100].
    :ivar float amplitude: The peak amplitude of the generated wave function in
        amps. [2e-12, 105e-3].
    :ivar float frequency: The frequency of the wave function in Hz. [1e-3, 1e5].
    :ivar float offset: The offset of the wave function in amps. [-105e-3, 105e-3]
    :ivar phase_marker: The phase marker command subgroup, an instance of
        :class:`~.SourceWavePhaseMarker`.
    :ivar arbitrary: The arbitrary sub command group, an instance of
        :class:`~.SourceWaveArbitrary`.
    :ivar ranging: The source ranging mode. Valid are 'best' or 'fixed'.
    :ivar duration: The waveform duration in seconds. Valid are floats in the
        range [100e-9, 999999.999] or `float('inf')`
    :ivar cycles: The waveform duration in cycles. Valid are floats in the
        range [1e-3, 99999999900] or `float('inf')`.
    """
    def __init__(self, transport, protocol):
        super(SourceWave, self).__init__(transport, protocol)
        self.function = Command(
            ':SOUR:WAVE:FUNC?',
            ':SOUR:WAVE:FUNC',
            Mapping({
                'sin': 'SIN',
                'square': 'SQU',
                'ramp': 'RAMP',
                'arbitrary0': 'ARB0',
                'arbitrary1': 'ARB1',
                'arbitrary2': 'ARB2',
                'arbitrary3': 'ARB3',
                'arbitrary4': 'ARB4',
            })
        )
        self.duty_cycle = Command(
            ':SOUR:WAVE:DCYC?',
            ':SOUR:WAVE:DCYC',
            Integer(min=0, max=100)
        )
        self.amplitude = Command(
            ':SOUR:WAVE:AMPL?',
            ':SOUR:WAVE:AMPL',
            Float(min=2e-12, max=105e-3)
        )
        self.frequency = Command(
            ':SOUR:WAVE:FREQ?',
            ':SOUR:WAVE:FREQ',
            Float(min=1e-3, max=1e5)
        )
        self.offset = Command(
            ':SOUR:WAVE:OFFS?',
            ':SOUR:WAVE:OFFS',
            Float(min=-105e-3, max=105e-3)
        )
        self.phase_marker = SourceWavePhaseMarker(self._transport, self._protocol)
        self.arbitrary = SourceWaveArbitrary(self._transport, self._protocol)
        self.ranging = Command(
            ':SOUR:WAVE:RANG?',
            ':SOUR:WAVE:RANG',
            Mapping({'best': 'BEST', 'fixed': 'FIX'})
        )
        self.duration = Command(
                ':SOUR:WAVE:DUR:TIME?',
                ':SOUR:WAVE:DUR:TIME',
            # TODO check if lowercase 'inf' works.
            # The Keithley accepts 'INF' as a valid duration.
            Float(min=100e-9, max=999999.999)
        )
        self.cycles = Command(
            ':SOUR:WAVE:DUR:CYCL?',
            ':SOUR:WAVE:DUR:CYCL',
            # TODO check if lowercase 'inf' works.
            # The Keithley accepts 'INF' as a valid duration.
            Float(min=1e-3, max=99999999900)
        )
        self.external_trigger = SourceWaveETrigger(self._transport, self._protocol)

    def arm(self):
        """Arm waveform function."""
        self._write(':SOUR:WAVE:ARM')

    def initiate(self):
        """Initiate waveform output."""
        self._write(':SOUR:WAVE:INIT')

    def abort(self):
        """Abort waveform output."""
        self._write(':SOUR:WAVE:ABOR')


class SourceWavePhaseMarker(Driver):
    """The phase marker command subgroup of the SourceWave node.

    :ivar int level: The marker phase in degrees. [0, 360].
    :ivar int output_line: The output trigger line. [1, 6].
    :ivar bool enabled: The state of the phase marker.

    """
    def __init__(self, transport, protocol):
        super(SourceWavePhaseMarker, self).__init__(transport, protocol)
        self.level = Command(
            ':SOUR:WAVE:PMAR?',
            ':SOUR:WAVE:PMAR',
            Integer(min=0, max=360)
        )
        self.output_line = Command(
            ':SOUR:WAVE:PMAR:OLIN?',
            ':SOUR:WAVE:PMAR:OLIN',
            Integer(min=1, max=6)
        )
        self.enabled = Command(
            ':SOUR:WAVE:PMAR:STAT?',
            ':SOUR:WAVE:PMAR:STAT',
            Boolean
        )


class SourceWaveArbitrary(Driver):
    """The arbitrary waveform command subgroup of the SourceWave node.

    It supports slicing notation to read and write up to 100 points into memory.

    """
    def __init__(self, transport, protocol):
        super(SourceWaveArbitrary, self).__init__(transport, protocol)
        self._extend = Command(write=(
            ':SOUR:WAVE:ARB:APPEND',
            itertools.repeat(Float(min=-1, max=1.), 100)
        ))
        self._sequence = Command(
                ':SOUR:WAVE:ARB:DATA?',
                ':SOUR:WAVE:ARB:DATA',
            itertools.repeat(Float(min=-1, max=1.), 100)
        )

    def copy(self, index):
        """Copy arbitrary points into NVRAM.

        :param index: The K6221 can store up to 4 arbitrary wavefunctions. The
            index parameter chooses the buffer index. Valid are 1 to 4.

        """
        self._write(('SOUR:WAVE:ARB:COPY', Integer(min=1, max=4)), index)

    def extend(self, iterable):
        """Extends the list."""
        self._extend = iterable

    def __getitem__(self, item):
        return self._sequence[item]

    def __setitem__(self, item, value):
        seq = self._sequence
        seq[item] = value
        self._sequence = seq

    def __len__(self):
        return self._query((':SOUR:WAVE:ARB:POIN?', Integer))


class SourceWaveETrigger(Driver):
    """The external trigger command subgroup of the SourceWave node.

    .. note:: These commands were introduced with firmware revision **A03**.

    :ivar bool enabled: The state of the external trigger mode of the wave
        function generator.
    :ivar int input_line: The trigger input line. In the range [1, 6] or
        `None`.
    :ivar bool ignore: The retriggering mode. It defines wether or not the
        waveform restarts upon retriggering.
    :ivar float inactive_value: The inactive value. [-1.00, 1.00].

    """
    def __init__(self, transport, protocol):
        super(SourceWaveETrigger, self).__init__(transport, protocol)
        self.enabled = Command(
            ':SOUR:WAVE:EXTR?',
            ':SOUR:WAVE:EXTR',
            Boolean
        )
        self.input_line = Command(
            ':SOUR:WAVE:EXTR:ILIN?',
            ':SOUR:WAVE:EXTR:ILIN',
            Enum(None, 1, 2, 3, 4, 5, 6)
        )
        # TODO check wether True means restart waveform or not.
        self.ignore = Command(
            ':SOUR:WAVE:EXTR:IGN?',
            ':SOUR:WAVE:EXTR:IGN',
            Boolean
        )
        self.inactive_value = Command(
            ':SOUR:WAVE:EXTR:IVAL?',
            ':SOUR:WAVE:EXTR:IVAL',
            Float(min=-1., max=1.)
        )


# -----------------------------------------------------------------------------
# Status Command Layer
# -----------------------------------------------------------------------------
class Status(Driver):
    """The status sub commands.

    :ivar measurement: The measurement status register subcommands, an instance
        of :class:`~.StatusEvent`. See :attr:`~.Status.MEASUREMENT`.
    :ivar operation: The operation event register subcommands, an instance of
        :class:`~.StatusEvent`. See :attr:`~.Status.OPERATION`.
    :ivar questionable: The questionable event register subcommands, an instance
        of :class:`~.StatusEvent`.. See :attr:`~.Status.QUESTIONABLE`.
    :ivar queue: The status queue subcommands, an instance of
        :class:`~StatusQueue`.

    """
    #: The measurement status register bits and their corresponding keys.
    MEASUREMENT = {
        0: 'reading overflow',
        1: 'interlock',
        2: 'over temperature',
        3: 'compliance',
        5: 'reading available',
        6: 'trace notify',
        7: 'buffer available',
        8: 'buffer half full',
        9: 'buffer full',
        12: 'buffer quarter full',
        13: 'buffer 3/4 full',
    }
    #: The questionable event register bits and their corresponding keys.
    QUESTIONABLE = {
        4: 'power',
        8: 'calibration',
    }
    #: The operation event register bits and their corresponding keys.
    OPERATION = {
        0: 'calibrating',
        1: 'sweep done',
        2: 'sweep aborted',
        3: 'sweeping',
        4: 'wave started',
        5: 'waiting for trigger',
        6: 'waiting for arm',
        7: 'wave stopped',
        8: 'filter settled',
        10: 'idle',
        11: 'rs232 error',
    }
    def __init__(self, transport, protocol):
        super(Status, self).__init__(transport, protocol)
        self.measurement = StatusEvent(
            transport,
            protocol,
            'MEAS',
            Status.MEASUREMENT
        )
        self.operation = StatusEvent(
            transport,
            protocol,
            'OPER',
            Status.OPERATION
        )
        self.questionable = StatusEvent(
            transport,
            protocol,
            'QUES',
            Status.QUESTIONABLE
        )
        self.queue = StatusQueue(transport, protocol)

    def preset(self):
        """Returns the status registers to their default states."""
        self._write(':STAT:PRES')


class StatusEvent(Driver):
    """A status event sub command group.

    :ivar event: The event register.(read-only)
    :ivar enable: The event enable register.
    :ivar condition: The condition register. If the event condition does not
        exist anymore, the bit is cleared.

    """
    def __init__(self, transport, protocol, node, register):
        super(StatusEvent, self).__init__(transport, protocol)
        self.event = Command(
            ':STAT:{}?'.format(node),
            ':STAT:{}'.format(node),
            Register(register)
        )
        self.enable = Command(
                ':STAT:{}:ENAB?'.format(node),
                ':STAT:{}:ENAB'.format(node),
            Register(register)
        )
        self.condition = Command(
            ':STAT:{}:COND?'.format(node),
            ':STAT:{}:COND'.format(node),
            Register(register)
        )


class StatusQueue(Driver):
    """The status queue sub commands.

    :ivar next: The most recent error message. (read-only)
    :ivar enable: A list of enabled error messages.
    :ivar disable: A list of disabled error messages.

    """
    def __init__(self, transport, protocol):
        super(StatusQueue, self).__init__(transport, protocol)
        self.next = Command((':STAT:QUE?', itertools.repeat(Integer())))
        self.enable = Command(
            ':STAT:QUE:ENAB?',
            ':STAT:QUE:ENAB',
            itertools.repeat(Integer())
        )
        self.disable = Command(
            ':STAT:QUE:DIS?',
            ':STAT:QUE:DIS',
            itertools.repeat(Integer())
        )

    def clear(self):
        """Clears all messages from the error queue."""
        self._write(':STAT:QUE:CLE')


# -----------------------------------------------------------------------------
# System Command Layer
# -----------------------------------------------------------------------------
class System(Driver):
    """The System command subsystem.

    :ivar communicate: The commuicate sub commands, an instance of
        :class:`~.SystemCommunicate`.
    :ivar int key: Reading queries the last pressed key, writing simulates a key
        press. See the manual for valid key-press codes.
    :ivar bool key_click: Enables/disables the key click.
    :ivar bool beep: The state of the beeper.
    :ivar poweron_setup: Chooses which setup is loaded at power on. Valid are
        'reset', 'preset', 'save0', 'save1', 'save2', 'save3' and 'save4'.
    :ivar error: The latest error code and message. (read-only)
    :ivar version: The scpi revision number. (read-only)
    :ivar analog_board: The analog board subcommands, an instance of
        :class:`~.StatusBoard`.

    """
    def __init__(self, transport, protocol):
        super(System, self).__init__(transport, protocol)
        self.communicate = SystemCommunicate(transport, protocol)
        self.key = Command(
            ':SYST:KEY?',
            ':SYST:KEY',
            Integer
        )
        self.key_click = Command(
            ':SYST:KCL?',
            ':SYST:KCL',
            Boolean
        )
        self.beep = Command(
            ':SYST:BEEP:STAT?',
            ':SYST:BEEP:STAT',
            Boolean
        )
        self.poweron_setup = Command(
            ':SYST:POS?',
            ':SYST:POS',
            Mapping({
                'reset': 'RST', 'preset': 'PRES', 'save0': 'SAV0',
                'save1': 'SAV1', 'save2': 'SAV2', 'save3': 'SAV3',
                'save4': 'SAV4'
            })
        )
        self.error = Command(('SYST:ERR?', Integer, String))
        self.version = Command((':SYST:VERS?', String))
        self.analog_board = SystemBoard(transport, protocol, node='ABO')
        self.digital_board = SystemBoard(transport, protocol, node='DBO')
        self.password = SystemPassword(transport, protocol)

        def preset(self):
            """Returns the device to system preset settings."""
            self._write(':SYST:PRES')

        def clear(self):
            """Clears the error code and message from the error queue."""
            self._write(':SYS:CLE')

        def reset_timestamp(self):
            """Resets the system timestamp to zero."""
            self._write(':SYS:TST:RES')

        def reset_reading(self):
            """Resets the system reading number to zero."""
            self._write(':SYS:RNUM:RES')


class SystemCommunicate(Driver):
    """The system communicate command subsystem.

    :ivar gpib: The gpib subsystem. An instance of
        :class:`~.SystemCommunicateGpib`.
    :ivar serial: The serial subsystem. An instance of
        :class:`~.SystemCommunicateSerial`
    :ivar ethernet: The ethernet subsystem. An instance of
        :class:`~.SystemCommunicateEthernet`.
    :ivar bool local_lockout: Enables/Disables the local lockout.
        .. note:: Only valid if RS232 interface is used.

    """

    def __init__(self, transport, protocol):
        super(SystemCommunicate, self).__init__(transport, protocol)
        self.gpib = SystemCommunicateGpib(transport, protocol)
        self.serial = SystemCommunicateSerial(transport, protocol)
        self.ethernet = SystemCommunicateEthernet(transport, protocol)
        self.local_lockout = Command(
            ':SYST:COMM:RWL?',
            ':SYST:COMM:RWL',
            Boolean
        )

    def select(self, interface):
        """Selects the communication interface.

        :param interface: Valid are 'gpib', 'serial' or 'ethernet'

        """
        self._write(
            ':SYST:COMM:SEL',
            Mapping({'gpib': 'GPIB', 'serial': 'SER', 'ethernet': 'ETH'})
        )

    def local(self):
        """Set's the device in local mode.

        .. note RS232 only.

        """
        self._write(':SYST:COMM:LOC')

    def remote(self):
        """Set's the device in remote mode.

        .. note RS232 only.

        """
        self._write(':SYST:COMM:REM')


class SystemCommunicateGpib(Driver):
    """The gpib command subsystem.

    :ivar int address: The gpib address, in the range 0 to 30.

    """
    def __init__(self, transport, protocol):
        super(SystemCommunicateGpib, self).__init__(transport, protocol)
        self.address = Command(
            ':SYST:COMM:GPIB:ADDR?',
            ':SYST:COMM:GPIB:ADDR',
            Integer(min=0, max=30)
        )


class SystemCommunicateSerial(Driver):
    """The serial command subsystem.

    :ivar handshake: The serial control handshaking. Valid are 'ibfull', 'rfr'
        and 'off'.
    :ivar pace: The flow control, either 'xon' or 'xoff'.
    :ivar terminator: The output terminator. Valid are '\\r', '\\n', '\\r\\n'
        and '\\n\\r'.
    :ivar baudrate: The baudrate, see :attr:`~.SystemCommunicateSerial.BAUDRATE`

    """
    BAUDRATE = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    def __init__(self, transport, protocol):
        super(SystemCommunicateSerial, self).__init__(transport, protocol)
        self.handshake = Command(
            ':SYST:COMM:SER:CONT:RTS?',
            ':SYST:COMM:SER:CONT:RTS',
            Mapping({'ibfull': 'IBFULL', 'rfr': 'RFR', 'off': 'OFF'})
        )
        self.pace = Command(
            ':SYST:COMM:SER:PACE?',
            ':SYST:COMM:SER:PACE',
            Mapping({'xon': 'XON', 'xoff': 'XOFF'})
        )
        self.terminator = Command(
            ':SYST:COMM:SER:TERM?',
            ':SYST:COMM:SER:TERM',
            Mapping({'\r': 'CR', '\n': 'LF', '\r\n': 'CRLF', '\n\r': 'LFCR'})
        )
        self.baudrate = Command(
            ':SYST:COMM:SER:BAUD?',
            ':SYST:COMM:SER:BAUD',
            Set(*SystemCommunicateSerial.BAUDRATE)
        )

    def send(self, data):
        """Send data via serial port of the device..

        .. warning:: Not implemented yet.

        """
        raise NotImplementedError()

    def enter(self, data):
        """Read data from serial port of the device.

        .. warning:: Not implemented yet.

        """
        raise NotImplementedError()


class SystemCommunicateEthernet(Driver):
    """The ethernet subcommands.

    :ivar str address: The ip address of the form "n.n.n.n".
    :ivar str maks: The subnet mask.
    :ivar str gateway: The gateway address.
    :ivar bool dhcp: Enables/Disables the dhcp.

    """
    def __init__(self, transport, protocol):
        super(SystemCommunicateEthernet, self).__init__(transport, protocol)
        self.address = Command(
            ':SYST:COMM:ETH:ADDR?',
            ':SYST:COMM:ETH:ADDR',
            String
        )
        self.mask = Command(
            ':SYST:COMM:ETH:MASK?',
            ':SYST:COMM:ETH:MASK',
            String
        )
        self.gateway = Command(
            ':SYST:COMM:ETH:GAT?',
            ':SYST:COMM:ETH:GAT',
            String
        )
        self.dhcp = Command(
            ':SYST:COMM:ETH:DHCP?',
            ':SYST:COMM:ETH:DHCP',
            Boolean
        )

    def save(self):
        """Saves the ethernet setting changes."""
        self._write(':SYST:COMM:ETH:SAVE')


class SystemBoard(Driver):
    """The system board subcommands.

    :ivar serial: The serial number. (read-only)
    :ivar revision: The revision number. (read-only)

    """
    def __init__(self, transport, protocol, node):
        super(SystemBoard, self).__init__(transport, protocol)
        self.serial = Command((':SYST:{}:SNUM?'.format(node), String))
        self.revision = Command((':SYST:{}:REV?'.format(node), String))


class SystemPassword(Driver):
    """The system password subcommands.

    :ivar bool enable: The state of the password protection.

    """
    def __init__(self, transport, protocol):
        super(SystemPassword, self).__init__(transport, protocol)
        self.enable = Command(
            ':SYST:PASS:ENAB?',
            ':SYST:PASS:ENAB',
            Boolean
        )

    def enable_protected_cmds(self, password):
        """Enables the protected commands."""
        self._write((':SYST:PASS:CDIS', String), password)

    def disable_protected_cmds(self, password):
        """Disables the protected commands."""
        self._write((':SYST:PASS:CEN', String), password)

    def new_password(self, password):
        """Set's a new password."""
        self._write((':SYST:PASS:NEW', String), password)


# -----------------------------------------------------------------------------
# Trace Command Layer
# -----------------------------------------------------------------------------
class Trace(Driver):
    """The trace command subsystem.

    :ivar points: The buffer size in number of delta readings. [1, 65536].
    :ivar actual_points: The number of points stored in the buffer. (read-only).
    :ivar notify: The number of readings that trigger the trace notify bit.
    :ivar feed: The buffer feed. Valid are 'sens1', 'calc1' and `None`.
    :ivar feed_control: The buffer control. Valid are 'next' and 'never'.
    :ivar data: The trace data subsystem, an instance of :class:`~.TraceData`.

    """
    def __init__(self, transport, protocol):
        super(Trace, self).__init__(transport, protocol)
        self.points = Command(
            ':TRAC:POIN?',
            ':TRAC:POIN',
            Integer(min=1, max=65536)
        )
        self.actual_points = Command((':TRAC:POIN:ACT?', Integer))
        self.notify = Command(
            ':TRAC:NOT?',
            ':TRAC:NOT',
            Integer(min=1, max=65536)
        )
        self.feed = Command(
            ':TRAC:FEED?',
            ':TRAC:FEED',
            Mapping({'sens1': 'SENS1', 'calc1': 'CALC1', None: 'NONE'})
        )
        self.feed_control = Command(
            ':TRAC:FEED:CONT?',
            ':TRAC:FEED:CONT',
            Mapping({'next': 'NEXT', 'never': 'NEV'})
        )
        # TODO check if something is missing
        self.timestamp_format = Command(
            ':TRAC:TST:FORM?',
            ':TRAC:TST:FORM',
            Mapping({'absolute': 'ABS', 'delta': 'DELT'})
        )

    def clear(self):
        """Clears the readings from buffer."""
        self._write(':TRAC:CLE')

    def free(self):
        """The number of free memory bytes."""
        # TODO return type wrong
        # example response: '2097152,0'
        return self._query((':TRAC:FREE?', Float))  # TODO check return type.


class TraceData(Driver):
    """The data command subsystem of the Trace node.

    The TraceData class provides a listlike interface to access the stored
    values.

    E.g.::

        # requests a single reading at position 1
        # (Note: Indices start at 0)
        k6221.trace.data[1]

        # request a range of values
        k6221.trace.data[4:8]

        # Requests all readings in buffer.
        k6221.trace.data[:]


    :ivar type: The type of the stored readings. Valid are `None`, 'delta',
        'dcon', 'pulse'. (read-only).

    """
    def __init__(self, transport, protocol):
        super(TraceData, self).__init__(transport, protocol)
        self.type = Command(
            ':TRAC:DATA:TYPE?',
            ':TRAC:DATA:TYPE',
            Mapping({
                None: 'NONE',
                'delta': 'DELT',
                'dcon': 'DCON',
                'pulse': 'PULS'
            })
        )

    def __getitem__(self, item):
        # TODO
        raise NotImplementedError()


# -----------------------------------------------------------------------------
# Trigger Command Layer
# -----------------------------------------------------------------------------
class Arm(Driver):
    """The arm command subsystem.

    :ivar source: The event detectpr. Valid are 'immediate', 'timer', 'bus',
        'tlink', 'bstest', 'pstest', 'nstest' or 'manual'.
    :ivar float timer: The timer interval in seconds in the range
        [0.00, 99999.99].
    :ivar source_bypass: The arm source bypass. Valid entries are 'source' or
        'acceptor'.
    :ivar int input_line: The arm input signal line, in the range [1, 6].
    :ivar int output_line: The arm output signal line, in the range [1, 6].
    :ivar output: The output trigger. Valid are 'tenter', 'texit' and `None`.

    """
    def __init__(self, transport, protocol):
        super(Arm, self).__init__(transport, protocol)
        self.source = Command(
            ':ARM:SOUR?',
            ':ARM:SOUR',
            Mapping({
                'immediate': 'IMM', 'timer': 'TIM', 'bus': 'BUS',
                'tlink': 'TLIN', 'bstest': 'BST', 'pstest': 'PST',
                'nstest': 'NST', 'manual': 'MAN'
            })
        )
        self.timer = Command(
            ':ARM:TIM?',
            ':ARM:TIM',
            Float(min=0, max=99999.99, fmt='{0:.2f}')
        )
        self.source_bypass = Command(
            ':ARM:DIR?',
            ':ARM:DIR',
            Mapping({'source': 'SOUR', 'acceptor': 'ACC'})
        )
        self.input_line = Command(
            ':ARM:ILIN?',
            ':ARM:ILIN',
            Integer(min=1, max=6)
        )
        self.output_line = Command(
            ':ARM:OLIN?',
            ':ARM:OLIN',
            Integer(min=1, max=6)
        )
        self.output = Command(
            ':ARM:OUTP?',
            ':ARM:OUTP',
            Mapping({'tenter': 'TENT', 'texit': 'TEX', None: 'NONE'})
        )

    def signal(self):
        """Bypass the arm control source."""
        self._write(':ARM:SIGN')


class Trigger(Driver):
    """The trigger command subsystem.

    :ivar source: The event detector. Valid are 'immediate' or 'tlink'.
    :ivar source_bypass: The trigger source bypass. Valid entries are 'source' or
        'acceptor'.
    :ivar int input_line: The trigger input signal line, in the range [1, 6].
    :ivar int output_line: The trigger output signal line, in the range [1, 6].
    :ivar output: The output trigger. Valid are 'source', 'delay' and `None`.

    """
    def __init__(self, transport, protocol):
        super(Trigger, self).__init__(transport, protocol)
        self.source = Command(
            ':TRIG:SOUR?',
            ':TRIG:SOUR',
            Mapping({'immediate': 'IMM', 'tlink': 'TLIN'})
        )
        self.source_bypass = Command(
            ':TRIG:DIR?',
            ':TRIG:DIR',
            Mapping({'source': 'SOUR', 'acceptor': 'ACC'})
        )
        self.input_line = Command(
            ':TRIG:ILIN?',
            ':TRIG:ILIN',
            Integer(min=1, max=6)
        )
        self.output_line = Command(
            ':TRIG:OLIN?',
            ':TRIG:OLIN',
            Integer(min=1, max=6)
        )
        self.output = Command(
            ':TRIG:OUTP?',
            ':TRIG:OUTP',
            Mapping({'source': 'SOUR', 'delay': 'DEL', None: 'NONE'})
        )

    def signal(self):
        """Bypass the trigger control source."""
        self._write(':TRIG:SIGN')


# -----------------------------------------------------------------------------
# Units Command Layer
# -----------------------------------------------------------------------------
class Units(Driver):
    """The units command subsystem.

    :ivar voltage: The units voltage subsystem, an instance of :class:`~.UnitVoltage`
    :ivar power: The units power subsystem, an instance of :class:`~.UnitPower`

    """
    def __init__(self, transport, protocol):
        super(Units, self).__init__(transport, protocol)
        self.voltage = UnitVoltage(self._transport, self._protocol)
        self.power = UnitPower(self._transport, self._protocol)


class UnitVoltage(Driver):
    """The voltage command subgroup of the Units node.

    :ivar dc: The voltage reading units, valid are 'V', 'Ohm', 'W', 'Siemens'.

    """
    def __init__(self, transport, protocol):
        super(UnitVoltage, self).__init__(transport, protocol)
        self.dc = Command(
            ':UNIT:VOLT?',
            ':UNIT:VOLT',
            Mapping({'V': 'V', 'Ohm': 'OHM', 'W': 'W', 'Siemens': 'SIEM'})
        )


class UnitPower(Driver):
    """The power command subgroup of the Units node.

    :ivar type: The power reading units in the pulse delta mode, valid are
        'peak' and 'average'.

    """
    def __init__(self, transport, protocol):
        super(UnitPower, self).__init__(transport, protocol)
        self.type = Command(
            ':UNIT:POW?',
            ':UNIT:POW',
            Mapping({'peak': 'PEAK', 'average': 'AVER'})
        )
