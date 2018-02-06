import asyncio
import os
from datetime import datetime
from uuid import uuid4

import twyla.service.events as events
import twyla.service.message as message


async def ticker(interval):
    while True:
        event_payload = message.EventPayload(
            message_type='integration',
            tenant='test-tenant',
            bot_slug='test-slug',
            channel='test-channel',
            channel_user_id='test-user-id',
            meta=message.Meta(uuid=uuid4(), timestamp=datetime.now())
        )
        await asyncio.sleep(interval)
        await events.emit('my-events', event_payload.to_json())


os.environ['TWYLA_RABBITMQ_HOST'] = 'localhost'
os.environ['TWYLA_RABBITMQ_PORT'] = '5672'
os.environ['TWYLA_RABBITMQ_USER'] = 'guest'
os.environ['TWYLA_RABBITMQ_PASS'] = 'guest'
os.environ['TWYLA_RABBITMQ_EXCHANGE'] = 'events_test'
os.environ['TWYLA_RABBITMQ_VHOST'] = '/'
os.environ['TWYLA_RABBITMQ_PREFIX'] = 'test-service'


loop = asyncio.get_event_loop()
loop.run_until_complete(ticker(2))
