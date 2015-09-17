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
    from slave.driver import Command
    from slave.types import Integer, Enum

    class Device(IEC60488, PowerOn):
        """An iec60488 conforming device api with additional commands."""
        def __init__(self, transport):
            super(Device, self).__init__(transport)
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
    from slave.transport import Visa
    from slave.srs import SR830

    lockin = SR830(Visa('GPIB::08'))
    # configure the lockin amplifier
    lockin.reserve = 'high'
    lockin.time_constant = 3
    # take 60 measurements and print the result
    for i in range(60):
        print lockin.x
        time.sleep(1)

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
with slave; see the file COPYING.

.. _GNU General Public License: http://www.gnu.org/licenses/gpl.html
