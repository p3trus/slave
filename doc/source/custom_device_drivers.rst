Implementing Custom Device Drivers
==================================

Implementing custom device drivers is straight forward. The following sections
will guide you through several use cases. We will implement a driver for an
imaginary device, extending it's interface step-by-step, showing more and more
functionallity and tricks.

.. note::

   When developing new device drivers, it is usefull to enable logging. See
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
        def __init__(self, connection):
            super(Device, self).__init__(connection)
            self.enabled = Command('ENABLED?', 'ENABLED', Boolean())

Now let's try it. We're using a :class:`~slave.core.SimulatedConnection` here (see
:ref:`simulated_connection` for a detailed explanation)::

    >>> from slave.core import SimulatedConnection
    >>> device = Device(SimulatedConnection())
    >>> device.enabled = False
    >>> device.enabled
    False

It looks as if an instance variable with the name 'enabled' and a value of
`False` was created. But this is not the case. We can check it with the
following line::

    >>> type(device.__dict__['enabled'])
    <class 'slave.core.Command'>

The assignement did not overwrite the Command attribute. Instead, the
:class:`~slave.core.InstrumentBase` base class forwarded the `False` to the
:meth:`~slave.core.Command.write` method of the :class:`~slave.core.Command`. The 
:meth:`~slave.core.Command.write` method then created the command message
**'ENABLED 0'**, using the :class:`~slave.types.Boolean` type to convert the
False and passed it to the connection's
:meth:`~slave.core.SimulatedConnection.write` method. Likewise the read call was
forwarded to the :class:`~slave.core.Command`'s query method. 

