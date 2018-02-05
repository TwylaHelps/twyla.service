import asyncio
import os
import unittest

import twyla.service.events as events
import twyla.service.test.helpers as helpers
from twyla.service.message import EventPayload


class TestQueues(unittest.TestCase):
    def setUp(self):
        self.event_name = 'test-event'

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


    def test_emit_listen_roundtrip(self):
        received = []
        event_payload = EventPayload(
            message_type='integration',
            tenant='test-tenant',
            bot_slug='test-slug',
            channel='test-channel',
            channel_user_id='test-user-id'
        )
        event_payload2 = {
            'message_type': 'integration',
            'tenant': 'test-tenant',
            'bot_slug': 'test-slug',
            'channel': 'test-channel',
            'channel_user_id': 'test-user-id',
            'content': {}
        }

        async def consumer(event_name):
            nonlocal received
            async for e in events.listen(event_name):
                received.append(e)
                await e.ack()
                if len(received) == 2:
                    return

        async def producer(event_name):
            nonlocal event_payload
            nonlocal event_payload2
            await events.emit(self.event_name,
                              event_payload.to_json())
            await events.emit(self.event_name,
                              event_payload2)

        tasks = [
            asyncio.ensure_future(consumer(self.event_name)),
            asyncio.ensure_future(producer(self.event_name)),
        ]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.wait(tasks)
        )

        assert len(received) == 2

        received_json = helpers.aio_run(received[0].payload()).to_json()
        assert event_payload.to_json() == received_json

        received2 = helpers.aio_run(received[1].payload()).dict()
        del received2['meta']
        assert event_payload2 == received2
