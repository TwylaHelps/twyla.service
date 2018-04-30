import unittest
import unittest.mock as mock

from twyla.service.test import helpers
from twyla.service import events

class QueueMock:
    def __init__(self):
        self.listeners = []
        self.connected = False

    async def connect(self):
        self.connected = True

    async def listen(self, event_name, callback):
        self.listeners.append((event_name, callback))


class EventsTests(unittest.TestCase):

    @mock.patch('twyla.service.events.queues')
    def test_listen(self, mock_queues):
        qm = QueueMock()
        mock_queues.QueueManager.return_value = qm

        event_bus = events.EventBus('TWYLA_', 'testing', ['a-domain.an-event'])

        async def callback(*args, **kwargs):
            pass

        helpers.aio_run(event_bus.listen('a-domain.an-event', callback))
        assert qm.connected
        assert len(qm.listeners) == 1
        assert qm.listeners[0] == ('a-domain.an-event', callback)
