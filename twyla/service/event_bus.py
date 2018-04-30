from aioamqp.protocol import OPEN

from twyla.service import queues
from twyla.service.event import Event

class MessageToEventAdapter:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, channel, body, envelope, properties):
        event = Event(channel, body, envelope)
        await self.callback(event)


class EventBus:

    def __init__(self, config_prefix: str, group: str):
        self.config_prefix = config_prefix
        self.group = group
        self.queue_manager = queues.QueueManager(config_prefix, group)


    async def listen(self, event_name, callback):
        await self.queue_manager.connect()
        await self.queue_manager.listen(event_name, MessageToEventAdapter(callback))


    async def emit(self, event):
        await self.queue_manager.connect()
        data = event.to_json()
        await self.queue_manager.emit(event.event_name, data)
