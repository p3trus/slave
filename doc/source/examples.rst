Usage Examples
==============

Simple Measurement
------------------

This examples shows a simple measurement script, using a Stanford Research
Systems LockIn amplifier and is discussed in more detail in the
:ref:`quickstart` section.

.. literalinclude:: ../../examples/quickstart.py

Magnetotransport Measurement
----------------------------

In this example, we assume a sample with standard four terminal wiring is placed
inside a Quantum Desing PPMS. We're using our own Lock-In amplifier to measure
the resistance as a function of temperature.

.. literalinclude:: ../../examples/magnetotransport.py


Differential Conductance
------------------------

In this example we're showing how to use the Keithley :class:`~.K6221`
currentsource and :class:`~.K2182` nanovoltmeter combo to perform a differential
conductance measurement.

.. literalinclude:: ../../examples/differential_conductance.py