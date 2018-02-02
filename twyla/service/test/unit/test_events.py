import unittest
import unittest.mock as mock

import twyla.service.test.helpers as helpers
import twyla.service.events as events


class EventsModuleTest(unittest.TestCase):
    @mock.patch('twyla.service.events.queues')
    def test_listen(self, mock_queues):
        async def async_gen_mock(val):
            yield val

        qm = mock_queues.QueueManager.return_value
        qm.connect = helpers.AsyncMock()
        qm.listen = async_gen_mock

        async def run_loop():
            async for event in events.listen('some-event'):
                assert event == 'some-event'
        helpers.aio_run(run_loop())

        qm.connect.assert_called_once_with(qm)


    def test_load(self):
        helpers.aio_run(events.load('some-event'))
