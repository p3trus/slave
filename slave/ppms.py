# -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS. Licensed under the GNU GPL.
from slave.core import Command
from slave.types


class PPMS(object):
    """

    :ivar advisory_number: The advisory code number, a read only integer in the
        range 0 to 999.
    :ivar field: The magnetic field configuration, represented by the following
        tuple (<field>, <rate>, <approach mode>, <magnet mode>), where

         * <field> is the magnetic field setpoint in Oersted with a resolution
          of 0.01 Oersted. The min and max fields depend on the magnet used.
         * <rate> is the ramping rate in Oersted/second with a resolution of
           0.1 Oersted/second. The min and max values depend on the magnet
           used.
         * <approach mode> is the approach mode, either 'linear',
            'no overshoot' or 'oscillate'.
        * <magnet mode> is the state of the magnet at the end of the charging
          process, either 'persistent' or 'driven'.

    """
    def __init__(self):
        self.advisory_number = Command(('ADVNUM?', Integer(min=0, max=999))
        # TODO Allow for configuration of the ranges
        self.field = Command(
            'FIELD?',
            'FIELD',
            (
                Float(min=-9e4, max=9e4, fmt='{0:.2f}'),
                Float(min=10.5, max=196., fmt='{0:.1f}'),
                Enum('linear', 'no overshoot', 'oscillate'),
                Enum('persistent', 'driven')
            )
        )

