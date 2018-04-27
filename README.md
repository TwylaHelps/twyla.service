[![Build Status](https://travis-ci.org/TwylaHelps/twyla.service.svg?branch=master)](https://travis-ci.org/TwylaHelps/twyla.service)
[![codecov](https://codecov.io/gh/TwylaHelps/twyla.service/branch/master/graph/badge.svg)](https://codecov.io/gh/TwylaHelps/twyla.service)

# Twyla Service

The Twyla Service library provides primitives to build micro services that just
work within the Twyla platform.

## Table of Contents

- [Installation](#installation)
- [RPC](#rpc-not-yet-implemented)
  - [Using RPC Requests](#using-rpc-requests)
  - [Managing Changes](#managing-changes)
- [Event Bus](#event-bus)
  - [Creating Events](#creating-events)
  - [Listening to Events](#listening-to-events)
  - [Managing Changes](#managing-changes-1)
- [Service Contracts](#service-contracts)
- [Logging/Tracing](#logging-tracing)

## Installation

- Clone this repository to your machine.
- `cd` to the directory and run `pipenv install --dev`.
- Make sure that all tests pass: `pytest`.

## Configuration

The configuration values are read from environment variables whose names should
have the same prefix. This prefix should be passed to the `EventBus` class on
initialization. If the prefix is `EVENT_BUS`, for example, the following values
should be set in the environment:

```
EVENT_BUS_AMQP_HOST
EVENT_BUS_AMQP_PORT
EVENT_BUS_AMQP_USER
EVENT_BUS_AMQP_PASS
EVENT_BUS_AMQP_VHOST
```

## RPC (not yet implemented)

Remote procedure calls are used for synchronous communication between services
and to communicate with the integrations. RPC is done via the HTTP protocol.

The RPC implementation is a wrapper around the Python `aiohttp` library.

### Using RPC Requests

    import asyncio
    import twyla.service.rpc as rpc

    run = asyncio.get_event_loop().run_until_complete
    res = run(rpc.call('navitaire-api.get_booking', data={'pnr': 'A1324B'}))


### Managing Changes

See the Managing Changes section of the Event Bus. Most of those points apply to
RPC as well.


## Event Bus

Events are used for asynchronous communication between services.

Events are emitted by services to either signal a state change (e.g. change of
user data, start of a proxy session to a 3rd party bot or service) or request
information from other services within the platform (e.g. query information
about a booking).

The latter is similar to RPC but decouples the request from awaiting and
processing the response. The main disadvantage of this method of requesting
information compared to RPC is the lack of a guaranteed response (RPC requests
will always have a success, failure, or timeout response).


### Creating Events

Events have to implement a specific contract that defines the structure and
value types within the structure of the event. Pydantic is used to parse and
validate events.

For validation, a content schema set and context schema have to be defined using `twyla.service.message.get_schemata`. These schemata have to conform to [JSONSchema](json-schema.org).

    import twyla.service.message as message

    an_event_content_schema =
    '''
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


    context_schema =
    '''
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

The event can either implement one of the predefined contracts in this library
or an automatically discovered contract that gets exposed by the services that
listen to a particular event.

    import twyla.service.events as events
    import twyla.service.message as message
    import twyla.service.test.helpers as helpers

    payload = message.EventPayload(
        event_name='integration',
        content={'emission': 'Hello, there'},
        context={
            'tenant': 'test-tenant',
            'channel-id': 1
        }
    )

    helpers.aio_run(events.emit('test-event', payload))

The capability to discover event schemata decouples the provider of the schema
from the service using it (e.g. environment, configuration files, or other
services).

Events get augmented with additional information when emitted. Every event gets
an ID that is used for correlation in tracing by passing it on in events that
are related down the line. If an event is the start of the chain then a new ID
is generated. Additional metadata includes the timestamp and version).

Events can also be emitted as dicts. Those will be automatically serialized but
will get dropped by consumers that fail to validate them.

    import twyla.service.events as events
    import twyla.service.message as message
    import twyla.service.test.helpers as helpers

    payload = {
        'message_type': 'integration',
        'tenant': 'test-tenant',
        'bot_slug': 'test-slug',
        'channel': 'test-channel',
        'channel_user_id': 'test-user-id',
        'content': {}
    }

    helpers.aio_run(events.emit('test-event', payload))


### Listening to Events

Events get provided by an async generator and all business logic can be fully
controlled within the scope of the services.

    import twyla.service.events as events
    import twyla.service.test.helpers as helpers

    async def consumer(event_name):
        async for event in events.listen(event_name):
            print(event.to_json())
            # Do more things with the event
            await event.ack()

    helpers.aio_run(consumer('test-event'))

> NOTE: Providing events from a generator lets the developer take care of side
> effects more easily than in a callback based system. It is generally more easy
> to reason about the listener that way as all logic and resources can be kept
> in the service scope (no hidden magic). It is very easy to mock the listener
> entirely with `helpers.AsyncMock`s as well.


### Managing Changes

Sometimes events have to be changed. Changes to contracts between independent
services have to be done carefully and in a particular way to avoid version
conflicts.

Small events: Events should always only carry the information they require and
it is usually better to create a new event than expanding an existing one unless
all listeners will require the new information and the scope of the event stays
exactly the same. This will make changes easier due to better decoupling and
smaller overall event scope.

Additive changes: Changes should always be additive. Implementation of additive
changes will always be easier to do in a compatible way with additional data
than with changed data. Deprecation of old attributes will be easier as well and
using additive changes means services stay backwards compatible with one another
even in cases where consumers or producers have to be rolled back.

Consumer first: always implement and deploy changes in consumers first and make
sure the consumer is compatible to the old and new version of the contract. Once
the consumers fully accept the new version of the contract implementation of the
changes in the producer can safely be deployed. This is especially required in
cases where producers live outside of the system and can not be easily rolled
back (like mobile apps).

## Service Contracts

TBD


## Logging/Tracing

For logging utilities, check [twyla.logging](https://github.com/TwylaHelps/twyla.logging).
