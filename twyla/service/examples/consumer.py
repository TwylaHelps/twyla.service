from concurrent.futures._base import CancelledError
import asyncio
import os

import twyla.service.events as events


async def listener(event_name):
    async for e in events.listen(event_name):
        print(e.body)
        await e.ack()


os.environ['TWYLA_RABBITMQ_HOST'] = 'localhost'
os.environ['TWYLA_RABBITMQ_PORT'] = '5672'
os.environ['TWYLA_RABBITMQ_USER'] = 'guest'
os.environ['TWYLA_RABBITMQ_PASS'] = 'guest'
os.environ['TWYLA_RABBITMQ_EXCHANGE'] = 'events_test'
os.environ['TWYLA_RABBITMQ_VHOST'] = '/'
os.environ['TWYLA_RABBITMQ_PREFIX'] = 'test-service'

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(listener('my-events'))
except CancelledError:
    print('Lost connection. Done.')
