import asyncio
import json
import logging

import aioamqp
from aioamqp.protocol import OPEN

from twyla.service.event import Event, split_event_name


class QueueManager:

    def __init__(self, queue_configuration):
        self.queue_configuration = queue_configuration
        self.protocol = None
        self.channel = None
        self.closed_event = asyncio.Event()
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        if self.protocol is not None and self.channel is not None:
            return
        _, protocol = await aioamqp.connect(
            self.queue_configuration['amqp_host'],
            self.queue_configuration['amqp_port'],
            self.queue_configuration['amqp_user'],
            self.queue_configuration['amqp_pass'],
            self.queue_configuration['amqp_vhost'],
            loop=self.loop
        )
        self.protocol = protocol
        self.channel = await self.protocol.channel()
        return asyncio.ensure_future(self.signal_on_disconnect())


    async def signal_on_disconnect(self):
        await self.protocol.wait_closed()
        self.closed_event.set()


    # Binding queues is only relevant for listeners, publishing will be done to
    # the exchange.
    async def bind_queue(self, event_name, event_group):
        domain, event_type = split_event_name(event_name)
        queue_name = f'{domain}.{event_type}.{event_group}'
        await self.declare_exchange(domain)
        await self.channel.queue_declare(queue_name, durable=True)
        await self.channel.queue_bind(
            exchange_name=domain,
            queue_name=queue_name,
            routing_key=event_type)
        return queue_name


    async def stop(self):
        if self.channel is not None and self.channel.is_open:
            await self.channel.close()
        if self.protocol is not None and self.protocol.state is OPEN:
            await self.protocol.close()


    async def declare_exchange(self, exchange_name):
        await self.channel.exchange_declare(exchange_name=exchange_name,
                                            type_name='topic',
                                            durable=True)


    async def emit(self, event_name, payload):
        # Try to json.dumps if the payload is not a string or bytes
        if not isinstance(payload, str) and not isinstance(payload, bytes):
            payload = json.dumps(payload)
        domain, event_type = split_event_name(event_name)
        retval = await self.channel.publish(
            payload=payload,
            exchange_name=domain,
            routing_key=event_type)

    async def listen(self, event_name, event_group, callback):
        queue_name = await self.bind_queue(event_name, event_group)
        await self.channel.basic_consume(callback=callback,
                                         queue_name=queue_name)
