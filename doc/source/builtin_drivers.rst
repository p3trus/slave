.. _builtin_drivers:

Built-in Device Drivers
=======================

Slave ships with several completely implemented device drivers.

Lock-in Amplifiers
------------------

=================  ==========================  ============================================
Manufacturer       Model                       Class
=================  ==========================  ============================================
Lakeshore          LS370 AC Resistance Bridge  :class:`slave.lakeshore.ls370.LS370`
Signal Recovery    SR7225                      :class:`slave.signal_recovery.sr7225.SR7225`
Signal Recovery    SR7230                      :class:`slave.signal_recovery.sr7230.SR7230`
Stanford Research  SR830                       :class:`slave.srs.sr830.SR830`
Stanford Research  SR850                       :class:`slave.srs.sr850.SR850`
=================  ==========================  ============================================

Voltmeter
---------

============  =====  ===================================
Manufacturer  Model  Class
============  =====  ===================================
Keithley      2182A  :class:`slave.keithley.k2182.K2182`
============  =====  ===================================

Current Source
--------------

============  =====  ===================================
Manufacturer  Model  Class
============  =====  ===================================
Keithley      6221   :class:`slave.keithley.k6221.K6221`
============  =====  ===================================

Temperature Controllers
-----------------------

============  =====  ====================================
Manufacturer  Model  Class
============  =====  ====================================
Lakeshore     LS340  :class:`slave.lakeshore.ls340.LS340`
============  =====  ====================================

Magnet Power Supplies
---------------------

==================  ============================  ========================================
Manufacturer        Model                         Class
==================  ============================  ========================================
CryoMagnetics Inc.  Magnet Power Supply Model 4G  :class:`slave.cryomagnetics.mps4g.MPS4G`
==================  ============================  ========================================

Cryostats
---------

==============  =============== =======================================
Manufacturer    Model           Class
==============  =============== =======================================
Quantum Design  PPMS Model 6000 :class:`slave.quantum_design.ppms.PPMS`
==============  =============== =======================================

Data Acquisition Cards
----------------------

=============== ========== ==================================
Manufacturer    Model      Class
=============== ========== ==================================
ICS Electronics Model 4807 :class:`slave.ics.ics4807.ICS4807`
=============== ========== ==================================
