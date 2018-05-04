import asyncio
from concurrent.futures._base import CancelledError
import os
import pytest
import unittest
import unittest.mock as mock

import twyla.service.queues as queues

from twyla.service.test.integration.common import RabbitRest


def noop(*args, **kwargs):
    pass


class TestQueues(unittest.TestCase):

    def setUp(self):
        self.patcher = mock.patch.dict(
            os.environ,
            {'TWYLA_AMQP_HOST': 'localhost',
             'TWYLA_AMQP_PORT': '5672',
             'TWYLA_AMQP_USER': 'guest',
             'TWYLA_AMQP_PASS': 'guest',
             'TWYLA_AMQP_VHOST': '/'})
        self.patcher.start()
        self.rabbit = RabbitRest()


    def tearDown(self):
        self.patcher.stop()

    def test_load_configuration_with_prefix(self):
        qm = queues.QueueManager('TWYLA_')
        assert qm.config['amqp_host'] == 'localhost'
        assert qm.config['amqp_port'] == '5672'
        assert qm.config['amqp_user'] == 'guest'
        assert qm.config['amqp_pass'] == 'guest'
        assert qm.config['amqp_vhost'] == '/'


    def test_raise_exception_on_invalid_event_name(self):
        qm = queues.QueueManager('TWYLA_')
        loop = asyncio.get_event_loop()
        with pytest.raises(AssertionError):
            loop.run_until_complete(qm.listen('an-event', 'the-group', noop))


    def test_declare_queues_and_exchanges_for_listener(self):
        qm = queues.QueueManager('TWYLA_')
        loop = asyncio.get_event_loop()
        async def doit():
            await qm.connect()
            await qm.listen('a-domain.an-event', 'the-group', noop)
        loop.run_until_complete(doit())
        rabbit_queues = self.rabbit.queues()
        assert 'a-domain.an-event.the-group' in [x['name'] for x in rabbit_queues]
        bindings = self.rabbit.queue_bindings('a-domain.an-event.the-group')
        assert len(bindings) == 2
        binding_to_exchange = [x for x in bindings if x['source'] == 'a-domain']
        assert len(binding_to_exchange) == 1
        assert binding_to_exchange[0]['routing_key'] == 'an-event'


    def test_declare_exchange(self):
        qm = queues.QueueManager('TWYLA_')
        loop = asyncio.get_event_loop()
        async def doit():
            await qm.connect()
            await qm.declare_exchange("emit-domain")
        loop.run_until_complete(doit())
        exchanges = self.rabbit.exchanges()
        assert 'emit-domain' in [x['name'] for x in exchanges]
