import json

from datetime import datetime
from uuid import UUID, uuid4
from typing import List

import jsonschema
from pydantic import BaseModel, ValidationError

import twyla.service.jsontool as jsontool

def split_event_name(event_name: str):
    assert "." in event_name, "Event names should be of format domain.event_name"
    return event_name.split('.', 1)


class Event:

    def __init__(self, channel, body, envelope):
        self.channel = channel
        self.body = body
        self.envelope = envelope
        self.payload = None
        self.event_name = None
        self.domain = None
        self.event_type = None


    def validate(self):
        self.payload = EventPayload.from_json(self.body)
        self.event_name = self.payload.event_name
        self.domain, self.event_type = split_event_name(self.event_name)


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


_CONTENT_SCHEMA_SET = None
_CONTEXT_SCHEMA = None


def set_schemata(content_schema_set, context_schema):
    global _CONTENT_SCHEMA_SET, _CONTEXT_SCHEMA
    assert isinstance(content_schema_set, dict)
    _CONTENT_SCHEMA_SET = content_schema_set
    _CONTEXT_SCHEMA = context_schema


def get_schemata():
    return _CONTENT_SCHEMA_SET, _CONTEXT_SCHEMA


class EventPayload(BaseModel):
    event_name: str
    content: dict
    context: dict
    meta: Meta = Meta()

    def validate(self):
        content_schema_set, context_schema = get_schemata()
        content_schema = content_schema_set[self.event_name]

        if any([content_schema_set is None, context_schema is None]):
            raise Exception(
                '''
                Please set the schemata using twyla.service.message.set_schema:
                set_schema(content_schema_set, context_schema)
                '''
            )
        jsonschema.validate(self.content, content_schema)
        jsonschema.validate(self.context, context_schema)
        return self

    @classmethod
    def from_json(cls, jayson):
        payload = cls.parse_raw(jayson)
        payload = payload.validate()
        return payload

    def to_json(self):
        return jsontool.dumps(self.dict())
