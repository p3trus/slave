Slave:
======

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

Requirements
------------

 * Python 2.6 or higher
 * Sphinx (optional, to build the documentation)
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
`make html`.

.. _stable: http://slave.readthedocs.org/en/latest/
.. _develop: http://slave.readthedocs.org/en/develop/

Licensing
---------

You should have received a copy of the `GNU General Public License`_ along 
with Slave; see the file COPYING.

.. _GNU General Public License: http://www.gnu.org/licenses/gpl.html
.. _GPIB: http://de.wikipedia.org/wiki/IEC-625-Bus
.. _pyvisa: http://pyvisa.sourceforge.net/
