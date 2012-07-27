#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, Integer, Mapping


class SR830(InstrumentBase):
    def __init__(self, connection):
        self.connection = connection

        # Reference and phase commands
        # ============================
        #: Sets and queries the reference phase
        self.phase = Command(connection, 'PHAS?', 'PHAS',
                             Float(min=-360., max=729.99))
        #: Sets or queries the internal reference frequency.
        self.frequency = Command(connection, 'FREQ?', 'FREQ',
                                 Float(min=0.001, max=102000.))
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

        # Setup commands
        # ==============
        #: Sets or queries the output interface
        self.output_interface = Command(connection, 'OUTX?', 'OUTX',
                                        Mapping({'RS232': 0, 'GPIB': 1}))
        #: Sets the remote mode override.
        self.overide_remote = Command(connection, write=('OVRM', Boolean))

        # Data storage commands
        # =====================
        self.sample_rate = Command(connection, 'SRAT?', 'SRAT',
                                   Integer(min=0, max=14))

        # Data transfer commands
        self.x = Command(connection, ('OUTP?1', Float))
        self.y = Command(connection, ('OUTP?2', Float))
        self.r = Command(connection, ('OUTP?3', Float))
        self.theta = Command(connection, ('OUTP?4', Float))

        self.channel1 = Command(connection, ('OUTR?1', Float))
        self.channel2 = Command(connection, ('OUTR?2', Float))

    def autogain(self):
        """Executes the auto gain command."""
        self.connection.ask('AGAN')

    def autoreserver(self):
        """Executes the auto reserver command."""
        self.connection.ask('ARSV')

    def autophase(self):
        """Executes the autophase command."""
        self.connection.ask('APHS')

    def trigger(self):
        """Emits a trigger event."""
        self.connection.ask('TRIG')

    def start(self):
        """Starts or resumes data storage."""
        self.connection.ask('STRT')

    def pause(self):
        """Pauses data storage."""
        self.connection.ask('PAUS')

    def reset_buffer(self):
        """Resets internal data buffers."""
        self.connection.ask('REST')

    def reset_configuration(self):
        """Resets the SR830 to it's default configuration."""
        self.connection.ask('*RST')
