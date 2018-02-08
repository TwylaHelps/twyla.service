import unittest
import unittest.mock as mock

import pydantic
import pytest

import twyla.service.message as message
import twyla.service.test.helpers as helpers


class PayloadTest(unittest.TestCase):
    def setUp(self):
        self.test_body = '''
        {
            "tenant": "test-tenant",
            "message_type": "integration-request",
            "bot_slug": "slow-slug",
            "content": {},
            "channel": "fbmessenger",
            "channel_user_id": "some-user-id"
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

        assert isinstance(payload.meta, message.Meta)
        assert isinstance(payload.content, message.Content)
        assert payload.tenant == 'test-tenant'
        assert payload.message_type == 'integration-request'
        assert payload.bot_slug == 'slow-slug'
        assert payload.channel == 'fbmessenger'
        assert payload.channel_user_id == 'some-user-id'


    def test_payload_serialization_roundtrip(self):
        payload = message.EventPayload.parse_raw(self.test_body)
        raw_json = payload.to_json()

        new_payload = message.EventPayload.parse_raw(raw_json)

        assert payload.meta.timestamp == new_payload.meta.timestamp
        assert payload.meta.session_id == new_payload.meta.session_id
        assert payload.message_type == new_payload.message_type
        assert payload.bot_slug == new_payload.bot_slug
        assert payload.channel == new_payload.channel
        assert payload.channel_user_id == new_payload.channel_user_id


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
