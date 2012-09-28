Custom Device drivers
=====================

First steps
-----------

Implementing a custom device driver is straight forward. The code below shows a
simple class  supporting a single query and writeable command.
::

    from slave.core import Command, InstrumentBase
    from slave.types import Integer

    class CustomDevice(InstrumentBase):
        def __init__(self, connection):
            super(CustomDevice, self).__init__(connection) # Don't forget this!
            self.cmd = Command('QUERY?', 'WRITE', Integer)

The first step is deriving from :class:`~.slave.core.InstrumentBase`. It
applies some magic to redirect attribute read and write access to the 
:meth:`~.slave.core.Command.query` and :meth:`~.slave.core.Command.write`
methods of the :class:`~.salve.core.Command` class.

The next step is implementing the commands itself. This is done in the
`.__init__()` method via the :class:`~.slave.core.Command` class.

IEC 60488-2
-----------

The `IEC 60488-2`_ describes a standard digital interface for programmable
instrumentation. It is used by devices connected via the IEEE 488.1 bus,
commonly known as GPIB. It is an adoption of the *IEEE std. 488.2-1992*
standard.

The `IEC 60488-2`_ requires the existance of several commands which are
logically grouped.

Reporting Commands
 * `*CLS` - Clears the data status structure [#]_.
 * `*ESE` - Write the event status enable register [#]_.
 * `*ESE?` - Query the event status enable register [#]_.
 * `*ESR?` - Query the standard event status register [#]_.
 * `*SRE` - Write the status enable register [#]_.
 * `*SRE?` - Query the status enable register [#]_.
 * `*STB` - Query the status register [#]_.

Internal operation commands
 * `*IDN?` - Identification query [#]_.
 * `*RST` -  Perform a device reset [#]_.
 * `*TST?` - Perform internal self-test [#]_.

Synchronisation commands
 * `*OPC` - Set operation complete flag high [#]_.
 * `*OPC?` -  Query operation complete flag [#]_.
 * `*WAI` - Wait to continue [#]_.

To ease development, these are implemented in the
:class:`~.slave.ieee488.IEEE488` base class. To implement a `IEC 60488-2`_
compliant device driver, you only have to inherit from it and implement the
device specific commands, e.g::

    from slave.core import Command
    from slave.ieee488 import IEEE488

    class CustomDevice(IEEE488):
        pass

This is everything you need to do to implement the required `IEC 60488-2`_
command interface.

Optional Commands
^^^^^^^^^^^^^^^^^

Despite the required commands, there are several optional command groups
available. The standard requires that if one command is used, it's complete
group must be implemented. The optional commands are

Power on common commands
 * `*PSC` - Set the power-on status clear bit [#]_.
 * `*PSC?` - Query the power-on status clear bit [#]_.

The optional command groups are implemented as Mixin classes. A device
supporting required `IEC 60488-2`_ commands as well as the optional Power-on
commands is implemented as follows::

    from slave.core import Command
    from slave.ieee488 import IEEE488, PowerOn

    class CustomDevice(IEEE488, PowerOn):
        pass

.. rubric:: Footnotes

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

.. _IEC 60488-2: http://dx.doi.org/10.1109/IEEESTD.2004.95390
