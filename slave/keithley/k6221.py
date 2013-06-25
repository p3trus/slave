#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
"""The k6221 module implements a complete programmable interface of the Keithley
:class:`~.K6221` ac/dc current source.

"""
from slave.core import Command, InstrumentBase
from slave.iec60488 import (IEC60488, Trigger, ObjectIdentification,
    StoredSetting)
from slave.types import Boolean, Enum, Float, Integer, Mapping, String


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

    :ivar status: The status command subgroup, an instance of
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
    def __init__(self, connection):
        super(K6221, self).__init__(connection)
        # The command subgroups
        self.math = Math(self.connection, self._cfg)
        self.buffer_statistics = BufferStatistics(self.connection, self._cfg)
        self.digital_io = DigitalIO(self.connection, self._cfg)
        self.display = Display(self.connection, self._cfg)
        self.format = Format(self.connection, self._cfg)
        self.output = Output(self.connection, self._cfg)
        self.sense = Sense(self.connection, self._cfg)
        self.source = Source(self.connection, self._cfg)
        self.status = Status(self.connection, self._cfg)
        self.system = System(self.connection, self._cfg)
        self.trace = Trace(self.connection, self._cfg)
        # The trigger command layer
        self.triggering = Trigger(self.connection, self._cfg)
        self.units = Units(self.connection, self._cfg)


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
class Math(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(Math, self).__init__(connection, cfg)
        self.format = Command(
            ':CALC:FORM?',
            ':CALC:FORM',
            Mapping({None: 'NONE', 'linear': 'MXB', 'reciprocal': 'REC'})
        )
        self.m = Command(
            ':CALC:KMAT:MMF?',
            ':CALC:KMAT:MMF',
            # TODO max value should be included in range
            Float(min=-9.99999e20, max=9.99999e20)
        )
        self.b = Command(
            ':CALC:KMAT:MBF?',
            ':CALC:KMAT:MBF',
            # TODO max value should be included in range
            Float(min=-9.99999e20, max=9.99999e20)
        )
        self.enabled = Command(':CALC:STAT?', ':CALC:STAT', Boolean)
        self.latest = Command(query=(':CALC:DATA?', Float))
        self.fresh = Command(query=(':CALC:DATA:FRESH', Float))


class BufferStatistics(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(BufferStatistics, self).__init__(connection, cfg)
        self.format = Command(
            ':CALC2:FORM?',
            ':CALC2:FORM',
            Mapping({
                'mean': 'MEAN', 'sdev': 'SDEV', 'max': 'MAX',
                'min': 'MIN', 'peak': 'PKPK'
            })
        )
        self.enabled = Command(':CALC2:STAT?', ':CALC2:STAT', Boolean)
        self.data = Command(query=(':CALC2:DATA?', Float))

    def immediate(self):
        """Perform the calculation on the buffer content."""
        self._write(':CALC2:IMM')


class DigitalIO(InstrumentBase):
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
    ivar force_pattern: The force pattern, a register dictionairy with the
        same form as the limit_pattern.

    """
    def __init__(self, connection, cfg):
        super(DigitalIO, self).__init__(connection, cfg)
        self.force_output = Command(':CALC3:LIM?', ':CALC3:LIM', Boolean)
        self.test_limit = Command(':CALC3:LIM?', ':CALC3:LIM', Boolean)
        pattern = Register({'out1': 0, 'out2': 1, 'out3': 2, 'out4': 3})
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
class Display(InstrumentBase):
    """The display command subgroup.

    :ivar enabled: A boolean representing the state of the frontpanel display
        and controls.
    :ivar top: The top line display. An instance of :class:`~.Window`.
    :ivar bottom: The bottom line display. An instance of :class:`~.Window`.

    """
    def __init__(self, connection, cfg):
        super(Display, self).__init__(connection, cfg)
        self.enabled = Command(':DISP:ENAB?', ':DISP:ENAB', Boolean)
        self.top = DisplayWindow(1, self.connection, self._cfg)
        self.bottom = DisplayWindow(2, self.connection, self._cfg)


class DisplayWindow(InstrumentBase):
    """The window command subgroup of the Display node.

    :ivar text: The window text. An instance of :class:`~.DisplayWindowText`.
    :ivar blinking: A boolean representing the blinking state of the message
        characters.

    """
    def __init__(self, id, connection, cfg):
        super(DisplayWindow, self).__init__(connection, cfg)
        self.id = int(id)
        self.text = DisplayWindowText(self.id, self.connection, self.cfg)
        self.blinking = Command(':DISP:ATTR?', ':DISP:ATTR', Boolean)


class DisplayWindowText(InstrumentBase):
    """The text command subgroup of the Window node.

    :ivar data: An ascii encoded message with up to 20 characters.
    :ivar bool enabled: The state of the text message.

    """
    def __init__(self, id, connection, cfg):
        super(DisplayWindowText, self).__init__(connection, cfg)
        # TODO check encoding.
        self.text = Command(
            ':DISP:WIND{0}:TEXT:DATA?'.format(id),
            ':DISP:WIND{0}:TEXT:DATA'.format(id),
            String(max=21)
        )
        self.enabled = Command(
            ':DISP:WIND{0}:TEXT:STAT?'.format(id),
            ':DISP:WIND{0}::TEXT:STAT'.format(id),
            Boolean
        )


# -----------------------------------------------------------------------------
# Format Command Layer
# -----------------------------------------------------------------------------
class Format(InstrumentBase):
    """The format command subgroup.

    :ivar data_type:
    :ivar elements:
    :ivar byte_order: The byte order. Valid are 'normal' and 'swapped'.

        .. note::

            After a reset, it defaults to 'normal' but the system preset
            is 'swapped'.

    :ivar status_register: The format of the status register. Valid are
        'ascii', 'octal', 'hex' and 'binary'.

    """
    def __init__(self, connection, cfg):
        super(Format, self).__init__(connection, cfg)
        # TODO write doc
        self.data = Command(
            ':FORM?',
            ':FORM',
            Mapping({
                'ascii': 'ASC', 'real32': 'REAL,32', 'real64': 'REAL,64',
                'sreal': 'SRE', 'dreal': 'DRE'
            })
        )
        # TODO
        # Example response 'READ,TST'
        # self.elements = Command(':FORM:ELEM?', ':FORM:ELEM', #TODO)
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
class Output(InstrumentBase):
    """The output command subsystem.

    :ivar enabled: A boolean representing the state of the output.
    :ivar low_to_earth: A boolean representing the state of the low to earth
        ground connection.
    :ivar inner_shield: The connection of the triax inner shield, either
        'output low' or 'guard'.
    :ivar response: The output response. Valid are 'fast' or 'slow'.
    :ivar interlock: A boolean representing the state of the interlock.
        `False` if the interlock is tripped (output is disabled) and `True` if
        the interlock is closed.

    """
    def __init__(self, connection, cfg):
        super(Output, self).__init__(connection, cfg)
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
class Sense(InstrumentBase):
    """The Sense command subsystem.

    :ivar data: The sense data subsystem, an instance of :class:`~.SenseData`.
    :ivar average: The sense average subsystem, an instance of
        :class:`~.SenseAverage`.

    """
    def __init__(self, connection, cfg):
        super(Sense, self).__init__(connection, cfg)
        self.data = SenseData(self.connection, self._cfg)
        self.average = SenseAverage(self.connection, self._cfg)


class SenseData(InstrumentBase):
    """The data command subsystem of the Sense node.

    :ivar fresh: Similar to latest, but the same reading can only be returned once.
        (read-only)
    :ivar latest: Represents the latest pre-math delta reading. (read-only)

    """
    def __init__(self, connection, cfg):
        super(SenseData, self).__init__(connection, cfg)
        self.fresh = Command(':SENS:DATA:FRES?', ':SENS:DATA:FRES', Float)
        self.latest = Command(':SENS:DATA?', ':SENS:DATA', Float)


class SenseAverage(InstrumentBase):
    """The average command subsystem of the Sense node.

    :ivar tcontrol: The filter control. Valid are 'moving', 'repeat'.
    :ivar window: The filter window in percent of the range, a float in the
        range [0.00, 10].
    :ivar count: The filter count size, an integer in the range [2, 300].
    :ivar enabled: The state of the averaging filter, either `True` or `False`.

    """
    def __init__(self, connection, cfg):
        super(SenseAverage, self).__init__(connection, cfg)
        self.tcontrol = Command(
            ':SENS:AVER:TCON?',
            ':SENS:AVER:TCON',
            Mapping({'moving': 'MOV', 'repeat': 'REP'})
        )
        self.window = Command(
            ':SENS:AVER:WIND?',
            ':SENS:AVER:WIND',
            Float(min=0., max=10.001)  # TODO max should be 10 and should be included.
        )
        self.count = Command(
            ':SENS:AVER:COUN?',
            ':SENS:AVER:COUN',
            Integer(min=2, max=301)
        )
        self.enabled = Command(':SENS:AVER?', ':SENS:AVER', Boolean)


# -----------------------------------------------------------------------------
# Source Command Layer
# -----------------------------------------------------------------------------
class Source(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(Source, self).__init__(connection, cfg)
        self.current = SourceCurrent(self.connection, self._cfg)
        self.delay = Command(
            ':SOUR:DEL?',
            ':SOUR:DEL',
            Float(min=1e-3, max=1e6, fmt='{0:.3f}')
        )
        self.sweep = SourceSweep(self.connection, self._cfg)
        self.list = SourceList(self.connection, self._cfg)
        self.delta = SourceDelta(self.connection, self._cfg)
        self.pulse_delta = SourcePulseDelta(self.connection, self._cfg)
        self.differential_conductance = SourceDifferentialConductance(self.connection, self._cfg)
        self.wave = SourceWave(self.connection, self._cfg)

    def clear(self):
        """Clears the current source."""
        self._write(':SOUR:CLE')


class SourceCurrent(InstrumentBase):
    """The current command subsystem of the Source node.

    :ivar float amplitude: The current amplitude in ampere. [-105e-3, 105e3].
    :ivar float range: The current range in ampere. [-105e-3, 105e3].
    :ivar bool auto_range: A boolean flag to enable/disable auto ranging.
    :ivar float compliance: The voltage compliance in volts. [0.1, 105].
    :ivar bool filtering: The state of the analog filter.
    :ivar float start: The start current. [-105e-3, 105e-3].
    :ivar float step: The step current. [-1e-13, 105e-3].
    :ivar float stop: The stop current. [-105e-3, 105e-3].
    :ivar float center: The center current. [-105e-3, 105e-3].
    :ivar float span: The span current. [2e-13, 210e-3].

    """
    def __init__(self, connection, cfg):
        super(SourceCurrent, self).__init__(connection, cfg)
        self.amplitude = Command(
            ':SOUR:CURR?',
            ':SOUR:CURR',
            # TODO max should be included in range.
            Float(min=-105e-3, max=105e3)
        )
        self.range = Command(
            ':SOUR:RANG?',
            ':SOUR:RANG',
            # TODO max should be included in range
            Float(min=-105e-3, max=105e3)
        )
        self.auto_range = Command(
            ':SOUR:RANG:AUTO?',
            ':SOUR:RANG:AUTO',
            Boolean
        )
        self.compliance = Command(
            ':SOUR:COMPL?',
            ':SOUR:COMPL',
            # TODO max should be included in range
            Float(min=0.1, max=105)
        )
        self.start = Command(
            ':SOUR:STAR?',
            ':SOUR:STAR',
            # TODO max should be included in range
            Float(min=-105e-3, max=105e-3)
        )
        self.step = Command(
            ':SOUR:STEP?',
            ':SOUR:STEP',
            # TODO max should be included in range
            Float(min=1e-13, max=105e-3)
        )
        self.stop = Command(
            ':SOUR:STOP?',
            ':SOUR:STOP',
            # TODO max should be included in range
            Float(min=-105e-3, max=105e-3)
        )
        self.center = Command(
            ':SOUR:CENT?',
            ':SOUR:CENT',
            # TODO max should be included in range
            Float(min=-105e-3, max=105e-3)
        )
        self.span = Command(
            ':SOUR:SPAN?',
            ':SOUR:SPAN',
            # TODO max should be included in range
            Float(min=2e-13, max=210e-3)
        )


class SourceSweep(InstrumentBase):
    """The sweep command subsystem of the Source node.

    :ivar :

    """
    def __init__(self, connection, cfg):
        super(SourceSweep, self).__init__(connection, cfg)


class SourceList(InstrumentBase):
    """The list command subsystem of the Source node.

    """
    def __init__(self, connection, cfg):
        super(SourceList, self).__init__(connection, cfg)
        # TODO


class SourceDelta(InstrumentBase):
    """The delta command subsystem of the Source node.

    :ivar :

    """
    def __init__(self, connection, cfg):
        super(SourceDelta, self).__init__(connection, cfg)
        # TODO


class SourcePulseDelta(InstrumentBase):
    """The pulse delta command subsystem of the Source node.

    :ivar :

    """
    def __init__(self, connection, cfg):
        super(SourcePulseDelta, self).__init__(connection, cfg)
        # TODO


class SourceDifferentialConductance(InstrumentBase):
    """The differential conductance command subsystem of the Source node.

    :ivar :

    """
    def __init__(self, connection, cfg):
        super(SourceDifferentialConductance, self).__init__(connection, cfg)
        # TODO


class SourceWave(InstrumentBase):
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
    :ivar ranging: The source ranging mode. Valid are 'best' or 'fixed'.
    :ivar duration: The waveform duration in seconds. Valid are floats in the
        range [100e-9, 999999.999] or `float('inf')`
    :ivar cycles: The waveform duration in cycles. Valid are floats in the
        range [1e-3, 99999999900] or `float('inf')`.
    """
    def __init__(self, connection, cfg):
        super(SourceWave, self).__init__(connection, cfg)
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
            Integer(min=0, max=101)
        )
        self.amplitude = Command(
            ':SOUR:WAVE:AMPL?',
            ':SOUR:WAVE:AMPL',
            # TODO The max should be included in the range
            Float(min=2e-12, max=105e-3)
        )
        self.frequency = Command(
            ':SOUR:WAVE:FREQ?',
            ':SOUR:WAVE:FREQ',
            # TODO The max should be included in the range
            Float(min=1e-3, max=1e5)
        )
        self.offset = Command(
            ':SOUR:WAVE:OFFS?',
            ':SOUR:WAVE:OFFS',
            # TODO The max should be included in the range
            Float(min=-105e-3, max=105e-3)
        )
        self.phase_marker = SourceWavePhaseMarker(self.connection, self._cfg)
        self.arbitrary = SourceWaveArbitrary(self.connection, self._cfg)
        self.ranging = Command(
            ':SOUR:WAVE:RANG?',
            ':SOUR:WAVE:RANG',
            Mapping({'best': 'BEST', 'fixed': 'FIX'})
        )
        self.duration = Command(
                ':SOUR:WAVE:DUR:TIME?',
                ':SOUR:WAVE:DUR:TIME',
            # TODO check if lowercase 'inf' works.
            Float(min=100e-9, max=1e6)
        )
        self.cycles = Command(
            ':SOUR:WAVE:DUR:CYCL?',
            ':SOUR:WAVE:DUR:CYCL',
            # TODO enforce max but allow infinity.
            # TODO check if lowercase 'inf' works.
            Float(min=1e-3)
        )
        self.external_trigger = SourceWaveETrigger(self.connection, self._cfg)

    def arm(self):
        """Arm waveform function."""
        self._write(':SOUR:WAVE:ARM')

    def initiate(self):
        """Initiate waveform output."""
        self._write(':SOUR:WAVE:INIT')

    def abort(self):
        """Abort waveform output."""
        self._write(':SOUR:WAVE:ABOR')


class SourceWavePhaseMarker(InstrumentBase):
    """The phase marker command subgroup of the SourceWave node.

    :ivar int level: The marker phase in degrees. [0, 360].
    :ivar int output_line: The output trigger line. [1, 6].
    :ivar bool enabled: The state of the phase marker.

    """
    def __init__(self, connection, cfg):
        super(SourceWavePhaseMarker, self).__init__(connection, cfg)
        self.level = Command(
            ':SOUR:WAVE:PMAR?',
            ':SOUR:WAVE:PMAR',
            Integer(min=0, max=361)
        )
        self.output_line = Command(
            ':SOUR:WAVE:PMAR:OLIN?',
            ':SOUR:WAVE:PMAR:OLIN',
            Integer(min=1, max=7)
        )
        self.enabled = Command(
            ':SOUR:WAVE:PMAR:STAT?',
            ':SOUR:WAVE:PMAR:STAT',
            Boolean
        )


class SourceWaveArbitrary(InstrumentBase):
    """The arbitrary waveform command subgroup of the SourceWave node.

    """
    def __init__(self, connection, cfg):
        super(SourceWaveArbitrary, self).__init__(connection, cfg)
        # TODO


class SourceWaveETrigger(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(SourceWaveETrigger, self).__init__(connection, cfg)
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


# -----------------------------------------------------------------------------
# Status Command Layer
# -----------------------------------------------------------------------------
class Status(InstrumentBase):
    def __init__(self, connection, cfg):
        super(Status, self).__init__(connection, cfg)


# -----------------------------------------------------------------------------
# System Command Layer
# -----------------------------------------------------------------------------
class System(InstrumentBase):
    def __init__(self, connection, cfg):
        super(System, self).__init__(connection, cfg)


# -----------------------------------------------------------------------------
# Trace Command Layer
# -----------------------------------------------------------------------------
class Trace(InstrumentBase):
    """The trace command subsystem.

    :ivar points: The buffer size in number of delta readings. [1, 65536].
    :ivar actual_points: The number of points stored in the buffer. (read-only).
    :ivar notify: The number of readings that trigger the trace notify bit.
    :ivar feed: The buffer feed. Valid are 'sens1', 'calc1' and `None`.
    :ivar feed_control: The buffer control. Valid are 'next' and 'never'.
    :ivar data: The trace data subsystem, an instance of :class:`~.TraceData`.

    """
    def __init__(self, connection, cfg):
        super(Trace, self).__init__(connection, cfg)
        self.points = Command(
            ':TRAC:POIN?',
            ':TRAC:POIN',
            Integer(min=1, max=65536)
        )
        self.actual_points = Command(query=(':TRAC:POIN:ACT?', Integer))
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


class TraceData(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(TraceData, self).__init__(connection, cfg)
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
class Arm(InstrumentBase):
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
    def __init__(self, connection, cfg):
        super(Arm, self).__init__(connection, cfg)
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
            Float(min=0, max=1e5, fmt='{0:.2f}')
        )
        self.source_bypass = Command(
            ':ARM:DIR?',
            ':ARM:DIR',
            Mapping({'source': 'SOUR', 'acceptor': 'ACC'})
        )
        self.input_line = Command(
            ':ARM:ILIN?',
            ':ARM:ILIN',
            Integer(min=1, max=7)
        )
        self.output_line = Command(
            ':ARM:OLIN?',
            ':ARM:OLIN',
            Integer(min=1, max=7)
        )
        self.output = Command(
            ':ARM:OUTP?',
            ':ARM:OUTP',
            Mapping({'tenter': 'TENT', 'texit': 'TEX', None: 'NONE'})
        )

    def signal(self):
        """Bypass the arm control source."""
        self._write(':ARM:SIGN')


class Trigger(InstrumentBase):
    """The trigger command subsystem.

    :ivar source: The event detector. Valid are 'immediate' or 'tlink'.
    :ivar source_bypass: The trigger source bypass. Valid entries are 'source' or
        'acceptor'.
    :ivar int input_line: The trigger input signal line, in the range [1, 6].
    :ivar int output_line: The trigger output signal line, in the range [1, 6].
    :ivar output: The output trigger. Valid are 'source', 'delay' and `None`.

    """
    def __init__(self, connection, cfg):
        super(Trigger, self).__init__(connection, cfg)
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
            Integer(min=1, max=7)
        )
        self.output_line = Command(
            ':TRIG:OLIN?',
            ':TRIG:OLIN',
            Integer(min=1, max=7)
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
class Units(InstrumentBase):
    """The units command subsystem.

    :ivar voltage: The units voltage subsystem, an instance of :class:`~.UnitVoltage`
    :ivar power: The units power subsystem, an instance of :class:`~.UnitPower`

    """
    def __init__(self, connection, cfg):
        super(Units, self).__init__(connection, cfg)
        self.voltage = UnitVoltage(self.connection, self._cfg)
        self.power = UnitPower(self.connection, self._cfg)


class UnitVoltage(InstrumentBase):
    """The voltage command subgroup of the Units node.

    :ivar dc: The voltage reading units, valid are 'V', 'Ohm', 'W', 'Siemens'.

    """
    def __init__(self, connection, cfg):
        super(UnitVoltage, self).__init__(connection, cfg)
        self.dc = Command(
            ':UNIT:VOLT?',
            ':UNIT:VOLT',
            Mapping({'V': 'V', 'Ohm': 'OHM', 'W': 'W', 'Siemens': 'SIEM'})
        )


class UnitPower(InstrumentBase):
    """The power command subgroup of the Units node.

    :ivar type: The power reading units in the pulse delta mode, valid are
        'peak' and 'average'.

    """
    def __init__(self, connection, cfg):
        super(UnitPower, self).__init__(connection, cfg)
        self.type = Command(
            ':UNIT:POW?',
            ':UNIT:POW',
            Mapping({'peak': 'PEAK', 'average': 'AVER'})
        )
