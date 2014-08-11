#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from future.builtins import *
import pytest
from mock import MagicMock

from slave.transport import Transport

@pytest.fixture
def transport():
    transport = Transport()
    transport.__read__ = MagicMock(return_value=b'RESPONSE')
    return transport

class TestTransport(object):
    def test_read_bytes_with_empty_buffer(self, transport):        
        assert transport.read_bytes(1024) == b'RESPONSE'
        transport.__read__.assert_called_with(1024)
        assert not transport._buffer # buffer should be empty

    def test_read_bytes_with_nonempty_buffer(self, transport):
        transport._buffer.extend(b'BUFFER')
        assert transport.read_bytes(1024) == b'BUFFER'
        assert not transport.__read__.called
        assert not transport._buffer # buffer should be empty
        
    def test_read_bytes_with_nonempty_buffer_and_more_bytes_than_requested(self, transport):
        transport._buffer.extend(b'BUFFER')
        assert transport.read_bytes(3) == b'BUF'
        assert not transport.__read__.called
        assert transport._buffer == b'FER'

    def test_read_until(self, transport):
        assert transport.read_until(b'P') == b'RESP'
        transport.__read__.assert_called_with(transport._max_bytes)
        assert transport._buffer == b'ONSE'
