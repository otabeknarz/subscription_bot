import asyncio
import logging
from functools import lru_cache
from typing import Optional

import aiohttp
from telethon import TelegramClient, events

from .task_manager import get_task_manager, TaskManager
from . import handlers
from .redis_connection import get_redis, RedisConnection

# local modules
from .settings import get_settings, Settings
from .state_manager import get_state_manager, StateManager, MainBotStates

# Define global settings
bot_settings: Settings = get_settings()

# Define a global state manager
state: StateManager = get_state_manager()

# Define a global redis client
redis_client: RedisConnection = get_redis()

# Define a global task manager
task_manager: TaskManager = get_task_manager()

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_data(
        self, url: str, params: dict = None
    ) -> tuple[dict, int] | tuple[None, None]:
        """Make GET request to backend"""
        try:
            async with self.session.get(url, params=params) as response:
                return await response.json(), response.status
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None, None

    async def post_data(
        self, url: str, data: dict, params: dict = None
    ) -> tuple[dict, int] | tuple[None, None]:
        """Make POST request to backend"""
        try:
            async with self.session.post(url, params=params, json=data) as response:
                return await response.json(), response.status
        except Exception as e:
            logger.error(f"Error posting data: {str(e)}")
            return None, None

    async def patch_data(
        self, url: str, data: dict, params: dict = None
    ) -> tuple[dict, int] | tuple[None, None]:
        """Make PATCH request to backend"""
        try:
            async with self.session.patch(url, params=params, json=data) as response:
                return await response.json(), response.status
        except Exception as e:
            logger.error(f"Error patching data: {str(e)}")
            return None, None


class Bot:
    """
    Base bot class
    """

    def __init__(
        self,
        id: str,
        token: str,
        username: str,
        client: TelegramClient,
        bot_owner: dict = None,
        is_running: bool = False,
    ):
        self.bot_id: str = id
        self.bot_token: str = token
        self.bot_username: str = username
        self.bot_owner: dict = bot_owner or {"id": None, "name": None, "username": None}
        self.session: Optional[aiohttp.ClientSession] = None
        self.backend: BackendClient = BackendClient()
        self.client: TelegramClient = client
        self.is_running: bool = is_running

    def __str__(self):
        return f"Bot {self.bot_id}"

    def __repr__(self):
        return f"Bot(bot_id={self.bot_id}, bot_token={self.bot_token})"

    def to_dict(self):
        return {
            "id": self.bot_id,
            "token": self.bot_token,
            "username": self.bot_username,
            "owner": self.bot_owner,
            "is_running": self.is_running,
        }

    async def start(self):
        """Start the bot"""
        if not self.session:
            logger.info(f"Initializing session... for bot {self.bot_id}")
            await self.backend.init_session()
        await self.client.start(bot_token=self.bot_token)

        try:
            logger.info(f"Bot {self.bot_id} is running...")
            self.is_running = True
            await self.client.run_until_disconnected()
        finally:
            await self.backend.close_session()


class MainBot(Bot):
    """
    Main bot class that handles all main bot operations
    """

    COMMANDS = {
        "/start": handlers.start_handler,
        "Mening botlarim": handlers.fetch_bots_handler,
        "Mening kanallarim": handlers.fetch_channels_handler,
        "Kanal qo'shish": handlers.enter_channel_id,
        "Bot qo'shish": handlers.enter_bot_token,
        "Bekor qilish": handlers.cancel_handler,
        "Bot larimni boshqarish": handlers.change_bot_status_handler,
    }

    STATE_COMMANDS = {
        # adding channel
        "enter_channel_id": handlers.enter_channel_name,
        "enter_channel_name": handlers.complete_add_channel,
        # adding bot
        "enter_bot_token": handlers.assign_channel_to_bot,
        "assign_channel_to_bot": handlers.complete_add_bot,
    }

    def __init__(self):
        super().__init__(
            id=bot_settings.MAIN_BOT_ID,
            token=bot_settings.MAIN_BOT_TOKEN,
            username=bot_settings.MAIN_BOT_USERNAME,
            client=TelegramClient(
                "sessions/main_session", bot_settings.API_ID, bot_settings.API_HASH
            ),
        )
        self.bots: list[TelegramBot] = []
        self.setup_handlers()

    def setup_handlers(self):
        # handle all messages
        @self.client.on(events.NewMessage())
        async def dispatcher_handler(event):
            state_data = state.get_state_with_data(event.chat.id)
            if not await MainBot.COMMANDS.get(
                event.message.message, handlers.do_nothing
            )(event, self.backend):
                return
            if state_data:
                await MainBot.STATE_COMMANDS.get(
                    state_data.get("state"), handlers.do_nothing
                )(event, self.backend)

        # handle all callbacks
        @self.client.on(events.callbackquery.CallbackQuery())
        async def callback_handler(event: events.callbackquery.CallbackQuery.Event):
            await handlers.handle_callback(event, self.backend)

    async def fetch_bots(self):
        """Fetch all bots from the backend and initialize TelegramBot instances"""
        logger.info("Fetching bots...")
        bots, status_code = await self.backend.fetch_data(bot_settings.BOTS_URL)
        self.bots = [
            TelegramBot(
                bot_id=bot["id"],
                bot_token=bot["token"],
                bot_username=bot["username"],
                bot_owner=bot["owner"],
                is_running=bot["is_running"],
            )
            for bot in bots
        ]
        logger.info(f"Fetched {len(self.bots)} bots.")
        redis_client.set_active_bots(
            [bot.to_dict() for bot in self.bots if bot.is_running]
        )

    async def start_bots(self):
        """Start all initialized TelegramBot instances"""
        # Start main bot
        task_manager.add_task(self.bot_id, self.start())
        # Add all bots to task manager
        for bot in self.bots:
            if bot.is_running:
                task_manager.add_task(bot.bot_id, bot.start())
        # Run all tasks
        await task_manager.run_tasks()

    async def refresh_bots(self):
        """Reload all bots"""
        self.bots = []
        await self.fetch_bots()
        await self.start_bots()

    async def start_main_bot(self):
        await self.backend.init_session()
        try:
            await self.fetch_bots()
        except Exception as e:
            logger.error(f"Error fetching bots: {str(e)}")
        await self.start_bots()

    def get_bot_object(self, bot_id: str):
        return next(bot for bot in self.bots if bot.bot_id == bot_id)


@lru_cache
def get_main_bot() -> MainBot:
    return MainBot()


class TelegramBot(Bot):
    """
    Telegram bot class that handles all telegram bot operations
    """

    def __init__(
        self,
        bot_id: str,
        bot_token: str,
        bot_username: str,
        bot_owner: dict = None,
        is_running: bool = False,
    ):
        super().__init__(
            bot_id,
            bot_token,
            bot_username,
            TelegramClient(
                f"sessions/bot_session_{bot_id}_{bot_username}",
                bot_settings.API_ID,
                bot_settings.API_HASH,
            ),
            bot_owner,
            is_running,
        )
        self.setup_handlers()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(pattern="/start"))
        async def start_handler(event):
            await event.respond("Welcome! Bot is running with async backend support.")

        @self.client.on(events.NewMessage(pattern="salom"))
        async def fetch_handler(event):
            # Example of async backend request while handling telegram message
            await event.respond("Salom qalaysan")

        @self.client.on(events.NewMessage(pattern="token"))
        async def send_token(event):
            # Example of async backend request while handling telegram message
            await event.respond(f"Token: <code>{self.bot_token}</code>")

        @self.client.on(events.NewMessage(pattern="sleep"))
        async def sleep_handler(event):
            await event.respond("Sleeping for 10 seconds...")
            await asyncio.sleep(10)
            await event.respond("Slept for 10 seconds")

    # async def periodic_task(self, interval: int = 60):
    #     """Example of periodic background task"""
    #     while True:
    #         try:
    #             # Make periodic backend request
    #             data = await self.backend.fetch_data('/api/status')
    #             logger.info(f"Periodic task data: {data}")
    #             await asyncio.sleep(interval)
    #         except Exception as e:
    #             logger.error(f"Error in periodic task: {str(e)}")
    #             await asyncio.sleep(5)  # Short sleep on error
