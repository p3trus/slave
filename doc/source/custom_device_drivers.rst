Implementing Custom Device Drivers
==================================

Implementing custom device drivers is straight forward. The following sections
will guide you through several use cases.

First Steps
-----------

In this tutorial we will implement a custom device driver for an imaginary
device. We will extend the interface step by step, showing more
and more functionallity and tricks.

Let's assume we've got a simple device supporting the following commands:

 * 'ENABLED <on/off>' -- Enables/disables the control loop of the device.
   *<on/off>* is either 0 or 1.
 * 'ENABLED?' -- returns <on/off>

A possible implementation could look like this::

    from slave.core import InstrumentBase
    from slave.types import Boolean

    class Device(InstrumentBase):
        def __init__(self, connection):
            super(Device, self).__init__(connection)
            self.enabled = Command('ENABLED?', 'ENABLED', Boolean())

Now let's use it (we're using a :class:`~slave.core.SimulatedConnection`, see
:ref:`simulated_connection` for a detailed explanation)::

  >>> from slave.core import SimulatedConnection
  >>> device = Device(SImulatedConnection())
  >>> device.enabled = False
  >>> device.enabled
  False

