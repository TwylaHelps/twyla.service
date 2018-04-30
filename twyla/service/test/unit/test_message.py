import json
import unittest
import unittest.mock as mock
from types import SimpleNamespace as Bunch

import pydantic
import pytest

import twyla.service.message as message
import twyla.service.test.helpers as helpers
import twyla.service.test.common as common

EVENT_PAYLOAD = json.dumps(
    {"event_name": "a-domain.an-event",
     "content": {
         "name": "test-name",
         "text": "test-text"},
     "context": {
         "channel": "test-channel",
         "channel_user": {
             "name": "test-user",
             "id": 24
         }}
    })

INVALID_PAYLOAD = json.dumps(
    {"message_type": "integration-request",
     "bot_slug": "slow-slug",
     "content": {},
     "channel": "fbmessenger",
     "channel_user_id": "some-user-id"
    })


class MockChannel:

    def __init__(self):
        self.acked = []
        self.rejected = []
        self.dropoped = []

    async def basic_client_ack(self, delivery_tag):
        self.acked.append(delivery_tag)

    async def basic_reject(self, delivery_tag, requeue):
        self.rejected.append((delivery_tag, requeue))


class PayloadTest(unittest.TestCase):

    def setUp(self):
        self.content_schema_set, self.context_schema  = common.schemata_fixtures()
        message._CONTENT_SCHEMA_SET = None
        message._CONTEXT_SCHEMA = None


    def tearDown(self):
        message._CONTENT_SCHEMA_SET = None
        message._CONTEXT_SCHEMA = None


    def test_validation_with_no_schemata_set(self):
        with pytest.raises(Exception):
            payload = message.EventPayload.from_json(EVENT_PAYLOAD)


    def test_validation_with_only_content(self):
        message.set_schemata(self.content_schema_set, None)
        with pytest.raises(Exception):
            payload = message.EventPayload.from_json(EVENT_PAYLOAD)


    def test_set_schemata_with_incorrect_content_schemata_set(self):
        with pytest.raises(AssertionError):
            message.set_schemata(INVALID_PAYLOAD, self.context_schema)


    def test_set_schemata_happy_path(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        content_schema_set, context_schema = message.get_schemata()
        assert content_schema_set == self.content_schema_set
        assert context_schema == self.context_schema


    def test_payload_from_json(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        payload = message.EventPayload.from_json(EVENT_PAYLOAD)

        assert isinstance(payload.meta, message.Meta)
        assert isinstance(payload.content, dict)
        assert isinstance(payload.context, dict)

        assert payload.event_name == 'a-domain.an-event'
        assert payload.content['name'] == 'test-name'
        assert payload.content['text'] == 'test-text'
        assert payload.context['channel'] == 'test-channel'
        assert payload.context['channel_user']['name'] == 'test-user'
        assert payload.context['channel_user']['id'] == 24


    def test_payload_serialization_roundtrip(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        payload = message.EventPayload.from_json(EVENT_PAYLOAD)
        raw_json = payload.to_json()

        new_payload = message.EventPayload.from_json(raw_json)

        assert payload.meta.timestamp == new_payload.meta.timestamp
        assert payload.meta.session_id == new_payload.meta.session_id
        assert payload.event_name == new_payload.event_name
        assert payload.content['name'] == new_payload.content['name']
        assert payload.content['text'] == new_payload.content['text']
        assert payload.context['channel'] == new_payload.context['channel']
        assert payload.context['channel_user']['name'] == new_payload.context['channel_user']['name']
        assert payload.context['channel_user']['id'] == new_payload.context['channel_user']['id']


class EventTests(unittest.TestCase):

    def setUp(self):
        content_schema_set, context_schema  = common.schemata_fixtures()
        message.set_schemata(content_schema_set, context_schema)

    def tearDown(self):
        message._CONTENT_SCHEMA_SET = None
        message._CONTEXT_SCHEMA = None

    def test_ack_event(self):
        envelope = Bunch(delivery_tag=12345)
        mock_channel = MockChannel()
        event = message.Event(
            channel=mock_channel,
            body=EVENT_PAYLOAD,
            envelope=envelope,
            name='get_booking')

        payload = event.payload()

        assert isinstance(payload, message.EventPayload)

        helpers.aio_run(event.ack())
        assert len(mock_channel.acked) == 1
        assert mock_channel.acked[0] == 12345


    def test_reject_event(self):
        envelope = Bunch(delivery_tag=12345)
        mock_channel = MockChannel()
        event = message.Event(
            channel=mock_channel,
            body=EVENT_PAYLOAD,
            envelope=envelope,
            name='get_booking')

        helpers.aio_run(event.reject())
        assert len(mock_channel.rejected) == 1
        assert mock_channel.rejected[0] == (12345, True)


    def test_drop_event(self):
        envelope = Bunch(delivery_tag=12345)
        mock_channel = MockChannel()
        event = message.Event(
            channel=mock_channel,
            body=EVENT_PAYLOAD,
            envelope=envelope,
            name='get_booking')

        helpers.aio_run(event.drop())
        assert len(mock_channel.rejected) == 1
        assert mock_channel.rejected[0] == (12345, False)


    def test_event_class_bad_body(self):
        event = message.Event(
            channel=helpers.AsyncMock(),
            body=INVALID_PAYLOAD,
            envelope=mock.MagicMock(),
            name='get_booking')

        with pytest.raises(pydantic.ValidationError):
            helpers.aio_run(event.payload())
