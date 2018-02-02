import asyncio
import unittest.mock as mock


class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(self, *args, **kwargs)


aio_run = asyncio.get_event_loop().run_until_complete
