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
Stanford Research  SR830                       :class:`slave.srs.sr830.SR830`
Stanford Research  SR850                       :class:`slave.srs.sr850.SR850`
=================  ==========================  ============================================

Temperature Controllers
-----------------------

============  =====  ==============================
Manufacturer  Model  Class
============  =====  ==============================
Lakeshore     LS340  :class:`slave.lakeshore.LS340`
============  =====  ==============================

Magnet Power Supplies
---------------------

==================  ============================  ==================================
Manufacturer        Model                         Class
==================  ============================  ==================================
CryoMagnetics Inc.  Magnet Power Supply Model 4G  :class:`slave.cryomagnetics.MPS4G`
==================  ============================  ==================================
