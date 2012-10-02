#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
from slave.types import Boolean, Float, Mapping, Register, Set, String


#: A list with all valid shim identifiers.
SHIMS = ['Z', 'Z2', 'Z3', 'Z4', 'X', 'Y', 'ZX', 'ZY', 'C2', 'S2', 'Z2X', 'Z2Y']


class Range(InstrumentBase):
    """Represents a MPS4G current range.

    :param connection: A connection object.
    :param idx: The current range index. Valid values are 0, 1, 2, 3, 4.
    :ivar limit: The upper limit of the current range.
    :ivar rate: The sweep rate of this current range.

    """
    def __init__(self, connection, idx):
        super(Range, self).__init__(connection)
        self.idx = idx = int(idx)
        if not idx in range(0, 5):
            raise ValueError('Invalid range index.'
                             ' Must be one of {0}'.format(range(0, 5)))
        self.limit = Command('RANGE? {0}'.format(idx),
                             'RANGE {0} '.format(idx),
                             Float)
        self.rate = Command('RATE? {0}'.format(idx),
                            'RATE {0}'.format(idx),
                            Float)


class Shim(InstrumentBase):
    """Represents a Shim option of the 4GMPS.

    :param connection: A connection object.
    :param shim: The identifier of the shim.

    :ivar limit: The current limit of the shim.
    :ivar status: Represents the shim status, `True` if it's enabled, `False`
        otherwise.
    :ivar current: The magnet current of the shim. Queriing returns a value,
        unit tuple. While setting the current, the unit is omited. The value
        must be supplied in the configured units (ampere, kilo gauss).

    """
    def __init__(self, connection, shim):
        super(Shim, self).__init__(connection)
        if not shim in SHIMS:
            raise ValueError('Invalid shim identifier, '
                             'must be one of {0}'.format(SHIMS))
        self._shim = shim = str(shim)
        self.limit = Command('SLIM?', 'SLIM', Float(min=-30., max=30.))
        state = {
            True: '{0} Enabled'.format(shim),
            False: '{0} Disabled'.format(shim)
        }
        self.status = Command(('SHIM?',
                               Mapping(state)))
        self.current = Command(('IMAG? {0}'.format(shim), [Float, String]),
                               ('IMAG {0}'.format(shim), Float))

    def disable(self):
        """Disables the shim."""
        self.connection.write('SHIM Disable {0}'.format(self._shim))

    def select(self):
        """Selects the shim as the current active shim."""
        self.connection.write('SHIM {0}'.format(self._shim))


class MPS4G(InstrumentBase):
    """Represents the Cryomagnetics, inc. 4G Magnet Power Supply.

    :param connection: A connection object.
    :ivar channel: The selected channel.
    :ivar error: The error response mode of the usb interface.
    :ivar current: The magnet current.Queriing returns a value, unit tuple.
        While setting the current, the unit is omited. The value must be
        supplied in the configured units (ampere, kilo gauss).
    :ivar output_current: The power supply output current.
    :ivar lower_limit: The lower current limit. Queriing returns a value, unit
        tuple. While setting the lower current limit, the unit is omited. The
        value must be supplied in the configured units (ampere, kilo gauss).
    :ivar mode: The selected operation mode, either `'Shim'` or `'Manual'`.
    :ivar name: The name of the currently selected coil. The length of the name
        is in the range of 0 to 16 characters.
    :ivar switch_heater: The state of the persistent switch heater. If `True`
        the heater is switched on and off otherwise.
    :ivar upper_limit: The upper current limit. Queriing returns a value, unit
        tuple. While setting the upper current limit, the unit is omited. The
        value must be supplied in the configured units (ampere, kilo gauss).
    :ivar unit: The unit used for all input and display operations. Must be
        either `'A'` or `'G'` meaning Ampere or Gauss.
    :ivar voltage_limit: The output voltage limit. Must be in the range of 0.00
        to 10.00.
    :ivar magnet_voltage: The magnet voltage in the range -10.00 to 10.00.
    :ivar magnet_voltage: The output voltage in the range -12.80 to 12.80.
    :ivar standard_event_status: The standard event status register.
    :ivar standard_event_status_enable: The standard event status enable
        register.
    :ivar id: The identification, represented by the following tuple
        *(<manufacturer>, <model>, <serial>, <firmware>, <build>)*
    :ivar operation_completed: The operation complete bit.
    :ivar status: The status register.
    :ivar service_request_enable: The service request enable register.
    :ivar sweep_status: A string representing the current sweep status.

    """
    def __init__(self, connection, shims=None):
        super(MPS4G, self).__init__(connection)
        if shims:
            if isinstance(shims, basestring):
                shims = [shims]
            for shim in list(shims):
                setattr(self, str(shim), Shim(connection, shim))

        self.channel = Command('CHAN?', 'CHAN', Set(1, 2))
        self.error = Command('ERROR?', 'ERROR', Boolean)
        self.current = Command(('IMAG?', [Float, String]),
                               ('IMAG', Float))
        self.output_current = Command(('IOUT?', [Float, String]))
        self.lower_limit = Command(('LLIM?', [Float, String]),
                                   ('LLIM', Float))
        self.mode = Command(('MODE?', String))
        self.name = Command('NAME?', 'NAME', String)
        self.switch_heater = Command('PSHTR?', 'PSHTR',
                                     Mapping({True: 'ON', False: 'OFF'}))
        for idx in range(0, 5):
            setattr(self, 'range{0}'.format(idx), Range(connection, idx))
        self.upper_limit = Command(('ULIM?', [Float, String]),
                                   ('ULIM', Float))
        self.unit = Command('UNITS?', 'UNITS', Set('A', 'G'))
        self.voltage_limit = Command('VLIM?', 'VLIM', Float(min=0., max=10.))
        self.magnet_voltage = Command(('VMAG?', Float(min=-10., max=10.)))
        self.output_voltage = Command(('VMAG?', Float(min=-12.8, max=12.8)))
        ESR = Register({'operation complete': 0,
                        'request control': 1,
                        'query error': 2,
                        'device error': 3,
                        'execution error': 4,
                        'command error': 5,
                        'user request': 6,
                        'power on': 7})
        self.standard_event_status = Command(('*ESR?', ESR))
        self.standard_event_status_enable = Command('*ESE?', '*ESE', ESR)
        self.id = Command(('*IDN?', [String, String, String, String, String]))
        self.operation_completed = (('*OPC?', Boolean))
        STB = Register({'sweep mode active': 0,
                        'standby mode active': 1,
                        'quench condition present': 2,
                        'power module failure': 3,
                        'message available': 4,
                        'extended status byte': 5,
                        'master summary status': 6,
                        'menu mode': 7})
        self.status = Command(('*STB?', STB))
        self.service_request_enable = Command('*SRE?', '*SRE', STB)
        self.sweep_status = Command(('SWEEP?', String))

    def clear(self):
        """Clears the status."""
        self.connection.write('*CLS')

    def local(self):
        """Sets the front panel in local mode."""
        self.connection.write('LOCAL')

    def remote(self):
        """Sets the front panel in remote mode."""
        self.connection.write('REMOTE')

    def quench_reset(self):
        """Resets the quench condition."""
        self.connection.write('QRESET')

    def locked(self):
        """Sets the front panel in locked remote mode."""
        self.connection.write('RWLOCK')

    def complete_operation(self):
        """
        Sets the operation complete bit in the standard event status register.
        """
        self.connection.write('*OPC')

    def reset(self):
        """Resets the instrument.

        Implemented for compliance with IEEE Std 488.2-1992, but does not
        change the power supply operation due to safety concerns.

        """
        self.connection.write('*RST')

    def test(self):
        """Queries the self test.

        Implemented for compliance with IEEE Std 488.2-1992, but does not
        change the power supply operation due to safety concerns.

        """
        return bool(self.connection.ask('*TST?'))

    def wait_to_continue(self):
        """The wait to continue command.

        Implemented for compliance with IEEE Std 488.2-1992, but since the
        4GMPS only implements sequential commands, the no-operation pending
        flag is always `True`.

        """
        self.connection.write('*WAI')

    def disable_shims(self):
        """Disables all shims."""
        self.connection.write('SHIM Disable All')

    def enable_shims(self):
        """Enables all shims."""
        self.connection.write('SHIM Enable All')

    def sweep(self, mode, speed=None):
        """Starts the output current sweep.

        :param mode: The sweep mode. Valid entries are `'UP'`, `'DOWN'`,
            `'PAUSE'`or `'ZERO'`. If in shim mode, `'LIMIT'` is valid as well.
        :param speed: The sweeping speed. Valid entries are `'FAST'`, `'SLOW'`
            or `None`.

        """
        sweep_modes = ['UP', 'DOWN', 'PAUSE', 'ZERO', 'LIMIT']
        sweep_speed = ['SLOW', 'FAST', None]
        if not mode in sweep_modes:
            raise ValueError('Invalid sweep mode.')
        if not speed in sweep_speed:
            raise ValueError('Invalid sweep speed.')
        if speed is None:
            self.connection.write('SWEEP {0}'.format(mode))
        else:
            self.connection.write('SWEEP {0} {1}'.format(mode, speed))