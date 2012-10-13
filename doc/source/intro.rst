Getting started
===============

The main goal of slave is to make it easier to communicate with scientific
instruments. Slave tries to ease the implementation of new instruments and
comes with a variety of ready-to-use implementations.

Basic usage
-----------

The easiest way to use the slave library is in combination with already
implemented instruments and best shown with an example. In the following
tutorial we will implement a small measurement script, which initializes a
Stanford Research SR830 lock-in and starts a measurement.

The first step is to construct a connection. Here we use `pyvisa`_ to connect
with the SR830 via GPIB on channel 8::

    import visa
    connection = visa.instrument('GPIB::08')

The next step is to construct and configure the SR830 instrument::

    from slave.sr830 import SR830

    lockin = SR830(connection)
    # Set the dynamic reserve to `high`.
    lockin.reserve = 'high'
    # Set the time constant to 3s.
    lockin.time_constant = 3

The last step is to start the actual measurement::

    import time
    # measure the x value 60 times and wait 1s between each measurement.
    for i in range(60):
        print lockin.x
        time.sleep(1) # delay for 1s.

Putting it all together we get a small 12 line script, capable of performing a
complete measurement.

::

    #!/usr/bin/env python
    import time

    import visa
    from slave.sr830 import SR830

    lockin = SR830(visa.instrument('GPIB::08'))
    lockin.reserve = 'high'
    lockin.time_constant = 3
    for i in range(60):
        print lockin.x
        time.sleep(1)

The connection object
---------------------

Slave makes heavy use of an object, referred to as connection. It represents
the connection to the real instrument, e.g. serial, gpib, usb, ... and is not
implemented by Slave itself. Slave was build with `pyvisa`_ in mind, but is not
restricted to it as long as the connection object fulfills the requirements.

These are:
 * a `write()` member function, taking a command string.
 * a `ask()` member function, taking a command string and returning a string
   response.

.. _pyvisa: http://pyvisa.sourceforge.net/

Simulation mode
---------------

Slave has a simple built-in Simulation mode. This is usefull for testing higher
level applications using slave. In simulation mode you can use the devices
without a real connection. The communication is simulated randomly. Creating a 
device in simulation mode is easy and shown below using the
:class:`~.slave.sr830.SR830` device.
::

    from slave.core import SimulatedConnection
    from slave.sr830 import SR830

    lockin = SR830(SimulatedConnection())
    print lockin.x # Will output a random float

Instead of a real connection object, you pass in a
:class:`~.slave.core.SimulatedConnection`.

Logging
-------

Slave uses python's standard logging_ module. This is especially usefull for
developers implementing new devices. Currently only the Command class uses it.
The logging levels in use are:

 * *INFO*
 * *DEBUG*

.. _logging: http://docs.python.org/library/logging.html

Info level
^^^^^^^^^^

At the *INFO* logging level, the generated command message units, query message
units and responses are logged. This is usefull to check if the device
communication is working correctly. A generated log entry might look like
::

    INFO:slave.core:query message unit: "RMOD?"
    INFO:slave.core:response: "0"

This means the query string "RMOD?" was emited, and the device response was
"0".

Debug level
^^^^^^^^^^^

Additionally on *DEBUG* level, the construction of Commands is logged. It is
usefull to verify that the objects were constructed properly. This creates
messages similar to that
::

    DEBUG:slave.core:created Command(query=('*IDN?', [String(), String(), String(), String()], []), write=(None, [String(), String(), String(), String()]), connection=None, cfg={'program header prefix': '', 'response data separator': ',', 'program header separator': ' ', 'response header separator': ' ', 'program data separator': ','})

Usage
^^^^^

To use logging with Slave, you can do something like this
::

    import logging
    import slave

    logging.basicConfig(filename='logfile.log',
                        filemode='w',
                        level=logging.DEBUG)

    # Use slave ...
