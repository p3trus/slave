.. _logging:

Logging
=======

Slave makes use of python's standard logging module. It is quite useful for
development of new device drivers and diagnosing of communication errors.

You can use it in the following way::

    import logging

    logging.basicConfig(filename='log.txt', filemode='w', level=logging.DEBUG)

    # Now use slave ...
