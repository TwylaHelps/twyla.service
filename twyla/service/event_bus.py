import sys
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
        self.run_stop_on_queue_close = True
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
        aio_loop.add_signal_handler(signal.SIGINT, self.signal_handler)
        aio_loop.add_signal_handler(signal.SIGTERM, self.signal_handler)
        self.queue_disconnect_future = asyncio.ensure_future(self.stop_on_queue_disconnect())
        try:
            await self.start()
        except: # pylint: disable-msg=bare-except
            logger.exception("Error running main event loop")
            aio_loop.stop()


    async def stop_on_queue_disconnect(self):
        await asyncio.wait_for(self.queue_manager.closed_event.wait(), None)
        if self.run_stop_on_queue_close:
            await self.stop_main()


    def signal_handler(self):
        asyncio.ensure_future(self.stop_main())


    async def stop_main(self):
        # The next two lines get rid of the stop_on_queue_disconnect task
        self.run_stop_on_queue_close = False
        self.queue_manager.closed_event.set()
        await self.queue_manager.stop()
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
        if self.aio_loop.is_running():
            self.aio_loop.stop()


    def main(self):
        self.aio_loop = asyncio.get_event_loop()
        try:
            logger.info("Starting twyla.service main event loop")
            self.aio_loop.create_task(self.main_task(self.aio_loop))
            # See http://bugs.python.org/issue23548
            atexit.register(self.aio_loop.close)
            self.aio_loop.run_forever()
        except: #pylint: disable-msg=bare-except
            logger.exception("Error running twyla.service Event Bus")
        finally:
            if self.aio_loop.is_running():
                self.aio_loop.stop()
