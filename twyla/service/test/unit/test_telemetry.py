# pylint: disable-msg=protected-access
import unittest
import unittest.mock

import twyla.service.telemetry as telemetry


class TelemetryTestCase(unittest.TestCase):
    class TestEvent:
        pass

    class TestEvent2:
        pass

    def setUp(self):

        # result will be used to record side effects
        self.result = None
        self.result2 = None
        self.result3 = None

        # Make sure we have some different handlers
        def _test_recorder(event):
            self.result = event

        def _test_recorder2(event):
            self.result2 = event

        def _test_recorder3(one, two, three):
            self.result3 = [one, two, three]

        self.test_recorder = _test_recorder
        self.test_recorder2 = _test_recorder2
        self.test_recorder3 = _test_recorder3

    def test_register_non_callable(self):
        t = telemetry.Telemetry()

        self.assertEqual(len(t._registry), 0)

        with self.assertRaises(TypeError):
            t.register(TelemetryTestCase.TestEvent, 'not callable')

    def test_register(self):
        t = telemetry.Telemetry()

        self.assertEqual(len(t._registry), 0)

        t.register(TelemetryTestCase.TestEvent, self.test_recorder)
        self.assertEqual(len(t._registry), 1)
        self.assertEqual(len(t._registry[TelemetryTestCase.TestEvent]), 1)
        self.assertEqual(t._registry[TelemetryTestCase.TestEvent][0],
                         self.test_recorder)

        t.register(TelemetryTestCase.TestEvent, self.test_recorder2)
        self.assertEqual(len(t._registry), 1)
        self.assertEqual(len(t._registry[TelemetryTestCase.TestEvent]), 2)
        self.assertEqual(t._registry[TelemetryTestCase.TestEvent][0],
                         self.test_recorder)
        self.assertEqual(t._registry[TelemetryTestCase.TestEvent][1],
                         self.test_recorder2)

    def test_deregister(self):
        t = telemetry.Telemetry()

        t.register(TelemetryTestCase.TestEvent, self.test_recorder)
        t.register(TelemetryTestCase.TestEvent, self.test_recorder2)

        t.deregister(TelemetryTestCase.TestEvent, self.test_recorder)
        self.assertEqual(len(t._registry), 1)
        self.assertEqual(len(t._registry[TelemetryTestCase.TestEvent]), 1)
        self.assertEqual(t._registry[TelemetryTestCase.TestEvent][0],
                         self.test_recorder2)

        t.register(TelemetryTestCase.TestEvent, self.test_recorder2)
        self.assertEqual(len(t._registry), 1)
        self.assertEqual(len(t._registry[TelemetryTestCase.TestEvent]), 2)

        t.deregister(TelemetryTestCase.TestEvent, self.test_recorder2)
        self.assertEqual(len(t._registry), 1)
        self.assertEqual(len(t._registry[TelemetryTestCase.TestEvent]), 0)

    def test_notify(self):
        t = telemetry.Telemetry()

        t.register(TelemetryTestCase.TestEvent, self.test_recorder)
        t.notify(TelemetryTestCase.TestEvent, 'event1')
        self.assertEqual(self.result, 'event1')
        self.assertIsNone(self.result2)

        # Reset side effects
        # pylint: disable-msg=attribute-defined-outside-init
        self.result1 = None
        self.result2 = None

        t.register(TelemetryTestCase.TestEvent, self.test_recorder2)
        t.notify(TelemetryTestCase.TestEvent, 'event1')
        self.assertEqual(self.result, 'event1')
        self.assertEqual(self.result2, 'event1')

        # Reset side effects and telemetry
        self.result1 = None
        self.result2 = None
        t = telemetry.Telemetry()

        t.register(TelemetryTestCase.TestEvent, self.test_recorder)
        t.register(TelemetryTestCase.TestEvent2, self.test_recorder2)
        t.notify(TelemetryTestCase.TestEvent, 'event1')
        self.assertEqual(self.result, 'event1')
        self.assertIsNone(self.result2)

        t.notify(TelemetryTestCase.TestEvent2, 'event2')
        self.assertEqual(self.result, 'event1')
        self.assertEqual(self.result2, 'event2')

    def test_notify_multi_args(self):
        class Events():
            def __init__(self, name):
                self.name = name

            def __getattr__(self, attr_name):
                return '.'.join([self.name, attr_name])

        chat_events = Events('chat')

        t = telemetry.Telemetry()
        t.register(chat_events.incoming, self.test_recorder3)
        self.assertIsNone(self.result3)
        t.notify(chat_events.incoming, 1, 2, 3)
        self.assertEqual(self.result3, [1, 2, 3])


class GraphiteTestCase(unittest.TestCase):
    class SocketRecorder:
        def __init__(self):
            self.recv = None

        def sendall(self, b: bytes):
            self.recv = b

        def close(self):
            pass

    def setUp(self):
        self.sock = GraphiteTestCase.SocketRecorder()

    def test_sending_data(self):
        client = telemetry.Graphite('localhost', 1234)
        client._get_socket = unittest.mock.MagicMock(
            return_value=self.sock)
        data = {
            'with_timestamp': ['metric.test', 1234, 1234],
            'without_timestamp': ['metric.test', 5678],
        }

        client.send(*data['with_timestamp'])
        self.assertEqual(self.sock.recv, b'metric.test 1234 1234\n')

        client.send(*data['without_timestamp'])
        self.assertTrue(self.sock.recv.startswith(b'metric.test 5678 '))
        self.assertFalse(self.sock.recv.endswith(b' 0\n'))

