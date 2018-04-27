import asyncio
import json
import logging
import sys

import aioamqp
from aioamqp.protocol import OPEN

import twyla.service.configuration as config
from twyla.service.message import Event

# TODO: add actual logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

def split_event_name(event_name: str):
    assert "." in event_name, "Event names should be of format domain.event_name"
    splat = event_name.split('.', 1)
    return splat[0], splat[1]



class QueueManager:

    def __init__(self, configuration_prefix, event_group):
        self.config = config.from_env(configuration_prefix)
        self.event_group = event_group
        self.protocol = None
        self.channel = None
        self.loop = asyncio.get_event_loop()


    async def connect(self):
        await self.get_connection()
        self.channel = await self.protocol.channel()
        return asyncio.ensure_future(self.cancel_on_disconnect())


    async def cancel_on_disconnect(self):
        await self.protocol.wait_closed()
        await self.stop()
        for task in asyncio.Task.all_tasks():
            # Cancel all pending tasks (this should be only the current method
            # and the event listener in most cases). Make sure to not cancel
            # this method.
            my_class_name = self.__class__.__name__
            my_method_name = sys._getframe().f_code.co_name
            my_name = f'{my_class_name}.{my_method_name}'
            task_name = task._coro.__qualname__

            # This checks if the task name is QueueManager.cancel_on_disconnect
            # in a refactoring friendly way.
            if task_name == my_name:
                continue

            # await self.protocol.wait_closed() will block this coroutine until
            # the connection to rabbit closes for any reason. Then the rest of
            # the function is executed cleaning the up all the things and
            # raising the CancelledError to <loop>.run_until_complete() runs
            # and by that passing handling of connection problems upwards in
            # the call stack.
            task.cancel()


    async def get_connection(self):
        _, protocol = await aioamqp.connect(
            self.config['amqp_host'],
            self.config['amqp_port'],
            self.config['amqp_user'],
            self.config['amqp_pass'],
            self.config['amqp_vhost'],
            loop=self.loop
        )

        self.protocol = protocol


    # Binding queues is only relevant for listeners, publishing will be done to
    # the exchange.
    async def bind_queue(self, event_name):
        domain, event = split_event_name(event_name)
        queue_name = f'{domain}.{event}.{self.event_group}'
        await self.channel.exchange_declare(
            exchange_name=domain,
            type_name='topic',
            durable=True)
        await self.channel.queue_declare(queue_name, durable=True)
        await self.channel.queue_bind(
            exchange_name=domain,
            queue_name=queue_name,
            routing_key=event)


    async def stop(self):
        if self.channel is not None and self.channel.is_open:
            await self.channel.close()
        if self.protocol is not None and self.protocol.state is OPEN:
            await self.protocol.close()


    async def emit(self, event_name, payload):
        # Declare the queue to make sure no messages get lost if no consumer
        # has connected, yet.
        await self.bind_queue(event_name)

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
            msg = Event(channel=channel,
                        body=body,
                        envelope=envelope,
                        name=event_name)
            await buff.put(msg)

        # queue_name = f'{self.config["prefix"]}-{event_name}'
        # await self.channel.basic_consume(callback=callback,
        #                                  queue_name=queue_name)
