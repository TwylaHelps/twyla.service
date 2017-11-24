import unittest
import asyncio

from twyla.service import queues

class QueueManagerTests(unittest.TestCase):

    def test_connect(self):
        manager = queues.QueueManager('amqp://queue/url')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager.connect())
