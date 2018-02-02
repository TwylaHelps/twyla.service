import asyncio
import unittest
import twyla.service.events as events


async def main():
    async for event in events.listen('xpi.put_booking'):
        if event.message() == b'drop':
            await event.drop()
            print(f'dropped {event.body}')
        else:
            await event.ack()
            print(f'acked {event.body}')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())


class TestQueues(unittest.TestCase):
    def test_emit_listen_roundtrip(self):
        pass
