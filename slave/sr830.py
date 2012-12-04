#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The sr830 module implements an interface for the Stanford Research SR830.

The SR830 lock in amplifier is an IEEE Std. 488-2 1987 compliant device.

"""

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Float, Integer, Register, Set, String


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
    """Wraps a readable and writeable register."""
    def __init__(self, query, write, register, connection):
        super(Status, self).__init__(connection)
        for k, v in register.iteritems():
            q = query + ' {0}'.format(int(v))
            w = write + ' {0},'.format(int(v)) if write else None
            name = k.replace(' ', '_')
            setattr(self, name, Command(q, w, Boolean))
        self.value = Command(query, write, Register(register))

    def __call__(self):
        """returns self.value."""
        return self.value


class ErrorStatus(Status):
    def __init__(self, connection):
        register = {
            'backup error': 1,
            'ram error': 2,
            'rom error': 4,
            'gpib error': 5,
            'dsp error': 6,
            'math error': 7,
        }
        super(ErrorStatus, self).__init__('ERRS?', None,
                                          register, connection)


class ErrorEnable(Status):
    def __init__(self, connection):
        register = {
            'backup error': 1,
            'ram error': 2,
            'rom error': 4,
            'gpib error': 5,
            'dsp error': 6,
            'math error': 7,
        }
        super(ErrorEnable, self).__init__('ERRE?', 'ERRE',
                                          register, connection)


class LockInStatus(Status):
    def __init__(self, connection):
        register = {
            'input overload': 0,
            'TC filter overload': 1,
            'output overload': 2,
            'reference unlock': 3,
            'frequency range switch': 4,
            'indirect TC change': 5,
            'triggered': 6,
        }
        super(LockInStatus, self).__init__('LIAS?', None,
                                           register, connection)


class LockInEnable(Status):
    def __init__(self, connection):
        register = {
            'input overload': 0,
            'TC filter overload': 1,
            'output overload': 2,
            'reference unlock': 3,
            'frequency range switch': 4,
            'indirect TC change': 5,
            'triggered': 6,
        }
        super(LockInEnable, self).__init__('LIAE?', 'LIAE',
                                           register, connection)


class SerialPollStatus(Status):
    """Represents the serial poll status register."""
    def __init__(self, connection):
        register = {
            'no scan': 0,
            'no command': 1,
            'error': 2,
            'lockin': 3,
            'output_buffer': 4,
            'standard status ': 5,
            'service request': 6,
        }
        super(SerialPollStatus, self).__init__('*STB?', None,
                                               register, connection)


class SerialPollEnable(Status):
    """Represents the serial poll enable register."""
    def __init__(self, connection):
        register = {
            'no scan': 0,
            'no command': 1,
            'error': 2,
            'lockin': 3,
            'output_buffer': 4,
            'standard status ': 5,
            'service request': 6,
        }
        super(SerialPollEnable, self).__init__('*SRE?', '*SRE',
                                               register, connection)


class StandardEventStatus(Status):
    """
    Represents the standard event status.

    The standard event status bits are cleared by reading or explicitly
    clearing them via the :class:`~SR830.clear` member function.

    """
    def __init__(self, connection):
        register = {
            'input queue overflow': 0,
            'output queue overflow': 2,
            'execution failed': 4,
            'illegal command': 5,
            'user interaction': 6,
            'power on': 7,
        }
        super(StandardEventStatus, self).__init__('*ESR?', None,
                                                  register, connection)


class StandardEventEnable(Status):
    """Represents the standard event enable register."""
    def __init__(self, connection):
        register = {
            'input queue overflow': 0,
            'output queue overflow': 2,
            'execution failed': 4,
            'illegal command': 5,
            'user interaction': 6,
            'power on': 7,
        }
        super(StandardEventEnable, self).__init__('*ESE?', 'ESE',
                                                  register, connection)


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
        #: Sets or queries the sensitivity in units of volt.
        self.sensitivity = Command('SENS?', 'SENS',
                                   Enum(2e-9, 5e-9, 10e-9, 20e-9, 50e-9,
                                        100e-9, 200e-9, 500e-9, 1e-6, 2e-6,
                                        5e-6, 10e-6, 20e-6, 50e-6, 100e-6,
                                        200e-6, 500e-6, 1e-3, 2e-3, 5e-3,
                                        10e-3, 20e-3, 50e-3, 100e-3, 200e-3,
                                        500e-3, 1))
        #: Sets or queries the dynamic reserve.
        self.reserve = Command('RMOD?', 'RMOD', Enum('high', 'medium', 'low'))
        #: Sets or queries the time constant in seconds.
        self.time_constant = Command('OFLT?', 'OFLT',
                                     Enum(10e-6, 30e-6, 100e-6, 300e-6, 1e-3,
                                          3e-3, 10e-3, 30e-3, 100e-3, 300e-3,
                                          1, 3, 10, 30, 100, 300, 1e3, 3e3,
                                          10e3, 30e3))
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
        #:
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
        #:
        #:    Do not use :class:`~SR830.start() to execute the scan, use
        #:    :class:`~SR830.delayed_start instead.
        self.fast_mode = Command('FAST?', 'FAST',
                                 Enum('off', 'DOS', 'Windows'))

        # Interface Commands
        # ==================
        #: Queries the device identification string
        self.idn = Command('*IDN?', type_=[String, String, String, String])
        #: Queries or sets the state of the frontpanel.
        self.state = Command('LOCL?', 'LOCL',
                             Enum('local', 'remote', 'lockout'))

        # Status reporting commands
        # =========================
        self.error_status = ErrorStatus(connection)
        self.error_enable = ErrorEnable(connection)
        self.lockin_status = LockInStatus(connection)
        self.lockin_enable = LockInEnable(connection)
        self.serial_poll_status = SerialPollStatus(connection)
        self.serial_poll_enable = SerialPollEnable(connection)
        self.std_event_status = StandardEventStatus(connection)
        self.std_event_enable = StandardEventEnable(connection)
        #: Enables or disables the clearing of the status registers on poweron.
        self.clear_on_poweron = Command('*PSC?', '*PSC', Boolean)

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

        :param args: Specifies the values to record. Valid ones are 'X', 'Y',
          'R', 'theta', 'AuxIn1', 'AuxIn2', 'AuxIn3', 'AuxIn4', 'Ref', 'CH1'
          and 'CH2'. If none are given 'X' and 'Y' are used.

        """
        params = {'X': 1, 'Y': 2, 'R': 3, 'Theta': 4, 'AuxIn1': 5, 'AuxIn2': 6,
                  'AuxIn3': 7, 'AuxIn4': 8, 'Ref': 9, 'CH1': 10, 'CH2': 11}
        if not args:
            args = ['X', 'Y']
        if len(args) > 6:
            raise ValueError('Too many parameters (max: 6).')
        cmd = 'SNAP? ' + ','.join(map(lambda x: str(params[x]), args))
        result = self.connection.ask(cmd)
        return map(float, result.split(','))

    def clear(self):
        """Clears all status registers."""
        self.connection.write('*CLS')

    def trace(self, buffer, start, length=1):
        """Reads the points stored in the channel buffer.

        :param buffer: Selects the channel buffer (either 1 or 2).
        :param start: Selects the bin where the reading starts.
        :param length: The number of bins to read.

        .. todo::
           Use binary command TRCB to speed up data transmission.
        """
        query = 'TRCA? {0}, {1}, {2}'.format(buffer, start, length)
        result = self.connection.ask(query)
        return (float(f) for f in result.split())
