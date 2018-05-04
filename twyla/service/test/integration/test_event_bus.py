import asyncio
import json
from concurrent.futures._base import CancelledError
import os
import pytest
import unittest
import unittest.mock as mock

from twyla.service.event_bus import EventBus
import twyla.service.queues as queues
import twyla.service.test.helpers as helpers
import twyla.service.test.common as common
from twyla.service.event import set_schemata, EventPayload, Event
from twyla.service.test.integration.common import RabbitRest


class TestQueues(unittest.TestCase):

    def setUp(self):
        set_schemata(*common.schemata_fixtures())
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


    def test_emit(self):
        self.rabbit.create_queue("a-domain.an-event.testing", "a-domain", "an-event")
        event_bus = EventBus('TWYLA_')
        event = EventPayload(
            event_name='a-domain.an-event',
            content={
                'name': 'test-name-content',
                'text': 'test-text-content',
            },
            context={
                'channel': 'test-channel',
                'channel_user': {
                    'name': 'test-name',
                    'id': 24
                }
            }
        )
        async def doit():
            await event_bus.emit(event)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(doit())
        messages = self.rabbit.get_messages('a-domain.an-event.testing')
        assert len(messages) == 1
        message = EventPayload.from_json(messages[0]['payload'])
        assert message.event_name == 'a-domain.an-event'
        assert message.content['name'] == 'test-name-content'


    def test_listen(self):
        event_payload = EventPayload(
            event_name='other-domain.to-be-listened',
            content={
                'name': 'test-name-content',
                'text': 'test-text-content',
            },
            context={
                'channel': 'test-channel',
                'channel_user': {
                    'name': 'test-name',
                    'id': 24
                }
            }
        )

        event_bus = EventBus('TWYLA_')
        received = []
        async def event_callback(event):
            received.append(event)
            await event.ack()

        async def doit():
            # the first listen call is to create and bind the queue
            await event_bus.listen('other-domain.to-be-listened', 'testing', event_callback)
            self.rabbit.publish_message('other-domain', 'to-be-listened', event_payload.to_json())
            await event_bus.listen('other-domain.to-be-listened', 'testing', event_callback)


        loop = asyncio.get_event_loop()
        loop.run_until_complete(doit())
        assert len(received) == 1
        event = received[0]
        assert isinstance(event, Event)
        event.validate()
        assert event.event_name == 'other-domain.to-be-listened'




    @mock.patch('twyla.service.event_bus.queues')
    def test_cancel_on_disconnect(self, mock_queues):
        # 'mock' queue manager with an instance that we control to test the
        # disconnect callback more easily.
        qm = queues.QueueManager('TWYLA_')
        mock_queues.QueueManager.return_value = qm


        async def consumer_callback(channel, body, envelope, properties):
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

        async def listen():
            event_bus = EventBus('TWYLA_')
            await event_bus.listen('a-domain.to-be-listened', 'testing', consumer_callback)

        async def stopper():
            while qm.protocol is None:
                await asyncio.sleep(1)
            await qm.protocol.close()


        tasks = [asyncio.ensure_future(listen()), asyncio.ensure_future(stopper())]

        loop = asyncio.get_event_loop()
        with pytest.raises(CancelledError):
            loop.run_until_complete(asyncio.wait(tasks))
