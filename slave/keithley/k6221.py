#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from slave.core import Command, InstrumentBase
from slave.iec60488 import (IEC60488, Trigger, ObjectIdentification,
    StoredSetting)
from slave.types import Boolean, Enum, Float, Integer, Mapping


class Output(InstrumentBase):
    """A keithley 6221 output object.

    :param connection: A connection object.

    :ivar inner_shield: The inner shield connection, either 'output low' or
        'guard'.
    :ivar interlock: Represents the state of the interlock, either 'open' or
        'closed'.
    :ivar output_low: The output low connection, either 'float' or 'ground'.
    :ivar response: The output response mode, either 'fast' or 'slow'.

    """
    def __init__(self, connection):
        super(Output, self).__init__(connection)
        self.inner_shield = Command(
            'OUTP:ISH?',
            'OUTP:ISH',
            Mapping({'output low': 'OLOW', 'guard': 'GUAR'})
        )
        self.interlock = Command((
            'OUTP:INT:TRIP?',
            Enum('open', 'closed')
        ))
        self.output_low = Command(
            'OUTP:LTE?',
            'OUTP:LTE',
            Enum('float', 'ground')
        )
        self.response = Command(
            'OUTP:RESP?',
            'OUTP:RESP',
            Mapping({'fast': 'FAST', 'slow': 'SLOW'})
        )
        self.status = Command((
            'OUTP?',
            Enum('disabled', 'enabled')
        ))

    def enable(self):
        """Enables the output."""
        self.connection.write('OUTP 1')

    def disable(self):
        """Disables the output."""
        self.connection.write('OUTP 0')


class Current(InstrumentBase):
    """The current subgroup of the keithley 6221`Source command group.

    :param connection: A connection object.

    :ivar auto_range: A boolean representing the state of the current auto
        range.
    :ivar center: The center current, valid entries are -105e-3 to 105e-3.
    :ivar compliance: The voltage compliance in volt, valid are 0.1 to 105.
    :ivar filter: The state of the analog filter, a boolean.
    :ivar value: The current source output in ampere, valid entries are
        -105e-3 to 105e-3
    :ivar range: The current source output range, valid entries are
        -105e-3 to 105e-3. The keithley 6221 automatically determines the
        correct range.

        .. note::
            Using the manual current_range is normally not neccessary. Per
            default auto range is enabled in remote mode.

    :ivar span: The current span in ampere, valid entries are 2e-13 to 210e-3.
    :ivar start: The start current in ampere, valid are -105e-3 to
        105e-3.
    :ivar stop: The stop current in ampere, valid are -105e-3 to
        105e-3.
    :ivar step: The step current in ampere, valid are 1e-13 to 105e-3.


    """
    def __init__(self, connection):
        super(Current, self).__init__(connection)
        self.auto_range = Command(
            'SOUR:CURR::RANG:AUTO?',
            'SOUR:CURR::RANG:AUTO',
            Boolean
        )
        self.center = Command(
            'SOUR:CURR:CENT?',
            'SOUR:CURR:CENT',
            Float(min=-105e-3, max=105e-3)
        )
        self.compliance = Command(
            'SOUR:CURR:COMP?',
            'SOUR:CURR:COMP',
            Float(min=0.1, max=105.)
        )
        self.value = Command(
            'SOUR:CURR?',
            'SOUR:CURR',
            Float(min=-105e-3, max=105e-3)
        )
        self.range = Command(
            'SOUR:CURR:RANG?',
            'SOUR:CURR:RANG',
            Float(min=-105e-3, max=105e-3)
        )
        self.span = Command(
            'SOUR:CURR:SPAN?',
            'SOUR:CURR:SPAN',
            Float(min=2e-13, max=210e-3)
        )
        self.start = Command(
            'SOUR:CURR:STAR?',
            'SOUR:CURR:STAR',
            Float(min=-105e-3, max=105e-3)
        )
        self.stop = Command(
            'SOUR:CURR:STOP?',
            'SOUR:CURR:STOP',
            Float(min=-105e-3, max=105e-3)
        )
        self.step = Command(
            'SOUR:CURR:STEP?',
            'SOUR:CURR:STEP',
            Float(min=1e-13, max=105e-3)
        )
        self.filter = Command(
            'SOUR:CURR:FILT?',
            'SOUR:CURR:FILT',
            Boolean
        )


class Sweep(InstrumentBase):
    """The current subgroup of the keithley 6221`Source command group.

    :param connection: A connection object.

    :ivar compliance_abort: The state of the compliance abort, `True` if it's
        enabled, `False` otherwise.
    :ivar points: The number of sweep points, 1 to 65535.
    :ivar ranging: The sweep ranging mode, either 'auto', 'best' or 'fixed'.
    :ivar type: The sweep type, either 'linear', 'log' or 'custom'.

    """
    def __init__(self, connection):
        super(Sweep, self).__init__(connection)
        self.type = Command(
            'SOUR:SWE:SPAC?',
            'SOUR:SWE:SPAC',
            Mapping({'linear': 'LIN', 'log': 'LOG', 'custom': 'LIST'})
        )
        self.points = Command(
            'SOUR:SWE:POIN?',
            'SOUR:SWE:POIN',
            Integer(min=1, max=65535)
        )
        self.ranging(
            'SOUR:SWE:RANG?',
            'SOUR:SWE:RANG?',
            Mapping({'auto': 'AUTO', 'best': 'BEST', 'fixed': 'FIX'})
        )
        # TODO self.count = Command()
        self.compliance_abort = Command(
            'SOUR:SWE:CAB?',
            'SOUR:SWE:CAB',
            Boolean
        )

    def abort(self):
        """Abort sweep immediately."""
        self.connection.write('SOUR:SWE:ABOR')

    def arm(self):
        """Arm the sweep."""
        self.connection.write('SOUR:SWE:ARM')


class Source(InstrumentBase):
    """Represents the keithley 6221`Source command group.

    :param connection: A connection object.

    :ivar current: An instance of :class:`.Current`.
    :ivar delay: The source delay in seconds in the range 1e-3 to 999999.999.
    :ivar sweep: An instance of :class:`.Sweep`.

    """
    def __init__(self, connection):
        super(Source, self).__init__(connection)
        self.current = Current(connection)
        self.delay = Command(
            'SOUR:DEL?',
            'SOUR:DEL',
            Float(min=1e-3, max=999999.999)
        )
        self.sweep = Sweep(connection)

    def clear(self):
        self.connection.write('SOUR:CLE')


class K6221(IEC60488, Trigger, ObjectIdentification, StoredSetting):
    """The Keithley model 6221 ac/dc current source reference.

    :param connection: A connection object.

    :ivar output: An instance of :class:`.Output`.
    :ivar source: An instance of :class:`.Source`.

    """
    def __init__(self, connection):
        super(K6221, self).__init__(connection)
        self.output = Output(connection)
        self.source = Source(connection)

