.. Slave documentation master file, created by
   sphinx-quickstart on Wed Aug  8 15:36:18 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################
Welcome to Slave
################

This is the documentation of the Slave library, a micro framework designed to
simplify instrument communication and control.

It provides an intuitive way of creating instrument api's, inspired by object
relational mappers. This adds an additional layer of abstraction, separating
the user space from the device space representation of the command.
Command message creation as well as argument and response parsing is done
automatically, e.g. (see :ref:`custom_device_drivers`)::

    from slave.iec60488 import IEC60488, PowerOn
    from slave.core import Command
    from slave.types import Integer, Enum

    class Device(IEC60488, PowerOn):
        def __init__(self, connection):
            super(Device, self).__init__(connection)
            self.command = Command(
                'QRY?',  # query message header 
                'WRT',  # command message header
                [Integer, Enum('first', 'second')] # response and command data type
            )

This way command message creation as well as argument and response parsing is done
automatically.

Additionally slave comes with a variety of ready-to-use implementations of
device drivers, such as

* Stanford Research SR830 lockin amplifier (:mod:`slave.sr830`)
* Signal Recovery SR7225 lockin amplifier (:mod:`slave.sr7225`)
* Lakeshore LS370 AC Resistance Bridge (:mod:`slave.ls370`)
* Lakeshore LS340 Temperature Controller (:mod:`slave.ls340`)

and several more are in work.

Usage is quite simple, a simple example is shown below (see :ref:`getting_started`)::

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

Content
=======

.. toctree::
   :maxdepth: 2

   intro
   custom_device
   slave

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Python: http://www.python.org
.. _pyvisa: http://pyvisa.sourceforge.net/
.. _pyserial: http://pyserial.sourceforge.net/
