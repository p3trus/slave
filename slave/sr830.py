#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The sr830 module implements an interface for the Stanford Research SR830.
"""

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Float, Integer, Set, String


__all__ = ['SR830']


class Aux(InstrumentBase):
    def __init__(self, connection, id):
        super(Aux, self).__init__(connection)
        self.id = id = int(id)
        #: Queries the aux input voltages.
        self.input = Command(('OAUX? {0}'.format(id), Float))
        #: Sets and queries the output voltage.
        self.output = Command('AUXV? {0}'.format(id),
                              'AUXV {0},'.format(id),
                              Float(min=-10.5, max=10.5))


class Status(InstrumentBase):
    def __init__(self, connection):
        super(Status, self).__init__(connection)
        #: Queries the input overload status byte.
        self.input_overload = Command(('LIAS? 0', Boolean))
        #: Queries the time constant filter overload status byte.
        self.tc_filter_overload = Command(('LIAS? 1', Boolean))
        #: Queries the output overload status byte.
        self.output_overload = Command(('LIAS? 2', Boolean))
        #: Queries the reference unlock status byte.
        self.reference_unlock = Command(('LIAS? 3', Boolean))
        #: Status byte which is set when the detection frequency changes its
        #: range.
        self.detection_frequency_range_switch = Command(('LIAS? 4', Boolean))
        #: Status byte which is set, when an indirect time constant change
        #: occured, e.g. by a change of the dynamic reserve, frequency range,
        #: filter slope or expand.
        self.indirect_tc_change = Command(('LIAS? 5', Boolean))
        #: Status byte, which is set when the data storage is triggered
        #: (only in external trigger mode).

    def __call__(self, mapped=True):
        """Returns the lockin status.

        :param mapped: If mapped is False, the raw integer is returned.
           Otherwise the bits are converted into a dict with bitname, value
           pairs.

        """
        status = int(self.connection.ask('LIAS?'))
        if mapped:
            get_bit = lambda x, i: bool(x & (1 << i))
            status = {
                'input overload': get_bit(status, 0),
                'time const filter overload': get_bit(status, 1),
                'output overload': get_bit(status, 2),
                'reference unlock': get_bit(status, 3),
                'detection frequency range switch': get_bit(status, 4),
                'indirect tc change': get_bit(status, 5)
            }
        return status


class SR830(InstrumentBase):
    """
    Stanford Research SR830 Lock-In Amplifier instrument class.

    The SR830 provides a simple, yet powerful interface to a Stanford Research
    SR830 lock-in amplifier.

    E.g.::

        import visa
        from slave.sr830 import SR830
        # create a connection with a sr830 instrument via GPIB on channel 8
        connection = visa.Instrument('GPIB::8')
        # instantiate the lockin interface.
        lockin = SR830(connection)
        # execute a simple measurement
        for i in range(100):
            print 'X:', lockin.x
            time.sleep(1)

    .. todo::
        Implementation of the TRCA, TRCB, ESE, ESR,
        SRE, STB, PSC, ERRE, ERRS, LIAE, LIAS commands.

    """
    def __init__(self, connection):
        """Constructs a SR830 instrument object.

        :param connection: Represents a hardware connection to the real
          instrument, e.g. a py-visa connection object.

        """
        super(SR830, self).__init__(connection)

        # Reference and phase commands
        # ============================
        #: Sets and queries the reference phase
        self.phase = Command('PHAS?', 'PHAS',
                             Float(min=-360., max=729.99))
        #: Sets or queries the reference source
        self.reference = Command('FMOD?', 'FMOD',
                                 Enum('external', 'internal'))
        #: Sets or queries the internal reference frequency.
        self.frequency = Command('FREQ?', 'FREQ',
                                 Float(min=0.001, max=102000.))
        #: Sets or triggers the reference trigger mode.
        self.reference_trigger = Command('RSLP?', 'RSLP',
                                         Enum('sine', 'rise', 'fall'))
        #: Sets or queries the detection harmonic.
        self.harmonic = Command('HARM?', 'HARM', Integer(min=1, max=19999))
        #: Sets or queries the amplitude of the sine output.
        self.amplitude = Command('SLVL?', 'SLVL', Float(min=0.004, max=5.))

        # Input and filter commands
        # =========================
        #: Sets or queries the input configuration.
        self.input = Command('ISRC?', 'ISRC', Enum('A', 'A-B', 'I', 'I100'))
        #: Sets or queries the input shield grounding.
        self.ground = Command('IGND?', 'IGND', Boolean)
        #: Sets or queries the input coupling.
        self.coupling = Command('ICPL?', 'ICPL', Enum('AC', 'DC'))
        #: Sets or queries the input line notch filter status.
        self.filter = Command('ILIN?', 'ILIN',
                              Enum('unfiltered', 'notch', '2xnotch', 'both'))

        # Gain and time constant commands
        # ===============================
        #: Sets or queries the sensitivity.
        self.sensitivity = Command('SENS?', 'SENS', Integer(min=0, max=26))
        #: Sets or queries the dynamic reserve.
        self.reserve = Command('RMOD?', 'RMOD', Enum('high', 'medium', 'low'))
        #: Sets or queries the time constant.
        self.time_constant = Command('OFLT?', 'OFLT', Integer(min=0, max=19))
        #: Sets or queries the low-pass filter slope.
        self.slope = Command('OFSL?', 'OFSL', Integer(min=0, max=3))
        #: Sets or queries the synchronous filtering mode.
        self.sync = Command('SYNC?', 'SYNC', Boolean)

        # Display and output commands
        # ===========================
        #: Set or query the channel 1 display settings.
        self.ch1_display = Command('DDEF? 1', 'DDEF 1',
                                   [Enum('X', 'R', 'Xnoise',
                                         'AuxIn1', 'AuxIn2'),
                                    Enum('none', 'AuxIn1', 'AuxIn2')])
        #: Set or query the channel 2 display settings.
        self.ch2_display = Command('DDEF? 2', 'DDEF 2',
                                   [Enum('Y', 'Theta', 'Ynoise',
                                         'AuxIn3', 'AuxIn4'),
                                    Enum('none', 'AuxIn3', 'AuxIn4')])
        #: Sets the channel1 output.
        self.ch1_output = Command('FPOP? 1', 'FPOP 1,', Enum('CH1', 'X'))
        #: Sets the channel2 output.
        self.ch2_output = Command('FPOP? 2', 'FPOP 2,', Enum('CH2', 'Y'))
        #:Sets or queries the x value offset and expand.
        self.x_offset_and_expand = Command('OEXP? 1', 'OEXP 1',
                                         [Float(min=-105., max=105.),
                                          Set(0, 10, 100)])
        #:Sets or queries the x value offset and expand.
        self.y_offset_and_expand = Command('OEXP? 2', 'OEXP 2',
                                         [Float(min=-105., max=105.),
                                          Set(0, 10, 100)])
        #:Sets or queries the x value offset and expand
        self.r_offset_and_expand = Command('OEXP? 3', 'OEXP 3',
                                         [Float(min=-105., max=105.),
                                          Set(0, 10, 100)])


        # Aux input and output commands
        # =============================
        for id in range(1, 5):
            setattr(self, 'aux{0}'.format(id), Aux(connection, id))

        # Setup commands
        # ==============
        #: Sets or queries the output interface.
        self.output_interface = Command('OUTX?', 'OUTX', Enum('RS232', 'GPIB'))
        #: Sets the remote mode override.
        self.overide_remote = Command(write=('OVRM', Boolean))
        #: Sets or queries the key click state.
        self.key_click = Command('KCLK?', 'KCLK', Boolean)
        #: Sets or queries the alarm state.
        self.alarm = Command('ALRM?', 'ALRM', Boolean)

        # Data storage commands
        # =====================
        self.sample_rate = Command('SRAT?', 'SRAT', Integer(min=0, max=14))
        #: The send command sets or queries the end of buffer mode.
        #: .. note::
        #:    If loop mode is used, the data storage should be paused to avoid
        #:    confusion about which point is the most recent.
        self.send_mode = Command('SEND?', 'SEND', Enum('shot', 'loop'))

        # Data transfer commands
        # ======================
        #: Reads the value of x.
        self.x = Command(('OUTP? 1', Float))
        #: Reads the value of y.
        self.y = Command(('OUTP? 2', Float))
        #: Reads the value of r.
        self.r = Command(('OUTP? 3', Float))
        #: Reads the value of theta.
        self.theta = Command(('OUTP? 4', Float))
        #: Reads the value of channel 1.
        self.ch1 = Command(('OUTR? 1', Float))
        #: Reads the value of channel 2.
        self.ch2 = Command(('OUTR? 2', Float))
        #: Queries the number of data points stored in the internal buffer.
        self.data_points = Command(('SPTS?', Integer))
        #: Sets or queries the data transfer mode.
        #: .. note::
        #:    Do not use :class:`~SR830.start() to execute the scan, use
        #:    :class:`~SR830.delayed_start instead.
        self.fast_mode = Command('FAST?', 'FAST',
                                 Enum('off', 'DOS', 'Windows'))

        # Interface Commands
        # ==================
        #: Queries the device identification string
        self.idn = Command('*IDN?', type=[String, String, String, String])
        #: Queries or sets the state of the frontpanel.
        self.state = Command('LOCL?', 'LOCL',
                             Enum('local', 'remote', 'lockout'))
        # Status reporting commands
        # =========================
        self.status = Status(connection)

    def auto_gain(self):
        """Executes the auto gain command."""
        self.connection.write('AGAN')

    def auto_reserve(self):
        """Executes the auto reserve command."""
        self.connection.write('ARSV')

    def auto_phase(self):
        """Executes the auto phase command."""
        self.connection.write('APHS')

    def auto_offset(self, signal):
        """Executes the auto offset command for the selected signal.

        :param i: Can either be 'X', 'Y' or 'R'.

        """
        signals = {'X': 1, 'Y': 2, 'R': 3}
        self.connection.ask('AOFF {0}'.format(signals[signal]))

    def trigger(self):
        """Emits a trigger event."""
        self.connection.write('TRIG')

    def start(self):
        """Starts or resumes data storage."""
        self.connection.write('STRT')

    def delayed_start(self):
        """Starts data storage after a delay of 0.5 sec."""
        self.connection.write('STRD')

    def pause(self):
        """Pauses data storage."""
        self.connection.write('PAUS')

    def reset_buffer(self):
        """Resets internal data buffers."""
        self.connection.write('REST')

    def reset_configuration(self):
        """Resets the SR830 to it's default configuration."""
        self.connection.write('*RST')

    def save_setup(self, id):
        """Saves the lock-in setup in the setup buffer."""
        id = int(id)
        if 0 < id < 10:
            self.connection.write('SSET {0}'.format(id))
        else:
            raise ValueError('Buffer id out of range.')

    def recall_setup(self, id):
        """Recalls the lock-in setup from the setup buffer.

        :param id: Represents the buffer id (0 < buffer < 10). If no
          lock-in setup is stored under this id, recalling results in
          an error in the hardware.
        """
        id = int(id)
        if 0 < id < 10:
            self.connection.write('RSET {0}'.format(id))

    def snap(self, *args):
        """Records up to 6 parameters at a time.

        :param *args: Specifies the values to record. Valid ones are 'X', 'Y',
          'R', 'theta', 'AuxIn1', 'AuxIn2', 'AuxIn3', 'AuxIn4', 'Ref', 'CH1'
          and 'CH2'. If none are given 'X' and 'Y' are used.

        """
        params = {'X': 1, 'Y': 2, 'R': 3, 'theta': 4, 'AuxIn1': 5, 'AuxIn2': 6,
                  'AuxIn3': 7, 'AuxIn4': 8, 'Ref': 9, 'CH1': 10, 'CH2': 11}
        if not args:
            args = ['X', 'Y']
        if len(args) > 6:
            raise ValueError('Too many parameters (max: 6).')
        cmd = 'SNAP? ' + ','.join(map(lambda x: params[x], args))
        result = self.connection.ask(cmd)
        return map(float, result.strip(','))

    def clear(self):
        """Clears all status registers."""
        self.connection.write('*CLS')
