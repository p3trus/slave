.. Slave documentation master file, created by
   sphinx-quickstart on Wed Aug  8 15:36:18 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################
Welcome to Slave
################

This is the documentation of the Slave library, a micro framework designed to
simplify instrument communication and control. It is divided into three parts,
a quick :ref:`overview <overview>`, the :ref:`user guide <user_guide>` and of
course the :ref:`api reference <api_reference>`.

.. _overview:

Overview
========

Slave provides an intuitive way of creating instrument api's, inspired by
object relational mappers.

::

    from slave.iec60488 import IEC60488, PowerOn
    from slave.core import Command
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
development. A short usage example is given below

.. literalinclude:: ../../examples/quickstart.py

For a complete list of built-in device drivers, see :ref:`builtin_drivers`.

.. _user_guide:

User Guide
==========

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   basic_concepts
   builtin_drivers
   logging
   examples
   changelog

.. _api_reference:

API Reference
=============

This part of the documentation covers the complete api of the slave library.

.. toctree::
   :maxdepth: 2

   slave

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
