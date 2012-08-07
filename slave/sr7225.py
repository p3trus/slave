#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Integer, Float, Register


class SR7225(InstrumentBase):
    """Represents a Signal Recovery SR7225 lock-in amplifier.

    .. todo::

       * Check the delimiter of SR7225 in use.
       * Implement ? high speed mode.
       * Implement propper range checking in sweep_rate command.
       * Aux input commands.
       * Implement DC, DCB, DCT command.

    """
    def __init__(self, connection):
        cfg = {
            'parm_delimiter': ' ',
        }
        super(SR7225, self).__init__(connection, cfg=cfg)
        # Signal channel
        # ==============
        #: Set or query the current mode.
        self.current_mode = Command('IMODE', 'IMODE',
                                    Enum('off', 'high bandwidth', 'low noise'))
        #: Set or query the voltage mode.
        #: .. note::
        #:
        #:    The :class:~.current_mode command has a higher precedence.
        self.voltage_mode = Command('VMODE', 'VMODE',
                                    Enum('test', 'A', 'A-B'))
        #: Sets/Queries the voltage mode input device.
        self.fet = Command('FET', 'FET', Enum('bipolar', 'FET'))
        #: Sets/Queries the input connector shielding.
        self.grounding = Command('FLOAT', 'FLOAT', Enum('ground', 'float'))
        #: Sets/Queries the input connector coupling.
        self.coupling = Command('CP', 'CP', Enum('AC', 'DC'))
        #: Sets/Queries the full scale sensitivity.
        self.sensitivity = Command('SEN', 'SEN', Integer(min=1, max=27))
        #: Sets/Queries the gain of the signal channel amplifier.
        self.ac_gain = Command('ACGAIN', 'ACGAIN', Integer(min=0, max=9))
        #: Sets/Queries the state of the automatic ac gain control.
        self.auto_ac_gain = Command('AUTOMATIC', 'AUTOMATIC', Boolean)
        #: Sets/Queries the line filter.
        self.line_filter = Command('LF', 'LF',
                                   [Enum('off', 'notch', 'double', 'both'),
                                    Enum('60 Hz', '50 Hz')])
        #: Sets/Queries the main analog to digital sample frequency.
        self.sample_frequency = Command('SAMPLE', 'SAMPLE',
                                        Integer(min=0, max=2))

        # Reference Channel
        # =================
        #: Sets/Queries the reference input mode.
        self.reference = Command('IE', 'IE', Enum('internal', 'rear', 'front'))
        #: Sets/Queries the reference harmonic mode.
        self.harmonic = Command('REFN', 'REFN', Integer(min=1, max=32))
        #: Sets/Queries the phase in degrees.
        self.reference_phase = Command('REFP.', 'REFP.',
                                       Float(min=-360., max=360.))
        #: Queries the reference frequency in Hz.
        self.reference_frequency = Command('FRQ.', type=Float)

        # Signal channel output filters
        # =============================
        #: Sets/Queries the low-pass filter slope.
        self.slope = Command('SLOPE', 'SLOPE',
                             Enum('6 dB', '12 dB', '18 dB', '24 dB'))
        #: Sets/Queries the filter time constant.
        self.time_constant = Command('TC', 'TC',
                                     Enum('10 us', '20 us', '40 us', '80 us',
                                          '160 us', '320 us', '640 us', '5 ms',
                                          '10 ms', '20 ms', '50 ms', '100 ms',
                                          '200 ms', '500 ms', '1 s', '2 s',
                                          '5 s', '10 s', '20 s', '50 s',
                                          '100 s', '200 s', '500 s', '1 ks',
                                          '2 ks', '5 ks', '10 ks', '20 ks',
                                          '50 ks', '100 ks'))
        #: Sets/Queries the synchronous filter.
        self.sync = Command('SYNC', 'SYNC', Boolean)

        # Signal Channel Output Amplifiers
        # ================================
        #: Sets/Queries the x channel offset
        self.x_offset = Command('XOF', 'XOF', Boolean,
                                Integer(min=-30000, max=30000))
        #: Sets/Queries the y channel offset
        self.y_offset = Command('YOF', 'YOF', Boolean,
                                Integer(min=-30000, max=30000))
        #: Sets/Queries the expansion control.
        self.expand = Command('EX', 'EX',
                              Enum('off', 'x', 'y', 'both'))
        #: Sets/Queries the output signal type on the rear CH1 connector.
        self.channel1_output = Command('CH 1', 'CH 1 ',
                                       Enum('x', 'y', 'r', 'phase1', 'phase2',
                                            'noise', 'ratio', 'log ratio'))
        #: Sets/Queries the output signal type on the rear CH2 connector.
        self.channel2_output = Command('CH 2', 'CH 2 ',
                                       Enum('x', 'y', 'r', 'phase1', 'phase2',
                                            'noise', 'ratio', 'log ratio'))

        # Instrument Outputs
        # ==================
        #: Queries the X demodulator output.
        self.x = Command('X.', type=Float)
        #: Queries the Y demodulator output.
        self.y = Command('Y.', type=Float)
        #: Queries the X and Y demodulator output.
        self.xy = Command('XY.', type=Float)
        #: Queries the magnitude.
        self.r = Command('MAG.', type=Float)
        #: Queries the signal phase.
        self.theta = Command('PHA.', type=Float)
        #: Queries the magnitude and signal phase.
        self.theta = Command('MP.', type=Float)
        #: Queries the ratio equivalent to X/ADC1.
        self.ratio = Command('RT.', type=Float)
        #: Queries the ratio equivalent to log(X/ADC1).
        self.log_ratio = Command('LR.', type=Float)
        #: Queries the square root of the noise spectral density measured at
        #: the Y channel output.
        self.noise = Command('NHZ.', type=Float)
        #: Queries the noise bandwidth.
        self.noise_bandwidth = Command('ENBW.', type=Float)
        #: Queries the noise output, the mean absolute value of the Y channel.
        self.noise_output = Command('NN.', type=Float)
        #: Sets/Queries the starmode.
        self.star = Command('STAR', 'STAR',
                            Enum('x', 'y', 'r', 'theta',
                                 'adc1', 'xy', 'rtheta', 'adc12'))
        # Internal oscillator
        # ===================
        #: Sets/Queries the oscillator amplitude.
        self.amplitude = Command('OA.', 'OA.', Float(min=0., max=5.))
        #: Sets/Queries the starting amplitude of the amplitude sweep.
        self.amplitude_start = Command('ASTART.', 'ASTART.',
                                       Float(min=0., max=5.))
        #: Sets/Queries the target amplitude of the amplitude sweep.
        self.amplitude_stop = Command('ASTOP.', 'ASTOP.',
                                      Float(min=0., max=5.))
        #: Sets/Queries the amplitude step of the amplitude sweep.
        self.amplitude_step = Command('ASTEP.', 'ASTEP.',
                                      Float(min=0., max=5.))
        #: Sets/Queries the synchronous oscillator mode.
        self.sync_oscillator = Command('SYNCOSC', 'SYNCOSC', Boolean)
        #: Sets/Queries the oscillator frequency.
        self.frequency = Command('OF.', 'OF.', Float(min=0, max=1.2e5))
        #: Sets/Queries the start frequency of the frequency sweep.
        self.frequency_start = Command('FSTART.', 'FSTART.',
                                       Float(min=0, max=1.2e5))
        #: Sets/Queries the target frequency of the frequency sweep.
        self.frequency_stop = Command('FSTOP.', 'FSTOP.',
                                       Float(min=0, max=1.2e5))
        #: Sets/Queries the frequency step of the frequency sweep.
        self.frequency_step = Command('FSTEP.', 'FSTEP.',
                                      [Float(min=0, max=1.2e5),
                                       Enum('log', 'linear')])
        #: Sets/Queries the amplitude and frequency sweep step rate
        self.sweep_rate = Command('SRATE', 'SRATE', Integer(min=0))
        # Auxiliary Inputs
        # ================
        # TODO

        # Output Data Curve Buffer
        # ========================
        #: Sets/Queries the curve length.
        self.curve_buffer_length = Command('LEN', 'LEN', Integer(min=0))
        #: Sets/Queries the storage intervall in ms.
        self.storage_intervall = Command('STR', 'STR', Integer(min=0, max=1e9))
        #: Sets/Queries the event marker.
        self.event_marker = Command('EVENT', 'EVENT',
                                    Integer(min=0, max=32767))
        #: Queries the curve acquisition status.
        self.measurement_status = Command(('M', [Enum('no activity',
                                                      'td running',
                                                      'tdc running',
                                                      'td halted',
                                                      'tdc halted'),
                                                 Integer, Integer, Integer]))
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

    def reset_curves(self):
        """Resets the curve storage memory and its status variables."""
        self.connection.write('NC')

    def take_data(self, continuously=False):
        """Starts data acquisition.

        :param continuously: If False, data is written until the buffer is full.
           If its True, the data buffer is used as a circular buffer. That
           means if data acquisition reaches the end of the buffer it
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
