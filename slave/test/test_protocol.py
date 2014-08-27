#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import collections

import pytest

from slave.protocol import IEC60488, SignalRecovery
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
        with pytest.raises(ValueError) as excinfo:
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
