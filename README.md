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

Events are used for asynchronous communication between services. They are
emitted by services to either signal a state change (e.g. change of user data,
start of a proxy session to a 3rd party bot or service) or to demand the
execution of a command (changing persistent state, generating a report etc.). An
event in twyla.service is embodied by the `twyla.service.event.Event` class,
which has a `payload` field that encapsulates the data, and various methods to
acknowledge, reject or drop the event. The `payload` field is of the type
`twyla.service.event.EventPayload`. The `EventPayload` class has the following
fields:

- `event_name: str`: A name that consists of a domain and an event type,
  separeted by a dot.

- `content: dict`: The event contents which will be serialized to JSON and
  transmitted to listeners.

- `context: dict`: Contextual data that is necessary for the proper processing
  of the content.

- `meta: dict`: Meta-information for correlation and debugging.

The `meta` field is generated automatically, and contains the following:

- `version: int`: The version of the message protocol

- `timestamp`: The time the event was generated

- `session_id`: A random UUID for tracing


### Validating Events

Both listeners and producers have to set validators for the events processed by
twyla.service. For this purpose, `twyla.service.message.get_schemata` can be
used to set schemata in the [JSONSchema](json-schema.org) format, as in the
following sample:

```Python
from twyla.service import event

content_schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Content",
    "description": "User input",
    "type": "object",
    "properties": {
        "emission": {"description": "Some emission",
                     "type": "string"},
        "user_id": {"description": "ID of the user",
                    "type": "string"}
    }
}

content_schema_set = {
    'api.user_input': 'content_schema'
}


context_schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Context",
    "description": "Some context",
    "type": "object",
    "properties": {
        "tenant": {"description": "The tenant",
                   "type": "string"},
        "channel-id": {"description": "ID of communication channel",
                       "type": "integer"}
    }
}

event.set_schemata(content_schema_set, context_schema)
```

twyla.service will then validate both incoming and outgoing events from a
service during operation.

### Raising Events

Picking off from the event validation sample above, here is an example of how to
raise an event:

```Python
import asyncio
from twyla.service.event_bus import EventBus

event_bus = EventBus('EVENT_BUS_')

payload = message.EventPayload(
    event_name='api.user_input',
    content={'emission': 'Hello, there',
             'user_id': 'abc123'},
    context={
        'tenant': 'test-tenant',
        'channel-id': 678
    }
)

loop = asyncio.get_event_loop()
loop.run_until_complete(EventBus.emit('test-event', payload))
```

### Listening to Events

Events get provided by an async generator and all business logic can be fully
controlled within the scope of the services.

```Python
from pprint import pprint
from twyla.service import event
from twyla.service.event_bus import EventBus

async def callback(event):
    pprint(event.to_json())

event_bus = EventBus('EVENT_BUS_')
event_bus.listen('api.user_input', 'consumer', callback)
event_bus.main()
```

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
