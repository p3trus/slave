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
inside a Quantum Desing PPMS. We're using our own Lock-In amlifier to measure
the resistance as a function of temperature.

.. literalinclude:: ../../examples/magnetotransport.py
