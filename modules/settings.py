from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=str(BASE_DIR / ".env"))


class Settings:
    def __init__(self):
        self.API_ID = os.getenv("API_ID")
        self.API_HASH = os.getenv("API_HASH")

        self.BACKEND_URL = os.getenv("BACKEND_URL")
        self.MAIN_BOT_ID = os.getenv("MAIN_BOT_ID")
        self.MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
        self.MAIN_BOT_USERNAME = os.getenv("MAIN_BOT_USERNAME")

        # URLs
        # API Endpoint
        self.API_ENDPOINT = f"{self.BACKEND_URL}/api/v1/"

        # Telegram getMe url
        self.TELEGRAM_GET_ME = "https://api.telegram.org/bot"

        # Bot URLs
        self.BOTS_URL = f"{self.API_ENDPOINT}bots/"
        self.BOT_ADD_URL = f"{self.API_ENDPOINT}bot/add/"
        self.BOT_UPDATE_URL = f"{self.API_ENDPOINT}bot/update/"

        # Account URLs
        self.ACCOUNT_ADD_URL = f"{self.API_ENDPOINT}account/add/"

        # Channel URLs
        self.CHANNELS_URL = f"{self.API_ENDPOINT}channels/"
        self.CHANNEL_ADD_URL = f"{self.API_ENDPOINT}channel/add/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
