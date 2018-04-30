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

    async def listen(self, event_name, callback):
        self.listeners.append((event_name, callback))


class EventsTests(unittest.TestCase):

    @mock.patch('twyla.service.event_bus.queues')
    def test_listen(self, mock_queues):
        qm = QueueMock()
        mock_queues.QueueManager.return_value = qm

        bus = event_bus.EventBus('TWYLA_', 'testing')

        async def callback(*args, **kwargs):
            pass

        helpers.aio_run(bus.listen('a-domain.an-event', callback))
        assert qm.connected
        assert len(qm.listeners) == 1
        assert qm.listeners[0] == ('a-domain.an-event', callback)
