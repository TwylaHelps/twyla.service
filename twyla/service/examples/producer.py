import asyncio
import os
from datetime import datetime
from uuid import uuid4

import twyla.service.events as events
import twyla.service.message as message

an_event_content_schema = '''
    {
        "$schema": "http://json-schema.org/draft-06/schema#",
        "title": "Content",
        "description": "Some content",
        "type": "object",
        "properties": {
            "emission": {
                "description": "Some emission",
                "type": "string"
            }
        }
    }
'''

content_schema_set = {
    'an-event': an_event_content_schema
}

context_schema = '''
    {
        "$schema": "http://json-schema.org/draft-06/schema#",
        "title": "Context",
        "description": "Some context",
        "type": "object",
        "properties": {
            "tenant": {
                "description": "Some tenant",
                "type": "string"
            },
            "channel-id": {
                "description": "Some channel ID",
                "type": "integer"
            }
        }
    }
'''

message.set_schemata(content_schema_set, context_schema)

async def ticker(interval):
    while True:
        event_payload = message.EventPayload(
            event_name='integration',
            content={'emission': 'Hello, there'},
            context={
                'tenant': 'test-tenant',
                'channel-id': 1
            }
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
