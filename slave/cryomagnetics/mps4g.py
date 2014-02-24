#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
import string

from slave.core import Command, InstrumentBase
from slave.iec60488 import IEC60488
from slave.types import Boolean, Float, Mapping, Set, String


#: A list with all valid shim identifiers.
SHIMS = ['Z', 'Z2', 'Z3', 'Z4', 'X', 'Y', 'ZX', 'ZY', 'C2', 'S2', 'Z2X', 'Z2Y']


class UnitFloat(Float):
    """Represents a floating point type. If a unit is present in the string
    representation, it will get stripped.

    """
    def __convert__(self, value):
        """Converts value to Float."""
        if isinstance(value, basestring):
            value = value.rstrip(string.ascii_letters)
        return float(value)


class Range(InstrumentBase):
    """Represents a MPS4G current range.

    :param connection: A connection object.
    :param idx: The current range index. Valid values are 0, 1, 2, 3, 4.
    :ivar limit: The upper limit of the current range.
    :ivar rate: The sweep rate of this current range.

    """
    def __init__(self, connection, cfg, idx):
        super(Range, self).__init__(connection, cfg)
        self.idx = idx = int(idx)
        if not idx in range(0, 5):
            raise ValueError('Invalid range index.'
                             ' Must be one of {0}'.format(range(0, 5)))
        self.limit = Command('RANGE? {0}'.format(idx),
                             'RANGE {0} '.format(idx),
                             Float(fmt='{0:.4f}'))
        self.rate = Command('RATE? {0}'.format(idx),
                            'RATE {0}'.format(idx),
                            Float(min=1e-4, max=100., fmt='{0:.4f}'))


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
    def __init__(self, connection, cfg, shim):
        super(Shim, self).__init__(connection, cfg)
        if not shim in SHIMS:
            raise ValueError('Invalid shim identifier, '
                             'must be one of {0}'.format(SHIMS))
        self._shim = shim = str(shim)
        self.limit = Command('SLIM?', 'SLIM', Float(min=-30., max=30.))
        state = {
            True: '{0} Enabled'.format(shim),
            False: '{0} Disabled'.format(shim)
        }
        self.status = Command(('SHIM?', Mapping(state)))
        self.current = Command('IMAG? {0}'.format(shim),
                               'IMAG {0}'.format(shim), UnitFloat)

    def disable(self):
        """Disables the shim."""
        self._write('SHIM Disable {0}'.format(self._shim))

    def select(self):
        """Selects the shim as the current active shim."""
        self._write('SHIM {0}'.format(self._shim))


class MPS4G(IEC60488):
    """Represents the Cryomagnetics, inc. 4G Magnet Power Supply.

    :param connection: A connection object.
    :param channel: This parameter is used to set the MPS4G in single channel
        mode. Valid entries are `None`, `1` and `2`.

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

    .. warning::

        Due to a bug in firmware version 1.25, a semicolon must be appended to.
        the end of the commands `'LLIM'` and `'ULIM'`. This is done
        automatically. Writing the name crashes the MPS4G software. A restart
        does not fix the problem. You need to load the factory defaults.

    .. note::

        If something bad happens and the MPS4G isn't reacting, you can load the
        factory defaults via the simulation mode. To enter it press *SHIFT* and
        *5* on the front panel at startup.

    """
    def __init__(self, connection, shims=None, channel=None):
        stb = {
            0: 'sweep mode active',
            1: 'standby mode active',
            2: 'quench condition present',
            3: 'power module failure',
            7: 'menu mode',
        }
        if not channel in (None, 1, 2):
            raise ValueError('Invalid channel. Must be either None, 1 or 2.')
        if channel:
            # if single channel mode is required, set the channel on every
            # command to avoid errors.
            cfg = {'program header prefix': 'CHAN {0};'.format(channel)}
        else:
            cfg = {}
        super(MPS4G, self).__init__(connection, stb=stb, cfg=cfg)
        if shims:
            if isinstance(shims, basestring):
                shims = [shims]
            for shim in list(shims):
                setattr(self, str(shim), Shim(connection, self._cfg, shim))

        if channel:
            # Channel is read only if channel is fixed
            self.channel = Command(('CHAN?', Set(1, 2)))
        else:
            self.channel = Command('CHAN?', 'CHAN', Set(1, 2))

        self.error = Command('ERROR?', 'ERROR', Boolean)
        self.current = Command('IMAG?', 'IMAG', UnitFloat)
        self.output_current = Command(('IOUT?', UnitFloat))
        # Custom format string to fix bug in firmware. The `;` must be appended
        self.lower_limit = Command('LLIM?', 'LLIM', UnitFloat(fmt='{0:.4f};'))
        self.mode = Command(('MODE?', String))
        self.name = Command('NAME?', 'NAME', String)
        self.switch_heater = Command('PSHTR?', 'PSHTR',
                                     Mapping({True: 'ON', False: 'OFF'}))
        for idx in range(0, 5):
            rng = Range(connection, self._cfg, idx)
            setattr(self, 'range{0}'.format(idx), rng)
        # Custom format string to fix bug in firmware. The `;` must be appended
        self.upper_limit = Command('ULIM?', 'ULIM', UnitFloat(fmt='{0:.4f};'))
        self.unit = Command('UNITS?', 'UNITS', Set('A', 'G'))
        self.voltage_limit = Command('VLIM?', 'VLIM',
                                     UnitFloat(min=0., max=10.))
        self.magnet_voltage = Command(('VMAG?', UnitFloat(min=-10., max=10.)))
        self.output_voltage = Command(('VMAG?',
                                       UnitFloat(min=-12.8, max=12.8)))
        self.sweep_status = Command(('SWEEP?', String))

    def local(self):
        """Sets the front panel in local mode."""
        self._write('LOCAL')

    def remote(self):
        """Sets the front panel in remote mode."""
        self._write('REMOTE')

    def quench_reset(self):
        """Resets the quench condition."""
        self._write('QRESET')

    def locked(self):
        """Sets the front panel in locked remote mode."""
        self._write('RWLOCK')

    def disable_shims(self):
        """Disables all shims."""
        self._write('SHIM Disable All')

    def enable_shims(self):
        """Enables all shims."""
        self._write('SHIM Enable All')

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
            self._write('SWEEP {0}'.format(mode))
        else:
            self._write('SWEEP {0} {1}'.format(mode, speed))
