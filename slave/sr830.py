#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, Integer, Mapping, String


class Aux(InstrumentBase):
    def __init__(self, connection, id):
        self.id = id = int(id)
        #: Queries the aux input voltages.
        self.input = Command(connection, 'OAUX? {}'.format(id))
        #: Sets and queries the output voltage.
        self.output = Command(connection, 'AUXV? {}'.format(id),
                              'AUXV {},'.format(id),
                              Float(min=-10.5, max=10.5))


class SR830(InstrumentBase):
    """
    Stanford Research SR830 Lock-In Amplifier instrument class.

    .. todo::
        Implementation of the DDEF, FPOP, OEXP, AOFF, TRCA, TRCB, ESE, ESR,
        SRE, STB, PSC, ERRE, ERRS, LIAE, LIAS commands.

    """
    def __init__(self, connection):
        """Constructs a SR830 instrument object.

        :param connection: Represents a hardware connection to the real
          instrument, e.g. a py-visa connection object.

        """
        self.connection = connection

        # Reference and phase commands
        # ============================
        #: Sets and queries the reference phase
        self.phase = Command(connection, 'PHAS?', 'PHAS',
                             Float(min=-360., max=729.99))
        #: Sets or queries the reference source
        self.reference = Command(connection, 'FMOD?', 'FMOD',
                                 Mapping({'external': 0, 'internal': 1}))
        #: Sets or queries the internal reference frequency.
        self.frequency = Command(connection, 'FREQ?', 'FREQ',
                                 Float(min=0.001, max=102000.))
        #: Sets or triggers the reference trigger mode.
        self.reference_trigger = Command(connection, 'RSLP?', 'RSLP',
                                         Mapping({'sine': 0,
                                                  'rise': 1,
                                                  'fall': 2}))
        #: Sets or queries the detection harmonic.
        self.harmonic = Command(connection, 'HARM?', 'HARM',
                                Integer(min=1, max=19999))
        #: Sets or queries the amplitude of the sine output.
        self.amplitude = Command(connection, 'SLVL?', 'SLVL',
                                 Float(min=0.004, max=5.))

        # Input and filter commands
        # =========================
        #: Sets or queries the input configuration.
        self.input = Command(connection, 'ISRC?', 'ISRC',
                             Mapping({'A': 0, 'A-B': 1, 'I': 2, 'I100': 3}))
        #: Sets or queries the input shield grounding.
        self.ground = Command(connection, 'IGND?', 'IGND', Boolean)
        #: Sets or queries the input coupling.
        self.coupling = Command(connection, 'ICPL?', 'ICPL',
                                Mapping({'AC': 0, 'DC': 1}))
        #: Sets or queries the input line notch filter status.
        self.filter = Command(connection, 'ILIN?', 'ILIN',
                              Mapping({'unfiltered': 0, 'notch': 1,
                                       '2xnotch': 2, 'both': 3}))

        # Gain and time constant commands
        # ===============================
        #: Sets or queries the sensitivity.
        self.sensitivity = Command(connection, 'SENS?', 'SENS',
                                   Integer(min=0, max=26))
        #: Sets or queries the dynamic reserve.
        self.reserve = Command(connection, 'RMOD?', 'RMOD',
                               Mapping({'high': 0, 'medium': 1, 'low': 2}))
        #: Sets or queries the time constant.
        self.time_constant = Command(connection, 'OFLT?', 'OFLT',
                                     Integer(min=0, max=19))
        #: Sets or queries the low-pass filter slope.
        self.slope = Command(connection, 'OFSL?', 'OFSL',
                             Integer(min=0, max=3))
        #: Sets or queries the synchronous filtering mode.
        self.sync = Command(connection, 'SYNC?', 'SYNC', Boolean)

        # Display and output commands
        # ===========================
        # TODO: DDEF, FPOP, OEXP, AOFF

        # Aux input and output commands
        # =============================
        for id in range(1, 5):
            setattr(self, 'aux{}'.format(id), Aux(connection, id))

        # Setup commands
        # ==============
        #: Sets or queries the output interface.
        self.output_interface = Command(connection, 'OUTX?', 'OUTX',
                                        Mapping({'RS232': 0, 'GPIB': 1}))
        #: Sets the remote mode override.
        self.overide_remote = Command(connection, write=('OVRM', Boolean))
        #: Sets or queries the key click state.
        self.key_click = Command(connection, 'KCLK?', 'KCLK', Boolean)
        #: Sets or queries the alarm state.
        self.alarm = Command(connection, 'ALRM?', 'ALRM', Boolean)

        # Data storage commands
        # =====================
        self.sample_rate = Command(connection, 'SRAT?', 'SRAT',
                                   Integer(min=0, max=14))
        #: The send command sets or queries the end of buffer mode.
        #: .. note::
        #:    If loop mode is used, the data storage should be paused to avoid
        #:    confusion about which point is the most recent.
        self.send_mode = Command(connection, 'SEND?', 'SEND',
                                 Mapping({'shot': 0, 'loop': 1}))

        # Data transfer commands
        # ======================
        #: Reads the value of x.
        self.x = Command(connection, ('OUTP? 1', Float))
        #: Reads the value of y.
        self.y = Command(connection, ('OUTP? 2', Float))
        #: Reads the value of r.
        self.r = Command(connection, ('OUTP? 3', Float))
        #: Reads the value of theta.
        self.theta = Command(connection, ('OUTP? 4', Float))
        #: Reads the value of channel 1.
        self.channel1 = Command(connection, ('OUTR? 1', Float))
        #: Reads the value of channel 2.
        self.channel2 = Command(connection, ('OUTR? 2', Float))
        #: Queries the number of data points stored in the internal buffer.
        self.data_points = Command(connection, ('SPTS?', Integer))
        #: Sets or queries the data transfer mode.
        #: .. note::
        #:    Do not use :class:`~SR830.start() to execute the scan, use
        #:    :class:`~SR830.delayed_start instead.
        self.fast_mode = Command(connection, 'FAST?', 'FAST',
                                 Mapping({'off': 0, 'DOS': 1, 'Windows': 2}))

        # Interface Commands
        # ==================
        #: Queries the device identification string
        self.idn = Command(connection, '*IDN?',
                           type=[String, String, String, String])
        #: Queries or sets the state of the frontpanel.
        self.state = Command(connection, 'LOCL?', 'LOCL',
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
        self.connection.ask('AOFF {}'.format(signals[signal]))

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
            self.connection.write('SSET {}'.format(id))
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
            self.connection.write('RSET {}'.format(id))

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
