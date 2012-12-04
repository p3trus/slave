from slave.core import Command, InstrumentBase
from slave.iec60488 import (IEC60488, Trigger, ObjectIdentification,
    StoredSetting)


class Output(InstrumentBase):
    """A keithley 6221 output object.

    :param connection: A connection object.

    :ivar interlock: Represents the state of the interlock, either 'open' or
        'closed'.
    :ivar response: The output response mode, either 'fast' or 'slow'

    """
    def __init__(self, connection):
        super(Output, self).__init__(connection)
        self.interlock = Command((
            'OUTP:INT:TRIP?',
            Enum('open', 'closed')
        ))
        self.response = Command(
            'OUTP:RESP?',
            'OUTP:RESP',
            Mapping({'fast': 'FAST', 'slow': 'SLOW'})
        )


class K6221(IEC60488, Trigger, ObjectIdentification, StoredSetting):
    """The Keithley model 6221 ac/dc current source reference.

    :param connection: A connection object.

    :ivar output: A keithley 6221 output object.

    """
    def __init__(self, connection):
        super(K6221, self).__init__(connection)
        self.output = Output(connection)
