#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Integer, Register, Set, String
import slave.types


class Float(slave.types.Float):
    """Custom float class used to correct a bug in the SR7225 firmware.

    When the SR7225 is queried in floating point mode and the value is exactly
    zero, it appends a `\\x00` value, a null byte. To workaround this firmware
    bug, the null byte is stripped before the conversion to float happens.

    """
    def __convert__(self, value):
        if isinstance(value, basestring):
            value = value.strip('\x00')
        return super(Float, self).__convert__(value)


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
    :ivar sensitivity: The full-scale sensitivity. The valid entries depend on
        the current mode.

        =========  ================  ===========
        'off'      'high bandwidth'  'low noise'
        =========  ================  ===========
        '2 nV'     '2 fA'            '2 fA'
        '5 nV'     '5 fA'            '5 fA'
        '10 nV'    '10 fA'           '10 fA'
        '20 nV'    '20 fA'           '20 fA'
        '50 nV'    '50 fA'           '50 fA'
        '100 nV'   '100 fA'          '100 fA'
        '200 nV'   '200 fA'          '200 fA'
        '500 nV'   '500 fA'          '500 fA'
        '1 uV'     '1 pA'            '1 pA'
        '2 uV'     '2 pA'            '2 pA'
        '5 uV'     '5 pA'            '5 pA'
        '10 uV'    '10 pA'           '10 pA'
        '20 uV'    '20 pA'           '20 pA'
        '50 uV'    '50 pA'           '50 pA'
        '100 uV'   '100 pA'          '100 pA'
        '200 uV'   '200 pA'           200 pA'
        '500 uV'   '500 pA'          '500 pA'
        '1 mV'     '1 nA'            '1 nA'
        '2 mV'     '2 nA'            '2 nA'
        '5 mV'     '5 nA'            '5 nA'
        '10 mV'    '10 nA'           ---
        '20 mV'    '20 nA'           ---
        '50 mV'    '50 nA'           ---
        '100 mV'   '100 nA'          ---
        '200 mV'   '200 nA'          ---
        '500 mV'   '500 nA'          ---
        '1 V'      '1 uA'            ---
        =========  ================  ===========

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

    :ivar rs232: The rs232 settings. *(<baud rate>, <settings>)*, where

        * *<baud rate>* The baud rate in bits per second. Valid entries are
          `75`, `110`, `134.5`, `150`, `300`, `600`, `1200`, `1800`, `2000`,
          `2400`, `4800`, `9600` and `19200`.
        * *<settings>* The sr7225 uses a 5bit register to configure the rs232
          interface.

            + `'9bit'` If it is `True`, data + parity use 9 bits and 8 bits
              otherwise.
            + `'parity'` If it's `True`, a single parity bit is used.
              If it's `False` no parity bit is used.
            + `'odd parity'` If it is `True` odd parity is used and even
              otherwise.
            + `'echo'` If it's `True`, echo is enabled.
            + `'promt'` If it's `True`, promt is enabled.

    :ivar gpib: The gpib configuration. *(<channel>, <terminator>)*, where

        * *<channel>* Is the gpib communication channel, an integer between 0
          and 31.
        * *<terminator>* The command terminator, either `'CR'`, `'CR echo'`,
          `'CRLF'`, `'CRLF echo'`, `'None'` or `'None echo'`. `'CR'` is the
          carriage return, `'LF'` the linefeed. When echo is on, every command
          or response of the gpib interface is echoed to the rs232 interface.

    :ivar delimiter: The response data separator. Valid entries are 13 or 32 to
        125 representing the ascii value of the character in use.

        .. warning::

            This command does **not** change the response data separator of the
            commands in use. Using it might lead to errors.

    :ivar status: The sr7225 status register.
    :ivar status_enable: The status enable register is used to mask the bits of
        the status register, which generate a service request.
    :ivar overload_status: The overload status register.
    :ivar remote: The remote mode of the front panel.

    .. rubric:: Instrument identification

    :ivar identification: The identification, it responds with `'7225'`.
    :ivar revision: The firmware revision. A multiline string.

        .. warning:: Not every connection can handle multiline responses.

    :ivar version: The firmware version.

    .. rubric:: Frontpanel

    :ivar lights: The status of the front panel lights. `True` if these are
        enabled, `False` otherwise.

    .. todo::

       * Implement * and ? high speed mode.
       * Implement DC, DCB, DCT command.
       * Use Enum for adc_trigger mode.
       * Implement daisy chain address command `\\N`.

    """
    #: All valid time constant values.
    TIME_CONSTANT = [
        10e-6, 20e-6, 40e-6, 80e-6, 160e-6, 320e-6, 640e-6, 5e-3, 10e-3, 20e-3,
        50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1e3,
        2e3, 5e3, 10e3, 20e3, 50e3, 100e3,
    ]
    #: All valid baud rates of the rs232 interface.
    BAUD_RATE = [
        75, 110, 134.5, 150, 300, 600, 1200, 1800, 2000, 2400, 4800, 9600,
        19200,
    ]
    #: The definition of the curve buffer register bits. To change the curve
    #: buffer settings use the :attr:`.curve_buffer_settings` attribute.
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
    #: The rs232 settings register definition.
    RS232 = {
        0: '9bit',
        1: 'parity',
        2: 'odd parity',
        3: 'echo',
        4: 'promt',
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
        self.voltage_mode = Command(
            'VMODE',
            'VMODE',
            Enum('test', 'A', 'A-B', start=1)
        )
        self.fet = Command('FET', 'FET', Enum('bipolar', 'fet'))
        self.grounding = Command('FLOAT', 'FLOAT', Enum('ground', 'float'))
        self.coupling = Command('CP', 'CP', Enum('ac', 'dc'))
        volt_sens = Enum(
            '2 nV', '5 nV', '10 nV', '20 nV', '50 nV', '100 nV', '200 nV',
            '500 nV', '1 uV', '2 uV', '5 uV', '10 uV', '20 uV', '50 uV',
            '100 uV', '200 uV', '500 uV', '1 mV', '2 mV', '5 mV', '10 mV',
            '20 mV', '50 mV', '100 mV', '200 mV', '500 mV', '1 V',
            start=1
        )
        self._voltage_sensitivity = Command('SEN', 'SEN', volt_sens)
        highbw_sens = Enum(
            '2 fA', '5 fA', '10 fA', '20 fA', '50 fA', '100 fA', '200 fA',
            '500 fA', '1 pA', '2 pA', '5 pA', '10 pA', '20 pA', '50 pA',
            '100 pA', '200 pA', '500 pA', '1 nA', '2 nA', '5 nA', '10 nA',
            '20 nA', '50 nA', '100 nA', '200 nA', '500 nA', '1 uA',
            start=1
        )
        self._highbandwidth_sensitivity = Command('SEN', 'SEN', highbw_sens)
        lownoise_sens = Enum(
            '2 fA', '5 fA', '10 fA', '20 fA', '50 fA', '100 fA', '200 fA',
            '500 fA', '1 pA', '2 pA', '5 pA', '10 pA', '20 pA', '50 pA',
            '100 pA', '200 pA', '500 pA', '1 nA', '2 nA', '5 nA', '10 nA',
            start=7
        )
        self._lownoise_sensitivity = Command('SEN', 'SEN', lownoise_sens)
        self.ac_gain = Command('ACGAIN', 'ACGAIN',
                               Enum('0 dB', '10 dB', '20 dB', '30 dB', '40 dB',
                                    '50 dB', '60 dB', '70 db', '80 dB', '90 dB'
                                    ))
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
        self.reference_frequency = Command(('FRQ.', Float))

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
        self.sweep_rate = Command('SRATE.', 'SRATE.',
                                  Float(min=0.05, max=1000))
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
        cb = Register(dict((v, k) for k, v in self.CURVE_BUFFER.iteritems()))
        self.curve_buffer_settings = Command('CBD', 'CBD', cb)
        self.curve_buffer_length = Command('LEN', 'LEN', Integer(min=0))
        self.storage_intervall = Command('STR', 'STR', Integer(min=0, max=1e9))
        self.event_marker = Command('EVENT', 'EVENT',
                                    Integer(min=0, max=32767))
        status_byte = Register(
            dict((v, k) for k, v in self.STATUS_BYTE.iteritems())
        )
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
        rs = Register(dict((v, k) for k, v in self.RS232.iteritems()))
        self.rs232 = Command('RS', 'RS', [Enum(*self.BAUD_RATE), rs])
        self.gpib = Command('GP', 'GP',
                            [Integer(min=0, max=31),
                             Enum('CR', 'CR echo', 'CRLF', 'CRLF echo',
                                  'None', 'None echo')])
        self.delimiter = Command('DD', 'DD', Set(13, *range(31, 126)))
        self.status = Command('ST', type_=status_byte)
        overload_byte = {
            'ch1 output overload': 1,
            'ch2 output overload': 2,
            'y output overload': 3,
            'x output overload': 4,
            'input overload': 6,
            'reference unlock': 7,
        }
        self.overload_status = Command('N', type_=Register(overload_byte))
        self.status_enable = Command('MSK', 'MSK', status_byte)
        self.remote = Command('REMOTE', 'REMOTE', Boolean)
        # Instrument identification
        # =========================
        self.identification = Command('ID', type_=String)
        self.revision = Command('REV', type_=String)
        self.version = Command('VER', type_=String)
        # Frontpanel
        # ==========
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

    def halt(self):
        """Halts the data acquisition."""
        self.connection.write('HC')

    def init_curves(self):
        """Initializes the curve storage memory and its status variables.

        .. warning:: All records of previously taken curves is removed.

        """
        self.connection.write('NC')

    def lock(self):
        """Updates all frequency-dependent gain and phase correction
        parameters.
        """
        self.connection.write('LOCK')

    def reset(self, complete=False):
        """Resets the lock-in to factory defaults.

        :param complete: If True all settings are reseted to factory defaults.
           If it's False, all settings are reseted to factory defaults with the
           exception of communication and LCD contrast settings.

        """
        self.connection.write('ADF {0:d}'.format(complete))

    @property
    def sensitivity(self):
        imode = self.current_mode
        if imode == 'off':
            return self._voltage_sensitivity
        elif imode == 'high bandwidth':
            return self._highbandwidth_sensitivity
        else:
            return self._lownoise_sensitivity

    @sensitivity.setter
    def sensitivity(self, value):
        imode = self.current_mode
        if imode == 'off':
            self._voltage_sensitivity = value
        elif imode == 'high bandwidth':
            self._highbandwidth_sensitivity = value
        else:
            self._lownoise_sensitivity = value

    def start_asweep(self, start=None, stop=None, step=None):
        """Starts a amplitude sweep.

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

    def stop(self):
        """Stops/Pauses the current sweep."""
        self.connection.write('SWEEP 0')

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
