# Twyla Service

The Twyla Service library provides primitives to build micro services that just
work within the Twyla platform.

## RPC

Remote procedure calls are used for synchronous communication between services
and to communicate with the integrations. RPC is done via the HTTP protocol.

The RPC implementation is a wrapper around the Python `aiohttp` library.

### Using RPC requests

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

The letter is similar to RPC but decouples the request from awaiting and
processing the response. The main disadvantage of this method of requesting
information compared to RPC is the lack of a guaranteed response (RPC requests
will always have a success, failure, or timeout response).


### Creating Events

Events have to implement a specific contract that defines the structure and
value types within the structure of the event.

The event can either either implement one of the predefined contracts in this
library or an automatically discovered contract that gets exposed by the
services that listen to a particular event.

    import twyla.service.event as event

    generic = event.contracts.Generic(name='generic_event', data={})
    generic.emit(data={'id': 'some-event-id'})

    create_user = event.discover('create_user')
    create_user.emit(data={'name': 'Homer'})

The capability to discover event schemata decouples the provider of the schema
from the service using it (e.g. environment, configuration files, or other
services).

Events get augmented with additional information when emitted. Every event gets
an ID that is used for correlation in tracing by passing it on in events that
are related down the line. If an event is the start of the chain then a new ID
is generated. Additional metadata includes the timestamp and emitting service).

### Emitting Events

    import twyla.service.event as event

    data={'user_id': '1234', 'name': 'Bart'}
    update_user = event.discover('client_app.update_user')
    update_user.emit(data)


### Listing to Events

    import twyla.service.event as event

    listener = event.listen('client_app.update_user')
    while update_event in listener:
        print(update_event.body)

> NOTE: Providing events from a generator lets the developer take care of side
> effects more easily than in a callback based system. It is generally more easy
> to reason about the listener that way as all logic can be kept in one place.
> It is very easy to mock the listener entirely with `MagicMock`s as well.

### Managing Changes

Sometimes events have to changed. Changes to contracts between independent
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

TBD

<!--  LocalWords:  integrations RPC Twyla namespaced DNS Kubernetes
 -->

> Notes:
> RPC is naturally namespaced, the name of services is exposed via
> Kubernetes service (DNS)
> events should be namespaced within a named business context
