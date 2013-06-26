Slave:
======

Slave is a micro framework designed to simplify instrument communication and 
control and comes with a variety of ready to use device drivers.

Overview
--------

Slave provides an intuitive way of creating instrument api's, inspired by
object relational mappers.

::

    from slave.iec60488 import IEC60488, PowerOn
    from slave.core import Command
    from slave.types import Integer, Enum

    class Device(IEC60488, PowerOn):
        """An iec60488 conforming device api with additional commands."""
        def __init__(self, connection):
            super(Device, self).__init__(connection)
            # A custom command
            self.my_command = Command(
                'QRY?', # query message header
                'WRT',  # command message header
                # response and command data type
                [Integer, Enum('first', 'second')]
            )

Commands mimic instance attributes. Read access queries the device, parses and
converts the response and finally returns it. Write access parses and converts
the arguments and sends them to the device. This leads to very intuitive
interfaces.

Several device drivers are already implemented, and many more are under
development. A short usage example is given below::

    import time
    import visa
    from slave.sr830 import SR830

    lockin = SR830(visa.instrument('GPIB::08'))
    # configure the lockin amplifier
    lockin.reserve = 'high'
    lockin.time_constant = 3
    # take 60 measurements and print the result
    for i in range(60):
        print lockin.x
        time.sleep(1)

The main goal of slave is to make it easier to communicate with scientific
instruments. Slave tries to ease the implementation of new instruments and
comes with a variety of ready-to-use implementations.

A simple measurement script, using `pyvisa`_ for the `GPIB`_ connection,
might look like::

    import time
    import visa
    from slave.sr830 import SR830

    # construct and initialize a SR830 instrument with a GPIB connection on 
    # channel 8.
    lockin = SR830(visa.instrument('GPIB::08'))
    lockin.reserve = 'high' # Set the dynamic reserve to `high`.
    lockin.time_constant = 3 # Set the time constant to 3s.

    # measure the x value 60 times and wait 1s between each measurement.
    for i in range(60):
        print lockin.x
        time.sleep(1) # delay for 1s.

.. _GPIB: http://de.wikipedia.org/wiki/IEC-625-Bus
.. _pyvisa: http://pyvisa.sourceforge.net/

Requirements
------------

 * Python 2.6 or higher
 * Sphinx (optional, to build the documentation)
 * sphinx_bootstrap_theme(optional, default theme used for the documentation)
 * distribute (Python 3.x)

Installation
------------

To install Slave, simply type

    python setup.py install

**Note** To install Slave in Python 3.x distribute is required.


Documentation
-------------

Slave is fully documented. Both the latest `stable`_ as well as the `develop`_
documentations are available online. To build the documentation manually, e.g.
the html documentation, navigate into the `/doc/` subfolder and execute
`make html`. For a prettier theme, install sphinx_boostrap_theme first
(`pip install sphinx_bootstrap_theme`).

.. _stable: http://slave.readthedocs.org/en/latest/
.. _develop: http://slave.readthedocs.org/en/develop/

Licensing
---------

You should have received a copy of the `GNU General Public License`_ along 
with Slave; see the file COPYING.

.. _GNU General Public License: http://www.gnu.org/licenses/gpl.html
