#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Integer, Float, Register, Set, String


class SR7225(InstrumentBase):
    """Represents a Signal Recovery SR7225 lock-in amplifier.

    :param connection: A connection object.

    .. rubric:: Signal Channel

    :ivar current_mode: The current mode, either `'off'`, `'high bandwidth'` or
        `'low noise'`.
    :ivar voltage_mode: The voltage mode, either `'test'`, `'A'` or `'A-B'`.
        The `'test'` mode corresponds to both inputs grounded.

        .. note:

            The :attr:`~.current_mode` has a higher precedence.

    :ivar fet: The voltage mode input device control. Valid entries are
        `'bipolar'` and `'fet'`, where

        * `'bipolar'` is a bipolar device with 10kOhm input impedance and
          2 nV/sqrt(Hz) voltage noise at 1 kHz.
        * `'fet'` 10MOhm input impedance and 5nV/sqrt(Hz) voltage noise at
          1kHz.

    :ivar grounding: The input connector shield grounding mode. Valid entries
        are `'ground'` and `'float'`.
    :ivar coupling: The input connector coupling, either `'ac'` or `'dc'`.
    :ivar sensitivity: The full-scale sensitivity, an integer between 1 and 27.
    :ivar ac_gain: The gain of the signal channel amplifier. An integer between
        0 and 9, corresponding to 0dB to 90dB.
    :ivar ac_gain_auto: A boolean corresponding to the ac gain automatic mode.
        It is `False` if the ac_gain is under manual control, and `True`
        otherwise.
    :ivar line_filter: The line filter configuration.
        *(<filter>, <frequency>)*, where

        * *<filter>* Is the filter mode. Valid entries are `'off'`, `'notch'`,
          `'double'` or `'both'`.
        * *<frequency>* Is the notch filter center frequency, either `'60Hz'`
          or `'50Hz'`.

    :ivar sample_frequency: The sampling frequency. An integer between 0 and 2,
        corresponding to three different sampling frequencies near 166kHz.

    .. rubric:: Reference channel

    :ivar reference: The reference input mode, either `'internal'`, `'rear'` or
        `'front'`.
    :ivar harmonic: The reference harmonic mode, an integer between 1 and 32
        corresponding to the first to 32. harmonic.
    :ivar reference_phase: The phase of the reference signal, a float ranging
        from -360.00 to 360.00 corresponding to the angle in degrees.
    :ivar reference_frequency: A float corresponding to the reference frequency
        in Hz.

        .. note::

            If :attr:`.reference` is not `'internal'` the reference frequency
            value is zero if the reference channel is unlocked.

    .. rubric:: Signal channel output filters

    :ivar slope: The output lowpass filter slope in dB/octave, either `'6dB'`,
        `'12dB'`, `'18dB'` or `'24dB'`.
    :ivar time_constant: A float representing the time constant in seconds. See
        :attr:`.TIME_CONSTANT` for the available values.
    :ivar sync: A boolean value, representing the state of the synchronous time
        constant mode.

    .. rubric:: Signal channel output amplifiers

    :ivar x_offset: The x-channel output offset control.
        *(<enabled>, <range>)*, where

        * *<enabled>* A boolean enabling/disabling the output offset.
        * *<range>* The range of the offset, an integer between -30000 and
          30000 corresponding to +/- 300%.

    :ivar y_offset: The y-channel output offset control.
        *(<enabled>, <range>)*, where

        * *<enabled>* A boolean enabling/disabling the output offset.
        * *<range>* The range of the offset, an integer between -30000 and
          30000 corresponding to +/- 300%.

    :ivar expand: The expansion control, either `'off'`, `'x'`, `'y'` or
        `'both'`.
    :ivar channel1_output: The output of CH1 connector of the rear panel
        Either `'x'`, `'y'`, `'r'`, `'phase1'`, `'phase2'`, `'noise'`,
        `'ratio'` or `'log ratio'`.
    :ivar channel2_output: The output of CH2 connector of the rear panel
        Either `'x'`, `'y'`, `'r'`, `'phase1'`, `'phase2'`, `'noise'`,
        `'ratio'` or `'log ratio'`.

    .. rubric:: Instrument outputs

    :ivar x: A float representing the X-channel output in either volt or
        ampere.
    :ivar y: A float representing the Y-channel output in either volt or
        ampere.
    :ivar xy: X and Y-channel output with the following format *(<x>, <y>)*.
    :ivar r: The signal magnitude, as float.
    :ivar theta: The signal phase, as float.
    :ivar r_theta: The magnitude and the signal phase. *(<r>, <theta>)*.
    :ivar ratio: The ratio equivalent to X/ADC1.
    :ivar log_ratio: The ratio equivalent to log(X/ADC1).
    :ivar noise: The square root of the noise spectral density measured at the
        Y channel output.
    :ivar noise_bandwidth: The noise bandwidth.
    :ivar noise_output: The noise output, the mean absolute value of the Y
        channel.
    :ivar star: The star mode configuration, one off `'x'`, `'y'`, `'r'`,
        `'theta'`, `'adc1'`, `'xy'`, `'rtheta'`, `'adc12'`

    .. rubric:: Internal oscillator

    :ivar amplitude: A float between 0. and 5. representing the oscillator
        amplitude in V rms.
    :ivar amplitude_start: Amplitude sweep start value.
    :ivar amplitude_stop: Amplitude sweep end value.
    :ivar amplitude_step: Amplitude sweep amplitude step.
    :ivar frequency: The oscillator frequency in Hz. Valid entries are 0. to
        1.2e5.
    :ivar frequency_start: The frequency sweep start value.
    :ivar frequency_stop: The frequency sweep stop value.
    :ivar frequency_step: The frequency sweep step size and sweep type.
        *(<step>, <mode>)*, where

        * *<step>* The step size in Hz.
        * *<mode>* The sweep mode, either 'log' or 'linear'.

    :ivar sync_oscillator: The state of the syncronous oscillator (demodulator)
        mode.

    :ivar sweep_rate: The frequency and amplitude sweep step rate in time per
        step. Valid entries are 0.05 to 1000. in 0.005 steps representing the
        time in seconds.

    .. rubric:: Auxiliary outputs

    :ivar dac1: The voltage of the auxiliary output 1 on the rear panel, a
        float between +/- 12.00.
    :ivar dac2: The voltage of the auxiliary output 2 on the rear panel, a
        float between +/- 12.00.

    :ivar output_port: The bits to be output on the rear panel digital output
        port, an Integer between 0 and 255.

    .. rubric:: Auxiliary inputs

    :ivar adc1: The auxiliary analog-to-digital input 1.
    :ivar adc2: The auxiliary analog-to-digital input 2.
    :ivar adc_trigger_mode: The trigger mode of the auxiliary ADC inputs,
        represented by an integer between 0 and 13.
    :ivar burst_time: The burst time per point rate for the ADC1 and ADC2.
        An integer between 25 and 5000 when storing only to ADC1 and 56 to 5000
        when storing to ADC1 and ADC2.

        .. note::

        The lower boundary of 56 in the second case is not tested by slave
        itself.

    .. rubric:: Output data curve buffer

    :ivar curve_buffer_settings: The curve buffer settings define what is to be
        stored in the curve buffer.
    :ivar curve_buffer_length: The length of the curve buffer. The max value
        depends on the the :attr:`.curve_buffer_settings`.
    :ivar storage_intervall: The storage intervall, an integer representing the
        time between datapoints in miliseconds.
    :ivar event_marker: If the `'event'` flag of the
        :attr:`.curve_buffer_settings` is `True`, the content of the event
        marker variable, an integer between 0 and 32767, is stored for each
        data point.
    :ivar measurement_status: The curve acquisition status.
        *(<acquisition status>, <sweeps>, <lockin status>, <points>)*, where
        * *<acquisition status>* is the curve acquisition status. It is either
          `'no activity'`, `'td running'`, `'tdc running'`, `'td halted'` or
          `'tdc halted'`.
        * *<sweeps>* The number of sweeps acquired.
        * *<lockin status>* The content of the status register, equivalent to
          :attr:`.status`.
        * *<points>* The number of points acquired.

    .. rubric:: Computer interfaces
    .. rubric:: Instrument identification
    .. rubric:: Frontpanel
    .. rubric:: Autodefault

    .. todo::

       * Check the delimiter of SR7225 in use.
       * Implement * and ? high speed mode.
       * Implement proper range checking in sweep_rate command.
       * Implement DC, DCB, DCT command.
       * Use Enum for adc_trigger mode.
       * Use Register for srq_mask Command instead of Integer.

    """
    #: All valid time constant values.
    TIME_CONSTANT = [
        10e-6, 20e-6, 40e-6, 80e-6, 160e-6, 320e-6, 640e-6, 5e-3, 10e-3, 20e-3,
        50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1e3,
        2e3, 5e3, 10e3, 20e3, 50e3, 100e3,
    ]

    #: The definition of the curve buffer register bits. To change the curve
    #: buffer settings use the :attr:`.curve_buffer_settings`attribute.
    CURVE_BUFFER = {
        0: 'x',
        1: 'y',
        2: 'r',
        3: 'theta',
        4: 'sensitivity',
        5: 'adc1',
        6: 'adc2',
        7: '7',
        8: 'dac1',
        9: 'dac2',
        10: 'noise',
        11: 'ratio',
        12: 'log ratio',
        13: 'event',
        14: 'reference frequency bits 0-15',
        15: 'reference frequency bits 16-32',
    }

    STATUS_BYTE = {
        0: 'cmd complete',
        1: 'invalid cmd',
        2: 'cmd param error',
        3: 'reference unlock',
        4: 'overload',
        5: 'new adc values after external trigger',
        6: 'asserted srq',
        7: 'data available',
    }

    def __init__(self, connection):
        cfg = {
             'program data separator': ',',
        }
        super(SR7225, self).__init__(connection, cfg=cfg)
        # Signal channel
        # ==============
        self.current_mode = Command('IMODE', 'IMODE',
                                    Enum('off', 'high bandwidth', 'low noise'))
        self.voltage_mode = Command('VMODE', 'VMODE',
                                    Enum('test', 'A', 'A-B'))
        self.fet = Command('FET', 'FET', Enum('bipolar', 'fet'))
        self.grounding = Command('FLOAT', 'FLOAT', Enum('ground', 'float'))
        self.coupling = Command('CP', 'CP', Enum('ac', 'dc'))
        self.sensitivity = Command('SEN', 'SEN', Integer(min=1, max=27))
        self.ac_gain = Command('ACGAIN', 'ACGAIN', Integer(min=0, max=9))
        self.auto_ac_gain = Command('AUTOMATIC', 'AUTOMATIC', Boolean)
        self.line_filter = Command('LF', 'LF',
                                   [Enum('off', 'notch', 'double', 'both'),
                                    Enum('60Hz', '50Hz')])
        self.sample_frequency = Command('SAMPLE', 'SAMPLE',
                                        Integer(min=0, max=2))

        # Reference Channel
        # =================
        self.reference = Command('IE', 'IE', Enum('internal', 'rear', 'front'))
        self.harmonic = Command('REFN', 'REFN', Integer(min=1, max=32))
        self.reference_phase = Command('REFP.', 'REFP.',
                                       Float(min=-360., max=360.))
        self.reference_frequency = Command('FRQ.', type_=Float)

        # Signal channel output filters
        # =============================
        self.slope = Command('SLOPE', 'SLOPE',
                             Enum('6dB', '12dB', '18dB', '24dB'))
        self.time_constant = Command('TC', 'TC', Enum(*self.TIME_CONSTANT))
        self.sync = Command('SYNC', 'SYNC', Boolean)

        # Signal Channel Output Amplifiers
        # ================================
        self.x_offset = Command('XOF', 'XOF', Boolean,
                                Integer(min=-30000, max=30000))
        self.y_offset = Command('YOF', 'YOF', Boolean,
                                Integer(min=-30000, max=30000))
        self.expand = Command('EX', 'EX',
                              Enum('off', 'x', 'y', 'both'))
        self.channel1_output = Command('CH 1', 'CH 1 ',
                                       Enum('x', 'y', 'r', 'phase1', 'phase2',
                                            'noise', 'ratio', 'log ratio'))
        self.channel2_output = Command('CH 2', 'CH 2 ',
                                       Enum('x', 'y', 'r', 'phase1', 'phase2',
                                            'noise', 'ratio', 'log ratio'))

        # Instrument Outputs
        # ==================
        self.x = Command('X.', type_=Float)
        self.y = Command('Y.', type_=Float)
        self.xy = Command('XY.', type_=[Float, Float])
        self.r = Command('MAG.', type_=Float)
        self.theta = Command('PHA.', type_=Float)
        self.r_theta = Command('MP.', type_=[Float, Float])
        self.ratio = Command('RT.', type_=Float)
        self.log_ratio = Command('LR.', type_=Float)
        self.noise = Command('NHZ.', type_=Float)
        self.noise_bandwidth = Command('ENBW.', type_=Float)
        self.noise_output = Command('NN.', type_=Float)
        self.star = Command('STAR', 'STAR',
                            Enum('x', 'y', 'r', 'theta',
                                 'adc1', 'xy', 'rtheta', 'adc12'))
        # Internal oscillator
        # ===================
        self.amplitude = Command('OA.', 'OA.', Float(min=0., max=5.))
        self.amplitude_start = Command('ASTART.', 'ASTART.',
                                       Float(min=0., max=5.))
        self.amplitude_stop = Command('ASTOP.', 'ASTOP.',
                                      Float(min=0., max=5.))
        self.amplitude_step = Command('ASTEP.', 'ASTEP.',
                                      Float(min=0., max=5.))
        self.sync_oscillator = Command('SYNCOSC', 'SYNCOSC', Boolean)
        self.frequency = Command('OF.', 'OF.', Float(min=0, max=1.2e5))
        self.frequency_start = Command('FSTART.', 'FSTART.',
                                       Float(min=0, max=1.2e5))
        self.frequency_stop = Command('FSTOP.', 'FSTOP.',
                                       Float(min=0, max=1.2e5))
        self.frequency_step = Command('FSTEP.', 'FSTEP.',
                                      [Float(min=0, max=1.2e5),
                                       Enum('log', 'linear')])
        self.sweep_rate = Command('SRATE', 'SRATE', Integer(min=0))
        # Auxiliary Outputs
        # ================
        self.dac1 = Command('DAC. 1', 'DAC. 1 ', Float(min=-12., max=12.))
        self.dac2 = Command('DAC. 2', 'DAC. 2 ', Float(min=-12., max=12.))
        self.output_port = Command('BYTE', 'BYTE', Integer(min=0, max=255))
        # Auxiliary Inputs
        # ================
        self.adc1 = Command('ADC. 1', type_=Float)
        self.adc2 = Command('ADC. 2', type_=Float)
        self.adc_trigger_mode = Command('TADC', type_=Integer(min=0, max=13))
        self.burst_time = Command('BURSTTPP', 'BURSTTPP',
                                  Integer(min=25, max=5000))
        # Output Data Curve Buffer
        # ========================
        cb = Register(dict((v, k) for k, v in self.CURVE_BUFFER))
        self.curve_buffer_settings = Command('CBD', 'CBD', cb)
        self.curve_buffer_length = Command('LEN', 'LEN', Integer(min=0))
        self.storage_intervall = Command('STR', 'STR', Integer(min=0, max=1e9))
        self.event_marker = Command('EVENT', 'EVENT',
                                    Integer(min=0, max=32767))
        status_byte = Register(dict((v, k) for k, v in self.STATUS_BYTE))
        self.measurement_status = Command(('M', [Enum('no activity',
                                                      'td running',
                                                      'tdc running',
                                                      'td halted',
                                                      'tdc halted'),
                                                 Integer,
                                                 status_byte,
                                                 Integer]))
        # Computer Interfaces
        # ===================
        #: RS232 settings.
        self.rs232 = Command('RS', 'RS',
                             [Enum(75, 110, 134.5, 150, 300, 600, 1200, 1800,
                                   2000, 2400, 4800, 9600, 19200),
                              Register({'9 bits': 0, 'parity bit': 1,
                                        'odd parity': 2, 'echo': 3,
                                        'prompt': 4})])
        self.gpib = Command('GP', 'GP',
                            [Integer(min=0, max=31),
                             Enum('CR', 'CR echo', 'CR, LF', 'CR, LF echo',
                                  'None', 'None echo')])
        #: Sets/Queries the ascii code of the delimiter.
        self.delimiter = Command('DD', 'DD', Set(13, *range(31, 126)))
        #: Queries the status byte.
        self.status = Command('ST', type_=status_byte)
        overload_byte = {
            'ch1 output overload': 1,
            'ch2 output overload': 2,
            'y output overload': 3,
            'x output overload': 4,
            'input overload': 6,
            'reference unlock': 7,
        }
        #: Queries the overload status.
        self.overload_status = Command('N', type_=Register(overload_byte))
        #: Sets/Queries the service request mask.
        self.srq_mask = Command('MSK', 'MSK', Integer(min=0, max=255))
        #: Sets/Queries the remote mode.
        self.remote = Command('REMOTE', 'REMOTE', Boolean)
        # Instrument identification
        # =========================
        #: Queries the instrument id.
        self.id = Command('ID', type_=String)
        #: Queries the firmware revision.
        self.revision = Command('REV', type_=String)
        #: Queries the firmware version.
        self.version = Command('VER', type_=String)
        #: Sets/Queries the front panel LED's and LCD backlight state.
        self.lights = Command('LTS', 'LTS', Boolean)

    def auto_sensitivity(self):
        """Triggers the auto sensitivity mode.

        When the auto sensitivity mode is triggered, the SR7225 adjustes the
        sensitivity so that the signal magnitude lies in between 30% and 90%
        of the full scale sensitivity.
        """
        self.connection.write('AS')

    def auto_measure(self):
        """Triggers the auto measure mode."""
        self.connection.write('ASM')

    def auto_phase(self):
        """Triggers the auto phase mode."""
        self.connection.write('AQN')

    def auto_offset(self):
        """Triggers the auto offset mode."""
        self.connection.write('AXO')

    def lock(self):
        """Updates all frequency-dependent gain and phase correction
        parameters.
        """
        self.connection.write('LOCK')

    def stop(self):
        """Stops/Pauses the current sweep."""
        self.connection.write('SWEEP 0')

    def start_fsweep(self, start=None, stop=None, step=None):
        """Starts a frequency sweep.

        :param start: Sets the start frequency.
        :param stop: Sets the target frequency.
        :param step: Sets the frequency step.

        """
        if start:
            self.frequency_start = start
        if stop:
            self.frequency_stop = stop
        if step:
            self.frequency_step = step
        self.connection.write('SWEEP 1')

    def start_asweep(self, start=None, stop=None, step=None):
        """Starts a frequency sweep.

        :param start: Sets the start frequency.
        :param stop: Sets the target frequency.
        :param step: Sets the frequency step.

        """
        if start:
            self.amplitude_start = start
        if stop:
            self.amplitude_stop = stop
        if step:
            self.amplitude_step = step
        self.connection.write('SWEEP 2')

    def start_afsweep(self):
        """Starts a frequency and amplitude sweep."""
        self.connection.write('SWEEP 3')

    def init_curves(self):
        """Initializes the curve storage memory and its status variables.

        .. note:: All records of previously taken curves is removed.

        """
        self.connection.write('NC')

    def take_data(self, continuously=False):
        """Starts data acquisition.

        :param continuously: If False, data is written until the buffer is
            full. If its True, the data buffer is used as a circular buffer.
            That means if data acquisition reaches the end of the buffer it
            continues at the beginning.

        """
        if continuously:
            self.connection.write('TDC')
        else:
            self.connection.write('TD')

    def take_data_triggered(self, mode):
        """Starts triggered data acquisition.

        :param mode: If mode is 'curve', a trigger signal starts the
           acquisition of a complete curve or set of curves. If its 'point',
           only a single data point is stored.

        """
        if mode == 'curve':
            self.connection.write('TDT 0')
        elif mode == 'point':
            self.connection.write('TDT 1')
        else:
            raise ValueError('mode must be either "curve" or "point"')

    def halt(self):
        """Halts the data acquisition."""
        self.connection.write('HC')

    def reset(self, complete=False):
        """Resets the lock-in to factory defaults.

        :param complete: If True all settings are reseted to factory defaults.
           If it's False, all settings are reseted to factory defaults with the
           exception of communication and LCD contrast settings.

        """
        self.connection.write('ADF {0:d}'.format(complete))
