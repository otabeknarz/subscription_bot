import asyncio
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manager class that manages all tasks in the main loop
    """

    def __init__(self):
        self.tasks = {}

    async def run_task(self, task_id: str, task):
        try:
            logger.info(f"Running task {task}")
            await task
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} has been cancelled.")
        finally:
            self.tasks.pop(task_id)
            logger.info(f"Task {task_id} has been completed.")
            del self.tasks[task_id]

    def add_task(self, bot_id: str, task):
        if bot_id in self.tasks.keys():
            return False
        loop = asyncio.get_running_loop()
        task = loop.create_task(self.run_task(bot_id, task), name=bot_id)
        self.tasks[bot_id] = task
        return True

    def remove_task(self, bot_id: str):
        if bot_id in self.tasks.keys():
            task = self.tasks.pop(bot_id)
            task.cancel()
            logger.info(f"Task {bot_id} has been cancelled.")
            return True
        else:
            return False

    async def run_tasks(self):
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)


@lru_cache
def get_task_manager() -> TaskManager:
    return TaskManager()
