Custom Device drivers
=====================

First steps
-----------

Implementing a custom device driver is straight forward. The code below shows a
simple class supporting a single query and writeable command.
::

    from slave.core import Command, InstrumentBase
    from slave.types import Integer

    class CustomDevice(InstrumentBase):
        def __init__(self, connection):
            super(CustomDevice, self).__init__(connection) # Don't forget this!
            self.cmd = Command('QUERY?', 'WRITE', Integer)

The first step is deriving from :class:`~.InstrumentBase`. It
applies some magic to redirect attribute read and write access to the 
:meth:`~.Command.query` and :meth:`~.Command.write` methods of the 
:class:`~.Command` class.

The next step is implementing the commands itself. This is done in the
`.__init__()` method via the :class:`~.Command` class.

The Command class
-----------------

The :class:`~.Command` class is at the heart of slave. It converts
user input into the appropriate command and parses the response.
The initializer takes five arguments, these are

 * query
 * write
 * type
 * connection
 * cfg

The usage is best shown by a simple example.
::

    from slave.core import Command, InstrumentBase
    from slave.types import Integer

    class CustomDevice(InstrumentBase):
        def __init__(self, connection):
            super(CustomDevice, self).__init__(connection)
            # A read only command, returning an integer.
            self.readable = Command('QUERY?', type=Integer())
            # A write only command, taking an integer.
            self.writeable = Command(write='WRITE', type=Integer(min=0, max=10))
            # A read and writeable command, taking and returning an integer.
            self.read_and_write = Command('QUERY?', 'WRITE', Integer)

So lets have a look at the readable attribute. 'QUERY?', the first argument of
the :class:`~.Command`, is the string sent to the instrument. `Integer`
specifies the return value. It is one of many special classes defined in the
:mod:`slave.types` module. These are responsible for parsing and validation of
the input and output. Similarly `writeable` is a write-only attribute, taking
an integer in the range 0 to 10.

Most of the time you can forget about connection and cfg. When using the
:class:`~.Command` as an instance variable, the :class:`~.InstrumentBase` base
class automatically injects the config and the connection object.

IEC 60488-2
-----------

The `IEC 60488-2`_ describes a standard digital interface for programmable
instrumentation. It is used by devices connected via the IEEE 488.1 bus,
commonly known as GPIB. It is an adoption of the *IEEE std. 488.2-1992*
standard.

The `IEC 60488-2`_ requires the existance of several commands which are
logically grouped.

Reporting Commands
 * `*CLS` - Clears the data status structure [#]_ .
 * `*ESE` - Write the event status enable register [#]_ .
 * `*ESE?` - Query the event status enable register [#]_ .
 * `*ESR?` - Query the standard event status register [#]_ .
 * `*SRE` - Write the status enable register [#]_ .
 * `*SRE?` - Query the status enable register [#]_ .
 * `*STB` - Query the status register [#]_ .

Internal operation commands
 * `*IDN?` - Identification query [#]_ .
 * `*RST` -  Perform a device reset [#]_ .
 * `*TST?` - Perform internal self-test [#]_ .

Synchronisation commands
 * `*OPC` - Set operation complete flag high [#]_ .
 * `*OPC?` -  Query operation complete flag [#]_ .
 * `*WAI` - Wait to continue [#]_ .

To ease development, these are implemented in the
:class:`~.IEEE488` base class. To implement a `IEC 60488-2`_
compliant device driver, you only have to inherit from it and implement the
device specific commands, e.g::

    from slave.core import Command
    from slave.iec60488 import IEC60488

    class CustomDevice(IEC60488):
        pass

This is everything you need to do to implement the required `IEC 60488-2`_
command interface.

Optional Commands
^^^^^^^^^^^^^^^^^

Despite the required commands, there are several optional command groups
defined. The standard requires that if one command is used, it's complete
group must be implemented. These are

Power on common commands
 * `*PSC` - Set the power-on status clear bit [#]_ .
 * `*PSC?` - Query the power-on status clear bit [#]_ .

Parallel poll common commands
 * `*IST?` - Query the individual status message bit [#]_ .
 * `*PRE` - Set the parallel poll enable register [#]_ .
 * `*PRE?` - Query the parallel poll enable register [#]_ .

Resource description common commands
 * `*RDT` - Store the resource description in the device [#]_ .
 * `*RDT?` - Query the stored resource description [#]_ .

Protected user data commands
 * `*PUD` - Store protected user data in the device [#]_ .
 * `*PUD?` - Query the protected user data [#]_ .

Calibration command
 * `*CAL?` - Perform internal self calibration [#]_ .

Trigger command
 * `*TRG` - Execute trigger command [#]_ .

Trigger macro commands
 * `*DDT` - Define device trigger [#]_ .
 * `*DDT?` - Define device trigger query [#]_ .

Macro Commands
 * `*DMC` - Define device trigger [#]_ .
 * `*EMC` - Define device trigger query [#]_ .
 * `*EMC?` - Define device trigger [#]_ .
 * `*GMC?` - Define device trigger query [#]_ .
 * `*LMC?` - Define device trigger [#]_ .
 * `*PMC` - Define device trigger query [#]_ .

Option Identification command
 * `*OPT?` - Option identification query [#]_ .

Stored settings commands
 * `*RCL` - Restore device settings from local memory [#]_ .
 * `*SAV` - Store current settings of the device in local memory [#]_ .

Learn command
 * `*LRN?` - Learn device setup query [#]_ .

System configuration commands
 * `*AAD` - Accept address command [#]_ .
 * `*DLF` - Disable listener function command [#]_ .

Passing control command
 * `*PCB` - Pass control back [#]_ .

The optional command groups are implemented as Mixin classes. A device
supporting required `IEC 60488-2`_ commands as well as the optional Power-on
commands is implemented as follows::

    from slave.core import Command
    from slave.iec60488 import IEC60488, PowerOn

    class CustomDevice(IEC60488, PowerOn):
        pass

----

.. [#] IEC 60488-2:2004(E) section 10.3
.. [#] IEC 60488-2:2004(E) section 10.10
.. [#] IEC 60488-2:2004(E) section 10.11
.. [#] IEC 60488-2:2004(E) section 10.12
.. [#] IEC 60488-2:2004(E) section 10.34
.. [#] IEC 60488-2:2004(E) section 10.35
.. [#] IEC 60488-2:2004(E) section 10.36
.. [#] IEC 60488-2:2004(E) section 10.14
.. [#] IEC 60488-2:2004(E) section 10.32
.. [#] IEC 60488-2:2004(E) section 10.38
.. [#] IEC 60488-2:2004(E) section 10.18
.. [#] IEC 60488-2:2004(E) section 10.19
.. [#] IEC 60488-2:2004(E) section 10.39
.. [#] IEC 60488-2:2004(E) section 10.25
.. [#] IEC 60488-2:2004(E) section 10.26
.. [#] IEC 60488-2:2004(E) section 10.15
.. [#] IEC 60488-2:2004(E) section 10.23
.. [#] IEC 60488-2:2004(E) section 10.24
.. [#] IEC 60488-2:2004(E) section 10.30
.. [#] IEC 60488-2:2004(E) section 10.31
.. [#] IEC 60488-2:2004(E) section 10.27
.. [#] IEC 60488-2:2004(E) section 10.28
.. [#] IEC 60488-2:2004(E) section 10.2
.. [#] IEC 60488-2:2004(E) section 10.37
.. [#] IEC 60488-2:2004(E) section 10.4
.. [#] IEC 60488-2:2004(E) section 10.5
.. [#] IEC 60488-2:2004(E) section 10.7
.. [#] IEC 60488-2:2004(E) section 10.8
.. [#] IEC 60488-2:2004(E) section 10.9
.. [#] IEC 60488-2:2004(E) section 10.13
.. [#] IEC 60488-2:2004(E) section 10.16
.. [#] IEC 60488-2:2004(E) section 10.22
.. [#] IEC 60488-2:2004(E) section 10.20
.. [#] IEC 60488-2:2004(E) section 10.29
.. [#] IEC 60488-2:2004(E) section 10.33
.. [#] IEC 60488-2:2004(E) section 10.17
.. [#] IEC 60488-2:2004(E) section 10.1
.. [#] IEC 60488-2:2004(E) section 10.6
.. [#] IEC 60488-2:2004(E) section 10.21

.. _IEC 60488-2: http://dx.doi.org/10.1109/IEEESTD.2004.95390
