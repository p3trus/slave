#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

import pytest

from slave.protocol import IEC60488


class MockTransport(object):
    def __init__(self, response=None):
        self.response = response
        self.message = None

    def write(self, data):
        self.message = data

    def read_until(self, delimiter):
        return self.response


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
        assert transport.message == b'HEADER\n'

    def test_write_with_data(self):
        protocol = IEC60488()
        transport = MockTransport()
        protocol.write(transport, 'HEADER', 'D1', 'D2', 'D3')
        assert transport.message == b'HEADER D1,D2,D3\n'

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
        assert excinfo.value.message == 'Response header mismatch'

    def test_query(self):
        protocol = IEC60488()
        transport = MockTransport(response=b'DATA,DATA')
        assert protocol.query(transport, 'HEADER') == ['DATA','DATA']
        assert transport.message == b'HEADER\n'
