#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase, CommandSequence
from slave.types import Enum, Float, Integer


class SR850(InstrumentBase):
    """A Stanford Research SR850 lock-in amplifier.

    :param connection: A connection object.

    .. rubric:: Reference and Phase Commands

    :ivar phase: The reference phase shift. A float between -360. and
        719.999 in degree.
    :ivar reference_mode: The reference source mode, either 'internal', 'sweep'
        or 'external'.
    :ivar frequency: The reference frequency in Hz. A float between 0.001 and
        102000.

        .. note::

            For harmonics greater than 1, the sr850 limits the max frequency to
            102kHz / harmonic.

    :ivar frequency_sweep: The type of the frequency sweep, either 'linear' or
        'log', when in 'internal' reference_mode.

    :ivar start_frequency: The start frequency of the internal frequency sweep
        mode. A float in the range 0.001 to 102000.
    :ivar stop_frequency: The stop frequency of the internal frequency sweep
        mode. A float in the range 0.001 to 102000.
    :ivar reference_slope: The reference slope in the external mode. Valid are:

        =========  ==================
        'sine'     sine zero crossing
        'rising'   TTL rising edge
        'falling'  TTL falling edge
        =========  ==================

    :ivar harmonic: The detection harmonic, an integer between 1 and 32767.
    :ivar amplitude: The amplitude of the sine output in volts. Valid entries
        are floats in the range 0.004 to 5.0 with a resolution of 0.002.

    .. rubric:: Reference and Phase Commands

    :ivar input: The input configuration, either 'A', 'A-B' or 'I'.
    :ivar input_gain: The conversion gain of the current input. Valid are
        '1 MOhm' and '100 MOhm'.
    :ivar ground: The input grounding, either 'float' or 'ground'.
    :ivar coupling: The input coupling, either 'AC' or 'DC'.
    :ivar filter: The input line filter configuration. Valid are 'unfiltered',
        'notch', '2xnotch' and 'both'.
    :ivar sensitivity: The input sensitivity in volt or microamps. Valid are
        2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6,
        5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3,
        10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, and 1.
    :ivar reserve_mode: The reserve mode configuration. Valid entries are
        'max', 'manual' and 'min'.
    :ivar reserve: The dynamic reserve. An Integer between 0 and 5 where 0 is
        the minimal reserve available.
    :ivar time_constant: The time constant in seconds. Valid are 10e-6, 30e-6,
        100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3, 1., 3., 10,
        30, 100, 300, 1e3, 3e3, 10e3, and 30e3.
    :ivar filter_slope: The lowpass filter slope in db/oct. Valid are 6, 12, 18
        and 24.
    :ivar sync_filter: The state of the syncronous filtering, either True or
        False.

        .. note::

            Syncronous filtering is only vailable if the detection frequency is
            below 200Hz

    .. rubric:: Output and Offset Commands

    :ivar ch1_display: The channel 1 frontpanel output source. Valid are 'x',
        'r', 'theta', 'trace1', 'trace2', 'trace3' and 'trace4'.
    :ivar ch2_display: The channel 2 frontpanel output source. Valid are 'y',
        'r', 'theta', 'trace1', 'trace2', 'trace3' and 'trace4'.
    :ivar x_offset_and_expand: The output offset and expand of the x quantity.
        A tuple (<offset>, <expand>), where

         * <offset> the offset in percent, in the range -105.0 to 105.0.
         * <expand> the expand in the range 1 to 256.

    :ivar y_offset_and_expand: The output offset and expand of the y quantity.
        A tuple (<offset>, <expand>), where

         * <offset> the offset in percent, in the range -105.0 to 105.0.
         * <expand> the expand in the range 1 to 256.

    :ivar r_offset_and_expand: The output offset and expand of the r quantity.
        A tuple (<offset>, <expand>), where

         * <offset> the offset in percent, in the range -105.0 to 105.0.
         * <expand> the expand in the range 1 to 256.

    .. rubric:: Trace and Scan Commands

    :ivar traces: A sequence of four traces represented by the following tuple
        *(<a>, <b>, <c>, <store>)* where 

        * *<a>, <b>, <c>* define the trace which is calculated as 
          *<a> * <b> / <c>*. Each one of them is one of the following
          quantities '1', 'x', 'y', 'r', 'theta', 'xn', 'yn', 'rn', 'Al1',
          'Al2', 'Al3', 'Al4', 'F', 'x**2', 'y**2', 'r**2', 'theta**2',
          'xn**2', 'yn**2', 'rn**2', 'Al1**2', 'Al2**2', 'Al3**2', 'Al4**2' or
          'F**2'
        * *<store>* is a boolean defining if the trace is stored.

    :ivar scan_sample_rate: The scan sample rate, valid are 62.5e-3, 125e-3,
        250e-3, 500e-3, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 in Hz or
        'trigger'.

    :ivar scan_length: The scan length in seconds. It well be set to the
        closest possible time. The minimal scan time is 1.0 seconds. The
        maximal scan time is determined by the scanning sample rate and the
        number of stored traces.

        ======  ===========
        Traces  Buffer Size
        ======  ===========
        1       64000
        2       32000
        3       48000
        4       16000
        ======  ===========

    :ivar scan_mode: The scan mode, valid are 'shot' or 'loop'.

    .. rubric:: Display and Scale Commands

    :ivar active_display: Selects the active display. Valid are 'full', 'top'
        or 'bottom'.
    :ivar screen_format: Selects the screen format. Valid are

        * 'single', The complete screen is used.
        * 'dual', A up/down split view is used.

    :ivar monitor_display: The monitor display mode, valid are 'settings' and
        'input/output'.
    :ivar full_display: An instance of :class:`~.Display`, representing the
        full display.
    :ivar top_display: An instance of :class:`~.Display`, representing the
        top display.
    :ivar bottom_display: An instance of :class:`~.Display`, representing the
        bottom display.

    """
    def __init__(self, connection):
        super(SR850, self).__init__(connection)
        # Reference and Phase Commands
        self.phase = Command('PHAS?', 'PHAS', Float(min=-360., max=719.999)
        )
        self.reference_mode = Command(
            'FMOD?',
            'FMOD',
            Enum('internal', 'sweep', 'external')
        )
        self.frequency = Command('FREQ?', 'FREQ', Float(min=0.001, max=102000))
        self.frequency_sweep = Command('SWPT?', 'SWPT', Enum('linear', 'log'))
        self.start_frequency = Command(
            'SLLM?',
            'SLLM',
            Float(min=0.001, max=102000)
        )
        self.stop_frequency = Command(
            'SULM?',
            'SULM',
            Float(min=0.001, max=102000)
        )
        self.reference_slope = Command(
            'RSLP?',
            'RSLP',
            Enum('sine', 'rising', 'falling')
        )
        self.harmonic = Command(
            'HARM?',
            'HARM',
            Integer(min=1, max=32767)
        )
        self.amplitude = Command(
            'SLVL?',
            'SLVL',
            Float(min=0.002, max=5.0)
        )
        # Input and Filter Commands
        self.input = Command('ISRC?', 'ISRC', Enum('A', 'A-B', 'I'))
        self.input_gain = Command('IGAN?', 'IGAN', Enum('1 MOhm', '100 MOhm'))
        self.ground = Command('IGND?', 'IGND', Enum('float', 'ground'))
        self.coupling = Command('ICPL?', 'ICPL', Enum('AC', 'DC'))
        self.filter = Command(
            'ILIN?',
            'ILIN',
            Enum('unfiltered', 'notch', '2xnotch', 'both')
        )
        # Gain and Timeconstant Commands
        self.sensitivity = Command(
            'SENS?',
            'SENS',
            Enum(2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6,
                 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3,
                 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1)
        )
        self.reserve_mode = Command(
            'RMOD?',
            'RMOD',
            Enum('max', 'manual', 'min')
        )
        self.reserve = Command('RSRV?', 'RSRV', Integer(min=0, max=5))
        self.time_constant = Command(
            'OFLT?',
            'OFLT',
            Enum(10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3,
                 300e-3, 1., 3., 10, 30, 100, 300, 1e3, 3e3, 10e3, 30e3)
        )
        self.filter_slope = Command('OFSL?', 'OFSL', Enum(6, 12, 18, 24))
        self.syncronous_filtering = Command('SYNC?', 'SYNC', Boolean)
        # Output and Offset Commands
        self.ch1_display = Command(
            'FOUT? 1',
            'FOUT 1,',
            Enum('x', 'r', 'theta', 'trace1', 'trace2', 'trace3', 'trace4')
        )
        self.ch2_display = Command(
            'FOUT? 2',
            'FOUT 2,',
            Enum('y', 'r', 'theta', 'trace1', 'trace2', 'trace3', 'trace4')
        )
        self.x_offset_and_expand = Command(
            'OEXP? 1',
            'OEXP 1,',
            (Float(min=-105., max=105.), Integer(min=1, max=256))
        )
        self.y_offset_and_expand = Command(
            'OEXP? 2',
            'OEXP 2,',
            (Float(min=-105., max=105.), Integer(min=1, max=256))
        )
        self.r_offset_and_expand = Command(
            'OEXP? 3',
            'OEXP 3,',
            (Float(min=-105., max=105.), Integer(min=1, max=256))
        )
        # Trace and Scan Commands
        traces = []
        quantities = Enum(
            '1', 'x', 'y', 'r', 'theta', 'xn', 'yn', 'rn', 'Al1', 'Al2', 'Al3',
            'Al4', 'F', 'x**2', 'y**2', 'r**2', 'theta**2', 'xn**2', 'yn**2',
            'rn**2', 'Al1**2', 'Al2**2', 'Al3**2', 'Al4**2', 'F**2')
        for i in range(1, 5):
            cmd = Command(
                'TRCD? {0}'.format(i),
                'TRCD {0},'.format(i),
                (quantities, quantities, quantities, Boolean)
            )
            traces.append(cmd)
        self.traces = CommandSequence(traces)
        self.scan_sample_rate = Command(
            'SRAT?',
            'SRAT',
            Enum(62.5e-3, 125e-3, 250e-3, 500e-3, 1, 2, 4,
                 8, 16, 32, 64, 128, 256, 512, 'trigger')
        )
        self.scan_length = Command('SLEN?', 'SLEN', Float(min=1))
        self.scan_mode = Command('SEND?', 'SEND', Enum('shot', 'loop'))
        # Display and Scale Commands
        # TODO: ADSP, SMOD, MNTR, DTYP, DTRC, DSCL, DOFF
        self.active_display = Command(
            'ADSP?',
            'ADSP',
            Enum('full', 'top', 'bottom')
        )
        self.screen_format = Command(
            'SMOD?',
            'SMOD',
            Enum('single', 'dual')
        )
        self.monitor_display = Command(
            'MNTR?',
            'MNTR',
            Enum('settings', 'input/output')
        )
        self.full_display = Display(0, self.connection, self._cfg)
        self.top_display = Display(1, self.connection, self._cfg)
        self.bottom_display = Display(2, self.connection, self._cfg)
        # Cursor Commands
        # TODO: CSEK, CWID, CDIV, CLNK, CDSP, CMAX, CURS, CBIN,

        # Mark Commands


    def auto_offset(quantity):
        """Automatically offsets the given quantity.

        :param quantity: The quantity to offset, either 'x', 'y' or 'r'

        """
        self._write(('AOFF', Enum('x', 'y', 'r', start=1), quantity))

    def auto_scale(self):
        """Autoscales the active display.

        .. note:: Just Bar and Chart displays are affected.

        """
        self._write('ASCL')


class Display(InstrumentBase):
    """Represents a SR850 display.

    .. note::

        The SR850 will generate an error if one tries to set a parameter of an
        invisible display.

    :ivar type: The display type, either 'polar', 'blank', 'bar' or 'chart'.

    :ivar trace: The trace number of the displayed trace.
    :ivar range: The displayed range, a float between 10^-18 and 10^18.

        .. note:: Only bar and chart displays are affected.

    :ivar offset: The display center value in units of the trace in the range
        10^-12 to 10^12.

    :ivar horizontal_scale: The display's horizontal scale. Valid are '2 ms',
        '5 ms', '10 ms', '20 ms', '50 ms', '0.1 s', '0.2 s', '0.5 s', '1 s',
        '2 s', '5 s', '10 s', '20 s', '50 s', '1 min', '100 s', '2 min',
        '200 s', '5 min', '500 s', '10 min', '1 ks', '20 min', '2 ks', '1 h',
        '10 ks', '3 h', '20 ks', '50 ks', '100 ks' and '200 ks'.

    :ivar bin: The bin number at the right edge of the chart display.
        (read only)

        .. note:: The selected display must be a chart display.

    """
    def __init__(self, idx, connection, cfg):
        super(Display, self).__init__(connection, cfg)
        idx = int(idx)
        self.type = Command(
            'DTYP? {0}'.format(idx),
            'DTYP {0},'.format(idx),
            Enum('polar', 'blank', 'bar', 'chart')
        )
        self.trace = Command(
            'DTRC? {0}'.format(idx),
            'DTRC {0},'.format(idx),
            Integer(min=1, max=4)
        )
        self.range = Command(
            'DSCL? {0}'.format(idx),
            'DSCL {0},'.format(idx),
            Float(min=1e-18, max=1e18)
        )
        self.offset = Command(
            'DOFF? {0}'.format(idx),
            'DOFF {0},'.format(idx),
            Float(min=1e-12, max=1e12)
        )
        self.horizontal_scale = Command(
            'DHZS? {0}'.format(idx),
            'DHZS {0},'.format(idx),
            Enum('2 ms', '5 ms', '10 ms', '20 ms', '50 ms', '0.1 s', '0.2 s',
                 '0.5 s', '1 s', '2 s', '5 s', '10 s', '20 s', '50 s', '1 min',
                 '100 s', '2 min', '200 s', '5 min', '500 s', '10 min', '1 ks',
                 '20 min', '2 ks', '1 h', '10 ks', '3 h', '20 ks', '50 ks',
                 '100 ks', '200 ks')
        )
        self.bin = Command(('RBIN ? {0}'.format(idx), Integer))
