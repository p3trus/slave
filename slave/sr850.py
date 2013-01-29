#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
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
                 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3
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
