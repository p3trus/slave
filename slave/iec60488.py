#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

"""
The iec60488 module implements a IEC 60488-2:2004(E) compliant interface.

The minimal required interface is implemented by the IEC60488 class. Optional
command groups a provided by mixin classes. They should not be used on their
own.

Usage::

    from slave.IEC60488 import IEC60488, PowerOn

    class CustomInstrument(IEC60488, PowerOn):
        '''A custom instrument compliant with the IEC 60488-2:2004(E),
        supporting the optional PowerOn commands.
        '''
        def __init__(self, connection):
            super(CustomInstrument, self).__init__(connection)
            # Implement custom commands.

"""
from slave.core import Command, InstrumentBase
from slave.types import Boolean, Integer, Register, String


STATUS_BYTE = {
    0: '0',
    1: '1',
    2: '2',
    3: '3',
    4: 'MAV',
    5: 'ESB',
    6: 'RQS',
    7: '7',
}

EVENT_STATUS_BYTE = {
    0: 'operation complete',
    1: 'request control',
    2: 'query error',
    3: 'device dependent error',
    4: 'execution error',
    5: 'command error',
    6: 'user request',
    7: 'power on',
}

PARALLEL_POLL_REGISTER = dict((i, str(i)) for i in range(8, 16))


def _construct_register(reg, default_reg):
    """Constructs a register dict."""
    if reg:
        x = dict((k, reg.get(k, d)) for k, d in default_reg.iteritems())
    else:
        x = dict(default_reg)
    # XXX invert dict because Register type uses inverted key, value pairs
    x = dict((v, k) for k, v in x.iteritems())
    return x


class IEC60488(InstrumentBase):
    """The IEC60488 class implements a IEC 60488-2:2004(E) compliant base
    class.

    :param connection: A connection object.
    :param esb: A dictionary mapping the 8 bit standard event status register.
        Integers in the range 0 to 7 are valid keys. If present they replace
        the default values.
    :param stb: A dictionary mapping the 8 bit status byte. Integers in the
        range 0 to 7 are valid keys. If present they replace the default
        values.
    :ivar event_status: A dictionary representing the 8 bit event status
        register.
    :ivar event_status_enable: A dictionary representing the 8 bit event status
        enable register.
    :ivar status: A dictonary representing the 8 bit status byte.
    :ivar status_enable: A dictionary representing the status enable register.
    :ivar operation_complete: The operation complete flag.
    :ivar identification: The device identification represented by the
        following tuple
        `(<manufacturer>, <model>, <serial number>, <firmware level>)`.

    A IEC 60488-2:2004(E) compliant interface must implement the following
    status reporting commands:

    * `*CLS` - See IEC 60488-2:2004(E) section 10.3
    * `*ESE` - See IEC 60488-2:2004(E) section 10.10
    * `*ESE?` - See IEC 60488-2:2004(E) section 10.11
    * `*ESR` - See IEC 60488-2:2004(E) section 10.12
    * `*SRE` - See IEC 60488-2:2004(E) section 10.34
    * `*SRE?` - See IEC 60488-2:2004(E) section 10.35
    * `*STB?` - See IEC 60488-2:2004(E) section 10.36

    In addition, the following internal operation common commands are required:

    * `*IDN?` - See IEC 60488-2:2004(E) section 10.14
    * `*RST` - See IEC 60488-2:2004(E) section 10.32
    * `*TST?` - See IEC 60488-2:2004(E) section 10.38

    Furthermore the following synchronisation commands are required:

    * `*OPC` - See IEC 60488-2:2004(E) section 10.18
    * `*OPC?` - See IEC 60488-2:2004(E) section 10.19
    * `*WAI` - See IEC 60488-2:2004(E) section 10.39

    """
    def __init__(self, connection, esb=None, stb=None, *args, **kw):
        super(IEC60488, self).__init__(connection, *args, **kw)
        self._esb = esb = _construct_register(esb, EVENT_STATUS_BYTE)
        self._stb = stb = _construct_register(stb, STATUS_BYTE)

        self.event_status = Command(('*ESR?', Register(esb)))
        self.event_status_enable = Command('*ESE?', '*ESE', Register(esb))
        self.status = Command(('*STB?', Register(stb)))
        self.operation_complete = Command(('*OPC?', Boolean))
        self.identification = Command(('*IDN?',
                                       [String, String, String, String]))

    def clear(self):
        """Clears the status data structure."""
        self.connection.write('*CLS')

    def complete_operation(self):
        """Sets the operation complete bit high of the event status byte."""
        self.connection.write('*OPC')

    def reset(self):
        """Performs a device reset."""
        self.connection.write('*RST')

    def test(self):
        """Performs a internal self-test and returns an integer in the range
        -32767 to + 32767.
        """
        return int(self.connection.ask('*TST?'))

    def wait_to_continue(self):
        """Prevents the device from executing any further commands or queries
        until the no operation flag is `True`.

        .. note::

           In devices implementing only sequential commands, the no-operation
           flag is always True.

        """
        self.connection.write('*WAI')


class PowerOn(object):
    """A mixin class, implementing the optional power-on common commands.

    :ivar poweron_status_clear: Represents the power-on status clear flag. If
        it is `False` the event status enable, service request enable and
        serial poll enable registers will retain their status when power is
        restored to the device and will be cleared if it is set to `True`.

    .. note:: This is a mixin class designed to work with the IEC60488 class

    The IEC 60488-2:2004(E) defines the following optional power-on common
    commands:

    * `*PSC` - See IEC 60488-2:2004(E) section 10.25
    * `*PSC?` - See IEC 60488-2:2004(E) section 10.26

    """
    def __init__(self, *args, **kw):
        super(PowerOn, self).__init__(*args, **kw)
        self.poweron_status_clear = Command('*PSC?', '*PSC', Boolean)


class ParallelPoll(object):
    """A mixin class, implementing the optional parallel poll common commands.

    :param ppr: A dictionary mapping the 8-16 bit wide parallel poll register.
        Integers in the range 8 to 15 are valid keys. If present they replace
        the default values.
    :ivar individual_status: Represents the state of the IEEE 488.1 "ist" local
        message in the device.
    :ivar parallel_poll_enable: A dictionary representing the 16 bit parallel
        poll enable register.

    .. note:: This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional parallel poll common
    commands:

    * `*IST?` - See IEC 60488-2:2004(E) section 10.15
    * `*PRE` - See IEC 60488-2:2004(E) section 10.23
    * `*PRE?` - See IEC 60488-2:2004(E) section 10.24

    These are mandatory for devices implementing the PP1 subset.

    """
    def __init__(self, ppr=None, *args, **kw):
        super(ParallelPoll, self).__init__(*args, **kw)
        ppr = _construct_register(ppr, PARALLEL_POLL_REGISTER)
        # The first 8 bits represent the status byte.
        ppr.update(self._stb)
        self._ppr = ppr
        self.parallel_poll_enable = Command('*PRE?', 'PRE', Register(ppr))
        self.individual_status = Command(('*IST?', Boolean))


class ResourceDescription(object):
    """A mixin class, implementing the optional resource description common
    commands.

    :ivar resource_description: Represents the content of the resource
        description memory.

        .. note:: Writing does not perform any validation.

    .. note:: This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional resource description
    common commands:

    * `*RDT` - See IEC 60488-2:2004(E) section 10.30
    * `*RDT?` - See IEC 60488-2:2004(E) section 10.31

    """
    def __init__(self, *args, **kw):
        super(ResourceDescription, self).__init__(*args, **kw)
        self.resource_description = Command('*RDT?', '*RDT', String)


class ProtectedUserData(object):
    """A mixin class, implementing the protected user data commands.

    :ivar protected_user_data: The protected user data. This is information
        unique to the device, such as calibration date, usage time,
        environmental conditions and inventory control numbers.

    .. note:: This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional protected user data
    commands:

    * `*RDT` - See IEC 60488-2:2004(E) section 10.27
    * `*RDT?` - See IEC 60488-2:2004(E) section 10.28

    """
    def __init__(self, *args, **kw):
        super(ProtectedUserData, self).__init__(*args, **kw)
        self.protected_user_data = Command('*RDT?', 'RDT', String)


class Calibration(object):
    """A mixin class, implementing the optional calibration command.

    :ivar protected_user_data: The protected user data. This is information
        unique to the device, such as calibration date, usage time,
        environmental conditions and inventory control numbers.

    .. note:: This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional calibration command:

    * `*CAL?` - See IEC 60488-2:2004(E) section 10.2

    """
    def __init__(self, *args, **kw):
        super(Calibration, self).__init__(*args, **kw)

    def calibrate(self):
        """Performs a internal self-calibration.

        :returns: An integer in the range -32767 to + 32767 representing the
            result. A value of zero indicates that the calibration completed
            without errors.

        """
        return int(self.connection.ask('*CAL?'))


class Trigger(object):
    """A mixin class, implementing the optional trigger command.

    :ivar protected_user_data: The protected user data. This is information
        unique to the device, such as calibration date, usage time,
        environmental conditions and inventory control numbers.

    .. note:: This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional trigger command:

    * `*TRG` - See IEC 60488-2:2004(E) section 10.37

    It is mandatory for devices implementing the DT1 subset.

    """
    def __init__(self, *args, **kw):
        super(Trigger, self).__init__(*args, **kw)

    def trigger(self):
        """Creates a trigger event.

        .. note::

            It first tries to execute `connection.trigger()`. If this fails,
            the `*TRG` is sent.

        """
        try:
            self.connection.trigger()
        except AttributeError:
            self.connection.write('*TRG')


class TriggerMacro(object):
    """A mixin class, implementing the optional trigger macro commands.

    :ivar trigger_macro: The trigger macro, e.g. `'#217TRIG WFM;MEASWFM?'`.

    .. note::

        This is a mixin class designed to work with the IEC60488 class
        and the Trigger mixin.

    The IEC 60488-2:2004(E) defines the following optional trigger macro
    commands:

    * `*DDT` - See IEC 60488-2:2004(E) section 10.4
    * `*DDT?` - See IEC 60488-2:2004(E) section 10.5

    """
    def __init__(self, *args, **kw):
        super(TriggerMacro, self).__init__(*args, **kw)
        self.trigger_macro = Command('*DDT?', '*DDT', String)


class Macro(object):
    """A mixin class, implementing the optional macro commands.

    :ivar macro_commands_enabled: Enables or disables the expansion of macros.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional macro commands:

    * `*DMC` - See IEC 60488-2:2004(E) section 10.7
    * `*EMC` - See IEC 60488-2:2004(E) section 10.8
    * `*EMC?` - See IEC 60488-2:2004(E) section 10.9
    * `*GMC?` - See IEC 60488-2:2004(E) section 10.13
    * `*LMC?` - See IEC 60488-2:2004(E) section 10.16
    * `*PMC` - See IEC 60488-2:2004(E) section 10.22

    """
    def __init__(self, *args, **kw):
        super(Macro, self).__init__(*args, **kw)
        self.macro_commands_enabled = Command(('*EMC?', Boolean))

    def define_macro(self, macro):
        """Executes the define macro command.

        :param macro: A macro string, e.g.
            `'"SETUP1",#221VOLT 14.5;CURLIM 2E-3'`

            .. note:: The macro string is not validated.

        """
        self.connection.write('*DMC {0}'.format(macro))

    def disable_macro_commands(self):
        """Disables all macro commands."""
        self.connection.write('*EMC 0')

    def enable_macro_commands(self):
        """Enables all macro commands."""
        self.connection.write('*EMC 1')

    def get_macro(self, label):
        """Returns the macro.

        :param label: The label of the requested macro.

        """
        return str(self.connection.write('*GMC? {0}'.format(label)))

    def macro_labels(self):
        """Returns the currently defined macro labels."""
        return str(self.connection.ask('*LMC?'))

    def purge_macros(self):
        """Deletes all previously defined macros."""
        self.connection.write('*PMC')


class ObjectIdentification(object):
    """A mixin class, implementing the optional object identification command.

    :ivar object_identification: Identifies reportable device options.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional object
    identification command:

    * `*OPT?` - See IEC 60488-2:2004(E) section 10.20

    """
    def __init__(self, *args, **kw):
        super(ObjectIdentification, self).__init__(*args, **kw)
        self.macro_commands_enabled = Command(('*OPT?', String))


class StoredSetting(object):
    """A mixin class, implementing the optional stored setting commands.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional stored setting
    commands:

    * `*RCL` - See IEC 60488-2:2004(E) section 10.29
    * `*SAV` - See IEC 60488-2:2004(E) section 10.33

    """
    def __init__(self, *args, **kw):
        super(StoredSetting, self).__init__(*args, **kw)
        self.__recall = Command(write=('*RCL', Integer(min=0)))
        self.__save = Command(write=('*SAV', Integer(min=0)))

    def recall(self, idx):
        """Restores the current settings from a copy stored in local memory.

        :param idx: Specifies the memory slot.

        """
        self.__recall = idx

    def save(self, idx):
        """Stores the current settings of a device in local memory.

        :param idx: Specifies the memory slot.

        """
        self.__save = idx


class Learn(object):
    """A mixin class, implementing the optional learn command.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional learn command:

    * `*LRN?` - See IEC 60488-2:2004(E) section 10.17

    """
    def __init__(self, *args, **kw):
        super(Learn, self).__init__(*args, **kw)

    def learn(self):
        """Executes the learn command.

        :returns: A string containing a sequence of *response message units*.
            These can be used as *program message units* to recover the state
            of the device at the time this command was executed.

        """
        return str(self.connection.ask('*LRN?'))


class SystemConfiguration(object):
    """A mixin class, implementing the optional system configuration commands.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional system configuration
    commands:

    * `*AAD` - See IEC 60488-2:2004(E) section 10.1
    * `*DLF` - See IEC 60488-2:2004(E) section 10.6

    """
    def __init__(self, *args, **kw):
        super(SystemConfiguration, self).__init__(*args, **kw)

    def accept_address(self):
        """Executes the accept address command."""
        self.connection.write('*AAD')

    def disable_listener(self):
        """Executes the disable listener command."""
        self.connection.write('*DLF')


class PassingControl(object):
    """A mixin class, implementing the optional passing control command.

    .. note::This is a mixin class designed to work with the IEC60488 class.

    The IEC 60488-2:2004(E) defines the following optional passing control
    command:

    * `*PCB` - See IEC 60488-2:2004(E) section 10.21

    """
    def __init__(self, *args, **kw):
        super(PassingControl, self).__init__(*args, **kw)

    def pass_control_back(self, primary, secondary):
        """The address to which the controll is to be passed back.

        Tells a potential controller device the address to which the control is
        to be passed back.

        :param primary: An integer in the range 0 to 30 representing the
            primary address of the controller sending the command.
        :param secondary: An integer in the range of 0 to 30 representing the
            secondary address of the controller sending the command. If it is
            missing, it indicates that the controller sending this command does
            not have extended addressing.

        """
        if secondary is None:
            cmd = Command(write=('*PCB', Integer(min=0, max=30)),
                          connection=self.connection)
            cmd.write(primary)
        else:
            type_ = [Integer(min=0, max=30), Integer(min=0, max=30)]
            cmd = Command(write=('*PCB', type_),
                          connection=self.connection)
            cmd.write((primary, secondary))
