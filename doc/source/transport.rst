.. _transport_object:

The transport object
=====================

The interface
-------------

Slave does not communicate with a device directly. It uses an object referred
to as *transport object*. This abstraction makes it possible to use the same
device drivers with different types of transports (e.g. rs232, GPIB, usb,
serial, ...). As long as an object conforms to the *transport interface* it
can be used with slave.

The interface is quite simple. Just two methods are required. They are defined
as follows:

.. py:method:: Transport.ask(command)

   Takes a command string and returns a string response.

.. py:method:: Transport.write(command)

   Takes a command string.

Adapters
--------

To enhance the compatibility with different communication libraries, the
:mod:`slave.transport` module implements several adapter classes.
These are

======================================  ======================================================  ===========
Class                                   Description                                             Notes
======================================  ======================================================  ===========
:class:`~slave.transport.GpibDevice`    A transport object wrapping the Linux-gpib driver.      Linux only
:class:`~slave.transport.TCPIPDevice`   A tiny wrapper around a socket transport.
:class:`~slave.transport.UsbTmcDevice`  A transport object, wrapping a usbtmc file descriptor.  Linux only
======================================  ======================================================  ===========

.. _simulated_transport:

Simulating a transport
-----------------------

Slave has a rudimentary simulation mode. Just use the
:class:`~slave.transport.SimulatedTransport` instead of an actual transport.
An example is shown below::

    from slave.transport import SimulatedTransport
    from slave.srs import SR380

    lockin = SR830(SimulatedTransport())
    print lockin.x  # prints a random float

A simple algorithm is used to create the responses.

For read-only commands, the response is randomly created with each query, since
these typically represent measured values. For read and writable commands, the
response is created just once and cached afterwards. Repeated queries will
return the same result unless a write was issued.

Implementing custom transports
-------------------------------
