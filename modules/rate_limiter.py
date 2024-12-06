import asyncio
from functools import lru_cache


class RateLimiting:
    LIMIT: int = 25
    INTERVAL: int = 60  # in seconds

    def __init__(self):
        self.QUEUE: list = []
        self.SENT_MESSAGES: int = 0

    # Methods for messages
    async def respond(self, event, message):
        if await self.check_for_queue():
            self.SENT_MESSAGES += 1
            await event.respond(message)
        else:
            await self.add_to_queue(event.respond(message))

    # Methods for controlling queues
    async def add_to_queue(self, task):
        self.QUEUE.append(task)

    async def check_for_queue(self):
        if self.SENT_MESSAGES >= self.LIMIT:
            return False
        else:
            return True

    async def periodic_check(self):
        while True:
            await asyncio.sleep(self.INTERVAL / 60)
            self.SENT_MESSAGES = 0
            messages_task = self.QUEUE[:self.LIMIT]
            self.QUEUE = self.QUEUE[self.LIMIT:]
            await asyncio.gather(*messages_task)


@lru_cache
def get_rate_limiting() -> RateLimiting:
    return RateLimiting()
