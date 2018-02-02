import os
import unittest
import unittest.mock as mock

import twyla.service.queues as queues
import twyla.service.test.helpers as helpers


class MockChannel:
    def __init__(self):
        self.exchange_declare_recorder = None
        pass

    async def exchange_declare(*args, **kwargs):
        pass


class MockProtocol:
    def __init__(self):
        self.channel_calls = 0

    async def channel(self):
        self.channel_calls += 1
        return MockChannel()


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
