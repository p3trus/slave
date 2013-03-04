Quickstart
==========

Python has several advantages that make it interresting for the scientifc
community as well as the test & measurement industry. It's easy to learn yet
powerfull. It supports a variety of communication protocolls through builtin
and third party packages such as `pyvisa`_, `pyserial`_ or `pyparallel`_.

.. _pyvisa:     http://pyvisa.sourceforge.net/
.. _pyserial:   http://pyserial.sourceforge.net/
.. _pyparallel: http://pyserial.sourceforge.net/pyparallel.html

Introduction
------------

The easiest way to use the slave library is in combination with already
implemented instruments and best shown with an example. In the following
tutorial we will implement a small measurement script, which initializes a
Stanford Research SR830 lock-in and starts a measurement.

The first step is to construct a connection object. Here we use `pyvisa`_ to connect
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

Slave does not communicate with the devices it self. It makes heavy use of an
object refered to as 'connection object'. Every object conforming to slave's 
'connection interface' can be used by slave device drivers.

The interface is quite simple, just two methods are required:

* An `ask()` method, taking a string command and returning a string response.
* A `write` method, taking a string command.

As long as these requirements are fullfiled any class can be used (e.g.
`pyvisa`_).If your communication library of choice does not conform to it, 
don't give up your hope. Implementing an adapter is pretty easy. Slave already
has several adapters to popular communication libraries. An abstract interface,
:class:`~slave.connection.Connection` interface easing the implementation of new ones.

