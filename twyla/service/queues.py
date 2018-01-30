import asyncio
import json
import logging
import os

import aioamqp
from aioamqp.protocol import OPEN
from twyla.service.message import Event

# TODO: add actual logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def load_config():
    """
    load_config is used to get RabbitMQ configuration from the environment.
    """

    config = {}
    config['host'] = os.environ.get('TWYLA_RABBITMQ_HOST', 'localhost')
    config['port'] = os.environ.get('TWYLA_RABBITMQ_PORT', '5672')
    config['user'] = os.environ.get('TWYLA_RABBITMQ_USER', 'guest')
    config['pass'] = os.environ.get('TWYLA_RABBITMQ_PASS', 'guest')
    config['exchange'] = os.environ.get('TWYLA_RABBITMQ_EXCHANGE', 'events')
    config['vhost'] = os.environ.get('TWYLA_RABBITMQ_VHOST', '/')

    return config


class QueueManager:
    def __init__(self):
        self.config = load_config()
        self.protocol = None
        self.channel = None
        self.loop = asyncio.get_event_loop()


    async def connect(self):
        await self.get_connection()
        self.channel = await self.protocol.channel()
        await self.declare()


    async def get_connection(self):
        _, protocol = await aioamqp.connect(
            self.config['host'],
            self.config['port'],
            self.config['user'],
            self.config['pass'],
            self.config['vhost'],
            loop=self.loop
        )

        self.protocol = protocol


    async def declare(self):
        await self.channel.exchange_declare(
            exchange_name=self.config['exchange'],
            type_name='topic',
            durable=True)


    # Binding queues is only relevant for listeners, publishing will be done to
    # the exchange.
    async def bind_queue(self, name):
        await self.channel.queue_declare(name, durable=True)
        await self.channel.queue_bind(
            exchange_name=self.config['exchange'],
            queue_name=name,
            routing_key=name)


    async def stop(self):
        try:
            if self.channel is not None and self.channel.is_open:
                await self.channel.close()
            if self.protocol is not None and self.protocol.state is OPEN:
                await self.protocol.close()
        except:  # pylint: disable=bare-except
            pass


    async def emit(self, event_name, payload):
        # Try to json.dumps if the payload is not a string or bytes
        if not isinstance(payload, str) and not isinstance(payload, bytes):
            payload = json.dumps(payload)

        await self.channel.publish(
            payload=payload,
            exchange_name=self.config['exchange'],
            routing_key=event_name)


    async def listen(self, event_name):
        buff = asyncio.Queue()
        await self.bind_queue(event_name)

        async def callback(channel, body, envelope, properties):
            # TODO: make properly validated message
            msg = Event(channel=channel, body=body, envelope=envelope)
            await buff.put(msg)

        await self.channel.basic_consume(callback=callback,
                                         queue_name=event_name)
        while True:
            msg = await buff.get()
            buff.task_done()
            yield msg
