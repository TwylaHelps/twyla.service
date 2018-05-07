import asyncio
import atexit
import signal
import logging
from aioamqp.protocol import OPEN

from twyla.service import queues
from twyla.service.event import Event

logger = logging.getLogger(__name__)

class MessageToEventAdapter:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, channel, body, envelope, properties):
        event = Event(channel, body, envelope)
        await self.callback(event)


class EventBus:

    def __init__(self, config_prefix: str):
        self.config_prefix = config_prefix
        self.event_listeners = {}
        self.queue_manager = queues.QueueManager(config_prefix)


    def listen(self, event_name: str, event_group: str, callback):
        self.event_listeners[event_name] = (callback, event_group)


    async def start(self):
        await self.queue_manager.connect()
        for event_name, (callback, group) in self.event_listeners.items():
            await self.queue_manager.listen(event_name, group, MessageToEventAdapter(callback))


    async def emit(self, event):
        await self.queue_manager.connect()
        data = event.to_json()
        await self.queue_manager.emit(event.event_name, data)


    async def main_task(self, aio_loop):
        for signame in ('SIGINT', 'SIGTERM'):
            aio_loop.add_signal_handler(
                getattr(signal, signame),
                lambda: asyncio.ensure_future(self.queue_manager.stop()))
        try:
            await self.start()
        except: # pylint: disable-msg=bare-except
            logger.exception("Error running main event loop")
            asyncio.ensure_future(self.queue_manager.stop())


    def main(self):
        aio_loop = asyncio.get_event_loop()
        try:
            logger.info("Starting twyla.service main event loop")
            aio_loop.create_task(self.main_task(aio_loop))
            # See http://bugs.python.org/issue23548
            atexit.register(aio_loop.close)
            aio_loop.run_forever()
        except: #pylint: disable-msg=bare-except
            logger.exception("Oops, error running Xpi")
        finally:
            if aio_loop.is_running():
                aio_loop.stop()
