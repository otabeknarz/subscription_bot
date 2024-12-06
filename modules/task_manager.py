import asyncio
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manager class that manages all tasks in the main loop
    """

    # Task groups
    BOTS: str = "BOTS"
    RATE_LIMITER: str = "RL"

    def __init__(self):
        self.tasks: dict = {
            self.RATE_LIMITER: {},
            self.BOTS: {},
        }

    async def run_task(self, task_id: str, task_group: str, task):
        try:
            logger.info(f"Running task {task}")
            await task
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} has been cancelled.")
        finally:
            self.tasks.get(task_group).pop(task_id)
            logger.info(f"Task {task_id} has been completed.")

    def add_task(self, task_id: str, task_group: str, task_obj):
        if task_id in self.tasks.get(task_group).keys():
            return False
        loop = asyncio.get_running_loop()
        task = loop.create_task(self.run_task(task_id, task_group, task_obj), name=task_id)
        self.tasks.get(task_group)[task_id] = task
        return True

    def remove_task(self, task_id: str, task_group: str):
        if task_id in self.tasks.get(task_group).keys():
            task = self.tasks.get(task_group).get(task_id)
            task.cancel()
            logger.info(f"Task {task_id} has been cancelled.")
            return True
        else:
            return False

    async def run_tasks_in_task_group(self, task_group: str):
        await asyncio.gather(
            *self.tasks.get(task_group).values(), return_exceptions=True
        )

    async def run_all_tasks_in_main_loop(self):
        all_tasks = []
        for value in self.tasks.values():
            for task in value.values():
                all_tasks.append(task)
        await asyncio.gather(
            *all_tasks, return_exceptions=True
        )


@lru_cache
def get_task_manager() -> TaskManager:
    return TaskManager()
