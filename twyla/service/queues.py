import aioamqp


class QueueManager:

    def __init__(self, queue_url):
        self.queue_url = queue_url


    async def connect(self):
        pass
