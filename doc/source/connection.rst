.. _connection_object:

The connection object
=====================

The interface
-------------

Slave does not communicate with a device directly. It uses an object referred
to as *connection object*. This abstraction makes it possible to use the same
device drivers with different types of connections (e.g. rs232, GPIB, usb,
serial, ...). As long as an object conforms to the *connection interface* it
can be used with slave.

The interface is quite simple. Just two methods are required. They are defined
as follows:

.. py:method:: Connection.ask(command)

   Takes a command string and returns a string response.

.. py:method:: Connection.write(command)

   Takes a command string.

Adapters
--------

To enhance the compatibility with different communication libraries, the
:mod:`slave.connection` module implements several adapter classes.
These are

=======================================  =======================================================  ===========
Class                                    Description                                              Notes
=======================================  =======================================================  ===========
:class:`~slave.connection.GpibDevice`    A connection object wrapping the linux-gpib driver.      linux only
:class:`~slave.connection.TCPIPDevice`   A tiny wrapper around a socket connection.
:class:`~slave.connection.UsbTmcDevice`  A connection object, wrapping a usbtmc file descriptor.  linux only
=======================================  =======================================================  ===========

.. _simulated_connection:

Simulating a connection
-----------------------

Slave has a rudimentary simulation mode. Just use the
:class:`~slave.core.Simulating` instead of an actual connection.
An example is shown below::

    from slave.core import SimulatedConnection
    from slave.sr830 import SR380

    lockin = SR830(SimulatedConnection())
    print lockin.x  # prints a random float

A simple algorithm is used to create the responses.

For read-only commands, the response is randomly created with each query, since
these typically represent measured values. For read and writeable commands, the
response is created just once and cached afterwards. Repeated queries will
return the same result unless a write was issued.

Implementing custom connections
-------------------------------
