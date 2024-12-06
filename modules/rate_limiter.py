import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, bot_id: str, bot_username: str):
        self.LIMIT: int = 25
        self.INTERVAL: int = 1000  # in milliseconds
        self.QUEUE: list = []
        self.SENT_MESSAGES: int = 0
        self.bot_id: str = bot_id
        self.bot_username: str = bot_username
        self.ALL_SENT_MESSAGES: int = 0

    def __str__(self):
        return f"Rate limiter for bot @{self.bot_username}"

    def __repr__(self):
        return f"RateLimiter(bot_id={self.bot_id}, bot_username={self.bot_username}, sent_messages={self.SENT_MESSAGES}, queue_length={len(self.QUEUE)})"

    def __len__(self):
        """Return the length of the messages queue"""
        return len(self.QUEUE)

    # Methods for messages
    async def respond(self, event, *args, **kwargs):
        rate_limiter = get_rate_limiter_from_memory(self.bot_id, self.bot_username)
        if await rate_limiter.check_for_queue():
            rate_limiter.SENT_MESSAGES += 1
            rate_limiter.ALL_SENT_MESSAGES += 1
            await event.respond(*args, **kwargs)
        else:
            await rate_limiter.add_to_queue(event.respond(*args, **kwargs))

    async def delete(self, event, *args, **kwargs):
        rate_limiter = get_rate_limiter_from_memory(self.bot_id, self.bot_username)
        if await rate_limiter.check_for_queue():
            rate_limiter.SENT_MESSAGES += 1
            rate_limiter.ALL_SENT_MESSAGES += 1
            await event.delete(*args, **kwargs)
        else:
            await rate_limiter.add_to_queue(event.delete(*args, **kwargs))

    # Methods for controlling queues
    async def add_to_queue(self, task):
        rate_limiter = get_rate_limiter_from_memory(self.bot_id, self.bot_username)
        rate_limiter.QUEUE.append(task)

    async def check_for_queue(self):
        rate_limiter = get_rate_limiter_from_memory(self.bot_id, self.bot_username)
        if rate_limiter.SENT_MESSAGES >= rate_limiter.LIMIT:
            return False
        else:
            return True

    async def periodic_check(self):
        rate_limiter = get_rate_limiter_from_memory(self.bot_id, self.bot_username)
        while True:
            await asyncio.sleep(rate_limiter.INTERVAL / 1000)
            rate_limiter.SENT_MESSAGES = 0
            messages_task = rate_limiter.QUEUE[:rate_limiter.LIMIT]
            rate_limiter.QUEUE = rate_limiter.QUEUE[rate_limiter.LIMIT:]
            for message_task in messages_task:
                await message_task


@lru_cache
def get_rate_limiter_from_memory(bot_id: str, bot_username: str) -> RateLimiter:
    """
    Get rate limiter from memory, every bot has own rate limiter instance in memory
    """
    return RateLimiter(bot_id, bot_username)
