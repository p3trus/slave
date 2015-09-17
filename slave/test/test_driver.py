#  -*- coding: utf-8 -*-
#
# Slave, (c) 2014, see AUTHORS.  Licensed under the GNU GPL.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *
import itertools as it

import pytest

from slave.driver import Command, Driver, _dump, _load, _to_instance, _typelist
from slave.types import Integer, String
from slave.transport import SimulatedTransport


class MockProtocol(object):
    def __init__(self, response=None):
        self.response = response
        self.transport = None
        self.header = None
        self.data = None

    def query(self, transport, header, *data):
        self.transport = transport
        self.header = header
        self.data = data
        return self.response

    def write(self, transport, header, *data):
        self.transport = transport
        self.header = header
        self.data = data


class MockTransport(object):
    pass


class Test_to_instance(object):
    def test_with_instance(self):
        assert isinstance(_to_instance(object()), object)

    def test_with_class(self):
        assert isinstance(_to_instance(object), object)


class Test_typelist(object):
    def test_with_list_of_objects(self):
        assert _typelist([0, 0, 0]) == [0, 0, 0]

    def test_with_list_of_types(self):
        assert _typelist([int, int, int]) == [0, 0, 0]

    def test_with_single_object(self):
        assert _typelist(0) == [0]

    def test_with_single_type(self):
        assert _typelist(int) == [0]

    def test_with_generator(self):
        gen = (0 for i in range(3))
        # generators/iterators should not be modified.
        assert _typelist(gen) == gen


class Test_load(object):
    def test_load(self):
        assert _load([Integer(), Integer()], ["1", "2"]) == [1, 2]

    def test_dump_with_infinite_iterator(self):
        assert _load(it.repeat(Integer()), ["1", "2", "3"]) == [1, 2, 3]

    def test_dump_with_too_many_values(self):
        with pytest.raises(ValueError) as excinfo:
            _load([Integer(), Integer()], ["1", "2", "3"])
        assert str(excinfo.value) == 'Too many values.'

    def test_dump_with_too_few_values(self):
        with pytest.raises(ValueError) as excinfo:
            _load([Integer(), Integer()], ["1"])
        assert str(excinfo.value) == 'Too few values.'


class Test_dump(object):
    def test_dump(self):
        assert _dump([Integer(), Integer()], [1, 2]) == ["1", "2"]

    def test_dump_with_infinite_iterator(self):
        assert _dump(it.repeat(Integer()), [1, 2, 3]) == ["1", "2", "3"]

    def test_dump_with_too_many_values(self):
        with pytest.raises(ValueError) as excinfo:
            _dump([Integer(), Integer()], [1, 2, 3])
        assert str(excinfo.value) == 'Too many values.'

    def test_dump_with_too_few_values(self):
        with pytest.raises(ValueError) as excinfo:
            _dump([Integer(), Integer()], [1])
        assert str(excinfo.value) == 'Too few values.'


class TestCommand(object):
    def test_write(self):
        protocol = MockProtocol()
        transport = MockTransport()
        cmd = Command(write=('HEADER', [Integer, Integer]))
        cmd.write(transport, protocol, 1, 2)
        assert protocol.transport == transport
        assert protocol.header == 'HEADER'
        assert protocol.data == ('1', '2')

    def test_write_without_data(self):
        protocol = MockProtocol()
        transport = MockTransport()
        cmd = Command(write='HEADER')
        cmd.write(transport, protocol)

    def test_write_with_query_only_cmd(self):
        protocol = MockProtocol()
        transport = MockTransport()
        cmd = Command(('HEADER', Integer))
        with pytest.raises(AttributeError) as excinfo:
            cmd.write(transport, protocol)
        assert str(excinfo.value) ==  'Command is not writeable'

    def test_write_with_generator_type(self):
        protocol = MockProtocol()
        transport = MockTransport()
        cmd = Command(write=('HEADER', it.repeat(Integer())))
        cmd.write(transport, protocol, 1, 2, 3)
        assert protocol.transport == transport
        assert protocol.header == 'HEADER'
        assert protocol.data == ('1', '2', '3')

    def test_query_without_message_data_and_single_data_response(self):
        protocol = MockProtocol(response=['1'])
        transport = MockTransport()
        cmd = Command(query=('HEADER', Integer))
        response = cmd.query(transport, protocol)
        assert protocol.transport == transport
        assert protocol.header == 'HEADER'
        assert protocol.data == ()
        assert response == 1

    def test_query_without_message_data_and_multi_data_response(self):
        protocol = MockProtocol(response=['1', '2'])
        transport = MockTransport()
        cmd = Command(query=('HEADER', [Integer, Integer]))
        response = cmd.query(transport, protocol)
        assert protocol.transport == transport
        assert protocol.header == 'HEADER'
        assert protocol.data == ()
        assert response == [1, 2]

    def test_query_with_write_only_cmd(self):
        protocol = MockProtocol()
        transport = MockTransport()
        cmd = Command(write='HEADER')
        with pytest.raises(AttributeError) as excinfo:
            cmd.query(transport, protocol)
        assert str(excinfo.value) ==  'Command is not queryable'

    def test_query_with_generator_type(self):
        protocol = MockProtocol(response=['1', '2', '3'])
        transport = MockTransport()
        cmd = Command(query=('HEADER', it.repeat(Integer())))
        response = cmd.query(transport, protocol)
        assert protocol.transport == transport
        assert protocol.header == 'HEADER'
        assert protocol.data == ()
        assert response == [1, 2, 3]

    def test_simulation_with_query_and_writeable_cmd(self):
        protocol = MockProtocol()
        transport = SimulatedTransport()
        cmd = Command('HEADER?', 'HEADER', Integer)
        response = cmd.query(transport, protocol)
        assert isinstance(response, int)
        assert cmd._simulation_buffer == [Integer().dump(response)]

    def test_simulation_with_query_only_cmd(self):
        protocol = MockProtocol()
        transport = SimulatedTransport()
        cmd = Command(query=('HEADER', [Integer, Integer]))
        response = cmd.query(transport, protocol)
        assert len(response) == 2
        for item in response:
            assert isinstance(item, int)
        # query only should not buffer simulated response
        with pytest.raises(AttributeError):
            cmd._simulation_buffer

    def test_write_with_simulation(self):
        protocol = MockProtocol()
        transport = SimulatedTransport()
        cmd = Command(write=('HEADER', [Integer, Integer]))
        cmd.write(transport, protocol, 1, 2)
        assert cmd._simulation_buffer == ['1', '2']


class MockDriver(Driver):
    def __init__(self, transport, protocol):
        super(MockDriver, self).__init__(transport, protocol)
        self.no_cmd = 'NO CMD'
        self.cmd = Command('QUERY', 'WRITE', String)
        self.multiple_types_cmd = Command('QUERY', 'WRITE', [Integer, String])


class TestDriver(object):
    def test_getting_normal_attribute(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        assert driver.no_cmd == 'NO CMD'

    def test_setting_normal_attribute(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        driver.no_cmd = 'MODIFIED'
        assert driver.__dict__['no_cmd'] == 'MODIFIED'

    def test_setting_new_attribute(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        driver.new_cmd = 'NEW'
        assert driver.__dict__['new_cmd'] == 'NEW'

    def test_getting_command(self):
        transport, protocol = MockTransport(), MockProtocol(response=['RESPONSE'])
        driver = MockDriver(transport, protocol)
        assert driver.cmd == 'RESPONSE'

    def test_writing_command(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        driver.cmd = 'MESSAGE'
        assert protocol.header == 'WRITE'
        assert protocol.data == ('MESSAGE',)

    def test_writing_a_sequence(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        driver.multiple_types_cmd = 1337, 'L33t'
        assert protocol.header == 'WRITE'
        assert protocol.data == ('1337', 'L33t')

    def test_query_method(self):
        transport, protocol = MockTransport(), MockProtocol(response=['RESPONSE'])
        driver = MockDriver(transport, protocol)
        assert driver._query(('QUERY', String, String), 'DATA') == 'RESPONSE'
        assert protocol.header == 'QUERY'
        assert protocol.data == ('DATA',)

    def test_write_method(self):
        transport, protocol = MockTransport(), MockProtocol()
        driver = MockDriver(transport, protocol)
        driver._write(('WRITE', [Integer, String]), 12, 'DATA')
        assert protocol.header == 'WRITE'
        assert protocol.data == ('12', 'DATA')
