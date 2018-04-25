import unittest
import unittest.mock as mock

import pydantic
import pytest

import twyla.service.message as message
import twyla.service.test.helpers as helpers


class PayloadTest(unittest.TestCase):
    def setUp(self):
        self.content_schema = '''
        {
            "$schema": "http://json-schema.org/draft-06/schema#",
            "title": "Request",
            "description": "A test request",
            "type": "object",
            "properties": {
                "name": { "type": "string" },
                "text": { "type": "string" }
            }
        }
        '''

        self.context_schema = '''
        {
            "$schema": "http://json-schema.org/draft-06/schema#",
            "title": "ShopContext",
            "description": "A test context",
            "type": "object",
            "properties": {
                "channel": { "type": "string" },
                "channel_user": { 
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" },
                        "id": { "type": "number" }
                    }
                }
            }
        }
        '''

        self.test_body = '''
        {
            "event_name": "Request",
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

    def test_payload_parsing(self):
        payload = message.EventPayload.parse_raw(self.test_body)
        payload = payload.validate(self.content_schema, self.context_schema)

        assert isinstance(payload.meta, message.Meta)
        assert isinstance(payload.content, dict)
        assert isinstance(payload.context, dict)

        assert payload.event_name == 'Request'
        assert payload.content['name'] == 'test-name'
        assert payload.content['text'] == 'test-text'
        assert payload.context['channel'] == 'test-channel'
        assert payload.context['channel_user']['name'] == 'test-user'
        assert payload.context['channel_user']['id'] == 24

    def test_payload_serialization_roundtrip(self):
        payload = message.EventPayload.parse_raw(self.test_body)
        payload = payload.validate(self.content_schema, self.context_schema)
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
