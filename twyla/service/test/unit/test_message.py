import unittest
import unittest.mock as mock

import pydantic
import pytest

import twyla.service.message as message
import twyla.service.test.helpers as helpers
import twyla.service.test.common as common


class PayloadTest(unittest.TestCase):
    def setUp(self):
        self.content_schema_set, self.context_schema  = common.schemata_fixtures()

        self.test_body = '''
        {
            "event_name": "an-event",
            "content": {
                "name": "test-name",
                "text": "test-text"
            },
            "context": {
                "channel": "test-channel",
                "channel_user": {
                    "name": "test-user",
                    "id": 24
                }
            }
        }
        '''

        self.invalid_test_body = '''
        {
            "message_type": "integration-request",
            "bot_slug": "slow-slug",
            "content": {},
            "channel": "fbmessenger",
            "channel_user_id": "some-user-id"
        }
        '''

        message._CONTENT_SCHEMA_SET = None
        message._CONTEXT_SCHEMA = None

    def test_schemata_are_empty_when_not_yet_set(self):
        content_schema_set, context_schema = message.get_schemata()
        assert content_schema_set is None
        assert context_schema is None

    def test_validation_with_no_schemata_set(self):
        payload = message.EventPayload.parse_raw(self.test_body)
        with pytest.raises(Exception):
            payload.validate()

    def test_validation_with_only_content(self):
        message.set_schemata(self.content_schema_set, None)
        payload = message.EventPayload.parse_raw(self.test_body)
        with pytest.raises(Exception):
            payload.validate()

    def test_set_schemata_with_incorrect_content_schemata_set(self):
        with pytest.raises(AssertionError):
            message.set_schemata(self.invalid_test_body, self.context_schema)
    
    def test_set_schemata_happy_path(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        content_schema_set, context_schema = message.get_schemata()
        assert content_schema_set == self.content_schema_set
        assert context_schema == self.context_schema

    def test_payload_parsing(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        payload = message.EventPayload.parse_raw(self.test_body)
        payload = payload.validate()

        assert isinstance(payload.meta, message.Meta)
        assert isinstance(payload.content, dict)
        assert isinstance(payload.context, dict)

        assert payload.event_name == 'an-event'
        assert payload.content['name'] == 'test-name'
        assert payload.content['text'] == 'test-text'
        assert payload.context['channel'] == 'test-channel'
        assert payload.context['channel_user']['name'] == 'test-user'
        assert payload.context['channel_user']['id'] == 24

    def test_payload_serialization_roundtrip(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        payload = message.EventPayload.parse_raw(self.test_body)
        payload = payload.validate()
        raw_json = payload.to_json()

        new_payload = message.EventPayload.parse_raw(raw_json)

        assert payload.meta.timestamp == new_payload.meta.timestamp
        assert payload.meta.session_id == new_payload.meta.session_id
        assert payload.event_name == new_payload.event_name
        assert payload.content['name'] == new_payload.content['name']
        assert payload.content['text'] == new_payload.content['text']
        assert payload.context['channel'] == new_payload.context['channel']
        assert payload.context['channel_user']['name'] == new_payload.context['channel_user']['name']
        assert payload.context['channel_user']['id'] == new_payload.context['channel_user']['id']

    def test_event_class(self):
        message.set_schemata(self.content_schema_set, self.context_schema)
        mock_envelope = mock.MagicMock()
        mock_envelope.delivery_tag = 1
        mock_channel = helpers.AsyncMock()
        event = message.Event(
            channel=mock_channel,
            body=self.test_body,
            envelope=mock_envelope,
            name='get_booking')

        payload = helpers.aio_run(event.payload())

        assert isinstance(payload, message.EventPayload)

        helpers.aio_run(event.ack())
        event.channel.basic_client_ack.assert_called_once_with(
            mock_channel,
            delivery_tag=1)

        helpers.aio_run(event.reject())
        event.channel.basic_reject.assert_called_with(
            mock_channel,
            delivery_tag=1,
            requeue=True)

        helpers.aio_run(event.drop())
        event.channel.basic_reject.assert_called_with(
            mock_channel,
            delivery_tag=1,
            requeue=False)

        assert event.channel.basic_reject.call_count == 2

    def test_event_class_bad_body(self):
        event = message.Event(
            channel=helpers.AsyncMock(),
            body=self.invalid_test_body,
            envelope=mock.MagicMock(),
            name='get_booking')

        with pytest.raises(pydantic.ValidationError):
            helpers.aio_run(event.payload())
