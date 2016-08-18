from slave.oxford import IPS120
from slave.signal_recovery import SR7230
from slave.transport import Serial, Socket
from slave.misc import LockInMeasurement

import numpy as np

import logging
import logging.config
import time

LOG_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'stream': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'debug.log',
            'backupCount': 3,
            'maxBytes': 1024,
        }
    },
    'root': {
        'handlers': ['stream'],
        'level': 'DEBUG',
        'propagate': True,
    },
}
logging.config.dictConfig(LOG_CFG)

lia1 = SR7230(Socket(address=('transport-lia1.e21.frm2', 50000)))
ips = IPS120(Serial(0, timeout=1))


try:
    ips.access_mode = 'remote unlocked'
    ips.activity = 'to zero'
    
    ips.field.sweep_rate = 0.2
    ips.field.target = 9
    
    lockins = [
        lia1,
    ]
    # Defines a list of environment variables to measure.
    env = [
        lambda: ips.field.value,
    ]
    DELAY = 0.5
    
    with LockinMeasurement('300K_9T_nc.dat'), lockins=lockins, measurables=env) as measure:
        # Start the field sweep
        ips.activity = 'to setpoint'
        while ips.status['mode'] != 'at rest':
            measure()
            time.sleep(DELAY)
            
    with LockinMeasurement('300K_9T_dn.dat'), lockins=lockins, measurables=env) as measure:
        ips.field.target = -9
        while ips.status['mode'] != 'at rest':
            measure()
            time.sleep(DELAY)

    with LockinMeasurement('300K_9T_up.dat'), lockins=lockins, measurables=env) as measure:
        ips.field.target = 9
        while ips.status['mode'] != 'at rest':
            measure()
            time.sleep(DELAY)

finally:
    ips.activity = 'to zero'