#  -*- coding: utf-8 -*-
#
# Slave, (c) 2015, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import time

from slave.driver import Driver, Command
from slave.types import String, Float, Enum
from slave.protocol import OxfordIsobus


class IPS120(Driver):
    """An Oxford Instruments IPS120-10 driver.
    
    E.g.::
    
        from slave.oxford import IPS120
        from slave.signal_recovery import SR7230
        from slave.transport import Serial, Socket
        from slave.misc import LockInMeasurement

        import numpy as np
        import time


        lia = SR7230(Socket(address=('transport-lia1.e21.frm2', 50000)))
        ips = IPS120(Serial(0, timeout=1, stopbits=2), address=2)

        ips.access_mode = 'remote unlocked'
        ips.activity = 'to zero'

        # Performs a manual stepscan from 0T to 1T and measures a voltage with a lockin amplifier.
        with LockInMeasurement('stepscan.csv', lockins=[lia], measurables=[lambda: ips.field.value]) as measure:
            fields = np.linspace(0, 1., 101)
            ips.field.sweep_rate = 1e-3

            ips.activity = 'to setpoint'
            for B in fields:
                ips.field.target = B

                # Wait until target field is reached.
                while ips.status['mode'] != 'at rest':
                    time.sleep(0.1)
                measure()

        # Performs a sweepscan from 1T to 0T and measures a voltage with a lockin amplifier.
        with LockInMeasurement('stepscan.csv', lockins=[lia], measurables=[lambda: ips.field.value]) as measure:
            ips.scan_field(measure, field=0, rate=0.2)

    :param transport: A transport object.
        
        .. note:: When using the serial interface, two stopbits must be used.
        
    :param address: The Oxford isobus address.
    
    :ivar access_mode: The access control mode. Valid modes are
        'local locked', 'remote locked', 'local unlocked'
        and 'remote unlocked'.
    :ivar activity: The current power supply activity. Valid are
        'hold', 'to setpoint', 'to zero' and 'clamped'.
    :ivar current: The current subsystem, an instance of :class:`~.Current`.
    :ivar field: The magnetic field subsystem, an instance of :class:`~.Field`.

    :ivar measured_current: The measured magnet current. (read-only)
    :ivar measured_voltage: The measured power supply voltage. (read-only)
    :ivar version: The firmware version. (read-only)
    
    """    
    STATUS = {
        u'0': 'normal',
        u'1': 'quenched',
        u'2': 'overheated',
        u'4': 'warming up',
        u'8': 'fault',
    }
    LIMIT = {
        u'0': 'normal',
        u'1': 'on positive voltage limit',
        u'2': 'on negative voltage limit',
        u'4': 'outside negative current limit',
        u'8': 'outside positive current limit',
    }
    ACCESS_MODE = [
        'local locked', 'remote locked', 'local unlocked', 'remote unlocked',
        'auto rundown', 'auto rundown', 'auto rundown', 'auto rundown'
    ]
    ACTIVITY = [
        'hold', 'to setpoint', 'to zero', 'unknown', 'clamped',
    ]
    HEATER = {
        u'0': 'switch closed, magnet at zero',
        u'1': 'switch open',
        u'2': 'off, magnet at field',
        u'5': 'heater fault',
        u'8': 'no switch fitted'
    }
    UNIT = {
        u'0': 'A, fast',
        u'1': 'T, fast',
        u'2': 'A, fast',
        u'3': 'T, fast',
        u'4': 'A, slow',
        u'5': 'T, slow',
        u'6': 'A, slow',
        u'7': 'T, slow',
    }
    MODE ={
        u'0': 'at rest',
        u'1': 'sweeping',
        u'2': 'sweep limiting',
        u'3': 'sweeping & sweep limiting'
    }
    
    def __init__(self, transport, address):
        super(IPS120, self).__init__(transport, OxfordIsobus(address=address))
        
        self.current = Current(self._transport, self._protocol)
        self.field = Field(self._transport, self._protocol)
        
        self.measured_current = Command(('R2', Float))
        self.measured_voltage = Command(('R1', Float))
        
        # TODO: version does not echo
        self.version = Command(
            ('V', String), 
            protocol=OxfordIsobus(address=address, echo=False)
        )

    @property
    def access_mode(self):
        return self.status['access_mode']
    
    @access_mode.setter
    def access_mode(self, mode):
        cmd = 'C', Enum(*self.ACCESS_MODE[:4])
        self._write(cmd, mode)

    @property
    def activity(self):
        return self.status['activity']
    
    @activity.setter
    def activity(self, value):
        cmd = 'A', Enum(*self.ACTIVITY)
        self._write(cmd, value)
        
    @property
    def status(self):
        response = self._protocol.query(self._transport, 'X')[0]
        return {
            'status': self.STATUS[response[0]],
            'limit': self.LIMIT[response[1]],
            'activity': self.ACTIVITY[int(response[3])],
            'access_mode': self.ACCESS_MODE[int(response[5])],
            'switch heater': self.HEATER[response[7]],
            'display unit': self.UNIT[response[9]],
            'mode': self.MODE[response[10]]
        }
        
    def set_field(self, target, rate, wait_for_stability=True):
        """Sets the field to the specified value.
        
        :param field: The target field in Tesla.
        :param rate: The field rate in tesla per minute.
        :param wait_for_stability: If True, the function call blocks until the
            target field is reached.
        
        """
        self.field.target = target
        self.field.sweep_rate = rate
        self.activity = 'to setpoint'
        while self.status['mode'] != 'at rest':
            time.sleep(1)
        
    def scan_field(self, measure, target, rate, delay=1):
        """Performs a field scan.

        Measures until the target field is reached.

        :param measure: A callable called repeatedly until stability at the
            target field is reached.
        :param field: The target field in Tesla.
        :param rate: The field rate in tesla per minute.
        :param delay: The time delay between each call to measure in seconds.

        :raises TypeError: if measure parameter is not callable.

        """
        if not hasattr(measure, '__call__'):
            raise TypeError('measure parameter not callable.')
        self.activity = 'hold'
        self.field.target = target
        self.field.sweep_rate = rate
        self.activity = 'to setpoint'
        while self.status['mode'] != 'at rest':
            measure()
            time.sleep(delay)


class Current(Driver):
    """The current subsystem.

    :ivar float sweep_rate: The current sweep rate in A/min.
    :ivar float target: The target current in A and a precission of
        0.0001 A.
    :ivar float value: The output current. (read-only)


    """
    def __init__(self, transport, protocol):
        super(Current, self).__init__(transport, protocol)
        
        self.sweep_rate = Command('R6', 'S', Float)
        self.target = Command('R5', 'I', Float(fmt='{:.4f}'))
        self.value = Command(('R0', Float))
        

class Field(Driver):
    """The magnetic field subsystem.
    
    :param transport: A transport object.
    :param protocol. A protocol object.
    
    :ivar float sweep_rate: The field sweep rate in T/min with a
        resolution of 0.0001 T/min (assuming extended resolution mode).
    :ivar float target: The target field in T.
    :ivar float value: The current field value. (read-only)

    """
    def __init__(self, transport, protocol):
        super(Field, self).__init__(transport, protocol)

        self.sweep_rate = Command('R9', 'T', Float(fmt='{:.4f}'))
        self.target = Command('R8', 'J', Float(max=9, min=-9, fmt='{:.5f}'))
        self.value = Command(('R7', Float))