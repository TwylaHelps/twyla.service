"""
This telemetry module contains a basic event handler.

Usage example:

    from twyla.api.telemetry import Telemetry

    incoming = lambda a, b, c: print(a, b, c)
    chat_metrics = Event('chat')

    t = Telemetry()
    t.register(chat_metrics.incoming, incoming)
    t.notify(chat_metrics.incoming, 1, 2, chat_metrics.incoming)

    # prints 1 2 chat.incoming

    # Telemetry has a default event instance named 'telemetry'
    t = Telemetry()
    t.register(t.event.incoming, incoming)
    t.notify(t.event.incoming, 1, 2, t.event.incoming)

    # prints 1 2 telemetry.incoming
"""

import socket
import time


# Event is a support class illustrated in the introductory usage example.
class Event:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, attr_name):
        return '.'.join([self.name, attr_name])


class Telemetry:
    def __init__(self, event: Event=Event('telemetry')):
        # The registry maps handlers to event classes
        self._registry = {}
        self.event = event

    def register(self, event_class, func):
        if not callable(func):
            raise TypeError('{} is not callable'.format(func))

        if event_class in self._registry.keys():
            self._registry[event_class].append(func)
        else:
            self._registry[event_class] = [func]

    def deregister(self, event_class, func):
        if event_class in self._registry.keys():
            # Remove all instances of func
            self._registry[event_class] = [f for f in
                                           self._registry[event_class]
                                           if f != func]

    def notify(self, event_class, *event):
        # Do nothing if the event class is unknown
        if event_class in self._registry.keys():
            for func in self._registry[event_class]:
                func(*event)

    def register_ticker(self, callback, attr: str):
        # Basic check if the callback is actually callable. Skipping signature
        # check as it is hard to do reliably anyway (me thinks)
        if not callable(callback):
            raise TypeError('The provided callback is not callable')

        name = getattr(self.event, attr)
        self.register(name, lambda: callback(name, 1))

    def register_timer(self, callback, attr: str):
        # Basic check if the callback is actually callable. Skipping signature
        # check as it is hard to do reliably anyway (me thinks)
        if not callable(callback):
            raise TypeError('The provided callback is not callable')

        name = getattr(self.event, attr)

        # call will be registered and closes over the callback (likely
        # graphite.send for now) and the name of the event that will be used as
        # parameter in the callback as well.
        #
        # t.register_timer(g.send, 'test')
        # t.notify(t.event.test, start_time)
        #
        # results in call(start_time) and thus
        # g.send(t.event.test, elapsed_time) being called.
        def call(start_time):
            elapsed_milli_seconds = (time.time() - start_time) * 1000
            callback(name, int(elapsed_milli_seconds))

        self.register(name, call)


class Graphite:
    def __init__(self, graphite_host: str='localhost', graphite_port: int=2003):
        super().__init__()
        self._graphite_server = (graphite_host, graphite_port)

    def _get_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self._graphite_server)

        return sock

    #pylint: disable-msg=bad-whitespace
    def send(self, name: str, value: int=0, timestamp: int=0):
        if not timestamp:
            timestamp = int(time.time())

        sock = self._get_socket()
        sock.sendall(bytes("%s %d %d\n" % (name, value, timestamp), 'ascii'))
        sock.close()