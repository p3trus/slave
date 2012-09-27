Basic usage
-----------

The easiest way to use the slave library is in combination with already
implemented instruments and best shown with an example. In the following
tutorial we will implement a small measurement script, which initializes a
Stanford Research SR830 lock-in and starts a measurement.

The first step is to construct a connection. Here we use pyvisa to connect with
the SR830 via GPIB on channel 8::

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
implemented by Slave itself. Slave was build with pyvisa in mind, but is not
restricted to it as long as the connection object fulfills the requirements.

These are:
 * a `write()` member function, taking a command string.
 * a `ask()` member function, taking a command string and returning a string
   response.
