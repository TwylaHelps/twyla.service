import asyncio
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


    async def wait_closed(self):
        # This never happens, as the protocol is mocked and the closed flag is
        # not set
        await asyncio.sleep(100)


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
        self.patcher = mock.patch.dict(
            os.environ,
            {'TWYLA_AMQP_HOST': 'localhost',
             'TWYLA_AMQP_PORT': '5672',
             'TWYLA_AMQP_USER': 'guest',
             'TWYLA_AMQP_PASS': 'guest',
             'TWYLA_AMQP_VHOST': '/'})
        self.patcher.start()


    def tearDown(self):
        self.patcher.stop()


    @mock.patch('twyla.service.queues.aioamqp', new_callable=MockAioamqp)
    def test_queue_manager_basic(self, mock_aioamqp):
        qm = queues.QueueManager('TWYLA_', 'generic')
        helpers.aio_run(qm.connect())

        # Check if the return value of the connect method sets the protocol
        # and channel properly
        assert isinstance(qm.protocol, MockProtocol)
        assert isinstance(qm.channel, MockChannel)

        assert qm.protocol.channel_calls == 1
        # no exchanges or queues called yet
        assert qm.channel.exchange_declare_calls == 0
        assert qm.channel.queue_declare_calls == 0
        assert qm.channel.queue_bind_calls == 0

        helpers.aio_run(qm.stop())

        assert qm.protocol.close_calls == 1
        assert qm.channel.close_calls == 1
