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


def load_config():
    """
    load_config is used to get RabbitMQ configuration from the environment.

    Required variables:
    Name                    | Example
    -------------------------------------
    TWYLA_RABBITMQ_HOST     | localhost
    TWYLA_RABBITMQ_PORT     | 5672
    TWYLA_RABBITMQ_USER     | guest
    TWYLA_RABBITMQ_PASS     | guest
    TWYLA_RABBITMQ_EXCHANGE | events
    TWYLA_RABBITMQ_VHOST    | /
    TWYLA_RABBITMQ_PREFIX   | xpi

    Every service should use a unique prefix; it will be used to prefix the
    queue names for the different events and allow multiple services to listen
    to the same events while multiple instances of the same service will be
    listening to the same queue.
    """

    return config.from_env('TWYLA_RABBITMQ_')


class QueueManager:
    def __init__(self):
        self.config = load_config()
        self.protocol = None
        self.channel = None
        self.loop = asyncio.get_event_loop()
        self.bound = False


    async def connect(self):
        await self.get_connection()
        self.channel = await self.protocol.channel()
        await self.declare()
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
        queue_name = f'{self.config["prefix"]}-{name}'
        await self.channel.queue_declare(queue_name, durable=True)
        await self.channel.queue_bind(
            exchange_name=self.config['exchange'],
            queue_name=queue_name,
            routing_key=name)
        self.bound = True


    async def stop(self):
        if self.channel is not None and self.channel.is_open:
            await self.channel.close()
        if self.protocol is not None and self.protocol.state is OPEN:
            await self.protocol.close()


    async def emit(self, event_name, payload):
        # Declare the queue to make sure no messages get lost if no consumer
        # has connected, yet.
        if not self.bound:
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

        queue_name = f'{self.config["prefix"]}-{event_name}'
        await self.channel.basic_consume(callback=callback,
                                         queue_name=queue_name)
        while True:
            msg = await buff.get()
            buff.task_done()
            yield msg
