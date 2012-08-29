#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The ls340 module implements an interface for the Lakeshore model LS340
temperature controller.
"""

from slave.core import Command, InstrumentBase
from slave.types import Boolean, Enum, Float, Integer, Register, Set, String


class Loop(InstrumentBase):
    """Represents a LS340 control loop.

    :ivar filter: The loop filter state.
    :ivar limit: The limit configuration, represented by the following list
        *[<limit>, <pos slope>, <neg slope>, <max current>, <max range>]*
    :ivar manual_output: The manual output value.
    :ivar mode: The control-loop mode. Valid entries are
        *'manual', 'zone', 'open', 'pid', 'pi', 'p'*
    :ivar parameters: The control loop parameters, a list containing
        *[<input('A', 'B')>, <units('kelvin', 'celsius', 'sensor')>, <enabled>,
        <powerup>]*.
    :ivar pid: The PID values.
    :ivar ramp: The control-loop ramp parameters, represented by the following
        list *[<enabled>, <rate>]*, where
         * *<enabled>*  Enables, disables the ramping.
         * *<rate>* Specifies the ramping rate in kelvin/minute.
    :ivar ramping: The ramping status. `True` if ramping and `False` otherwise.
    :ivar setpoint: The control-loop setpoint in its configured units.

    """
    def __init__(self, connection, idx):
        super(Loop, self).__init__(connection)
        self.idx = idx = int(idx)
        self.filter = Command('CFILT? {0}'.format(idx),
                              'CFILT {0}'.format(idx),
                              Boolean)
        self.limit = Command('CLIMIT? {0}'.format(idx),
                             'CLIMIT {0}'.format(idx),
                             [Float, Float, Float,
                              Enum(0.25, 0.5, 1., 2., start=1),
                              Integer(min=0, max=5)])
        # TODO: check limits.
        self.manual_output = Command('MOUT? {0}'.format(idx),
                                     'MOUT {0}'.format(idx),
                                     Float(min=0, max=100))
        self.mode = Command('CMODE? {0}'.format(idx), 'CMODE {0}'.format(idx),
                            Enum('manual', 'zone', 'open', 'pid', 'pi', 'p',
                                 start=1))

        self.parameters = Command('CSET? {0}'.format(idx),
                                  'CSET {0}'.format(idx),
                                  [Set('A', 'B'),
                                   Enum('kelvin', 'celsius', 'sensor',
                                        start=1),
                                   Boolean,
                                   Boolean])
        self.pid = Command('PID? {0}'.format(idx), 'PID {0}'.format(idx),
                           [Float, Float, Float])
        self.ramp = Command('RAMP? {0}'.format(idx), 'RAMP {0}'.format(idx),
                            [Boolean, Float])
        self.ramping = Command(('RAMPST? {0}'.format(idx), Boolean))
        self.setpoint = Command('SETP? {0}'.format(idx),
                                'SETP {0}'.format(idx), Float)


class LS340(InstrumentBase):
    """
    Represents a Lakeshore model LS340 temperature controller.

    The LS340 class implements an interface to the Lakeshore model LS340
    temperature controller.

    :param connection: An object, modeling the connection interface, used to
        communicate with the real instrument.
    :ivar beeper: A boolean value representing the beeper state.
    :ivar idn: A list of strings representing the manufacturer, model number,
        serial number and firmware date in this order.
    :ivar mode: Represents the interface mode. Valid entries are
        *'local', 'remote', 'lockout'*.
    :ivar range: The heater range.
    :ivar loop1: An instance of the Loop class, representing the first control
        loop.
    :ivar loop2: Am instance of the Loop class, representing the second control
        loop.
    :ivar logging: A Boolean value, enabling or disabling data logging.

    """
    def __init__(self, connection):
        super(LS340, self).__init__(connection)
        # Common Commands
        # ===============
        self.idn = Command(('*IDN?', [String, String, String, String]))
        # Control Commands
        # ================
        self.loop1 = Loop(connection, 1)
        self.loop2 = Loop(connection, 2)
        self.range = Command('RANGE?', 'RANGE', Integer(min=0, max=5))
        # System Commands
        # ===============
        self.beeper = Command('BEEP?', 'BEEP', Boolean)
        self.mode = Command('MODE?', 'MODE',
                            Enum('local', 'remote', 'lockout', start=1))
        # Data Logging Commands
        # =====================
        self.logging = Command('LOG?', 'LOG', Boolean)

    def clear(self):
        """
        Clears the interface.

        The clear member function clears the status byte register, the standard
        event status register and all pending operations.
        """
        self.connection.write('*CLS')

    def reset(self):
        """Resets the lock-in to power up settings."""
        self.connection.write('*RST')

    def self_test(self):
        """Performs a self test operation.

        :returns: A boolean value, `True` if all tests passed and `False` if an
            error occurred.
        """
        return bool(int(self.connection.ask('*TST')))
