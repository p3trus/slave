.. _logging:

Logging
=======

Slave makes use of python's standard logging module. It is quite useful for
development of new device drivers and diagnosing of communication errors.

You can use it in the following way::

    import logging

    logging.basicConfig(filename='log.txt', filemode='w', level=logging.DEBUG)

    # Now use slave ...

.. note::

        Be careful, IPython adds a default handler. Therefore
        `logging.basicConfig` is a no op.

A more complicated setup could look like this::

    import logging.config

    LOG_CFG = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'stream': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['stream'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
    logging.config.dictConfig(LOG_CFG)
