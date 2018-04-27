import asyncio
from concurrent.futures._base import CancelledError
import os
import pytest
import unittest
import unittest.mock as mock

import twyla.service.events as events
import twyla.service.queues as queues

class TestQueues(unittest.TestCase):

    def setUp(self):
        self.event_name = 'test-event'
        self.patcher = mock.patch.dict(
            os.environ,
            {'TWYLA_AMQP_HOST': 'localhost',
             'TWYLA_AMQP_PORT': '5672',
             'TWYLA_AMQP_USER': 'guest',
             'TWYLA_AMQP_PASS': 'guest',
             'TWYLA_AMQP_VHOST': '/'})
        self.patcher.start()


    def tearDown(self):
        self.patcher.stop()

    def test_load_configuration_with_prefix(self):
        qm = queues.QueueManager('TWYLA_', 'the-group')
        assert qm.config['amqp_host'] == 'localhost'
        assert qm.config['amqp_port'] == '5672'
        assert qm.config['amqp_user'] == 'guest'
        assert qm.config['amqp_pass'] == 'guest'
        assert qm.config['amqp_vhost'] == '/'
        assert qm.event_group == 'the-group'
