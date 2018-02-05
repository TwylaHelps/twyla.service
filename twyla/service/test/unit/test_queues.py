import os
import unittest
import unittest.mock as mock

from aioamqp.protocol import OPEN

import twyla.service.queues as queues
import twyla.service.test.helpers as helpers


class MockChannel:
    def __init__(self):
        self.exchange_declare_calls = 0
        self.queue_declare_calls = 0
        self.queue_bind_calls = 0
        self.close_calls = 0
        self.is_open = True

    async def exchange_declare(self, *args, **kwargs):
        self.exchange_declare_calls += 1

    async def queue_declare(self, *args, **kwargs):
        self.queue_declare_calls += 1

    async def queue_bind(self, *args, **kwargs):
        self.queue_bind_calls += 1

    async def close(self):
        self.close_calls += 1


class MockProtocol:
    def __init__(self):
        self.channel_calls = 0
        self.close_calls = 0
        self.state = OPEN

    async def channel(self):
        self.channel_calls += 1
        return MockChannel()

    async def close(self):
        self.close_calls += 1


class MockAioamqp:
    def __init__(self):
        self.connect_recorder = None


    async def connect(self, *args, **kwargs):
        self.connect_recorder = {
            'args': args,
            'kwargs': kwargs
        }

        return None, MockProtocol()


class QueueManagerTests(unittest.TestCase):
    def setUp(self):
        os.environ['TWYLA_RABBITMQ_HOST'] = 'localhost'
        os.environ['TWYLA_RABBITMQ_PORT'] = '5672'
        os.environ['TWYLA_RABBITMQ_USER'] = 'guest'
        os.environ['TWYLA_RABBITMQ_PASS'] = 'guest'
        os.environ['TWYLA_RABBITMQ_EXCHANGE'] = 'events_test'
        os.environ['TWYLA_RABBITMQ_VHOST'] = '/'
        os.environ['TWYLA_RABBITMQ_PREFIX'] = 'test-service'


    def tearDown(self):
        del os.environ['TWYLA_RABBITMQ_HOST']
        del os.environ['TWYLA_RABBITMQ_PORT']
        del os.environ['TWYLA_RABBITMQ_USER']
        del os.environ['TWYLA_RABBITMQ_PASS']
        del os.environ['TWYLA_RABBITMQ_EXCHANGE']
        del os.environ['TWYLA_RABBITMQ_VHOST']
        del os.environ['TWYLA_RABBITMQ_PREFIX']


    def test_load_config(self):
        config = queues.load_config()

        assert config == {
            'host': 'localhost',
            'port': '5672',
            'user': 'guest',
            'pass': 'guest',
            'exchange': 'events_test',
            'vhost': '/',
            'prefix': 'test-service'
        }


    @mock.patch('twyla.service.queues.aioamqp', new_callable=MockAioamqp)
    def test_queue_manager_basic(self, mock_aioamqp):
        qm = queues.QueueManager()
        helpers.aio_run(qm.connect())

        # Check if the return value of the connect method sets the protocol
        # and channel properly
        assert isinstance(qm.protocol, MockProtocol)
        assert isinstance(qm.channel, MockChannel)

        assert qm.protocol.channel_calls == 1
        assert qm.channel.exchange_declare_calls == 1
        assert qm.channel.queue_declare_calls == 0
        assert qm.channel.queue_bind_calls == 0

        helpers.aio_run(qm.stop())

        assert qm.protocol.close_calls == 1
        assert qm.channel.close_calls == 1
