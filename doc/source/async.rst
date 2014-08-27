.. _async_io:

Asynchronous IO
===============

Slave has a built-in compatibility layer for the tornado framework. It is
currently in an early state and only socket transports are supported.
Nevertheless, it is already usable. The following examples will show how to
make use of it.

A simple asynchronous poller
---------------------------

In this example we will implement a simple, basically useless, asynchronous
poller to explain the concept. It simply prints out the polled value. We will
extend this example to implement a monitor with a web interface.

::

    from tornado.ioloop import IOLoop, PeriodicCallback
    from tornado.gen import coroutine

    import slave.async
    # Monkey patch slave to use the asynchronous implementation
    slave.async.patch()

    # Due to the call to `patch()`, the driver and the transport automatically
    # use the asynchronous implementation.
    from slave.sr7230 import SR7230
    from slave.transport import TCPIPDevice

    lockin1 = SR7230(TCPIPDevice('192.168.178.11:80000'))

    def show(fn):
        @coroutine
        def print_fn():
            value = yield fn()
            print value
        return print_fn

    ioloop = tornado.ioloop.IOLoop.Instance()
    poller = [
        # poll the x voltage every 2 seconds, the sensitivity every 5.
        PeriodicCallback(show(lambda: lockin1.x), 2000),
        PeriodicCallback(show(lambda: lockin1.sensitivity), 5000)
    ]
    for p in poller:
        ioloop.add_callback(p.start)

    ioloop.start()
