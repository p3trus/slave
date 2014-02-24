#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase, CommandSequence
from slave.types import Boolean, Enum, Float, Integer, Register, String
from slave.iec60488 import IEC60488, PowerOn


class SR850(IEC60488, PowerOn):
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

    :ivar traces: A sequence of four :class:`~.Trace` instances.
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

    :ivar active_display: Sets the active display. Valid are 'full', 'top'
        or 'bottom'.
    :ivar selected_display: Selects the active display, either 'top' or
        'bottom'. If the active display 'full' it is already selected.
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

    .. rubric:: Cursor Commands

    :ivar cursor: The cursor of the active display, an instance of
        :class:`~.Cursor`.

    .. rubric:: Aux Input and Output Commands

    :ivar aux_input: A sequence of four read only items representing the aux
        inputs in volts.
    :ivar aux_input: A sequence of four :class:`~.Output` instances,
        representing the analog outputs.
    :ivar bool start_on_trigger: If start on trigger is True, a trigger signal will
        start the scan.

    .. rubric: Mark Commands

    :ivar marks: An instance of :class:`~.MarkList`, a sequence like structure
        giving access to the SR850 marks.

    .. rubric:: Math Commands

    :ivar math_operation: Sets the math operation used by the
        :meth:`~.SR850.calculate operation. Valid are '+', '-', '*', '/',
        'sin', 'cos', 'tan', 'sqrt', '^2', 'log' and '10^x'.
    :ivar math_argument_type: The argument type used in the :meth:`calculate`
        method, either 'trace' or 'constant'.
    :ivar float math_constant: Specifies the constant value used by the
        :meth:`~.SR850.calculate` operation if the
        :attr:`~.SR850.math_argument_type` is set to 'constant'.
    :ivar math_trace_argument: Specifies the trace number used by the
        :meth:`~.SR850.calculate` operation if the
        :attr:`~.SR850.math_argument_type` is set to 'trace'.

    :ivar fit_function: The function used to fit the data, either 'linear',
        'exp' or 'gauss'.
    :ivar fit_params: An instance of :class:`~.FitParameter` used to access the
        fit parameters.
    :ivar statistics: An instance of :class:`~.Statistics` used to access the
        results of the statistics calculation.

    .. rubric:: Store and Recall File Commands

    :ivar filename: The active filename.

        .. warning::

            The SR850 supports filenames with up to eight characters and an
            optional extension with up to three characters. The filename
            must be in the DOS format. Slave does not validate this yet.

    .. rubric:: Setup Commands

    :ivar interface: The communication interface in use, either 'rs232' or
        'gpib'.
    :ivar bool overide_remote: The gpib remote overide mode.
    :ivar bool key_click: Enables/disables the key click.
    :ivar bool alarm: Enables/disables the alarm.
    :ivar int hours: The hours of the internal clock. An integer in the range
        0 - 23.
    :ivar int minutes: The minutes of the internal clock. An integer in the
        range 0 - 59.
    :ivar int seconds: The seconds of the internal clock. An integer in the
        range 0 - 59.
    :ivar int days: The days of the internal clock. An integer in the range
        1 - 31.
    :ivar int month: The month of the internal clock. An integer in the range
        1 - 12.
    :ivar int years: The year of the internal clock. An integer in the range
        0 - 99.
    :ivar plotter_mode: The plotter mode, either 'rs232' or 'gpib'.
    :ivar plotter_baud_rate: The rs232 plotter baud rate.
    :ivar plotter_address: The gpib plotter address, an integer between 0 and
        30.
    :ivar plotting_speed: The plotting speed mode, either 'fast' or 'slow'.
    :ivar int trace_pen_number: The trace pen number in the range 1 to 6.
    :ivar int grid_pen_number: The grid pen number in the range 1 to 6.
    :ivar int alphanumeric_pen_number: The alphanumeric pen number in the range
        1 to 6.
    :ivar int cursor_pen_number: The cursor pen number in the range 1 to 6.
    :ivar printer: The printer type. Valid are 'epson', 'hp' and 'file'.

    .. rubric:: Data Transfer Commands

    :ivar float x: The in-phase signal in volt (read only).
    :ivar float y: The out-of-phase signal in volt (read only).
    :ivar float r: The amplitude signal in volt (read only).
    :ivar float theta: The in-phase signal in degree (read only).
    :ivar fast_mode: The fast mode. When enabled, data is automatically
        transmitted over the gpib interface. Valid are 'off', 'dos' or
        'windows'.

    .. note:: Use :meth:`SR850.start` with `delay=True` to start the scan.

    .. warning::

        When enabled, the user is responsible for reading the transmitted
        values himself.

    .. rubric:: Interface Commands

    :ivar access: The frontpanel access mode.

        =========  =========================================================
        Value      Description
        =========  =========================================================
        'local'    Frontpanel operation is allowed.
        'remote'   Frontpanel operation is locked out except the *HELP* key.
                   It returns the lock-in into the local state.
        'lockout'  All frontpanel operation is locked out.
        =========  =========================================================

    .. rubric:: Status Reporting Commands

    :ivar status: The status byte register, a dictionary with the following
        entries

        ===  =====================================================
        Key  Description
        ===  =====================================================
        SCN  No scan in progress.
        IFC  No command execution in progress.
        ERR  An enabled bit in the error status byte has been set.
        LIA  An enabled bit in the LIA status byte has been set.
        MAV  The message available byte.
        ESB  An enabled bit in the event status byte has been set.
        SRQ  A service request has occured.
        ===  =====================================================

    :ivar event_status: The event status register, a dictionairy with the
        following keys:

        =====  =====================================
        Key    Description
        =====  =====================================
        'INP'  An input queue overflow occured.
        'QRY'  An output queue overflow occured.
        'EXE'  A command execution error occured.
        'CMD'  Received an illegal command.
        'URQ'  A key press or knob rotation occured.
        'PON'  Set by power on.
        =====  =====================================

        If any bit is `True` and enabled, the 'ESB' bit in the
        :attr:`~.SR850.status` is set to `True`.

    :ivar event_status_enable: The event status enable register. It has the same
        keys as :attr:`.SR850.event_status`.

    :ivar error_status: The event status register, a dictionairy with the
        following keys

        ==================  ==================================
        Key                 Description
        ==================  ==================================
        'print/plot error'  A printing/plotting error occured.
        'backup error'      Battery backup failed.
        'ram error'         Ram memory test failed.
        'disk error'        A disk or file operation failed.
        'rom error'         Rom memory test failed.
        'gpib error'        GPIb fast data transfer aborted.
        'dsp error'         DSP test failed.
        'math error'        Internal math error occured.
        ==================  ==================================

        If any bit is `True` and enabled, the 'ERR' bit in the
        :attr:`~.SR850.status` is set to `True`.

    :ivar error_status_enable: The error status enable register. It has the same
        keys as :attr:`.SR850.error_status`.

    :ivar lia_status: The LIA status register, a dictionairy with the following
        keys

        =======================  ============================================
        Key                      Description
        =======================  ============================================
        'input overload'         An input or reserve overload occured.
        'filter overload'        A filter overload occured.
        'output overload'        A output overload occured.
        'reference unlock'       A reference unlock is detected.
        'detection freq change'  The detection frequency changed its range.
        'time constant change'   The time constant changed indirectly, either
                                 by changing the frequency range, dynamic
                                 reserve or filter slope.
        'triggered'              A trigger event occured.
        'plot'                   Completed a plot.
        =======================  ============================================


    """
    def __init__(self, connection):
        stb = {
            0: 'SCN',
            1: 'IFC',
            2: 'ERR',
            3: 'LIA',
            4: 'MAV',
            5: 'ESB',
            6: 'SRQ',
            7: '7'
        }
        esb = {
            0: 'INP',
            1: '1',
            2: 'QRY',
            3: '3',
            4: 'EXE',
            5: 'CMD',
            6: 'URQ',
            7: 'PON',
        }
        err = {
            0: 'print/plot error',
            1: 'backup error',
            2: 'ram error',
            3: 'disk error',
            4: 'rom error',
            5: 'gpib error',
            6: 'dsp error',
        }
        lia = {
            0: 'input overload',
            1: 'filter overload',
            2: 'output overload',
            3: 'reference unlock',
            4: 'detection freq change',
            5: 'time constant change',
            6: 'triggered',
            7: 'plot',
        }
        super(SR850, self).__init__(connection, stb=stb, esb=esb)
        # Status Reporting Commands
        def _invert(x):
            """Returns a dict, where keys and values are switched."""
            return dict((v, k) for k, v in x.iteritems())

        self.lia_status = Command(('LIAS?', Register(_invert(lia))))
        self.lia_status_enable = Command(
            'LIAE?',
            'LIAE',
            Register(_invert(lia))
        )
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
        self.traces = [
            Trace(i, self.connection, self._cfg) for i in range(1, 5)
        ]
        self.scan_sample_rate = Command(
            'SRAT?',
            'SRAT',
            Enum(62.5e-3, 125e-3, 250e-3, 500e-3, 1, 2, 4,
                 8, 16, 32, 64, 128, 256, 512, 'trigger')
        )
        self.scan_length = Command('SLEN?', 'SLEN', Float(min=1))
        self.scan_mode = Command('SEND?', 'SEND', Enum('shot', 'loop'))
        # Display and Scale Commands
        # XXX Not shure about the difference between ADSP and ATRC command.
        self.active_display = Command(
            'ADSP?',
            'ADSP',
            Enum('full', 'top', 'bottom')
        )
        self.selected_display = Command('ATRC?', 'ATRC', Enum('top', 'bottom'))
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
        self.cursor = Cursor(self.connection, self._cfg)
        # Mark Commands
        self.marks = MarkList(self.connection, self._cfg)
        # Aux Input and Output Comnmands
        def aux_in(i):
            """Helper function to create an aux input command."""
            return Command(query=('OAUX? {0}'.format(i), Float),
                           connection=self.connection,
                           cfg=self._cfg)

        self.aux_input = CommandSequence(aux_in(i) for i in xrange(1, 5))
        self.aux_output = tuple(
            Output(i, self.connection, self._cfg) for i in xrange(1, 5)
        )
        self.start_on_trigger = Command('TSTR?', 'TSTR', Boolean)
        # Math Commands
        self.math_argument_type = Command(
            'CAGT?',
            'CAGT',
            Enum('trace', 'constant')
        )
        self.math_operation = Command(
            'COPR?',
            'COPR',
            Enum('+', '-', '*', '/', 'sin', 'cos',
                 'tan', 'sqrt', '^2', 'log', '10^x')
        )
        self.math_constant = Command('CARG?', 'CARG', Float)
        self.math_trace_argument = Command(
            'CTRC?',
            'CTRC',
            Integer(min=1, max=4)
        )
        self.fit_function = Command(
            'FTYP?',
            'FTYP',
            Enum('line', 'exp', 'gauss')
        )
        self.fit_params = FitParameters(self.connection, self._cfg)
        self.statistics = Statistics(self.connection, self._cfg)
        # Store and Recall File Commands
        # TODO The filename syntax is not validated yet.
        self.filename = Command('FNAM?', 'FNAM', String(max=12))

        # Setup Commands
        self.interface = Command('OUTX?', 'OUTX', Enum('rs232', 'gpib'))
        self.overwrite_remote = Command('OVRM?', 'OVRM', Boolean)
        self.key_click = Command('KCLK?', 'KCLK', Boolean)
        self.alarm = Command('ALRM?', 'ALRM', Boolean)
        # TODO wrapp datetime commands with higher level interface.
        self.hours = Command('THRS?', 'THRS', Integer(min=0, max=23))
        self.minutes = Command('TMIN?', 'TMIN', Integer(min=0, max=59))
        self.seconds = Command('TSEC?', 'TSEC', Integer(min=0, max=59))
        self.month = Command('DMTH?', 'DMTH', Integer(min=1, max=12))
        self.day = Command('DDAY?', 'DDAY', Integer(min=1, max=31))
        self.year = Command('DYRS?', 'DYRS', Integer(min=0, max=99))
        self.plotter_mode = Command('PLTM?', 'PLTM', Enum('rs232', 'gpib'))
        self.plotter_baud_rate = Command(
            'PLTB?',
            'PLTB',
            Enum(300, 1200, 2400, 4800, 9600)
        )
        self.plotter_address = Command(
            'PLTA?',
            'PLTA',
            Integer(min=0, max=30)
        )
        self.plotting_speed = Command('PLTS?', 'PLTS', Enum('fast', 'slow'))
        self.trace_pen_number = Command('PNTR?', 'PNTR', Integer(min=1, max=6))
        self.grid_pen_number = Command('PNGD?', 'PNGD', Integer(min=1, max=6))
        self.alphanumeric_pen_number = Command(
            'PNAL?',
            'PNAL',
            Integer(min=1, max=6)
        )
        self.cursor_pen_number = Command(
            'PNCR?',
            'PNCR',
            Integer(min=1, max=6)
        )
        self.printer = Command('PRNT?', 'PRNT', Enum('epson', 'hp', 'file'))
        # Front Panel Controls and Auto Functions.
        # TODO ATRC.

        # Data Transfer Commands
        self.x = Command(('OUTP? 1', Float))
        self.y = Command(('OUTP? 2', Float))
        self.r = Command(('OUTP? 3', Float))
        self.theta = Command(('OUTP? 4', Float))
        self.fast_mode = Command(
            'FAST?',
            'FAST',
            Enum('off', 'dos', 'windows')
        )
        # Interface Commands
        self.access = Command(
            'LOCL?',
            'LOCL',
            Enum('local', 'remote', 'lockout')
        )

    def auto_gain(self):
        """Performs a auto gain action."""
        self._write('AGAN')

    def auto_phase(self):
        """Automatically selects the best matching phase."""
        self._write('APHS')

    def auto_offset(quantity):
        """Automatically offsets the given quantity.

        :param quantity: The quantity to offset, either 'x', 'y' or 'r'

        """
        self._write(('AOFF', Enum('x', 'y', 'r', start=1), quantity))

    def auto_reserve(self):
        """Automatically selects the best dynamic reserve."""
        self._write('ARSV')

    def auto_scale(self):
        """Autoscales the active display.

        .. note:: Just Bar and Chart displays are affected.

        """
        self._write('ASCL')

    def place_mark(self):
        """Places a mark in the data buffer at the next sample.

        .. note:: This has no effect if no scan is running.

        """
        self._write('MARK')

    def delete_mark(self):
        """Deletes the nearest mark to the left."""
        self._write('MDEL')

    def print_screen(self):
        """Prints the screen display with an attached printer."""
        self._write('PRSC')

    def plot_all(self):
        """Generates a plot of all data displays."""
        self._write('PALL')

    def plot_trace(self):
        """Generates a plot of the data trace."""
        self._write('PTRC')

    def plot_cursors(self):
        """Generates a plot of the enabled cursors."""
        self._write('PCUR')

    def start(self, delay=False):
        """Starts or resumes a scan.

        :param bool delay: If `True`, starts the scan with a delay of 0.5
            seconds.

        .. note:: It has no effect if the scan is already running.

        """
        if delay:
            self._write('STRD')
        else:
            self._write('STRT')

    def pause(self):
        """Pauses a scan and all sweeps in progress."""
        self._write('PAUS')

    def reset_scan(self):
        """Resets a scan.

        .. warning:: This will erase the data buffer.

        """
        self._write('REST')

    def snap(self, *args):
        """Records multiple values at once.

        It takes two to six arguments specifying which values should be
        recorded together. Valid arguments are 'x', 'y', 'r', 'theta',
        'aux1', 'aux2', 'aux3', 'aux4', 'frequency', 'trace1', 'trace2',
        'trace3' and 'trace4'.

        snap is faster since it avoids communication overhead. 'x' and 'y'
        are recorded together, as well as 'r' and 'theta'. Between these
        pairs, there is a delay of approximately 10 us. 'aux1', 'aux2', 'aux3'
        and 'aux4' have am uncertainty of up to 32 us. It takes at least 40 ms
        or a period to calculate the frequency.

        E.g.::

            lockin.snap('x', 'theta', 'trace3')

        """
        length = len(args)
        if not 2 <= length <= 6:
            msg = 'snap takes 2 to 6 arguments, {0} given.'.format(length)
            raise TypeError(msg)
        # The program data type.
        param = Enum(
            'x', 'y', 'r', 'theta', 'aux1', 'aux2', 'aux3', 'aux4',
            'frequency', 'trace1', 'trace2', 'trace3', 'trace4'
        )
        # construct command,
        cmd = 'SNAP?', (Float,) * length, (param, ) * length
        return self._ask(cmd, *args)

    def save(self, mode='all'):
        """Saves to the file specified by :attr:`~SR850.filename`.

        :param mode: Defines what to save.

            =======  ================================================
            Value    Description
            =======  ================================================
            'all'    Saves the active display's data trace, the trace
                     definition and the instrument state.
            'data'   Saves the active display's data trace.
            'state'  Saves the instrument state.
            =======  ================================================

        """
        if mode == 'all':
            self._write('SDAT')
        elif mode == 'data':
            self._write('SASC')
        elif mode=='state':
            self._write('SSET')
        else:
            raise ValueError('Invalid save mode.')

    def recall(self, mode='all'):
        """Recalls from the file specified by :attr:`~SR850.filename`.

        :param mode: Specifies the recall mode.

            =======  ==================================================
            Value    Description
            =======  ==================================================
            'all'    Recalls the active display's data trace, the trace
                     definition and the instrument state.
            'state'  Recalls the instrument state.
            =======  ==================================================

        """
        if mode == 'all':
            self._write('RDAT')
        elif mode == 'state':
            self._write('RSET')
        else:
            raise ValueError('Invalid recall mode.')

    def smooth(self, window):
        """Smooths the active display's data trace within the time window of
        the active chart display.

        :param window: The smoothing window in points. Valid are 5, 11, 17, 21
            and 25.

        .. note::

            Smoothing takes some time. Check the status byte to see when the
            operation is done. A running scan will be paused until the
            smoothing is complete.

        .. warning::

            The SR850 will generate an error if the active display trace is not
            stored when the smooth command is executed.

        """
        self._write(('SMTH', Enum(5, 11, 17, 21, 25)), window)

    def fit(self, range, function=None):
        """Fits a function to the active display's data trace within a
        specified range of the time window.

        E.g.::

            # Fit's a gaussian to the first 30% of the time window.
            lockin.fit(range=(0, 30), function='gauss')

        :param start: The left limit of the time window in percent.
        :param stop: The right limit of the time window in percent.
        :param function: The function used to fit the data, either 'line',
            'exp', 'gauss' or None, the default. The configured fit function is
            left unchanged if function is None.

        .. note::

            Fitting takes some time. Check the status byte to see when the
            operation is done. A running scan will be paused until the
            fitting is complete.

        .. warning::

            The SR850 will generate an error if the active display trace is not
            stored when the fit command is executed.

        """
        if function is not None:
            self.fit_function = function
        cmd = 'FITT', Integer(min=0, max=100), Integer(min=0, max=100)
        self._write(cmd, start, stop)

    def calculate_statistics(self, start, stop):
        """Starts the statistics calculation.

        :param start: The left limit of the time window in percent.
        :param stop: The right limit of the time window in percent.

        .. note::

            The calculation takes some time. Check the status byte to see when
            the operation is done. A running scan will be paused until the
            operation is complete.

        .. warning::

            The SR850 will generate an error if the active display trace is not
            stored when the command is executed.

        """
        cmd = 'STAT', Integer, Integer
        self._write(cmd, start, stop)

    def calculate(self, operation=None, trace=None, constant=None, type=None):
        """Starts the calculation.

        The calculation operates on the trace graphed in the active display.
        The math operation is defined by the :attr:`~.SR850.math_operation`,
        the second argument by the :attr:`~.SR850.math_argument_type`.

        For convenience, the operation and the second argument, can be
        specified via the parameters

        :param operation: Set's the math operation if not `None`. See
            :attr:`~.SR850.math_operation` for details.
        :param trace: If the trace argument is used, it sets the
            :attr:`~.math_trace_argument' to it and sets the
            :attr:`~.math_argument_type`to 'trace'
        :param constant: If constant is not `None`, the
            :attr:`~.math_constant`is set with this value and the
            :attr:`~.math_argument_type` is set to 'constant'
        :param type: If type is not `None`, the :attr:`~.math_argument_type` is
            set to this value.

        E.g. instead of::

            lockin.math_operation = '*'
            lockin.math_argument_type = 'constant'
            lockin.math_constant = 1.337
            lockin.calculate()

        one can write::

            lockin.calculate(operation='*', constant=1.337)

        .. note:: Do not use trace, constant and type together.

        .. note::

            The calculation takes some time. Check the status byte to see when
            the operation is done. A running scan will be paused until the
            operation is complete.

        .. warning::

            The SR850 will generate an error if the active display trace is not
            stored when the command is executed.

        """
        if operation is not None:
            self.math_operation = operation
        if trace is not None:
            self.math_trace_argument = trace
            type = 'trace'
        elif constant is not None:
            self.math_constant = constant
            type = 'constant'
        if type is not None:
            self.math_argument_type = type
        self._write('CALC')


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
    :ivar cursor: The cursor position of this display (read only), represented
        by the tuple *(<horizontal>, <vertical>)*, where

        * *<horizontal>* is the horizontal position in bin, delay, time or
          sweep frequency.
        * *<vertical>* is the vertical position.

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
        self.cursor = Command(('CURS? {0}'.format(idx), (Float, Float)))


class Cursor(InstrumentBase):
    """Represents the SR850 cursor of the active display.

    .. note::

        The cursor commands are only effective if the active display is a chart
        display.

    :ivar seek_mode: The cursor seek mode, valid are 'max', 'min' and 'mean'.
    :ivar width: The cursor width, valid are 'off', 'narrow', 'wide' and
        'spot'.
    :ivar vertical_division: The vertical division of the active display. Valid
        are 8, 10 or `None`.
    :ivar control_mode: The cursor control mode. Valid are 'linked',
        'separate'.
    :ivar readout_mode: The cursor readout mode. Valid are 'delay', 'bin',
        'fsweep' and 'time'.
    :ivar bin: The cursor bin position of the active display. It represents the
        center of the cursor region. This is not the same as the cursor readout
        position. To get the actual cursor location, use :attr:`Display.cursor`.

    """
    def __init__(self, connection, cfg):
        super(Cursor, self).__init__(connection, cfg)
        self.seek_mode = Command('CSEK?', 'CSEK', Enum('max', 'min', 'mean'))
        self.width = Command(
            'CWID?',
            'CWID',
            Enum('off', 'narrow', 'wide', 'spot')
        )
        self.vertical_division = Command(
            'CDIV?',
            'CDIV',
            Enum(8, 10, None)
        )
        self.control_mode = Command(
            'CLNK?',
            'CLNK',
            Enum('linked', 'separate')
        )
        self.readout_mode = Command(
            'CDSP?',
            'CDSP',
            Enum('delay', 'bin', 'fsweep', 'time')
        )
        self.bin = Command(
            'CBIN?',
            'CBIN',
            Integer
        )

    def move(self):
        """Moves the cursor to the max or min position of the data, depending
        on the seek mode.
        """
        self._write('CMAX')

    def next_mark(self):
        """Moves the cursor to the next mark to the right."""
        self._write('CNXT')

    def previous_mark(self):
        """Moves the cursor to the next mark to the left."""
        self._write('CPRV')


class Output(InstrumentBase):
    """Represents a SR850 analog output.

    :ivar mode: The analog output mode. Valid are 'fixed', 'log' and 'linear'.
    :ivar voltage: The output voltage in volt, in the range -10.5 to 10.5.
    :ivar limits: The output voltage limits and offset, represented by the
        following tuple *(<start>, <stop>, <offset>)*, where

        * *<start>* is the start value of the sweep. A float between 1e-3 and
          21.
        * *<stop>* is the stop value of the sweep. A float between 1e-3 and 21.
        * *<offset>* is the sweep offset value. A float between -10.5 and 10.5.

        .. note::

            If the output is in fixed mode, setting the limits will generate a
            lock-in internal error.

    """
    def __init__(self, idx, connection, cfg):
        super(Output, self).__init__(connection, cfg)
        idx = int(idx)
        self.mode = Command(
            'AUXM? {0}'.format(idx),
            'AUXM {0},'.format(idx),
            Enum('fixed', 'log', 'linear')
        )
        self.voltage = Command(
            'AUXV? {0}'.format(idx),
            'AUXV {0},'.format(idx),
            Float(min=-10.5, max=10.5)
        )
        self.limits = Command(
            'SAUX? {0}'.format(idx),
            'SAUX {0},'.format(idx),
            (
                Float(min=1e-3, max=21),
                Float(min=1e-3, max=21),
                Float(min=-10.5, max=10.5)
            )
        )


class Trace(InstrumentBase):
    """Represents a SR850 trace.

    :ivar float value: The value of the trace (read only).

    :ivar traces: A sequence of four traces represented by the following tuple
        *(<a>, <b>, <c>, <store>)* where 

        * *<a>, <b>, <c>* define the trace which is calculated as 
          *<a> * <b> / <c>*. Each one of them is one of the following
          quantities '1', 'x', 'y', 'r', 'theta', 'xn', 'yn', 'rn', 'Al1',
          'Al2', 'Al3', 'Al4', 'F', 'x**2', 'y**2', 'r**2', 'theta**2',
          'xn**2', 'yn**2', 'rn**2', 'Al1**2', 'Al2**2', 'Al3**2', 'Al4**2' or
          'F**2'
        * *<store>* is a boolean defining if the trace is stored.

        Traces support a subset of the slicing notation. To get the number of
        points stored, use the builtin :meth:`len` method. E.g.::

            # get point at bin 17.
            print trace[17]
            # get point 17, 18 and 19
            print trace[17:20]

        If the upper bound exceeds the number of store points, an internal
        lock-in error is generated.

    """
    def __init__(self, idx, connection, cfg):
        super(Trace, self).__init__(connection, cfg)
        self.idx = idx = int(idx)
        self.value = Command(('OUTR? {0}'.format(idx), Float))

        quantities = Enum(
            '1', 'x', 'y', 'r', 'theta', 'xn', 'yn', 'rn', 'Al1', 'Al2', 'Al3',
            'Al4', 'F', 'x**2', 'y**2', 'r**2', 'theta**2', 'xn**2', 'yn**2',
            'rn**2', 'Al1**2', 'Al2**2', 'Al3**2', 'Al4**2', 'F**2'
        )
        self.definition = Command(
            'TRCD? {0}'.format(idx),
            'TRCD {0},'.format(idx),
            (quantities, quantities, quantities, Boolean)
        )

    def __len__(self):
        """The number of points stored in the trace."""
        return self._write(('SPTS {0}'.format(self.idx), Integer))

    def __getitem__(self, item):
        if isinstance(item, slice):
            start = item.start
            length = item.stop - item.start
        else:
            start = item.start
            length = 1
        if length <= 0:
            raise ValueError('stop - start > 0 violated.')
        cmd = (
            'TRCA? {0},{1},{2}'.format(self.idx, start, length),
            (Float,) * length
        )
        return self._ask(cmd)


class Mark(InstrumentBase):
    """A SR850 mark.

    :ivar idx: The index of the mark.

    """
    def __init__(self, idx, connection, cfg):
        super(Mark, self).__init__(connection, cfg)
        self.idx = idx = int(idx)

    @property
    def bin(self):
        """The bin index of this mark.

        :returns: An integer bin index or None if the mark is inactive.

        """
        bin = self._query(('MBIN?', Integer, Integer), self.idx)
        return None if bin == -1 else bin

    @property
    def active(self):
        """The active state of the mark.

        :returns: True if the mark is active, False otherwise.

        """
        return False if self.bin is None else True

    @property
    def label(self):
        """The label string of the mark.

        .. note:: The label should not contain any whitespace charactes.

        """
        return self._query(('MTXT?', Integer), self.idx)

    @label.setter
    def label(self, value):
        if [c for c in value if c in string.whitespace]:
            raise ValueError('Invalid argument. Whitespaces are not allowed.')
        self._write(('MTXT', Integer, String), self.idx, value)


class MarkList(InstrumentBase):
    """A sequence like structure holding the eight SR850 marks."""
    def __init__(self, connection, cfg):
        super(MarkList, self).__init__(connection, cfg)
        self._marks = [Mark(i, self.connection, self._cfg) for i in xrange(8)]

    def active(self):
        """The indices of the active marks."""
        # TODO avoid direct usage of connection object.
        marks = tuple(int(x) for x in self.connection.ask('MACT').split(','))
        return marks[1:]

    def __getitem__(self, item):
        return self._marks[item]


class FitParameters(InstrumentBase):
    """The calculated fit parameters.

    The meaning of the fit parameters depends on the fit function used to
    obtain them. These are

    ========  ===============================
    Function  Definition
    ========  ===============================

    line   `y = a + b * (t - t0)`
    exp    `y = a * exp(-(t - t0) / b) + c`
    gauss  `y = a * exp(0.5 * (t / b)^2) + c`
    ========  ===============================

    :ivar a: The a parameter.

        ========  ===============================
        Function  Meaning
        ========  ===============================
        linear    Vertical offset in trace units.
        exp       Amplitude in trace units.
        gauss     Amplitude in trace units.
        ========  ===============================

    :ivar b: The b parameter.

        ========  ================================
        Function  Meaning
        ========  ================================
        linear    Slope in trace units per second.
        exp       Time constant in time.
        gauss     Line width in time.
        ========  ================================

    :ivar c: The c parameter.

        ========  ===============================
        Function  Meaning
        ========  ===============================
        linear    Unused.
        exp       Vertical offset in trace units.
        gauss     Vertical offset in trace units.
        ========  ===============================

    :ivar t0: The t0 parameter.

        ========  =============================
        Function  Meaning
        ========  =============================
        linear    Horizontal offset in time.
        exp       Horizontal offset in time.
        gauss     Peak center position in time.
        ========  =============================

    """
    def __init__(self, connection, cfg):
        super(FitParameters, self).__init__(connection, cfg)
        self.a = Command(('PARS? 0', Float))
        self.b = Command(('PARS? 1', Float))
        self.c = Command(('PARS? 2', Float))
        self.t0 = Command(('PARS? 3', Float))


class Statistics(InstrumentBase):
    """Provides access to the results of the statistics calculation.

    :ivar mean: The mean value.
    :ivar standard_deviation: The standart deviation.
    :ivar total_data: The sum of all the data points within the range.
    :ivar time_delta: The time delta of the range.

    """
    def __init__(self, connection, cfg):
        super(Statistics, self).__init__(connection, cfg)
        self.mean = Command(('SPAR? 0', Float))
        self.standard_deviation = Command(('SPAR? 1', Float))
        self.total_data = Command(('SPAR? 2', Float))
        self.time_delta = Command(('SPAR? 3', Float))
