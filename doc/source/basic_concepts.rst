.. _basic_concepts:

Basic Concepts
==============

`slave` uses three layers of abstraction. The transport layer resides at the
lowest level. It's responsibility is sending and receiving raw bytes. It has no
knowledge of their meaning. The protocol layer on the next higher level is
responsible for creating and parsing messages. The driver layer is at the
highest level. It knows which commands are supported and maps them to python
representations.


.. image:: _static/layers.*
   :align: center

.. _transport_layer:

Transport Layer
---------------

.. automodule:: slave.transport

Protocol Layer
--------------

.. automodule:: slave.protocol

Driver Layer
------------

.. automodule:: slave.driver


IEC60488 Compliant Drivers
--------------------------

.. automodule:: slave.iec60488
