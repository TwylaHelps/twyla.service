from datetime import datetime
from uuid import UUID, uuid4
from typing import List

from pydantic import BaseModel, ValidationError, validator

import twyla.service.jsontool as jsontool


class Event:
    def __init__(self, channel, body, envelope, name):
        self.channel = channel
        self.body = body
        self.envelope = envelope
        self.name = name

    async def payload(self):
        """
        The payload method is where the deserialization and validation of the
        event body happens. It returns an EventPayload object. The schema for
        deserialization and validation is loaded from a central schema service.
        """

        try:
            payload = EventPayload.parse_raw(self.body)
        except ValidationError:
            await self.drop()
            raise

        return payload

    async def ack(self):
        if self.channel is not None:
            await self.channel.basic_client_ack(
                delivery_tag=self.envelope.delivery_tag)

    async def reject(self):
        if self.channel is not None:
            await self.channel.basic_reject(
                delivery_tag=self.envelope.delivery_tag,
                requeue=True)

    async def drop(self):
        if self.channel is not None:
            await self.channel.basic_reject(
                delivery_tag=self.envelope.delivery_tag,
                requeue=False)


class Meta(BaseModel):
    version: int = 1
    timestamp: datetime = datetime.now()
    session_id: UUID = uuid4()


class IntegrationRequestContent(BaseModel):
    integration_type: str
    request_type: str
    queue_response: bool


class ControlContent(BaseModel):
    condition: str
    extra_info: List[str]


class Context(BaseModel):
    tenant: str
    bot_slug: str
    channel: str
    channel_user_id: str


class EventPayload(BaseModel):
    event_name: str
    content: dict
    context: Context
    meta: Meta = Meta()

    @validator('content', whole=True)
    def check_content(cls, v, values, **kwargs):
        '''
        Use pydantic as the validator for content and simply
        return the dict if valid.
        It should raise an exception otherwise.
        '''
        try:
            {
                'control': ControlContent,
                'integration-request': IntegrationRequestContent
            }[values['event_name']](**v)
            return v
        except ValidationError as error:
            raise Exception(error) from None

    def to_json(self):
        return jsontool.dumps(self.dict())
