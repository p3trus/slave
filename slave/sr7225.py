#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Integer, Float


class SR7225(InstrumentBase):
    """Represents a Signal Recovery SR7225 lock-in amplifier."""
    def __init__(self, connection):
        super(SR7225, self).__init__(connection)
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
