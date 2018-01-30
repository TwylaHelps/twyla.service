from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, validator


class Event:
    def __init__(self, channel, body, envelope):
        self.channel = channel
        self.body = body
        self.envelope = envelope


    def payload(self):
        """
        The payload method is where the deserialization and validation of the
        event body happens. It returns a Message object.
        """
        return self.body


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


class Content(BaseModel):
    pass


class Meta(BaseModel):
    version: int = None
    timestamp: datetime = None
    session_id: UUID = None


class Message(BaseModel):
    message_type: str = None
    tenant: str = None
    bot_slug: str = None
    content: Content = None
    channel: str = None
    channel_user_id: str = None
    meta: Meta = None
