import asyncio
import unittest
import unittest.mock as mock

from twyla.service.test import helpers
from twyla.service import event_bus


class QueueMock:

    def __init__(self):
        self.listeners = []
        self.connected = False

    async def connect(self):
        self.connected = True

    async def listen(self, event_name, event_group, callback):
        self.listeners.append((event_name, event_group, callback))


class EventsTests(unittest.TestCase):

    def test_message_to_event_adapter(self):
        passed_event = None

        async def msg_callback(event):
            nonlocal passed_event
            passed_event = event
        adapter = event_bus.MessageToEventAdapter(msg_callback)
        channel = object()
        envelope = object()

        async def doit():
            await adapter(channel, {}, envelope, None)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(doit())
        assert passed_event is not None
        assert passed_event.channel is channel
        assert passed_event.envelope is envelope

    @mock.patch('twyla.service.event_bus.queues')
    def test_listen(self, mock_queues):
        qm = QueueMock()
        mock_queues.QueueManager.return_value = qm

        bus = event_bus.EventBus('TWYLA_')

        async def callback(*args, **kwargs):
            pass
        bus.listen('a-domain.an-event', callback)

        bus.listen('a-domain.an-event', 'testing', callback)
        helpers.aio_run(bus.start())
        assert qm.connected
        assert len(qm.listeners) == 1
        assert qm.listeners[0][0] == 'a-domain.an-event'
        event_callback = qm.listeners[0][2]
        assert isinstance(event_callback, event_bus.MessageToEventAdapter)
