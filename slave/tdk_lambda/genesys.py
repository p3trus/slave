#  -*- coding: utf-8 -*-
#
# Slave, (c) 2016, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

from slave.driver import Command, Driver
from slave.types import Boolean, Enum, Float, Integer, Mapping, Set, String


class Genesys(Driver):
    """A generic TDK Lambda Genesys power supply driver.

    E.g.::
    
        from slave.transport import Serial
        from slave.tdk_lambda import Gen750
        
        tdk = Gen750(Serial(0), address=6)
        tdk.address() # Tell this device to listen to cmd's
        
        tdk.target_current = 1
        tdk.output_mode = 'current'
    
    :param transport: A transport object.
    :param address: The device address in the range 0 to 30.

    .. rubric:: Initialisation Commands

    :ivar remote_mode: The device remote mode, either 'local',
        'remote' or 'lockout'.
    :ivar bool multi_drop: A boolean indicating if the
        multi-drop option is installed. (read-only)
    :ivar int master_slave: Returns the master/slave setting, where 0 means
        slave and 1, 2, 3 and 4 are masters. (read-only)
    
    .. rubric:: ID Control Commands
    
    :ivar identification: Returns two identification, strings. (read-only)
    :ivar str revision: Returns the firmware revision. (read-only)
    :ivar str serial: Returns the serial number. (read-only)
    :ivar str test_date: Returns the last testing date. (read-only)
        
    .. rubric:: Output Control Commands
    
    :ivar float target_voltage: The target output voltage.
    :ivar float output_voltage: The actual output voltage. (read-only)
    :ivar float target_current: The target output current.
    :ivar float output_current: The actual output current. (read-only)
    :ivar data: Returns the current and voltage data, a tuple of the form
        *(<output voltage>, <target voltage>, <output current>, <target current>*
        *<overvoltage>, <undervoltage>)*. (read-only)
    :ivar output_mode: The power supply output mode, either 'off',
        'current' or 'voltage'. (read-only)
    :ivar lowpass_filter: The AD converter lowpass setting used in
        current and voltage measurements. Valid are '18 Hz', '23 Hz'
        and '46 Hz.
    :ivar bool output: Enables/Disables the output.
    :ivar bool foldback_protection: Enables/Disables the foldback protection.
    :ivar float foldback_delay: The foldback delay, a float representing seconds
        from 0 to 25.5 in 0.1 increments
    :ivar bool auto_restart: Enables/Disables the auto restart.
    :ivar float over_voltage: The over voltage protection limit.
    :ivar float under_voltage: The under voltage limit.

    """
    REMOTE_MODE = ['local', 'remote', 'lockout']
    OUTPUT_MODE = {
        'off': 'OFF',
        'current': 'CC',
        'voltage': 'CV',
    }
    LOWPASS_FILTER = {
        '18 Hz': '18',
        '23 Hz': '23',
        '46 Hz': '46',
    }
    FOLDBACK_DELAY = {(i / 10.): i for i in range(256)}
        
    def __init__(self, transport, address=6):
        protocol = TDKLambda()
        super(Gen750W, self).__init__(transport, protocol)
        self._address = address
        
        ON_OFF = Mapping({True: 'ON', False: 'OFF'})

        # Initialisation Commands
        self.remote_mode = Command('RMT?', 'RMT', Enum(*self.REMOTE_MODE))
        self.multi_drop = Command(('MDAV?', Boolean))
        self.master_slave = Command(('MS?', Integer))
        
        # ID Control Commands
        self.identification = Command(('IDN?', [String, String]))
        self.revision = Command(('REV?', String))
        self.serial = Command(('SN?', String))
        self.test_date = Command(('DATE?', String))
        
        # Output Control Voltage
        self.target_voltage = Command('PV?', 'PV', Float)
        self.output_voltage = Command(('MV?', Float))
        self.target_current = Command('PC?', 'PC', Float)
        self.output_current = Command(('MC?', Float))
        self.data = Command(('DVC?', [Float] * 4))
        self.output_mode = Command(('MODE?', Mapping(self.OUTPUT_MODE)))
        self.lowpass_filter = Command(
            'FILTER?',
            'FILTER',
            Mapping(self.LOWPASS_FILTER)
        )
        self.output = Command('OUT?', 'OUT', ON_OFF)
        self.foldback_protection = Command('FLD?', 'FLD', ON_OFF)
        self.foldback_delay = Command(
            'FBD?',
            'FBD',
            Mapping(self.FOLDBACK_DELAY)
        )
        self.over_voltage = Command('OVP?', 'OVP', Float)
        self.under_voltage = Command('UVL?', 'UVL', Float)
        self.auto_restart = Command('AST?', 'AST', ON_OFF)
        
        
    def clear(self):
        """Clears the status.
        
        This clears the fault event register and the status event register.

        """
        self._write('CLS')
        
    def address(self):
        """Adresses this unit to listen.
        
        Each device must be addressed before commands can be sent.
        This allows multiple devices to share the same serial bus.

        E.g.::
        
            tdk1.address()
            # send some commands, only tdk1 responds.
            
            tdk2.address()
            # send commands to tdk2
        
        """
        # TODO: Move addressing into protocol.
        response = self._query(
            ('ADR', String, Integer(min=0, max=30)),
            self._address
        )
        return response

    def foldback_reset(self):
        """Resets the additional foldback delay to zero."""
        self._write('FBDRST')

    def max_overvoltage(self):
        """Set's the over voltage limit to maximum."""
        self._write('OVM')
        
    def reset(self):
        """Resets the device."""
        self._write('RST')
        
    def save(self):
        """Saves current settings."""
        self._write('SAV')
        
    def recall(self):
        """Recalls saved settings."""
        self._write('RCL')