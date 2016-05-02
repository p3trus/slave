#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

import pytest

from slave.protocol import IEC60488, OxfordIsobus, Protocol, SignalRecovery
from slave.transport import Transport


class MockTransport(Transport):
    def __init__(self, responses=[]):
        self.responses = collections.deque(responses)
        self.messages = collections.deque()
        super(MockTransport, self).__init__()

    def __write__(self, data):
        self.messages.append(data)

    def __read__(self, num_bytes):
        return self.responses.popleft()


class TestIEC60488Protocol(object):
    def test_create_message_without_data(self):
        protocol = IEC60488(msg_prefix='PREFIX:')
        assert protocol.create_message('HEADER') == b'PREFIX:HEADER\n'

    def test_create_message_with_single_data(self):
        protocol = IEC60488(msg_prefix='PREFIX:')
        assert protocol.create_message('HEADER', 'DATA') == b'PREFIX:HEADER DATA\n'

    def test_create_message_with_multiple_data(self):
        protocol = IEC60488(msg_prefix='PREFIX:')
        assert protocol.create_message('HEADER', 'D1', 'D2', 'D3') == b'PREFIX:HEADER D1,D2,D3\n'

    def test_write_without_data(self):
        protocol = IEC60488()
        transport = MockTransport()
        protocol.write(transport, 'HEADER')
        assert transport.messages[0] == b'HEADER\n'

    def test_write_with_data(self):
        protocol = IEC60488()
        transport = MockTransport()
        protocol.write(transport, 'HEADER', 'D1', 'D2', 'D3')
        assert transport.messages[0] == b'HEADER D1,D2,D3\n'

    def test_parse_response_without_header_prefix_and_single_data(self):
        protocol = IEC60488()
        assert protocol.parse_response(b'DATA') == ['DATA']

    def test_parse_response_without_header_prefix_and_multiple_data(self):
        protocol = IEC60488()
        assert protocol.parse_response(b'DATA,DATA,DATA') == ['DATA', 'DATA', 'DATA']

    def test_parse_response_with_header_and_prefix(self):
        protocol = IEC60488(resp_prefix='PREFIX:', resp_header_sep=' ')
        assert protocol.parse_response(b'PREFIX:HEADER DATA,DATA', 'HEADER') == ['DATA', 'DATA']

    def test_parse_response_with_wrong_header(self):
        protocol = IEC60488()
        with pytest.raises(Protocol.ParsingError) as excinfo:
            protocol.parse_response(b'DATA,DATA', 'HEADER')
        assert str(excinfo.value) == 'Response header mismatch'

    def test_query(self):
        protocol = IEC60488()
        transport = MockTransport(responses=[b'DATA,DATA\n'])
        assert protocol.query(transport, 'HEADER') == ['DATA','DATA']
        assert transport.messages[0] == b'HEADER\n'


class CallbackBuffer(object):
    def __call__(self, data):
        self.data = data


class TestSignalRecovery(TestIEC60488Protocol):
    def test_write_with_callbacks(self):
        stb_callback, olb_callback = CallbackBuffer(), CallbackBuffer()
        protocol = SignalRecovery(
            stb_callback=stb_callback,
            olb_callback=olb_callback
        )
        transport = MockTransport(responses=[b'133.7\0\x02\x01'])
        response = protocol.query(transport, 'HEADER')
        assert stb_callback.data == 2
        assert olb_callback.data == 1

    def test_query_with_callbacks(self):
        stb_callback, olb_callback = CallbackBuffer(), CallbackBuffer()
        protocol = SignalRecovery(
            stb_callback=stb_callback,
            olb_callback=olb_callback
        )
        transport = MockTransport(responses=[b'133.7\0\x00\x01'])
        response = protocol.query(transport, 'HEADER')
        assert stb_callback.data == 0
        assert olb_callback.data == 1


class TestOxfordIsobus(object):
    def test_create_message_without_data_and_without_address(self):
        protocol = OxfordIsobus()
        assert protocol.create_message('R') == b'R\r'

    def test_create_message_without_data_with_address(self):
        protocol = OxfordIsobus(address=7)
        assert protocol.create_message('R') == b'@7R\r'

    def test_create_message_with_data_and_without_address(self):
        protocol = OxfordIsobus()
        assert protocol.create_message('R', '1337') == b'R1337\r'

    def test_create_message_with_data_and_address(self):
        protocol = OxfordIsobus(address=7)
        assert protocol.create_message('R', '1337') == b'@7R1337\r'

    def test_create_message_without_echo_data_and_address(self):
        protocol = OxfordIsobus(echo=False)
        assert protocol.create_message('R') == b'$R\r'

    def test_create_message_without_echo_data_and_with_address(self):
        protocol = OxfordIsobus(address=7, echo=False)
        assert protocol.create_message('R') == b'$@7R\r'

    def test_create_message_without_echo_with_data_and_without_address(self):
        protocol = OxfordIsobus(echo=False)
        assert protocol.create_message('R', '1337') == b'$R1337\r'

    def test_create_message_without_echo_with_data_and_address(self):
        protocol = OxfordIsobus(address=7, echo=False)
        assert protocol.create_message('R', '1337') == b'$@7R1337\r'

    def test_parse_response_without_data(self):
        protocol = OxfordIsobus()
        assert protocol.parse_response(b'R', 'R') == ''

    def test_parse_response_with_data(self):
        protocol = OxfordIsobus()
        assert protocol.parse_response(b'R1337', 'R') == '1337'

    def test_parse_response_with_error(self):
        protocol = OxfordIsobus()
        with pytest.raises(IOError) as excinfo:
            protocol.parse_response(b'?R', 'R')
        assert str(excinfo.value) == '?R'

    def test_parse_response_with_wrong_header(self):
        protocol = OxfordIsobus()
        with pytest.raises(ValueError) as excinfo:
            protocol.parse_response(b'U1', 'R')
        assert str(excinfo.value) == 'Response header mismatch'

    def test_write_with_data(self):
        transport = MockTransport(responses=[b'R\r'])
        protocol = OxfordIsobus(address=7)
        protocol.write(transport, 'R', '10')
        assert transport.messages[0] == b'@7R10\r'

    def test_write_with_response_data(self):
        transport = MockTransport(responses=[b'R10\r'])
        protocol = OxfordIsobus(address=7)
        with pytest.raises(ValueError) as excinfo:
            protocol.write(transport, 'R', '11')
        assert str(excinfo.value) == 'Unexpected response data:10'

    def test_query(self):
        transport = MockTransport(responses=[b'R1337\r'])
        protocol = OxfordIsobus(address=7)
        assert protocol.query(transport, 'R10') == ['1337']
        assert transport.messages[0] == b'@7R10\r'
