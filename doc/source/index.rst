.. Slave documentation master file, created by
   sphinx-quickstart on Wed Aug  8 15:36:18 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################
Welcome to Slave
################

This is the documentation of the Slave library, designed to simplify
instrument control.

`Python`_ has many advantages, that make it interresting for the test &
measurement industry. It is easy to learn yet powerfull. Libraries such as
`pyvisa`_ or `pyserial`_ are an important step in making python usefull in
these field. But developers still have to implement device drivers on their
own. Slave simplifies this even further, providing automatic command
construction, type parsing, etc. as well as several ready-to-use device
drivers, such as the

* Lakeshore ls340 temperature controller
* Lakeshore ls370 ac resistance bridge
* Signal recovery sr7225 lock-in amplifier
* Stanford Research sr830 lock-in amplifier
* Cryomagnetics 4G magnet power supply
* etc.

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
