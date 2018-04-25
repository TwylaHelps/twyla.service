import json

from datetime import datetime
from uuid import UUID, uuid4
from typing import List

import jsonschema
from pydantic import BaseModel, ValidationError

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


class EventPayload(BaseModel):
    event_name: str
    content: dict
    context: dict
    meta: Meta = Meta()

    def validate(self, content_schema, context_schema):
        content_schema = json.loads(content_schema)
        assert self.event_name == content_schema['title']
        
        jsonschema.validate(self.content, content_schema)
        jsonschema.validate(self.context, json.loads(context_schema))
        return self

    def to_json(self):
        return jsontool.dumps(self.dict())
