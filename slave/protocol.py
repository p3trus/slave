#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *


class Protocol(object):
    """Abstract protocol base class."""
    def query(self, transport, *args, **kw):
        raise NotImplementedError()

    def write(self, transport, *args, **kw):
        raise NotImplementedError()


class IEC60488(Protocol):
    """Implementation of IEC60488 protocol.
    """
    def __init__(self, msg_prefix='', msg_header_sep=' ', msg_data_sep=',', msg_term='\n',
                 resp_prefix='', resp_header_sep='', resp_data_sep=',', resp_term='\n', encoding='ascii'):
        self.msg_prefix = msg_prefix
        self.msg_header_sep = msg_header_sep
        self.msg_data_sep = msg_data_sep
        self.msg_term = msg_term

        self.resp_prefix = resp_prefix
        self.resp_header_sep = resp_header_sep
        self.resp_data_sep = resp_data_sep
        self.resp_term = resp_term

        self.encoding = encoding

    def create_message(self, header, *data):
        if not data:
            msg = ''.join((self.msg_prefix, header, self.msg_term))
        else:
            data = self.msg_data_sep.join(data)
            msg = ''.join((self.msg_prefix, header, self.msg_header_sep, data, self.msg_term))
        return msg.encode(self.encoding)

    def parse_response(self, response, header=None):
        """Parses the response message.

        The following graph shows the structure of response messages.

        ::

                                                        +----------+
                                                     +--+ data sep +<-+
                                                     |  +----------+  |
                                                     |                |
                  +--------+        +------------+   |    +------+    |
              +-->| header +------->+ header sep +---+--->+ data +----+----+
              |   +--------+        +------------+        +------+         |
              |                                                            |
            --+                                         +----------+       +-->
              |                                      +--+ data sep +<-+    |
              |                                      |  +----------+  |    |
              |                                      |                |    |
              |                                      |    +------+    |    |
              +--------------------------------------+--->+ data +----+----+
                                                          +------+

       """
        response = response.decode(self.encoding)
        if header:
            header = "".join((self.resp_prefix, header, self.resp_header_sep))
            if not response.startswith(header):
                raise ValueError('Response header mismatch')
            response = response[len(header):]
        return response.split(self.resp_data_sep)

    def query(self, transport, header, *data):
        message = self.create_message(header, *data)
        transport.write(message)
        response = transport.read_until(self.resp_term)
        # TODO: Currently, response headers are not handled.
        return self.parse_response(response)

    def write(self, transport, header, *data):
        message = self.create_message(header, *data)
        transport.write(message)
