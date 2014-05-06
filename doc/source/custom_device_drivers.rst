Implementing Custom Device Drivers
==================================

Implementing custom device drivers is straight forward. The following sections
will guide you through several use cases. We will implement a driver for an
imaginary device, extending it's interface step-by-step, showing more and more
functionality and tricks.

.. note::

   When developing new device drivers, it is useful to enable logging. See
   :ref:`logging` for more information.

First Steps
-----------

Let's assume we've got a simple device supporting the following commands:

 * 'ENABLED <on/off>' -- Enables/disables the control loop of the device.
   *<on/off>* is either 0 or 1.
 * 'ENABLED?' -- returns <on/off>

A possible implementation could look like this::

    from slave.core import Command, InstrumentBase
    from slave.types import Boolean

    class Device(InstrumentBase):
        def __init__(self, transport):
            super(Device, self).__init__(transport)
            self.enabled = Command('ENABLED?', 'ENABLED', Boolean())

Now let's try it. We're using a :class:`~slave.core.SimulatedTransport` here (see
:ref:`simulated_transport` for a detailed explanation)::

    >>> from slave.core import SimulatedTransport
    >>> device = Device(SimulatedTransport())
    >>> device.enabled = False
    >>> device.enabled
    False

It looks as if an instance variable with the name 'enabled' and a value of
`False` was created. But this is not the case. We can check it with the
following line::

    >>> type(device.__dict__['enabled'])
    <class 'slave.core.Command'>

The assignment did not overwrite the Command attribute. Instead, the
:class:`~slave.core.InstrumentBase` base class forwarded the `False` to the
:meth:`~slave.core.Command.write` method of the :class:`~slave.core.Command`. The 
:meth:`~slave.core.Command.write` method then created the command message
**'ENABLED 0'**, using the :class:`~slave.types.Boolean` type to convert the
False and passed it to the transport's
:meth:`~slave.core.SimulatedTransport.write` method. Likewise the read call was
forwarded to the :class:`~slave.core.Command`'s query method.

The IEC60488-2 standard
-----------------------

The `IEC 60488-2`_ describes a standard digital interface for programmable
instrumentation. It is used by devices connected via the IEEE 488.1 bus,
commonly known as GPIB. It is an adoption of the *IEEE std. 488.2-1992*
standard.

The `IEC 60488-2`_ requires the existence of several commands which are
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

Synchronization commands
 * `*OPC` - Set operation complete flag high [#]_ .
 * `*OPC?` -  Query operation complete flag [#]_ .
 * `*WAI` - Wait to continue [#]_ .

To ease development, these are implemented in the
:class:`~slave.iec60488.IEC60488` base class. To implement a `IEC 60488-2`_
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

The optional command groups are implemented as Mix-in classes. A device
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
