from aioamqp.protocol import OPEN

import twyla.service.queues as queues


async def listen(event_name):
    """
    listen is a small package level wrapper around QueueManager.listen for ease
    of use.

    Usage:
        import asyncio
        import twyla.service.events as events


        async def main():
            async for msg in events.listen('domain.event_name'):
                print(msg.body)
                await msg.ack()


        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    """
    qm = queues.QueueManager()
    await qm.connect()
    async for event in qm.listen(event_name):
        yield event


async def load(event_name):
    """
    Load the schema for the event and create a pydantic class.
    """
    pass


# qm is used to emit events to the exchange.
package_qm = None


async def emit(event_name, data={}):
    global package_qm
    if package_qm is None or package_qm.protocol.state != OPEN:
        package_qm = queues.QueueManager()
        await package_qm.connect()
    await package_qm.emit(event_name, data)
