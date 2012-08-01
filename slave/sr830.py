#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, Integer, Mapping, Set, String


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


class SR830(InstrumentBase):
    """
    Stanford Research SR830 Lock-In Amplifier instrument class.

    .. todo::
        Implementation of the FPOP, TRCA, TRCB, ESE, ESR,
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
                                 Mapping({'external': 0, 'internal': 1}))
        #: Sets or queries the internal reference frequency.
        self.frequency = Command('FREQ?', 'FREQ',
                                 Float(min=0.001, max=102000.))
        #: Sets or triggers the reference trigger mode.
        self.reference_trigger = Command('RSLP?', 'RSLP',
                                         Mapping({'sine': 0,
                                                  'rise': 1,
                                                  'fall': 2}))
        #: Sets or queries the detection harmonic.
        self.harmonic = Command('HARM?', 'HARM',
                                Integer(min=1, max=19999))
        #: Sets or queries the amplitude of the sine output.
        self.amplitude = Command('SLVL?', 'SLVL',
                                 Float(min=0.004, max=5.))

        # Input and filter commands
        # =========================
        #: Sets or queries the input configuration.
        self.input = Command('ISRC?', 'ISRC',
                             Mapping({'A': 0, 'A-B': 1, 'I': 2, 'I100': 3}))
        #: Sets or queries the input shield grounding.
        self.ground = Command('IGND?', 'IGND', Boolean)
        #: Sets or queries the input coupling.
        self.coupling = Command('ICPL?', 'ICPL',
                                Mapping({'AC': 0, 'DC': 1}))
        #: Sets or queries the input line notch filter status.
        self.filter = Command('ILIN?', 'ILIN',
                              Mapping({'unfiltered': 0, 'notch': 1,
                                       '2xnotch': 2, 'both': 3}))

        # Gain and time constant commands
        # ===============================
        #: Sets or queries the sensitivity.
        self.sensitivity = Command('SENS?', 'SENS',
                                   Integer(min=0, max=26))
        #: Sets or queries the dynamic reserve.
        self.reserve = Command('RMOD?', 'RMOD',
                               Mapping({'high': 0, 'medium': 1, 'low': 2}))
        #: Sets or queries the time constant.
        self.time_constant = Command('OFLT?', 'OFLT',
                                     Integer(min=0, max=19))
        #: Sets or queries the low-pass filter slope.
        self.slope = Command('OFSL?', 'OFSL',
                             Integer(min=0, max=3))
        #: Sets or queries the synchronous filtering mode.
        self.sync = Command('SYNC?', 'SYNC', Boolean)

        # Display and output commands
        # ===========================
        # TODO: FPOP
        disp1 = {'X': 0, 'R': 1, 'Xnoise': 2, 'AuxIn1': 3, 'AuxIn2': 4}
        ratio1 = {'none': 0, 'AuxIn1': 1, 'AuxIn2': 2}
        #: Set or query the channel 1 display settings.
        self.ch1_display = Command('DDEF? 1', 'DDEF 1',
                                   [Mapping(disp1), Mapping(ratio1)])

        disp2 = {'Y': 0, 'Theta': 1, 'Ynoise': 2, 'AuxIn3': 3, 'AuxIn4': 4}
        ratio2 = {'none': 0, 'AuxIn3': 1, 'AuxIn4': 2}
        #: Set or query the channel 2 display settings.
        self.ch2_display = Command('DDEF? 2', 'DDEF 2',
                                   [Mapping(disp2), Mapping(ratio2)])
        #: Sets the channel1 output.
        self.ch1_output = Command('FPOP? 1', 'FPOP 1,',
                                  Mapping({'CH1': 0, 'X': 1}))
        #: Sets the channel2 output.
        self.ch2_output = Command('FPOP? 2', 'FPOP 2,',
                                  Mapping({'CH2': 0, 'Y': 1}))
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
        self.output_interface = Command('OUTX?', 'OUTX',
                                        Mapping({'RS232': 0, 'GPIB': 1}))
        #: Sets the remote mode override.
        self.overide_remote = Command(write=('OVRM', Boolean))
        #: Sets or queries the key click state.
        self.key_click = Command('KCLK?', 'KCLK', Boolean)
        #: Sets or queries the alarm state.
        self.alarm = Command('ALRM?', 'ALRM', Boolean)

        # Data storage commands
        # =====================
        self.sample_rate = Command('SRAT?', 'SRAT',
                                   Integer(min=0, max=14))
        #: The send command sets or queries the end of buffer mode.
        #: .. note::
        #:    If loop mode is used, the data storage should be paused to avoid
        #:    confusion about which point is the most recent.
        self.send_mode = Command('SEND?', 'SEND',
                                 Mapping({'shot': 0, 'loop': 1}))

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
                                 Mapping({'off': 0, 'DOS': 1, 'Windows': 2}))

        # Interface Commands
        # ==================
        #: Queries the device identification string
        self.idn = Command('*IDN?',
                           type=[String, String, String, String])
        #: Queries or sets the state of the frontpanel.
        self.state = Command('LOCL?', 'LOCL',
                             Mapping({'local': 0, 'remote': 1, 'lockout': 2}))

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
          and 'CH2'.
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
