import asyncio
import json
from concurrent.futures._base import CancelledError
import os
import pytest
import unittest
import unittest.mock as mock
import signal

from twyla.service.event_bus import EventBus
import twyla.service.queues as queues
import twyla.service.test.helpers as helpers
import twyla.service.test.common as common
from twyla.service.event import set_schemata, EventPayload, Event
from twyla.service.test.integration.common import RabbitRest
from twyla.service.test.common import QUEUE_CONFIG

async def noop(*args, **kwargs):
    pass



class TestQueues(unittest.TestCase):

    def setUp(self):
        set_schemata(*common.schemata_fixtures())
        self.rabbit = RabbitRest()


    def test_emit(self):
        self.rabbit.create_queue("a-domain.an-event.testing", "a-domain", "an-event")
        event_bus = EventBus(QUEUE_CONFIG)
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

        event_bus = EventBus(QUEUE_CONFIG)
        received = []
        async def event_callback(event):
            received.append(event)
            await event.ack()
        event_bus.listen('other-domain.to-be-listened', 'testing', event_callback)

        async def doit():
            await event_bus.start()
            self.rabbit.publish_message('other-domain', 'to-be-listened', event_payload.to_json())
            await event_bus.start()


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
        qm = queues.QueueManager(QUEUE_CONFIG)
        mock_queues.QueueManager.return_value = qm

        async def listen():
            event_bus = EventBus(QUEUE_CONFIG)
            event_bus.listen('a-domain.to-be-listened', 'testing', noop)
            await event_bus.start()

        async def stopper():
            while qm.protocol is None:
                await asyncio.sleep(1)
            await qm.protocol.close()


        tasks = [asyncio.ensure_future(listen()), asyncio.ensure_future(stopper())]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))
        open_tasks = [t for t in asyncio.Task.all_tasks() if not t.done()]
        assert len(open_tasks) == 0


    def test_main_task(self):
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
        event_bus = EventBus(QUEUE_CONFIG)
        received = []
        async def callback(event):
            received.append(event)
            await event.ack()

        event_bus.listen('third-domain.to-be-listened', 'testing', callback)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(event_bus.start())
        self.rabbit.publish_message('third-domain', 'to-be-listened', event_payload.to_json())

        loop.run_until_complete(event_bus.main_task(loop))
        # remove_signal_handler returns False if there was no handler for the
        # given signal
        assert loop.remove_signal_handler(signal.SIGINT)
        assert loop.remove_signal_handler(signal.SIGTERM)
        assert len(received) == 1
